#!/usr/bin/env python3
"""Local review bookkeeping only: never edits notes or sends email."""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import uuid

import yaml

import configuration

DEFAULT_CONFIG = configuration.DEFAULT_CONFIG
ALLOWED = {'Inbox', 'Projects', 'People', 'Knowledge', 'Decisions', 'Preferences'}


def digest(value):
    if not isinstance(value, bytes):
        value = json.dumps(value, sort_keys=True, ensure_ascii=False).encode()
    return hashlib.sha256(value).hexdigest()


def atomic(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, name = tempfile.mkstemp(dir=path.parent, prefix='.pending-')
    try:
        with os.fdopen(fd, 'w') as out:
            json.dump(value, out, ensure_ascii=False, indent=2)
            out.write('\n')
            out.flush()
            os.fsync(out.fileno())
        os.replace(name, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class Queue:
    def __init__(self, config):
        self.cfg = configuration.load(config)
        self.project = self.cfg['project']
        self.notifications = self.cfg.get('notifications', {'enabled': False})
        self.root = Path(self.cfg['root']).resolve(strict=True)
        self.home = Path(self.cfg['state_dir']).resolve()
        if self.home == self.root or self.root in self.home.parents:
            raise ValueError('STATE_MUST_BE_OUTSIDE_BRAIN')
        self.home.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.home, 0o700)
        self.state_path = self.home / 'state.json'

    @contextlib.contextmanager
    def locked(self):
        with (self.home / 'queue.lock').open('a+') as lock:
            os.chmod(self.home / 'queue.lock', 0o600)
            fcntl.flock(lock, fcntl.LOCK_EX)
            state = json.loads(self.state_path.read_text()) if self.state_path.exists() else {
                'version': 1, 'processed': {}, 'issues': {}, 'events': {}, 'active': None,
                'last_success': None, 'runs': [], 'project': self.project, 'root': str(self.root)}
            if state.get('project') != self.project or state.get('root') != str(self.root):
                raise ValueError('STATE_BELONGS_TO_DIFFERENT_PROJECT_OR_ROOT')
            yield state
            atomic(self.state_path, state)

    def source(self, relative):
        p = Path(relative)
        if p.is_absolute() or '..' in p.parts or not p.parts:
            raise ValueError('INVALID_SOURCE_PATH')
        full = self.root / p
        resolved = full.resolve(strict=True)
        if self.root not in resolved.parents or any(part.is_symlink() for part in [full, *full.parents] if part != self.root and self.root in part.parents):
            raise ValueError('SOURCE_OUTSIDE_PROJECT_OR_SYMLINK')
        return full

    def scan(self):
        result = []
        for folder in sorted(ALLOWED):
            base = self.root / folder
            if not base.exists():
                continue
            if base.is_symlink():
                raise ValueError('SYMLINK_FOLDER')
            for current, dirs, files in os.walk(base, followlinks=False):
                dirs[:] = sorted(d for d in dirs if not d.startswith('.') and not (Path(current) / d).is_symlink())
                for name in sorted(files):
                    if not name.endswith('.md') or name.startswith('.'):
                        continue
                    p = Path(current) / name
                    if p.is_symlink():
                        continue
                    relative = p.relative_to(self.root).as_posix()
                    raw = self.source(relative).read_bytes()
                    text = raw.decode('utf-8')
                    meta = {}
                    if text.startswith('---\n'):
                        pieces = text.split('\n---', 1)
                        if len(pieces) != 2:
                            raise ValueError('MALFORMED_FRONTMATTER:' + relative)
                        meta = yaml.safe_load(pieces[0][4:]) or {}
                        if not isinstance(meta, dict):
                            raise ValueError('INVALID_FRONTMATTER:' + relative)
                    if meta.get('verification_only') is True or meta.get('status') == 'test_fixture':
                        continue
                    result.append({'path': relative, 'sha256': digest(raw), 'bytes': len(raw),
                                   'title': str(meta.get('title', p.stem))})
        return result

    def event(self, state, kind, details, report=None):
        key = 'mail-' + digest([kind, details])[:16]
        if key not in state['events']:
            state['events'][key] = {'id': key, 'kind': kind, 'details': details,
                'report': report, 'status': 'pending', 'attempts': 0,
                'created': time.time()}
            if not self.notifications.get('enabled', False):
                state['events'][key]['status'] = 'local_only'
        return key if state['events'][key]['status'] != 'local_only' else None

    def require_run(self, state, run_id):
        run = state.get('active')
        if not run or run['id'] != run_id or run['expires'] <= time.time():
            raise ValueError('RUN_NOT_ACTIVE_OR_LEASE_EXPIRED')
        return run

    def begin(self, limit):
        if not 1 <= limit <= 25:
            raise ValueError('LIMIT_OUT_OF_RANGE')
        with self.locked() as state:
            now = time.time()
            if state['active'] and state['active']['expires'] > now:
                return {'status': 'busy', 'run_id': state['active']['id']}
            if state['active'] and state['active'].get('kind') == 'archive':
                return {'status': 'archive_recovery_required', 'plan_id': state['active']['id']}
            if state['active']:
                self.event(state, 'failure', {'code': 'expired-run', 'run_id': state['active']['id']})
                state['active'] = None
            candidates = [s for s in self.scan() if state['processed'].get(s['path']) != s['sha256']]
            if not candidates:
                return {'status': 'idle', 'pending_emails': self.pending(state), 'open_issues': self.open_ids(state)}
            selected = candidates[:limit]
            run_id = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6]
            run = {'id': run_id, 'started': now, 'expires': now + self.cfg.get('lease_seconds', 3600),
                   'candidates': selected}
            state['active'] = run
            atomic(self.home / 'runs' / (run_id + '-manifest.json'), run)
            return {'status': 'ready', 'run_id': run_id, 'remaining': len(candidates) - len(selected),
                    'candidates': selected, 'open_issues': self.open_ids(state)}

    @staticmethod
    def pending(state):
        return [e for e in state['events'].values() if e['status'] not in {'sent', 'local_only'}]

    @staticmethod
    def open_ids(state):
        return [{'id': i['id'], 'key': i['key'], 'kind': i['kind'], 'summary': i['summary']}
                for i in state['issues'].values() if i['status'] == 'open']

    def finish(self, run_id, review_file, report):
        review = json.loads(Path(review_file).read_text())
        prefix = self.project + '/reviews/consolidation/'
        if not report.startswith(prefix):
            raise ValueError('INVALID_REPORT_PERMALINK')
        with self.locked() as state:
            run = self.require_run(state, run_id)
            expected = {s['path']: s['sha256'] for s in run['candidates']}
            reviewed = review.get('reviewed', [])
            if len(reviewed) != len(expected) or {r['path']: r['sha256'] for r in reviewed} != expected:
                raise ValueError('INCOMPLETE_OR_MISMATCHED_REVIEW')
            for r in reviewed:
                if r.get('outcome') not in {'no_action', 'review'} or not r.get('reason'):
                    raise ValueError('INVALID_REVIEW_OUTCOME')
            for path, checksum in expected.items():
                if digest(self.source(path).read_bytes()) != checksum:
                    raise ValueError('SOURCE_CHANGED_REVIEW_AGAIN:' + path)
            changed = []
            seen_keys = set()
            reviewed_issue_paths = set()
            for issue in review.get('issues', []):
                key = issue['key']
                if key in seen_keys or not key.strip() or len(key) > 200:
                    raise ValueError('INVALID_OR_DUPLICATE_ISSUE_KEY')
                seen_keys.add(key)
                if issue.get('kind') not in {'proposal', 'conflict'} or not issue.get('summary') or not issue.get('sources'):
                    raise ValueError('INVALID_ISSUE')
                for src in issue['sources']:
                    if digest(self.source(src['path']).read_bytes()) != src['sha256']:
                        raise ValueError('ISSUE_SOURCE_CHANGED:' + src['path'])
                    reviewed_issue_paths.add(src['path'])
                proposal = issue.get('proposal')
                if proposal:
                    if not proposal.get('change') or not proposal.get('status'):
                        raise ValueError('PROPOSAL_REQUIRES_CHANGE_AND_STATUS')
                    target = proposal['target']
                    target_path = Path(target)
                    resolved = (self.root / target_path).resolve()
                    if target_path.is_absolute() or '..' in target_path.parts or self.root not in resolved.parents:
                        raise ValueError('INVALID_PROPOSAL_TARGET')
                    if proposal['expected_checksum'] is None:
                        if resolved.exists():
                            raise ValueError('PROPOSAL_TARGET_ALREADY_EXISTS:' + target)
                    elif digest(self.source(target).read_bytes()) != proposal['expected_checksum']:
                        raise ValueError('PROPOSAL_TARGET_CHANGED:' + target)
                ident = 'review-' + digest(key)[:12]
                semantic = {k: issue[k] for k in ['key', 'kind', 'summary']}
                if proposal:
                    semantic['proposal'] = {k: proposal[k] for k in ['target', 'change', 'status']}
                fingerprint = digest(semantic)
                old = state['issues'].get(ident)
                if old and old['fingerprint'] == fingerprint:
                    old.update(sources=issue['sources'], report=report, updated=time.time())
                    if proposal:
                        old['proposal'] = proposal
                    continue
                record = {**issue, 'id': ident, 'fingerprint': fingerprint, 'status': 'open',
                          'report': report, 'run_id': run_id, 'updated': time.time()}
                if old:
                    record['previous'] = {k: old[k] for k in ['fingerprint', 'status', 'report']}
                state['issues'][ident] = record
                changed.append({'id': ident, 'fingerprint': fingerprint, 'kind': issue['kind']})
            if any(r['outcome'] == 'review' and r['path'] not in reviewed_issue_paths for r in reviewed):
                raise ValueError('REVIEW_OUTCOME_WITHOUT_ISSUE')
            # Each revision is marked reviewed, not approved or merged. Notes stay untouched.
            state['processed'].update(expected)
            records = state.setdefault('reviewed', {})
            for r in reviewed:
                records[r['path']] = {'sha256': r['sha256'], 'outcome': r['outcome'],
                                      'reason': r['reason'], 'reviewed_at': time.time()}
            state['last_success'] = time.time()
            completed = {'id': run_id, 'report': report, 'reviewed_count': len(reviewed),
                         'changed_issues': changed, 'finished': state['last_success']}
            state['runs'] = (state['runs'] + [completed])[-100:]
            state['active'] = None
            atomic(self.home / 'runs' / (run_id + '-review.json'), review)
            event = self.event(state, 'review', changed, report) if changed else None
            return {'status': 'completed', **completed, 'email_event': event,
                    'open_issues': self.open_ids(state)}

    def abort(self, run_id, reason):
        with self.locked() as state:
            run = self.require_run(state, run_id)
            if run.get('kind') == 'archive':
                raise ValueError('ARCHIVE_REQUIRES_RECOVERY_NOT_ABORT')
            state['active'] = None
            return {'status': 'aborted', 'email_event': self.event(state, 'failure', {'code': reason})}

    def renew(self, run_id):
        with self.locked() as state:
            run = self.require_run(state, run_id)
            run['expires'] = time.time() + self.cfg.get('lease_seconds', 3600)
            return {'status': 'renewed', 'expires': run['expires']}

    def claim(self):
        with self.locked() as state:
            if not self.notifications.get('enabled', False):
                return {'status': 'disabled', 'pending_events': len(self.pending(state))}
            uncertain = [e for e in self.pending(state) if e['status'] in {'reserved', 'uncertain', 'blocked'}]
            if uncertain:
                return {'status': 'reconcile_before_sending', 'events': uncertain}
            pending = [e for e in self.pending(state) if e['status'] == 'pending']
            if not pending:
                return {'status': 'none'}
            event = min(pending, key=lambda e: e['created'])
            event['status'] = 'reserved'
            event['attempts'] += 1
            event['claimed'] = time.time()
            return {'status': 'send', 'recipient': self.notifications['recipient'], 'provider': self.notifications['provider'], 'thread_url': self.notifications.get('thread_url'), 'event': event}

    def sent(self, event_id, message_id):
        with self.locked() as state:
            e = state['events'][event_id]
            if e['status'] not in {'reserved', 'uncertain'} or not message_id.strip():
                raise ValueError('INVALID_MAIL_ACK')
            e.update(status='sent', message_id=message_id, sent=time.time())
            return {'status': 'sent', 'event_id': event_id}

    def mail_failure(self, event_id, certainty):
        with self.locked() as state:
            e = state['events'][event_id]
            if e['status'] not in {'reserved', 'uncertain'}:
                raise ValueError('INVALID_MAIL_FAILURE_STATE')
            e['status'] = 'uncertain' if certainty == 'unknown' else ('blocked' if e['attempts'] >= 3 else 'pending')
            return {'status': e['status'], 'event_id': event_id}

    def resolve(self, issue_id, reason):
        with self.locked() as state:
            state['issues'][issue_id].update(status='resolved', resolution=reason, resolved=time.time())
            return {'status': 'resolved', 'issue_id': issue_id}

    def status(self):
        with self.locked() as state:
            return {'active': state['active'], 'last_success': state['last_success'],
                    'processed_revisions': len(state['processed']), 'open_issues': self.open_ids(state),
                    'pending_emails': self.pending(state)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default=str(DEFAULT_CONFIG))
    sub = p.add_subparsers(dest='command', required=True)
    b = sub.add_parser('begin'); b.add_argument('--limit', type=int, default=25)
    f = sub.add_parser('finish'); f.add_argument('--run', required=True); f.add_argument('--review', required=True); f.add_argument('--report', required=True)
    a = sub.add_parser('abort'); a.add_argument('--run', required=True); a.add_argument('--reason', required=True)
    r = sub.add_parser('renew'); r.add_argument('--run', required=True)
    sub.add_parser('status'); sub.add_parser('notify-claim')
    s = sub.add_parser('notify-sent'); s.add_argument('--event', required=True); s.add_argument('--message-id', required=True)
    e = sub.add_parser('notify-failed'); e.add_argument('--event', required=True); e.add_argument('--certainty', choices=['not-sent', 'unknown'], required=True)
    v = sub.add_parser('resolve'); v.add_argument('--issue', required=True); v.add_argument('--reason', required=True)
    args = p.parse_args()
    q = Queue(args.config)
    if args.command == 'begin':
        if not 1 <= args.limit <= 25:
            raise ValueError('LIMIT_OUT_OF_RANGE')
        result = q.begin(args.limit)
    elif args.command == 'finish': result = q.finish(args.run, args.review, args.report)
    elif args.command == 'abort': result = q.abort(args.run, args.reason)
    elif args.command == 'renew': result = q.renew(args.run)
    elif args.command == 'status': result = q.status()
    elif args.command == 'notify-claim': result = q.claim()
    elif args.command == 'notify-sent': result = q.sent(args.event, args.message_id)
    elif args.command == 'notify-failed': result = q.mail_failure(args.event, args.certainty)
    elif args.command == 'resolve': result = q.resolve(args.issue, args.reason)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'status': 'error', 'error': str(exc), 'error_type': type(exc).__name__}))
        sys.exit(1)

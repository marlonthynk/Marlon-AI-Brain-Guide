#!/usr/bin/env python3
"""Snapshot and archive planning. Note moves are performed by Basic Memory MCP."""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import uuid
from zoneinfo import ZoneInfo

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

spec = importlib.util.spec_from_file_location('brain_queue', Path(__file__).with_name('queue.py'))
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def meta(raw):
    text = raw.decode('utf-8')
    if not text.startswith('---\n'):
        return {}
    value = yaml.safe_load(text.split('\n---', 1)[0][4:]) or {}
    if not isinstance(value, dict):
        raise ValueError('INVALID_FRONTMATTER')
    return value


class Archive:
    def __init__(self, config):
        self.q = queue.Queue(config)
        self.cfg = self.q.cfg.get('archive', {})
        self.backups = Path(self.cfg.get('backup_dir', str(Path.home()/'.local/share/ai-brain-backups'))).resolve()
        if self.backups == self.q.root or self.q.root in self.backups.parents:
            raise ValueError('BACKUP_MUST_BE_OUTSIDE_BRAIN')
        if self.cfg.get('synced_vault'):
            vault = Path(self.cfg['synced_vault']).resolve()
            if self.backups == vault or vault in self.backups.parents:
                raise ValueError('BACKUP_MUST_BE_OUTSIDE_SYNCED_VAULT')
        self.plans = self.q.home / 'archive-plans'
        self.plans.mkdir(exist_ok=True, mode=0o700)

    def plan_file(self, ident):
        if Path(ident).name != ident or not ident.startswith('archive-'):
            raise ValueError('INVALID_PLAN_ID')
        return self.plans / (ident + '.json')

    @staticmethod
    def files(root):
        results = {}
        for current, dirs, files in os.walk(root, followlinks=False):
            for name in dirs + files:
                if (Path(current) / name).is_symlink():
                    raise ValueError('SNAPSHOT_REFUSES_SYMLINK')
            dirs.sort()
            for name in sorted(files):
                p = Path(current) / name
                if p.is_file(): results[p.relative_to(root).as_posix()] = p
        return results

    def snapshot(self, label):
        self.backups.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.backups, 0o700)
        ident = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8]
        temp = self.backups / ('.pending-' + ident)
        final = self.backups / ident
        temp.mkdir(mode=0o700)
        entries = {}
        sources = {'brain': self.q.root}
        # Only the specific worker/config/schedule, never harness auth or global credentials.
        for name, path in self.cfg.get('support_paths', {}).items():
            if not name.replace('-', '').isalnum(): raise ValueError('INVALID_BACKUP_LABEL')
            sources['support/' + name] = Path(path).expanduser().resolve(strict=True)
        try:
            inventories = {}
            for namespace, root in sources.items():
                inventory = self.files(root) if root.is_dir() else {root.name: root}
                inventories[namespace] = inventory
                for relative, src in inventory.items():
                    raw = src.read_bytes()
                    stat = src.stat()
                    key = namespace + '/' + relative
                    dest = temp / key
                    dest.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                    with dest.open('xb') as out:
                        out.write(raw); out.flush(); os.fsync(out.fileno())
                    os.chmod(dest, 0o600)
                    entries[key] = {'sha256': sha(raw), 'bytes': len(raw), 'mtime_ns': stat.st_mtime_ns}
            # Reject a torn snapshot if any source changed or appeared/disappeared during copying.
            for namespace, root in sources.items():
                inventory = self.files(root) if root.is_dir() else {root.name: root}
                if set(inventory) != set(inventories[namespace]): raise ValueError('SNAPSHOT_SOURCE_SET_CHANGED')
                for relative, src in inventory.items():
                    if sha(src.read_bytes()) != entries[namespace + '/' + relative]['sha256']:
                        raise ValueError('SNAPSHOT_SOURCE_CHANGED')
            manifest = {'version': 1, 'id': ident, 'created': time.time(), 'label': label,
                        'project': self.q.project, 'root': str(self.q.root), 'entries': entries}
            queue.atomic(temp/'manifest.json', manifest)
            os.rename(temp, final)
            return {'snapshot': str(final), 'id': ident, 'files': len(entries), 'verified': self.verify(final)['verified']}
        except Exception:
            # Failed incomplete copies remain clearly marked, never used for restore or moves.
            raise

    def verify(self, snapshot):
        path = Path(snapshot).resolve(strict=True)
        if path.parent != self.backups or path.name.startswith('.'):
            raise ValueError('INVALID_SNAPSHOT_LOCATION')
        manifest = json.loads((path/'manifest.json').read_text())
        if manifest.get('project') != self.q.project or manifest.get('root') != str(self.q.root):
            raise ValueError('SNAPSHOT_BELONGS_TO_DIFFERENT_PROJECT_OR_ROOT')
        for key, info in manifest['entries'].items():
            p = path / key
            if Path(key).is_absolute() or '..' in Path(key).parts or path not in p.resolve().parents or p.is_symlink():
                raise ValueError('UNSAFE_SNAPSHOT_PATH')
            if sha(p.read_bytes()) != info['sha256']:
                raise ValueError('SNAPSHOT_CHECKSUM_MISMATCH:' + key)
        return {'verified': True, 'snapshot': str(path), 'files': len(manifest['entries'])}

    def restore(self, snapshot, destination):
        self.verify(snapshot)
        dest = Path(destination).resolve()
        for protected in (self.q.root, self.q.home, self.backups):
            if dest == protected or protected in dest.parents or dest in protected.parents:
                raise ValueError('RESTORE_MUST_BE_OUTSIDE_LIVE_BRAIN_STATE_AND_BACKUPS')
        if dest.exists(): raise ValueError('RESTORE_DESTINATION_MUST_NOT_EXIST')
        manifest = json.loads((Path(snapshot)/'manifest.json').read_text())
        dest.mkdir(parents=True, mode=0o700)
        for key, info in manifest['entries'].items():
            target = dest / key
            target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
            with target.open('xb') as out:
                out.write((Path(snapshot)/key).read_bytes())
                out.flush(); os.fsync(out.fileno())
            os.chmod(target, 0o600)
            os.utime(target, ns=(info['mtime_ns'], info['mtime_ns']))
            if sha(target.read_bytes()) != info['sha256']: raise ValueError('RESTORE_VERIFY_FAILED')
        return {'restored_to': str(dest), 'files': len(manifest['entries']), 'verified': True, 'live_notes_changed': False}

    def week_due(self, state, now):
        if not self.cfg.get('enabled', False):
            return False, None
        zone = ZoneInfo(self.q.cfg.get('timezone', 'UTC'))
        local = dt.datetime.fromtimestamp(now, zone)
        start = dt.datetime.fromisoformat(self.cfg['start_at']).replace(tzinfo=zone)
        day = queue.configuration.DAYS.index(self.cfg.get('weekday', 'Friday'))
        hour, minute = map(int, self.cfg.get('time', '09:00').split(':'))
        slot = (local-dt.timedelta(days=(local.weekday()-day)%7)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        if slot > local: slot -= dt.timedelta(days=7)
        key = slot.date().isoformat()
        return slot >= start and state.get('archive', {}).get('last_week') != key, key

    def review_record(self, state, path, checksum):
        record = state.get('reviewed', {}).get(path)
        if record and record['sha256'] == checksum: return record
        for run in reversed(state.get('runs', [])):
            p = self.q.home/'runs'/(run['id']+'-review.json')
            if p.exists():
                for r in json.loads(p.read_text()).get('reviewed', []):
                    if r['path'] == path and r['sha256'] == checksum: return r
        return None

    def eligibility(self, state, p, now):
        relative = p.relative_to(self.q.root).as_posix()
        raw = self.q.source(relative).read_bytes()
        checksum = sha(raw)
        m = meta(raw)
        if m.get('verification_only') is True or m.get('status') == 'test_fixture': return None, 'verification fixture'
        if now-p.stat().st_mtime < 7*86400: return None, 'changed within seven days'
        if state['processed'].get(relative) != checksum: return None, 'current revision not reviewed'
        record = self.review_record(state, relative, checksum)
        if not record: return None, 'missing review outcome evidence'
        linked = [i for i in state['issues'].values() if any(s['path'] == relative for s in i.get('sources', [])) or i.get('proposal', {}).get('target') == relative]
        if any(i['status'] != 'resolved' for i in linked): return None, 'unresolved review item'
        if record['outcome'] == 'review' and not linked: return None, 'review disposition not recorded'
        clearance = state.get('archive', {}).get('clearances', {}).get(relative)
        if not clearance or clearance['sha256'] != checksum: return None, 'completion clearance needed'
        if relative.startswith('Inbox/Sessions/') and not clearance.get('session_closed_evidence'):
            return None, 'session completion not confirmed'
        if not m.get('permalink'): return None, 'stable permalink missing'
        category = 'Sessions' if relative.startswith('Inbox/Sessions/') else 'Captures'
        parts = Path(relative).parts
        tail = Path(*parts[2:]) if len(parts)>2 and parts[1] in {'Sessions','Captures'} else Path(*parts[1:])
        month = dt.datetime.fromtimestamp(now, ZoneInfo(self.q.cfg.get('timezone', 'UTC'))).strftime('%Y/%m')
        destination = (Path('Archive')/category/month/tail).as_posix()
        target = self.q.root/destination
        if self.q.root not in target.resolve().parents or any(p.is_symlink() for p in [target,*target.parents] if self.q.root in p.parents):
            raise ValueError('UNSAFE_ARCHIVE_DESTINATION')
        if (self.q.root/destination).exists(): return None, 'archive destination already exists'
        return {'source': relative, 'destination': destination, 'sha256': checksum,
                'permalink': m['permalink'], 'title': str(m.get('title',p.stem)),
                'reason': clearance['reason'], 'status': 'pending'}, None

    def clear(self, path, reason, session_closed_evidence):
        if not path.startswith('Inbox/') or not reason.strip(): raise ValueError('INVALID_CLEARANCE')
        raw = self.q.source(path).read_bytes()
        with self.q.locked() as state:
            if state.get('active'): raise ValueError('ANOTHER_RUN_ACTIVE')
            if state['processed'].get(path) != sha(raw): raise ValueError('REVISION_NOT_REVIEWED')
            if path.startswith('Inbox/Sessions/') and not session_closed_evidence:
                raise ValueError('SESSION_CLOSURE_EVIDENCE_REQUIRED')
            state.setdefault('archive', {}).setdefault('clearances', {})[path] = {
                'sha256': sha(raw), 'reason': reason, 'session_closed_evidence': session_closed_evidence,
                'cleared_at': time.time()}
        return {'status': 'cleared_for_preview', 'path': path}

    def plan(self, force=False):
        if not self.cfg.get('enabled', False) and not force:
            return {'status': 'disabled'}
        with self.q.locked() as state:
            if state.get('active'): return {'status': 'busy', 'active': state['active']['id']}
            now = time.time()
            due, week = self.week_due(state, now)
            if not due and not force: return {'status': 'not_due', 'last_due_slot': week}
            items, kept = [], []
            for p in sorted((self.q.root/'Inbox').rglob('*.md')):
                item, reason = self.eligibility(state,p,now)
                if item: items.append(item)
                else: kept.append({'path':p.relative_to(self.q.root).as_posix(),'reason':reason})
            ident = 'archive-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]
            plan = {'id':ident,'created':now,'week':week if due else None,'status':'preview',
                    'items':items,'kept':kept,'automatic_enabled':state.get('archive',{}).get('automatic_enabled',False)}
            queue.atomic(self.plan_file(ident),plan)
            return plan

    def record_preview(self, ident, report):
        if not report.startswith(self.q.project + '/reviews/'): raise ValueError('INVALID_REPORT')
        plan = json.loads(self.plan_file(ident).read_text())
        if plan['status'] != 'preview': raise ValueError('NOT_A_PREVIEW')
        with self.q.locked() as state:
            if state.get('active'): raise ValueError('ANOTHER_RUN_ACTIVE')
            archive = state.setdefault('archive', {})
            if plan['week'] and (not plan['items'] or not archive.get('automatic_enabled',False)):
                archive['last_week']=plan['week']
            archive['last_preview']=ident
            plan['report']=report
            event=None
            if plan['items'] and not archive.get('automatic_enabled',False):
                event=self.q.event(state,'archive_review', [{'source':i['source'],'sha256':i['sha256'],'destination':i['destination']} for i in plan['items']], report)
            queue.atomic(self.plan_file(ident),plan)
            return {'status':'preview_recorded','plan_id':ident,'eligible':len(plan['items']),'kept':len(plan['kept']),'email_event':event}

    def claim(self, ident, approval):
        if not self.cfg.get('enabled', False):
            raise ValueError('ARCHIVE_DISABLED')
        with self.q.locked() as state:
            if state.get('active'): raise ValueError('ANOTHER_RUN_ACTIVE')
            plan=json.loads(self.plan_file(ident).read_text())
            if plan['status']!='preview' or not plan['items']: raise ValueError('NO_UNEXECUTED_ITEMS')
            if not approval and not state.get('archive',{}).get('automatic_enabled',False): raise ValueError('FIRST_BATCH_REQUIRES_APPROVAL')
            for item in plan['items']:
                current,reason=self.eligibility(state,self.q.root/item['source'],time.time())
                if reason or current['sha256']!=item['sha256'] or current['destination']!=item['destination']:
                    raise ValueError('PREVIEW_STALE:'+str(reason))
            plan.update(status='claimed',approval=approval)
            queue.atomic(self.plan_file(ident),plan)
            state['active']={'id':ident,'kind':'archive','expires':time.time()+3600}
        try:
            snapshot=self.snapshot('before '+ident)
            plan['snapshot']=snapshot['snapshot']
            queue.atomic(self.plan_file(ident),plan)
            return {'status':'claimed','plan':plan,'snapshot':snapshot}
        except Exception:
            # No move is authorised until a verified snapshot exists. Preserve lease for explicit recovery.
            raise

    def check_item(self, ident, index):
        with self.q.locked() as state:
            self.q.require_run(state,ident)
            plan=json.loads(self.plan_file(ident).read_text())
            if 'snapshot' not in plan: raise ValueError('VERIFIED_SNAPSHOT_REQUIRED')
            self.verify(plan['snapshot'])
            if not 0 <= index < len(plan['items']): raise ValueError('INVALID_ITEM_INDEX')
            item=plan['items'][index]
            src=self.q.root/item['source']; dest=self.q.root/item['destination']
            if not src.exists() and dest.exists():
                raw=dest.read_bytes()
                if sha(raw)!=item['sha256'] or meta(raw).get('permalink')!=item['permalink']:
                    raise ValueError('MOVED_NOTE_CHANGED_REVIEW_REQUIRED')
                item['status']='moved'
                queue.atomic(self.plan_file(ident),plan)
                return {'status':'already_moved','item':item}
            current,reason=self.eligibility(state,src,time.time())
            if reason or current['sha256']!=item['sha256']: raise ValueError('SOURCE_NO_LONGER_ELIGIBLE:'+str(reason))
            if dest.exists(): raise ValueError('DESTINATION_EXISTS')
            return {'status':'ready_for_mcp_move','item':item}

    def complete(self, ident):
        plan=json.loads(self.plan_file(ident).read_text())
        for index in range(len(plan['items'])):
            if self.check_item(ident,index)['status']!='already_moved': raise ValueError('MOVES_INCOMPLETE')
        with self.q.locked() as state:
            self.q.require_run(state,ident)
            plan=json.loads(self.plan_file(ident).read_text())
            plan.update(status='complete',completed=time.time())
            queue.atomic(self.plan_file(ident),plan)
            a=state.setdefault('archive',{})
            a['last_completed']=ident
            if plan['week']: a['last_week']=plan['week']
            state['active']=None
            for item in plan['items']:
                state['processed'].pop(item['source'],None)
                state.get('reviewed',{}).pop(item['source'],None)
                a.get('clearances',{}).pop(item['source'],None)
            return {'status':'complete','moved':len(plan['items']),'plan_id':ident}

    def recover(self, ident):
        with self.q.locked() as state:
            active=state.get('active')
            if not active or active.get('kind')!='archive' or active['id']!=ident: raise ValueError('NO_MATCHING_ARCHIVE_LEASE')
            if active['expires']>time.time(): raise ValueError('LEASE_STILL_ACTIVE_DO_NOT_TAKE_OVER')
            active['expires']=time.time()+3600
        plan=json.loads(self.plan_file(ident).read_text())
        if 'snapshot' not in plan:
            # Claim failed before backup, so every original must still be intact.
            for item in plan['items']:
                if (self.q.root/item['destination']).exists() or sha(self.q.source(item['source']).read_bytes()) != item['sha256']:
                    raise ValueError('PRE_BACKUP_STATE_CHANGED_REVIEW_REQUIRED')
            plan['snapshot']=self.snapshot('recovery before '+ident)['snapshot']
            queue.atomic(self.plan_file(ident),plan)
        return {'status':'recovery_claimed','plan_id':ident,'next':'Run check-item for each entry; never repeat a verified completed move.'}

    def failure(self, ident, reason):
        with self.q.locked() as state:
            active=state.get('active')
            if active and (active.get('kind')!='archive' or active['id']!=ident):
                raise ValueError('ANOTHER_RUN_ACTIVE')
            event=self.q.event(state,'failure',{'code':reason,'archive_plan':ident})
            return {'status':'failure_recorded','email_event':event,'lease_preserved':bool(active)}

    def enable(self, approval):
        with self.q.locked() as state:
            if state.get('active'): raise ValueError('ANOTHER_RUN_ACTIVE')
            a=state.setdefault('archive',{})
            if not a.get('last_completed') or not approval.strip(): raise ValueError('COMPLETED_APPROVED_BATCH_AND_USER_CONSENT_REQUIRED')
            p=json.loads(self.plan_file(a['last_completed']).read_text())
            if not p.get('approval'): raise ValueError('FIRST_BATCH_MUST_HAVE_EXPLICIT_APPROVAL')
            a.update(automatic_enabled=True,automatic_approval=approval)
        return {'status':'automatic_eligible_moves_enabled'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',default=str(queue.DEFAULT_CONFIG))
    s=p.add_subparsers(dest='command',required=True)
    x=s.add_parser('snapshot'); x.add_argument('--label',default='weekly recovery snapshot')
    x=s.add_parser('verify'); x.add_argument('snapshot')
    x=s.add_parser('restore'); x.add_argument('snapshot'); x.add_argument('--destination',required=True)
    x=s.add_parser('plan'); x.add_argument('--force-preview',action='store_true')
    x=s.add_parser('clear'); x.add_argument('--path',required=True); x.add_argument('--reason',required=True); x.add_argument('--session-closed-evidence')
    x=s.add_parser('record-preview'); x.add_argument('--plan',required=True); x.add_argument('--report',required=True)
    x=s.add_parser('claim'); x.add_argument('--plan',required=True); x.add_argument('--approval-reference')
    x=s.add_parser('check-item'); x.add_argument('--plan',required=True); x.add_argument('--index',type=int,required=True)
    for name in ['complete','recover']:
        x=s.add_parser(name); x.add_argument('--plan',required=True)
    x=s.add_parser('enable'); x.add_argument('--approval-reference',required=True)
    x=s.add_parser('failure'); x.add_argument('--plan',required=True); x.add_argument('--reason',required=True)
    a=p.parse_args(); worker=Archive(a.config)
    if a.command=='snapshot': out=worker.snapshot(a.label)
    elif a.command=='verify': out=worker.verify(a.snapshot)
    elif a.command=='restore': out=worker.restore(a.snapshot,a.destination)
    elif a.command=='plan': out=worker.plan(a.force_preview)
    elif a.command=='clear': out=worker.clear(a.path,a.reason,a.session_closed_evidence)
    elif a.command=='record-preview': out=worker.record_preview(a.plan,a.report)
    elif a.command=='claim': out=worker.claim(a.plan,a.approval_reference)
    elif a.command=='check-item': out=worker.check_item(a.plan,a.index)
    elif a.command=='complete': out=worker.complete(a.plan)
    elif a.command=='recover': out=worker.recover(a.plan)
    elif a.command=='enable': out=worker.enable(a.approval_reference)
    elif a.command=='failure': out=worker.failure(a.plan,a.reason)
    print(json.dumps(out,ensure_ascii=False,indent=2))


if __name__=='__main__':
    try: main()
    except Exception as exc:
        print(json.dumps({'status':'error','error_type':type(exc).__name__,'error':str(exc)})); sys.exit(1)

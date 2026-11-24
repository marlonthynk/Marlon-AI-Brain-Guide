import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('brain_queue', Path(__file__).with_name('queue.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / 'brain'
        (self.root / 'Inbox').mkdir(parents=True)
        (self.root / 'Projects').mkdir()
        self.capture = self.root / 'Inbox/new.md'
        self.capture.write_text('---\ntitle: Capture\n---\nPossibly change launch to Friday.\n')
        self.target = self.root / 'Projects/Example.md'
        self.target.write_text('---\ntitle: Example\n---\nLaunch on Monday.\n')
        self.config = self.base / 'config.json'
        self.config.write_text(json.dumps({'root': str(self.root), 'state_dir': str(self.base / 'state'),
                                          'project': 'test-brain', 'mode': 'review_only', 'archive': {'backup_dir': str(self.base / 'backups')}, 'notifications': {'enabled': True, 'provider': 'gmail', 'recipient': 'self@example.invalid', 'thread_url': 'example-test-chat'}}))
        self.q = mod.Queue(self.config)

    def review(self, run, issue=True):
        data = {'reviewed': [{**s, 'outcome': 'review' if issue else 'no_action', 'reason': 'test review'} for s in run['candidates']], 'issues': []}
        if issue:
            data['issues'] = [{'key': 'example/launch', 'kind': 'conflict', 'summary': 'Confirm which date applies.',
                               'sources': [{'path': p.relative_to(self.root).as_posix(), 'sha256': mod.digest(p.read_bytes())} for p in [self.capture, self.target]]}]
        path = self.base / 'review.json'
        path.write_text(json.dumps(data))
        return path

    def finish(self, run, path):
        return self.q.finish(run['run_id'], path, 'test-brain/reviews/consolidation/test')

    def test_incremental_review_preserves_sources_and_suppresses_repeat(self):
        before = {p: p.read_bytes() for p in [self.capture, self.target]}
        run = self.q.begin(25)
        result = self.finish(run, self.review(run))
        self.assertEqual(len(result['changed_issues']), 1)
        self.assertEqual(self.q.begin(25)['status'], 'idle')
        self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_process_overlap_allows_one_run(self):
        command = [sys.executable, str(Path(mod.__file__)), '--config', str(self.config), 'begin']
        a = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
        b = subprocess.Popen(command, stdout=subprocess.PIPE, text=True)
        statuses = sorted([json.loads(a.communicate(timeout=10)[0])['status'], json.loads(b.communicate(timeout=10)[0])['status']])
        self.assertEqual(statuses, ['busy', 'ready'])

    def test_changed_source_rejects_commit_and_retries(self):
        run = self.q.begin(25)
        path = self.review(run)
        self.capture.write_text('Changed during review')
        with self.assertRaisesRegex(ValueError, 'SOURCE_CHANGED'):
            self.finish(run, path)
        self.assertEqual(self.q.status()['processed_revisions'], 0)
        self.q.abort(run['run_id'], 'concurrent-edit')
        self.assertEqual(len(self.q.begin(25)['candidates']), 2)

    def test_crash_expiry_recovers_unprocessed_work_and_blocks_late_writer(self):
        run = self.q.begin(25)
        with self.q.locked() as state:
            state['active']['expires'] = 1
        replacement = mod.Queue(self.config).begin(25)
        self.assertEqual(replacement['status'], 'ready')
        self.assertEqual(len(replacement['candidates']), 2)
        with self.assertRaisesRegex(ValueError, 'RUN_NOT_ACTIVE'):
            self.finish(run, self.review(run))
        self.assertEqual(len(self.q.status()['pending_emails']), 1)

    def test_missing_days_and_unchanged_evidence_do_not_duplicate_issues(self):
        run = self.q.begin(25)
        first = self.finish(run, self.review(run))
        # A changed source is found regardless of its age; there is no time-window cutoff.
        self.capture.write_text(self.capture.read_text() + '\nSame unresolved question; more evidence.\n')
        import os
        os.utime(self.capture, (1, 1))
        run = self.q.begin(25)
        self.assertEqual(len(run['candidates']), 1)
        second = self.finish(run, self.review(run))
        self.assertEqual(second['changed_issues'], [])
        self.assertEqual(second['open_issues'][0]['id'], first['open_issues'][0]['id'])
        self.assertEqual(len(self.q.status()['pending_emails']), 1)

    def test_ambiguous_email_is_not_resent_and_ack_clears_outbox(self):
        run = self.q.begin(25)
        self.finish(run, self.review(run))
        claim = self.q.claim()
        ident = claim['event']['id']
        self.assertEqual(claim['status'], 'send')
        self.assertEqual(mod.Queue(self.config).claim()['status'], 'reconcile_before_sending')
        self.q.mail_failure(ident, 'unknown')
        self.assertEqual(self.q.claim()['status'], 'reconcile_before_sending')
        self.q.sent(ident, 'verified-provider-message-id')
        self.assertEqual(self.q.claim()['status'], 'none')

    def test_email_retries_are_bounded(self):
        run = self.q.begin(25)
        self.finish(run, self.review(run))
        for n in range(3):
            claim = self.q.claim()
            self.assertEqual(claim['status'], 'send')
            result = self.q.mail_failure(claim['event']['id'], 'not-sent')
        self.assertEqual(result['status'], 'blocked')
        self.assertEqual(self.q.claim()['status'], 'reconcile_before_sending')

    def test_exclusions_and_path_boundary(self):
        (self.root / 'Reviews').mkdir()
        (self.root / 'Reviews/output.md').write_text('Worker output')
        (self.root / 'Inbox/fixture.md').write_text('---\nverification_only: true\n---\nTest')
        external = self.base / 'private.md'
        external.write_text('Synthetic outside source')
        (self.root / 'Inbox/symlink.md').symlink_to(external)
        self.assertEqual(len(self.q.begin(25)['candidates']), 2)
        with self.assertRaises(ValueError): self.q.source('../private.md')
        with self.assertRaises(ValueError): self.q.source('Inbox/symlink.md')

    def test_partial_review_never_advances_checkpoint(self):
        run = self.q.begin(25)
        path = self.review(run)
        data = json.loads(path.read_text())
        data['reviewed'].pop()
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'INCOMPLETE'):
            self.finish(run, path)
        self.assertEqual(self.q.status()['processed_revisions'], 0)

    def test_proposal_guard_and_resolved_issue_do_not_reopen(self):
        run = self.q.begin(25)
        path = self.review(run)
        data = json.loads(path.read_text())
        data['issues'][0]['proposal'] = {'target': '../outside.md', 'expected_checksum': None, 'change': 'test', 'status': 'tentative'}
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'INVALID_PROPOSAL_TARGET'):
            self.finish(run, path)
        result = self.finish(run, self.review(run))
        ident = result['open_issues'][0]['id']
        self.q.resolve(ident, 'User declined the unchanged proposal')
        self.capture.write_text(self.capture.read_text() + '\nSame claim.\n')
        run = self.q.begin(25)
        result = self.finish(run, self.review(run))
        self.assertEqual(result['open_issues'], [])
        self.assertEqual(result['changed_issues'], [])


if __name__ == '__main__':
    unittest.main()

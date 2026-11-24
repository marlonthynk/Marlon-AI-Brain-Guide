import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('portable_archive', Path(__file__).with_name('archive.py'))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class PortableTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.base = Path(tmp.name).resolve()
        self.root = self.base / 'vault with spaces/AI-Brain'
        (self.root / 'Inbox/Captures').mkdir(parents=True)
        self.note = self.root / 'Inbox/Captures/Example.md'
        self.note.write_text('---\ntitle: Example\npermalink: research-brain/inbox/captures/example\n---\nTentative idea.\n')
        self.cfg = {'project': 'research-brain', 'root': str(self.root), 'state_dir': str(self.base/'private state'),
                    'mode': 'review_only', 'timezone': 'Asia/Tokyo', 'notifications': {'enabled': False},
                    'archive': {'enabled': True, 'start_at': '2027-01-01T00:00:00',
                                'weekday': 'Tuesday', 'time': '18:30', 'backup_dir': str(self.base/'snapshots'),
                                'synced_vault': str(self.root.parent)}}
        self.config = self.base/'worker.json'
        self.save()
        self.a = mod.Archive(self.config)
        self.q = self.a.q

    def save(self):
        self.config.write_text(json.dumps(self.cfg))

    def review(self, issue=False):
        run = self.q.begin(25)
        data = {'reviewed': [{**s, 'outcome': 'review' if issue else 'no_action', 'reason': 'Synthetic review'} for s in run['candidates']], 'issues': []}
        if issue:
            data['issues'] = [{'key': 'example/status', 'kind': 'proposal', 'summary': 'Review tentative status.',
                               'sources': [{'path': s['path'], 'sha256': s['sha256']} for s in run['candidates']]}]
        p = self.base/'review.json'
        p.write_text(json.dumps(data))
        return self.q.finish(run['run_id'], p, 'research-brain/reviews/consolidation/example')

    def test_local_reports_keep_issues_without_email_or_note_changes(self):
        before = self.note.read_bytes()
        result = self.review(True)
        self.assertEqual(len(result['open_issues']), 1)
        self.assertIsNone(result['email_event'])
        self.assertEqual(self.q.status()['pending_emails'], [])
        self.assertEqual(self.q.claim()['status'], 'disabled')
        self.assertEqual(self.q.begin(25)['status'], 'idle')
        self.assertEqual(before, self.note.read_bytes())

    def test_custom_project_guards_and_snapshot_identity(self):
        run = self.q.begin(25)
        p = self.base/'review.json'
        p.write_text(json.dumps({'reviewed': [{**s, 'outcome': 'no_action', 'reason': 'Test'} for s in run['candidates']], 'issues': []}))
        with self.assertRaisesRegex(ValueError, 'INVALID_REPORT'):
            self.q.finish(run['run_id'], p, 'another-brain/reviews/consolidation/test')
        self.q.finish(run['run_id'], p, 'research-brain/reviews/consolidation/test')
        snap = self.a.snapshot('Custom project')
        manifest = json.loads((Path(snap['snapshot'])/'manifest.json').read_text())
        self.assertEqual(manifest['project'], 'research-brain')
        with self.assertRaisesRegex(ValueError, 'INVALID_REPORT'):
            self.a.record_preview(self.a.plan(True)['id'], 'another-brain/reviews/test')
        self.cfg['project'] = 'another-brain'
        self.save()
        other = mod.Archive(self.config)
        with self.assertRaisesRegex(ValueError, 'DIFFERENT_PROJECT'):
            other.q.status()
        with self.assertRaisesRegex(ValueError, 'DIFFERENT_PROJECT'):
            other.verify(snap['snapshot'])

    def test_custom_weekday_time_and_missed_slot(self):
        stamp = lambda s: dt.datetime.fromisoformat(s).timestamp()
        before = stamp('2027-01-05T09:29:59+00:00')
        due = stamp('2027-01-05T09:30:00+00:00')
        self.assertEqual(self.a.week_due({}, before)[1], '2026-12-29')
        self.assertFalse(self.a.week_due({}, before)[0])
        self.assertEqual(self.a.week_due({}, due), (True, '2027-01-05'))
        self.assertTrue(self.a.week_due({}, stamp('2027-01-07T09:30:00+00:00'))[0])
        self.assertFalse(self.a.week_due({'archive': {'last_week': '2027-01-05'}}, due)[0])

    def test_timezone_used_for_destination_across_year_boundary(self):
        self.review()
        old = dt.datetime(2026, 12, 1, tzinfo=dt.timezone.utc).timestamp()
        os.utime(self.note, (old, old))
        self.a.clear('Inbox/Captures/Example.md', 'Synthetic completed source', None)
        now = dt.datetime(2026, 12, 31, 16, tzinfo=dt.timezone.utc).timestamp()
        with self.q.locked() as state:
            item, reason = self.a.eligibility(state, self.note, now)
        self.assertIsNone(reason)
        self.assertIn('/2027/01/', item['destination'])

    def test_new_york_dst_slots(self):
        self.cfg['timezone'] = 'America/New_York'
        self.cfg['archive'].update(weekday='Sunday', time='09:00', start_at='2027-01-01T00:00:00')
        self.save()
        a = mod.Archive(self.config)
        stamp = lambda s: dt.datetime.fromisoformat(s).timestamp()
        self.assertEqual(a.week_due({}, stamp('2027-03-07T14:00:00+00:00')), (True, '2027-03-07'))
        self.assertEqual(a.week_due({}, stamp('2027-03-14T13:00:00+00:00')), (True, '2027-03-14'))
        self.assertEqual(a.week_due({}, stamp('2027-03-14T12:59:59+00:00'))[1], '2027-03-07')

    def test_disabled_archive_can_only_preview_not_claim(self):
        self.cfg['archive']['enabled'] = False
        self.save()
        a = mod.Archive(self.config)
        self.assertEqual(a.plan()['status'], 'disabled')
        with self.assertRaisesRegex(ValueError, 'ARCHIVE_DISABLED'):
            a.claim('archive-test', 'Approval')

    def test_invalid_configuration_and_overlapping_paths(self):
        cases = [('project', '../outside'), ('timezone', 'No/Such_Zone')]
        for key, value in cases:
            cfg = {**self.cfg, key: value}
            with self.assertRaises(Exception): mod.queue.configuration.validate(cfg)
        self.cfg['state_dir'] = str(self.root.parent/'synced state')
        with self.assertRaisesRegex(ValueError, 'OUTSIDE_SYNCED_VAULT'):
            mod.queue.configuration.validate(self.cfg)

    def test_enabling_email_does_not_retroactively_send_local_events(self):
        self.review(True)
        self.cfg['notifications'] = {'enabled': True, 'provider': 'outlook', 'recipient': 'self@example.invalid'}
        self.save()
        q = mod.queue.Queue(self.config)
        self.assertEqual(q.claim()['status'], 'none')
        # A materially new failure may now be notified through the configured provider.
        self.note.write_text(self.note.read_text() + 'New revision.\n')
        run = q.begin(25)
        q.abort(run['run_id'], 'test-failure')
        event = q.claim()
        self.assertEqual(event['provider'], 'outlook')
        self.assertEqual(event['recipient'], 'self@example.invalid')


if __name__ == '__main__':
    unittest.main()

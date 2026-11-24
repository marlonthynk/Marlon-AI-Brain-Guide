import datetime as dt
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('brain_archive',Path(__file__).with_name('archive.py'))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(); self.addCleanup(tmp.cleanup)
        self.base=Path(tmp.name); self.root=self.base/'brain'
        (self.root/'Inbox/Captures').mkdir(parents=True)
        self.path='Inbox/Captures/Example.md'; self.note=self.root/self.path
        self.note.write_text('---\ntitle: Example\npermalink: test-brain/inbox/captures/example\n---\nA reviewed source.\n')
        self.config=self.base/'config.json'
        self.config.write_text(json.dumps({'root':str(self.root),'state_dir':str(self.base/'state'),
          'project':'test-brain','mode':'review_only','notifications':{'enabled':True,'provider':'gmail','recipient':'self@example.invalid','thread_url':'example-test-chat'},'timezone':'Europe/London',
          'archive':{'enabled':True,'start_at':'2026-11-13T09:00:00','backup_dir':str(self.base/'backups')}}))
        self.a=mod.Archive(self.config); self.q=self.a.q
        self.review()

    def review(self):
        run=self.q.begin(25)
        data={'reviewed':[{**s,'outcome':'no_action','reason':'Already represented; no remaining work.'} for s in run['candidates']],'issues':[]}
        path=self.base/'review.json'; path.write_text(json.dumps(data))
        self.q.finish(run['run_id'],path,'test-brain/reviews/consolidation/test')

    def age(self):
        old=time.time()-8*86400; os.utime(self.note,(old,old))

    def ready(self):
        self.age(); self.a.clear(self.path,'Reviewed; no remaining useful change.',None)
        return self.a.plan(True)

    def move_fixture(self,plan):
        # Direct rename is confined to this temporary test project, never real memory.
        item=plan['items'][0]; dest=self.root/item['destination']; dest.parent.mkdir(parents=True)
        self.note.rename(dest)

    def test_age_review_clearance_and_open_issues_gate(self):
        self.assertEqual(self.a.plan(True)['items'],[])
        self.age(); self.assertEqual(self.a.plan(True)['items'],[])
        plan=self.ready(); self.assertEqual(len(plan['items']),1)
        with self.q.locked() as state:
            state['issues']['test']={'status':'open','sources':[{'path':self.path}]}
        self.assertEqual(self.a.plan(True)['items'],[])
        self.note.write_text(self.note.read_text()+'Changed revision.\n'); self.age()
        with self.assertRaisesRegex(ValueError,'REVISION_NOT_REVIEWED'):
            self.a.clear(self.path,'Changed',None)

    def test_sessions_need_explicit_completion_evidence(self):
        dest=self.root/'Inbox/Sessions/Example.md'; dest.parent.mkdir()
        self.note.rename(dest); self.note=dest; self.path='Inbox/Sessions/Example.md'; self.review(); self.age()
        with self.assertRaisesRegex(ValueError,'SESSION_CLOSURE'):
            self.a.clear(self.path,'Old source',None)
        self.assertEqual(self.a.plan(True)['items'],[])
        self.a.clear(self.path,'User confirmed work complete','User completion reference, test only')
        self.assertIn('/Sessions/',self.a.plan(True)['items'][0]['destination'])

    def test_first_batch_requires_approval_and_enable_requires_completed_batch(self):
        plan=self.ready()
        with self.assertRaisesRegex(ValueError,'FIRST_BATCH_REQUIRES_APPROVAL'): self.a.claim(plan['id'],None)
        with self.assertRaisesRegex(ValueError,'COMPLETED_APPROVED'): self.a.enable('Consent')
        self.a.claim(plan['id'],'Explicit approval of this test plan')
        self.assertEqual(self.q.begin(25)['status'],'busy')
        with self.assertRaisesRegex(ValueError,'ARCHIVE_REQUIRES_RECOVERY'): self.q.abort(plan['id'],'test')
        with self.assertRaisesRegex(ValueError,'MOVES_INCOMPLETE'): self.a.complete(plan['id'])
        self.move_fixture(plan); self.a.complete(plan['id'])
        self.assertEqual(self.a.enable('Explicit consent after verified first test batch')['status'],'automatic_eligible_moves_enabled')

    def test_stale_preview_and_destination_collision(self):
        plan=self.ready(); self.note.write_text(self.note.read_text()+'New content.\n')
        with self.assertRaisesRegex(ValueError,'PREVIEW_STALE'): self.a.claim(plan['id'],'Approved')
        self.review(); plan=self.ready()
        dest=self.root/plan['items'][0]['destination']; dest.parent.mkdir(parents=True); dest.write_text('Existing note')
        with self.assertRaisesRegex(ValueError,'PREVIEW_STALE'): self.a.claim(plan['id'],'Approved')
        self.assertEqual(dest.read_text(),'Existing note')

    def test_partial_move_recovery_is_idempotent_and_blocks_review_takeover(self):
        plan=self.ready(); self.a.claim(plan['id'],'Approved')
        self.assertEqual(self.a.check_item(plan['id'],0)['status'],'ready_for_mcp_move')
        self.move_fixture(plan)
        with self.q.locked() as state: state['active']['expires']=1
        self.assertEqual(self.q.begin(25)['status'],'archive_recovery_required')
        self.a.recover(plan['id'])
        self.assertEqual(self.a.check_item(plan['id'],0)['status'],'already_moved')
        self.assertEqual(self.a.check_item(plan['id'],0)['status'],'already_moved')
        self.assertEqual(self.a.complete(plan['id'])['moved'],1)
        self.assertEqual(self.q.begin(25)['status'],'idle')

    def test_failed_snapshot_can_recover_before_any_move(self):
        plan=self.ready()
        with patch.object(self.a,'snapshot',side_effect=OSError('test disk error')):
            with self.assertRaises(OSError): self.a.claim(plan['id'],'Approved')
        with self.assertRaisesRegex(ValueError,'VERIFIED_SNAPSHOT_REQUIRED'): self.a.check_item(plan['id'],0)
        self.a.failure(plan['id'],'snapshot-failed')
        with self.q.locked() as state: state['active']['expires']=1
        self.a.recover(plan['id'])
        self.assertEqual(self.a.check_item(plan['id'],0)['status'],'ready_for_mcp_move')
        self.assertEqual(len(self.q.status()['pending_emails']),1)

    def test_friday_slot_catchup_and_no_duplicate_week(self):
        def timestamp(value): return dt.datetime.fromisoformat(value).timestamp()
        empty={}
        self.assertFalse(self.a.week_due(empty,timestamp('2026-11-09T15:00:00+00:00'))[0])
        self.assertFalse(self.a.week_due(empty,timestamp('2026-11-13T08:59:00+00:00'))[0])
        self.assertEqual(self.a.week_due(empty,timestamp('2026-11-13T09:00:00+00:00')),(True,'2026-11-13'))
        state={'archive':{'last_week':'2026-11-13'}}
        self.assertFalse(self.a.week_due(state,timestamp('2026-11-16T10:00:00+00:00'))[0])
        self.assertTrue(self.a.week_due(empty,timestamp('2026-11-16T10:00:00+00:00'))[0])
        self.assertFalse(self.a.week_due(empty,timestamp('2027-07-02T07:59:00+00:00'))[1]=='2027-07-02')
        self.assertEqual(self.a.week_due(empty,timestamp('2027-07-02T08:00:00+00:00'))[1],'2027-07-02')

    def test_snapshot_restores_exact_bytes_and_rejects_corruption_or_live_restore(self):
        snap=self.a.snapshot('test'); before=self.note.read_bytes()
        self.note.write_text('Subsequent change')
        dest=self.base/'isolated-restore'; self.a.restore(snap['snapshot'],dest)
        self.assertEqual((dest/'brain'/self.path).read_bytes(),before)
        self.assertEqual(self.note.read_text(),'Subsequent change')
        for target in [self.root,self.q.home/'new',self.a.backups/'new',dest]:
            with self.assertRaises(ValueError): self.a.restore(snap['snapshot'],target)
        (Path(snap['snapshot'])/'brain'/self.path).write_text('Corruption')
        with self.assertRaisesRegex(ValueError,'SNAPSHOT_CHECKSUM_MISMATCH'): self.a.verify(snap['snapshot'])

    def test_preview_email_dedup_and_auto_pending_week_not_marked_complete(self):
        plan=self.ready(); report='test-brain/reviews/archive-tests/example'
        event=self.a.record_preview(plan['id'],report)['email_event']
        self.assertEqual(self.a.record_preview(plan['id'],report)['email_event'],event)
        self.assertEqual(len(self.q.status()['pending_emails']),1)
        with self.q.locked() as state: state['archive']['automatic_enabled']=True
        plan=self.a.plan(True); prior_week='1999-12-31'; plan['week']=prior_week; mod.queue.atomic(self.a.plan_file(plan['id']),plan)
        self.a.record_preview(plan['id'],report)
        with self.q.locked() as state: self.assertNotEqual(state['archive'].get('last_week'),prior_week)

    def test_symlink_destination_and_fixture_are_never_archived(self):
        self.ready(); (self.root/'Archive').symlink_to(self.base/'outside',target_is_directory=True)
        with self.assertRaisesRegex(ValueError,'UNSAFE_ARCHIVE_DESTINATION'): self.a.plan(True)
        (self.root/'Archive').unlink()
        self.note.write_text('---\nverification_only: true\n---\nTest only')
        self.assertEqual(self.a.plan(True)['kept'][0]['reason'],'verification fixture')


if __name__=='__main__': unittest.main()

#!/usr/bin/env python3
"""Isolated helper acceptance trial. No MCP, real note moves, email or schedule."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

REPO = Path(__file__).resolve().parents[1]
WORKER = REPO / 'skills/ai-brain-consolidate/scripts'
sys.path.insert(0, str(WORKER))
spec = importlib.util.spec_from_file_location('demo_archive', WORKER/'archive.py')
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


def run(destination):
    base = Path(destination).resolve()
    if base.exists():
        raise ValueError('DEMO_DESTINATION_MUST_NOT_EXIST')
    base.mkdir(parents=True)
    root = base/'isolated vault/AI-Brain'
    shutil.copytree(REPO/'examples/fictional-brain', root)
    for p in root.rglob('*.md'):
        p.write_text(p.read_text().replace('example-brain/', 'trial-brain/'))
    cfg = {'project': 'trial-brain', 'root': str(root), 'state_dir': str(base/'private state'),
           'mode': 'review_only', 'timezone': 'Pacific/Auckland', 'notifications': {'enabled': False},
           'archive': {'enabled': False, 'backup_dir': str(base/'snapshots'), 'synced_vault': str(root.parent)}}
    config = base/'worker.json'
    config.write_text(json.dumps(cfg, indent=2))
    a = archive.Archive(config)
    q = a.q
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*.md')}
    run = q.begin(25)
    sources = [{'path': s['path'], 'sha256': s['sha256']} for s in run['candidates']]
    target = 'Decisions/Harbour Decision.md'
    review = {'reviewed': [{**s, 'outcome': 'review', 'reason': 'Fictional trial proposal awaiting approval.'} for s in sources],
              'issues': [{'key': 'harbour/interval', 'kind': 'proposal', 'summary': 'Consider the tentative interval change.',
                          'sources': sources, 'proposal': {'target': target, 'expected_checksum': archive.sha((root/target).read_bytes()),
                          'status': 'tentative idea', 'change': 'Proposed only: 21 days, rationale longer observation window. Retain 14 days as history if approved.'}}]}
    review_file = base/'review.json'
    review_file.write_text(json.dumps(review, indent=2))
    result = q.finish(run['run_id'], review_file, 'trial-brain/reviews/consolidation/helper-demo')
    assert len(result['open_issues']) == 1 and result['email_event'] is None
    assert q.begin(25)['status'] == 'idle'
    assert q.claim()['status'] == 'disabled'
    assert before == {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*.md')}
    snap = a.snapshot('fictional helper trial')
    restored = base/'isolated restore'
    a.restore(snap['snapshot'], restored)
    assert before == {p.relative_to(restored/'brain').as_posix(): p.read_bytes() for p in (restored/'brain').rglob('*.md')}
    note = root/'Inbox/Captures/Interval idea.md'
    note.write_text(note.read_text()+'\nNew evidence.\n')
    second = q.begin(25)
    data = {'reviewed': [{**s, 'outcome': 'no_action', 'reason': 'Trial guard.'} for s in second['candidates']], 'issues': []}
    review_file.write_text(json.dumps(data))
    note.write_text(note.read_text()+'Concurrent change.\n')
    try:
        q.finish(second['run_id'], review_file, 'trial-brain/reviews/consolidation/rejected-demo')
    except ValueError as exc:
        assert 'SOURCE_CHANGED' in str(exc)
    else:
        raise AssertionError('Concurrent edit was accepted')
    q.abort(second['run_id'], 'synthetic-concurrent-edit')
    assert q.status()['open_issues'] and not q.status()['pending_emails']
    print(json.dumps({'passed': True, 'workspace': str(base), 'proposal_kept_unapproved': True,
                      'repeat_idle': True, 'snapshot_restore': True, 'concurrent_edit_rejected': True,
                      'email_sent': False, 'mcp_or_schedule_tested': False}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    args = parser.parse_args()
    run(args.destination)

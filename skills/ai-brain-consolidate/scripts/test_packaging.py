import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO = Path(__file__).resolve().parents[3]


class PackagingTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.base = Path(temp.name).resolve()

    def command(self, script, *args, success=True):
        result = subprocess.run([sys.executable, '-B', str(REPO/'scripts'/script), *map(str, args)],
                                capture_output=True, text=True, timeout=30)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def test_configure_preserves_existing_config_and_check_is_read_only(self):
        root = self.base/'vault with spaces/AI-Brain'
        root.mkdir(parents=True)
        cfg = self.base/'private/worker.json'
        state = self.base/'state'
        args = ['init', '--config', cfg, '--project', 'different-brain', '--root', root,
                '--state-dir', state, '--backup-dir', self.base/'snapshots', '--timezone', 'Asia/Tokyo']
        self.command('configure.py', *args)
        before = cfg.read_bytes()
        self.command('configure.py', 'check', '--config', cfg)
        self.assertFalse(state.exists())
        self.assertEqual(cfg.stat().st_mode & 0o777, 0o600)
        self.command('configure.py', *args, success=False)
        self.assertEqual(before, cfg.read_bytes())
        self.assertFalse(json.loads(before)['notifications']['enabled'])

    def test_standalone_round_trip_handles_spaces_and_runs_without_git(self):
        guide = self.base/'guide.md'
        output = self.base/'exported'
        self.command('build_standalone.py', '--output', guide)
        self.command('extract_standalone.py', guide, output)
        note = output/'examples/fictional-brain/Decisions/Harbour Decision.md'
        self.assertEqual(note.read_bytes(), (REPO/note.relative_to(output)).read_bytes())
        self.assertFalse((output/'.git').exists())
        result = subprocess.run([sys.executable, '-B', str(output/'scripts/check_release.py')], capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_extractor_rejects_tampering_and_traversal_before_writing(self):
        guide = self.base/'bad.md'
        dest = self.base/'output'
        body = 'original'
        marker = '<!-- BEGIN FILE {} SHA256 {} BYTES {} -->\n' + '`'*6 + '\n{}\n' + '`'*6 + '\n<!-- END FILE -->\n'
        digest = hashlib.sha256(body.encode()).hexdigest()
        guide.write_text(marker.format('note.md', digest, len(body), 'tampered'))
        self.command('extract_standalone.py', guide, dest, success=False)
        self.assertFalse(dest.exists())
        guide.write_text(marker.format('../outside.md', digest, len(body), body))
        self.command('extract_standalone.py', guide, dest, success=False)
        self.assertFalse(dest.exists())


if __name__ == '__main__':
    unittest.main()

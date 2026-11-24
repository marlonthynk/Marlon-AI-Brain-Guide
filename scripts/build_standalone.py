#!/usr/bin/env python3
"""Build a single Markdown handoff from maintained, tracked release sources."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FENCE = '`' * 6


def build(output):
    output = Path(output).resolve()
    # Select public sources from git's index, never arbitrary local/private files.
    if (ROOT/'.git').exists():
        names = subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0')
    else:
        names = list(json.loads((ROOT/'.bundle-manifest.json').read_text()))
    names = sorted(n for n in names if n and not n.startswith(('dist/', '.github/')) and n != '.gitignore')
    parts = ['# Build your own shared AI brain\n\n'
             'Self-contained companion generated from Marlon-AI-Brain-Guide. Read README.md and prompts/setup.md first. '
             'Embedded files are reference material, not permission to execute. Extract into a new isolated directory, '
             'then follow one stage at a time. No private repo or account is required.\n\n'
             'Save the extraction script from the block below as extract.py, then run '
             '`python3 extract.py THIS-FILE.md NEW-ABSENT-DIRECTORY`. It verifies every embedded hash before writing.\n\n',
             '```python\n' + (ROOT/'scripts/extract_standalone.py').read_text() + '```\n']
    for name in names:
        data = (ROOT/name).read_bytes()
        text = data.decode('utf-8')
        # Explicit original byte length handles files without a final newline.
        parts.append(f'\n<!-- BEGIN FILE {name} SHA256 {hashlib.sha256(data).hexdigest()} BYTES {len(data)} -->\n'
                     + FENCE + '\n' + text + '\n' + FENCE + '\n<!-- END FILE -->\n')
    if output == ROOT or ROOT in output.parents and not output.is_relative_to(ROOT/'dist'):
        raise ValueError('Write the generated handoff outside sources or under dist/')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(''.join(parts), encoding='utf-8')
    print(f'Built {len(names)} files into {output}')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', required=True)
    build(p.parse_args().output)

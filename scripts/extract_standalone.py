"""Verify and extract this generated handoff into a new directory."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import re
import sys


def extract(source, destination):
    source, dest = Path(source), Path(destination)
    if dest.exists():
        raise ValueError('Destination already exists')
    fence = '`' * 6
    pattern = r'^<!-- BEGIN FILE ([^\n]+?) SHA256 ([a-f0-9]{64}) BYTES ([0-9]+) -->\n' + fence + r'\n(.*?)\n' + fence + r'\n<!-- END FILE -->$'
    matches = re.findall(pattern, source.read_text(encoding='utf-8'), re.S | re.M)
    if not matches:
        raise ValueError('No embedded files')
    pending = {}
    for name, expected, size, body in matches:
        relative = PurePosixPath(name)
        if relative.is_absolute() or '..' in relative.parts or '\\' in name or name in pending:
            raise ValueError('Unsafe or duplicate path')
        data = body.encode('utf-8')
        if len(data) != int(size) or hashlib.sha256(data).hexdigest() != expected:
            raise ValueError('Hash/size mismatch: ' + name)
        pending[name] = data
    if len(matches) != source.read_text(encoding='utf-8').count('<!-- BEGIN FILE '):
        # Count only actual marker lines; marker text inside scripts is not a file.
        marker_lines = re.findall(r'^<!-- BEGIN FILE ', source.read_text(encoding='utf-8'), re.M)
        if len(matches) != len(marker_lines):
            raise ValueError('Incomplete embedded file')
    dest.mkdir(parents=True)
    for name, data in pending.items():
        target = dest.joinpath(*PurePosixPath(name).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (dest/'.bundle-manifest.json').write_text(json.dumps({name: hashlib.sha256(data).hexdigest() for name, data in pending.items()}, indent=2), encoding='utf-8')
    print(f'Extracted {len(pending)} verified files to {dest}')


if __name__ == '__main__':
    extract(*sys.argv[1:3])

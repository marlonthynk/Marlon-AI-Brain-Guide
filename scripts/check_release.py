#!/usr/bin/env python3
"""Check public tracked files, local Markdown links, JSON and reachable Git history."""
import json
from pathlib import Path
import re
import subprocess
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
PRIVATE = [
    r'/Users/(?!YOUR_USER/)[A-Za-z0-9._-]+/',
    r'codex://threads/[0-9a-f-]{30,}',
    r'(?i)(?:ghp_|github_pat_)[A-Za-z0-9_]{25,}',
    r'sk-proj-[A-Za-z0-9_-]{25,}',
    r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
]


def tracked():
    if not (ROOT/'.git').exists():
        manifest = json.loads((ROOT/'.bundle-manifest.json').read_text())
        for name, expected in manifest.items():
            p = ROOT/name
            if not p.resolve().is_relative_to(ROOT) or p.is_symlink():
                raise ValueError('UNSAFE_BUNDLE_PATH')
            import hashlib
            if hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                raise ValueError('BUNDLE_SOURCE_CHANGED:' + name)
        return list(manifest)
    return [p for p in subprocess.check_output(['git', '-C', str(ROOT), 'ls-files', '-z']).decode().split('\0') if p]


def inspect(name, raw, problems):
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        problems.add(name + ': unexpected binary public source')
        return
    for pattern in PRIVATE:
        if re.search(pattern, text):
            problems.add(name + ': private installation/credential pattern')
    # Public contact examples must be reserved example addresses.
    for email in re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', text):
        if not email.endswith(('@example.invalid', '@example.com', '@example.org')):
            problems.add(name + ': non-example email address')


def main():
    problems = set()
    names = tracked()
    for name in names:
        p = ROOT/name
        if p.is_symlink():
            problems.add(name + ': symlink')
            continue
        inspect(name, p.read_bytes(), problems)
        if name.endswith('.json'):
            try: json.loads(p.read_text())
            except ValueError: problems.add(name + ': invalid JSON')
        if name.endswith('.md'):
            for target in re.findall(r'(?<!!)\[[^\]\n]*\]\(([^)\n]+)\)', p.read_text()):
                target = target.strip('<>')
                if re.match(r'[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                    continue
                link = (p.parent/unquote(target.split('#', 1)[0])).resolve()
                if not link.exists() or (link != ROOT and ROOT not in link.parents):
                    problems.add(name + ': broken/escaping local link ' + target)
                elif '#' in target and link.suffix == '.md':
                    anchor = target.split('#', 1)[1]
                    headings = re.findall(r'^#+\s+(.+)$', link.read_text(), re.M)
                    slugs = {re.sub(r'[^\w\s-]', '', h.lower()).replace(' ', '-') for h in headings}
                    if anchor not in slugs:
                        problems.add(name + ': unknown heading anchor ' + target)
    # A clean public root history must not retain the private ancestor commits.
    objects = subprocess.check_output(['git', '-C', str(ROOT), 'rev-list', '--objects', '--all']).decode().splitlines() if (ROOT/'.git').exists() else []
    blobs = 0
    for line in objects:
        oid, _, name = line.partition(' ')
        if subprocess.check_output(['git', '-C', str(ROOT), 'cat-file', '-t', oid]).strip() == b'blob':
            inspect('history/' + name, subprocess.check_output(['git', '-C', str(ROOT), 'cat-file', 'blob', oid]), problems)
            blobs += 1
    if problems:
        raise SystemExit('\n'.join(sorted(problems)))
    print(f'Passed: {len(names)} tracked files, local links/anchors, JSON, identity/credential patterns, {blobs} history blobs.')
    print('External links and actual harness/scheduler behaviour require separate verification.')


if __name__ == '__main__':
    main()

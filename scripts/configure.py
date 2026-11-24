#!/usr/bin/env python3
"""Create or validate a private worker config. Does not install, schedule or send."""
import argparse
import json
import os
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / 'skills/ai-brain-consolidate/scripts'
sys.path.insert(0, str(SCRIPTS))
import configuration


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init')
    for name in ('config', 'project', 'root', 'state-dir', 'backup-dir', 'timezone'):
        init.add_argument('--' + name, required=True)
    init.add_argument('--synced-vault')
    init.add_argument('--archive-start', help='First eligible local date/time, e.g. 2027-01-08T09:00:00')
    init.add_argument('--archive-day', choices=configuration.DAYS, default='Friday')
    init.add_argument('--archive-time', default='09:00')
    init.add_argument('--enable-email', action='store_true')
    init.add_argument('--provider', choices=('gmail', 'outlook'), default='gmail')
    init.add_argument('--recipient')
    init.add_argument('--thread-url')
    check = sub.add_parser('check')
    check.add_argument('--config', required=True)
    args = parser.parse_args()
    if args.command == 'check':
        cfg = configuration.load(args.config)
    else:
        def absolute(value):
            return str(Path(value).expanduser().resolve())
        cfg = {
            'project': args.project, 'root': absolute(args.root),
            'state_dir': absolute(args.state_dir), 'timezone': args.timezone,
            'mode': 'review_only', 'lease_seconds': 3600,
            'notifications': {'enabled': args.enable_email, 'provider': args.provider,
                              'recipient': args.recipient, 'thread_url': args.thread_url},
            'archive': {'enabled': bool(args.archive_start), 'start_at': args.archive_start,
                        'weekday': args.archive_day, 'time': args.archive_time,
                        'backup_dir': absolute(args.backup_dir),
                        'synced_vault': absolute(args.synced_vault) if args.synced_vault else None,
                        'support_paths': {}}
        }
        configuration.validate(cfg)
        dest = Path(args.config).expanduser().resolve()
        # The config contains installation metadata and must stay outside the synced vault.
        for boundary in (cfg['root'], cfg['archive']['synced_vault'], cfg['archive']['backup_dir']):
            if boundary and configuration.contains(Path(boundary), dest):
                raise ValueError('CONFIG_MUST_BE_OUTSIDE_BRAIN_VAULT_AND_BACKUPS')
        dest.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(dest, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, 'w', encoding='utf-8') as out:
            json.dump(cfg, out, indent=2)
            out.write('\n')
        print('Created private config:', dest)
    print(json.dumps({'valid': True, 'project': cfg['project'],
                      'email_enabled': cfg.get('notifications', {}).get('enabled', False),
                      'archive_preview_enabled': cfg.get('archive', {}).get('enabled', False),
                      'note': 'No schedule, MCP registration, email or live-note operation performed.'}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError) as exc:
        print(json.dumps({'error': str(exc)}), file=sys.stderr)
        sys.exit(1)

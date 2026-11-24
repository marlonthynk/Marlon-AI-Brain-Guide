"""Validate one installation's settings without opening or changing its state."""
import datetime as dt
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

DEFAULT_CONFIG = Path.home() / '.config/shared-ai-brain/worker.json'
DAYS = ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday')


def absolute(value, field):
    if not isinstance(value, str) or not Path(value).is_absolute() or any(x in value for x in ('YOUR_', '<', '>')):
        raise ValueError('ABSOLUTE_PATH_REQUIRED:' + field)
    return Path(value).resolve()


def contains(parent, child):
    return parent == child or parent in child.parents


def load(path):
    cfg = json.loads(Path(path).read_text(encoding='utf-8'))
    validate(cfg)
    location = Path(path).resolve()
    for boundary in (cfg['root'], cfg['archive']['backup_dir'], cfg['archive'].get('synced_vault')):
        if boundary and contains(Path(boundary).resolve(), location):
            raise ValueError('CONFIG_MUST_BE_OUTSIDE_BRAIN_VAULT_AND_BACKUPS')
    return cfg


def validate(cfg):
    project = cfg.get('project', '')
    if not isinstance(project, str) or not re.fullmatch(r'[a-z0-9][a-z0-9_-]*', project):
        raise ValueError('PROJECT_MUST_BE_A_LOCAL_SLUG')
    root = absolute(cfg.get('root'), 'root')
    state = absolute(cfg.get('state_dir'), 'state_dir')
    if not root.is_dir():
        raise ValueError('BRAIN_DIRECTORY_MISSING')
    if contains(root, state) or contains(state, root):
        raise ValueError('STATE_MUST_BE_SEPARATE_FROM_BRAIN')
    if cfg.get('mode') != 'review_only':
        raise ValueError('ONLY_REVIEW_ONLY_MODE_SUPPORTED')
    zone = ZoneInfo(cfg.get('timezone', 'UTC'))
    lease = cfg.get('lease_seconds', 3600)
    if type(lease) is not int or not 60 <= lease <= 86400:
        raise ValueError('INVALID_LEASE_SECONDS')
    notice = cfg.get('notifications', {'enabled': False})
    if type(notice.get('enabled', False)) is not bool:
        raise ValueError('INVALID_NOTIFICATION_MODE')
    if notice.get('enabled'):
        if notice.get('provider') not in ('gmail', 'outlook'):
            raise ValueError('UNSUPPORTED_EMAIL_PROVIDER')
        recipient = notice.get('recipient', '')
        if not re.fullmatch(r'[^\s@,;<>]+@[^\s@,;<>]+\.[^\s@,;<>]+', recipient):
            raise ValueError('ONE_NOTIFICATION_RECIPIENT_REQUIRED')
    archive = cfg.get('archive', {'enabled': False})
    if type(archive.get('enabled', False)) is not bool:
        raise ValueError('INVALID_ARCHIVE_MODE')
    backups = absolute(archive.get('backup_dir'), 'archive.backup_dir')
    for protected in (root, state):
        if contains(protected, backups) or contains(backups, protected):
            raise ValueError('BACKUP_MUST_BE_SEPARATE_FROM_BRAIN_AND_STATE')
    vault = archive.get('synced_vault')
    if vault:
        vault = absolute(vault, 'archive.synced_vault')
        if not contains(vault, root):
            raise ValueError('BRAIN_MUST_BE_IN_DECLARED_VAULT')
        if contains(vault, state) or contains(vault, backups):
            raise ValueError('STATE_AND_BACKUPS_MUST_BE_OUTSIDE_SYNCED_VAULT')
    if archive.get('weekday', 'Friday') not in DAYS:
        raise ValueError('INVALID_ARCHIVE_WEEKDAY')
    if not re.fullmatch(r'(?:[01]\d|2[0-3]):[0-5]\d', archive.get('time', '09:00')):
        raise ValueError('INVALID_ARCHIVE_TIME')
    if archive.get('enabled'):
        start = dt.datetime.fromisoformat(archive.get('start_at') or '')
        if start.tzinfo is not None:
            raise ValueError('ARCHIVE_START_MUST_BE_LOCAL_WALL_TIME')
        start.replace(tzinfo=zone)
    for label, value in archive.get('support_paths', {}).items():
        if not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9-]*', label):
            raise ValueError('INVALID_BACKUP_LABEL')
        support = absolute(value, 'archive.support_paths.' + label)
        if contains(support, backups) or contains(backups, support):
            raise ValueError('BACKUP_MUST_NOT_OVERLAP_SUPPORT_PATH')
    return cfg

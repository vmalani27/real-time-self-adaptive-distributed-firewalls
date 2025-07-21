import re
import hashlib
import json

def validate_rule(rule):
    """Validates a rule before applying. Checks for nftables structure and denies dangerous characters/commands."""
    if not isinstance(rule, str):
        return False
    # Basic nftables rule structure: must start with 'nft add rule'
    if not rule.strip().startswith('nft add rule'):
        return False
    # Deny dangerous shell characters
    if re.search(r'[;&|`$><]', rule):
        return False
    # Deny commands that could flush/delete tables
    dangerous_cmds = [
        'flush', 'delete table', 'delete chain', 'reset', 'shutdown', 'reboot', 'mkfs', 'rm -rf', 'wget', 'curl', 'python', 'bash', 'sh', 'os.system', 'subprocess', 'eval', 'exec'
    ]
    for cmd in dangerous_cmds:
        if cmd in rule:
            return False
    # Only allow alphanumerics, spaces, and basic punctuation
    if not re.match(r'^[a-zA-Z0-9\s\-\./:_]+$', rule):
        return False
    return True

def hash_log_entry(entry):
    """Hashes a log entry for tamper-evidence. Accepts dict or str, returns SHA-256 hex digest."""
    if isinstance(entry, dict):
        entry_str = json.dumps(entry, sort_keys=True)
    else:
        entry_str = str(entry)
    return hashlib.sha256(entry_str.encode('utf-8')).hexdigest() 
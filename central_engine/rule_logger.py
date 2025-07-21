import json
import time
import os
from central_engine import dispatcher

LOG_FILE = 'central_engine/rule_log.jsonl'

def log_rule(rule_dict):
    entry = dict(rule_dict)
    entry['logged_at'] = int(time.time())
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(entry) + '\n')

def get_latest_rule():
    # TODO: implement
    pass

def rollback_last_rule():
    if not os.path.exists(LOG_FILE):
        print('No rules to rollback.')
        return
    with open(LOG_FILE, 'r') as f:
        lines = f.readlines()
    if not lines:
        print('No rules to rollback.')
        return
    # Find last active rule (not already rolled back/inactive)
    idx = len(lines) - 1
    last_rule = None
    while idx >= 0:
        entry = json.loads(lines[idx])
        if not entry.get('inactive') and not entry.get('rolled_back') and entry.get('rule_str'):
            last_rule = entry
            break
        idx -= 1
    if last_rule is None:
        print('No active rules to rollback.')
        return
    print('Rolling back rule:', last_rule)
    # Construct nft delete command from rule_str
    rule_str = last_rule['rule_str']
    # Only handle rules that start with 'nft add rule ...'
    if not rule_str.startswith('nft add rule '):
        print('Unsupported rule format for rollback.')
        return
    delete_str = rule_str.replace('nft add rule', 'nft delete rule', 1)
    # Prepare rollback payload
    rollback_obj = {'rule_str': delete_str, 'metadata': last_rule.get('metadata', {})}
    # Dispatch delete command to agent (REST fallback)
    status, resp = dispatcher.dispatch_rule(rollback_obj)
    print(f"Rollback dispatch status: {status}, response: {resp}")
    # Mark rule as rolled_back in log
    entry = json.loads(lines[idx])
    entry['rolled_back'] = True
    entry['rollback_status'] = status
    entry['rollback_resp'] = resp
    lines[idx] = json.dumps(entry) + '\n'
    with open(LOG_FILE, 'w') as f:
        f.writelines(lines)

def log_rule_version(rule, version, timestamp, status):
    """Logs rule version, timestamp, and status for rollback and audit."""
    pass 
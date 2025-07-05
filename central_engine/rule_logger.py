import json
import time
import os

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
    last_rule = json.loads(lines[-1])
    print('Rolling back rule:', last_rule)
    last_rule['inactive'] = True
    lines[-1] = json.dumps(last_rule) + '\n'
    with open(LOG_FILE, 'w') as f:
        f.writelines(lines)

def log_rule_version(rule, version, timestamp, status):
    """Logs rule version, timestamp, and status for rollback and audit."""
    pass 
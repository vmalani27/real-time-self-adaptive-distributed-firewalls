import subprocess
import shlex
import re

def build_nft_command(rule):
    """Builds the nft command from a rule string."""
    pass

def execute_nft_command(cmd):
    """Executes the nft command using subprocess."""
    pass

def apply_rule(rule_str):
    if not isinstance(rule_str, str) or not rule_str.startswith('nft '):
        return {'status': 'fail', 'message': 'Invalid rule'}
    if not re.match(r'^[a-zA-Z0-9\s\-\./:_]+$', rule_str):
        return {'status': 'fail', 'message': 'Unsafe characters in rule'}
    try:
        cmd = shlex.split(rule_str)
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            return {'status': 'success', 'message': result.stdout.strip()}
        else:
            return {'status': 'fail', 'message': result.stderr.strip()}
    except Exception as e:
        return {'status': 'fail', 'message': str(e)} 
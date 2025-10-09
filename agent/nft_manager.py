import subprocess
import shlex
import re
import shutil
import os

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
        # Determine nft executable path. Allow overriding via NFT_PATH env var.
        nft_exec = os.environ.get('NFT_PATH') or shutil.which('nft')
        if not nft_exec:
            return {
                'status': 'fail',
                'message': "nft executable not found. Ensure nftables is installed and in PATH, or set NFT_PATH to the absolute path to the nft binary."
            }

        parts = shlex.split(rule_str)
        # Replace a leading 'nft' with the resolved absolute path
        if parts[0] in ('nft', os.path.basename(nft_exec), nft_exec):
            parts[0] = nft_exec
        else:
            # If the rule doesn't start with nft or its path, reject for safety
            return {'status': 'fail', 'message': 'Rule must start with nft or provide the full nft path'}

        result = subprocess.run(parts, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return {'status': 'success', 'message': result.stdout.strip()}
        else:
            return {'status': 'fail', 'message': result.stderr.strip()}
    except Exception as e:
        return {'status': 'fail', 'message': str(e)} 
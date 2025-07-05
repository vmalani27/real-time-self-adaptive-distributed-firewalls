import os
import csv
import threading
from datetime import datetime
from typing import Dict, Any

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../logs')
LOG_FIELDS = [
    'timestamp', 'agent_id', 'tool', 'src_ip', 'src_port',
    'dest_ip', 'dest_port', 'protocol', 'alert_type', 'severity', 'message'
]

_locks = {}
_locks_lock = threading.Lock()

def _get_logfile_and_lock(agent_id: str, tool: str):
    """Get the CSV file path and a lock for the agent/tool pair."""
    filename = f"{agent_id}_{tool}.csv"
    filepath = os.path.join(LOG_DIR, filename)
    with _locks_lock:
        if filepath not in _locks:
            _locks[filepath] = threading.Lock()
    return filepath, _locks[filepath]

def ensure_log_dir():
    os.makedirs(LOG_DIR, exist_ok=True)

def append_log(payload: Dict[str, Any]):
    """
    Accepts a log payload (dict), parses it, and appends to the correct CSV file.
    """
    ensure_log_dir()
    agent_id = payload.get('agent_id', 'unknown')
    tool = payload.get('tool', 'unknown')
    filepath, lock = _get_logfile_and_lock(agent_id, tool)
    row = {
        'timestamp': payload.get('timestamp', datetime.utcnow().isoformat()),
        'agent_id': agent_id,
        'tool': tool,
        'src_ip': payload.get('src_ip', ''),
        'src_port': payload.get('src_port', ''),
        'dest_ip': payload.get('dest_ip', ''),
        'dest_port': payload.get('dest_port', ''),
        'protocol': payload.get('protocol', ''),
        'alert_type': payload.get('alert_type', ''),
        'severity': payload.get('severity', ''),
        'message': payload.get('message', ''),
    }
    with lock:
        file_exists = os.path.isfile(filepath)
        with open(filepath, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=LOG_FIELDS)
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)

def handle_ws_log(payload: Dict[str, Any]):
    """Entry point for WebSocket log submissions."""
    append_log(payload)

def handle_rest_log(payload: Dict[str, Any]):
    """Entry point for REST log submissions."""
    append_log(payload) 
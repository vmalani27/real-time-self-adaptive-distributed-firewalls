import os
import requests
from utils.helpers import load_env_config, get_config_value

# Load configuration once at module level
config = load_env_config()

def send_ack(status):
    """Sends status back to controller after rule is applied."""
    CONTROLLER_URL = get_config_value('CONTROLLER_URL', 'http://localhost:8000/ack', config)
    API_KEY = get_config_value('API_KEY', 'changeme', config)
    headers = {'x-api-key': API_KEY}
    try:
        resp = requests.post(CONTROLLER_URL, json=status, headers=headers, timeout=5)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[ack_sender] Failed to send ACK: {e}")
        return False 
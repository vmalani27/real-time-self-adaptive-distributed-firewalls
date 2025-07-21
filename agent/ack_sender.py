import os
import requests

def send_ack(status):
    """Sends status back to controller after rule is applied."""
    # CONTROLLER_URL and API_KEY from environment variables
    CONTROLLER_URL = os.environ.get('CONTROLLER_URL', 'http://localhost:8000/ack')
    API_KEY = os.environ.get('API_KEY', 'changeme')
    headers = {'x-api-key': API_KEY}
    try:
        resp = requests.post(CONTROLLER_URL, json=status, headers=headers, timeout=5)
        resp.raise_for_status()
        return True
    except Exception as e:
        print(f"[ack_sender] Failed to send ACK: {e}")
        return False 
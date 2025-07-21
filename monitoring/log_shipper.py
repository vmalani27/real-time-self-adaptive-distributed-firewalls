import os
import requests

def ship_logs(log_file):
    """Pushes logs to central logging server or appends to a central file."""
    LOG_SERVER_URL = os.environ.get('LOG_SERVER_URL', 'http://localhost:9000/logs')
    if not os.path.exists(log_file):
        print(f"[log_shipper] Log file not found: {log_file}")
        return False
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            while True:
                chunk = f.read(1024 * 1024)  # 1MB chunk
                if not chunk:
                    break
                payload = {'filename': os.path.basename(log_file), 'content': chunk}
                resp = requests.post(LOG_SERVER_URL, json=payload, timeout=10)
                resp.raise_for_status()
        print(f"[log_shipper] Successfully shipped logs from {log_file}")
        return True
    except Exception as e:
        print(f"[log_shipper] Failed to ship logs: {e}")
        return False 
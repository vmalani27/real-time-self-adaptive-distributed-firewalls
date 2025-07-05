import os
import time
import json
import requests
from datetime import datetime

OFFSET_FILE = '/tmp/suricata_eve_log.offset'

def post_with_retry(url, payload, retries=3, delay=2):
    for attempt in range(retries):
        try:
            resp = requests.post(url, json=payload, timeout=3)
            if resp.status_code == 200:
                return True
        except Exception as e:
            if attempt == retries - 1:
                print(f"[SuricataAlerts] Failed to send alert after {retries} attempts: {e}")
            else:
                time.sleep(delay)
    return False

def start_suricata_alerts(config):
    agent_id = config.get('AGENT_ID', 'unknown')
    suricata_log_path = config.get('SURICATA_LOG_PATH', '/var/log/suricata/eve.json')
    controller_ip = config.get('CONTROLLER_IP', '127.0.0.1')
    controller_port = config.get('CONTROLLER_ALERT_PORT', '5051')
    alert_url = f"http://{controller_ip}:{controller_port}/api/suricata-alert"
    seen = set()
    offset = 0
    # Load offset if exists
    if os.path.exists(OFFSET_FILE):
        try:
            with open(OFFSET_FILE, 'r') as f:
                offset = int(f.read().strip())
        except Exception:
            offset = 0
    while True:
        if not os.path.exists(suricata_log_path):
            time.sleep(5)
            continue
        with open(suricata_log_path, 'r') as f:
            f.seek(offset)
            lines = f.readlines()
            offset = f.tell()
        # Save offset
        with open(OFFSET_FILE, 'w') as f:
            f.write(str(offset))
        for line in lines:
            try:
                entry = json.loads(line)
            except Exception:
                continue
            if entry.get('event_type') != 'alert':
                continue
            alert = entry.get('alert', {})
            if alert.get('severity', 0) < 2:
                continue
            sig_id = alert.get('signature_id', 'unknown')
            src_ip = entry.get('src_ip', 'unknown')
            dest_ip = entry.get('dest_ip', 'unknown')
            timestamp = entry.get('timestamp', datetime.utcnow().isoformat())
            uniq = f"{sig_id}:{src_ip}->{dest_ip}:{timestamp}"
            if uniq in seen:
                continue
            seen.add(uniq)
            alert_obj = {
                "agent_id": agent_id,
                "event_type": "suricata_alert",
                "description": alert.get('signature', 'Suricata alert'),
                "source_ip": src_ip,
                "dest_ip": dest_ip,
                "timestamp": timestamp
            }
            post_with_retry(alert_url, alert_obj)
        time.sleep(10) 
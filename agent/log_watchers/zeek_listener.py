# Zeek log watcher is deprecated and not used anymore.
# All code below is commented out.
# import os
# import time
# import json
# import requests
# from datetime import datetime
# 
# OFFSET_FILE = '/tmp/zeek_conn_log.offset'
# 
# def parse_conn_log(line):
#     # Zeek conn.log TSV: https://docs.zeek.org/en/current/scripts/base/protocols/conn/main.zeek.html#type-Conn::Info
#     fields = line.strip().split('\t')
#     if len(fields) < 9:
#         return None
#     return {
#         'ts': fields[0],
#         'uid': fields[1],
#         'src_ip': fields[2],
#         'src_port': fields[3],
#         'dest_ip': fields[4],
#         'dest_port': fields[5],
#         'proto': fields[6],
#         'service': fields[7],
#         'duration': fields[8],
#     }
# 
# def detect_beaconing(conn_entries):
#     # Simple: flag >N connections from same src_ip to same dest_ip in short time
#     counts = {}
#     for entry in conn_entries:
#         key = (entry['src_ip'], entry['dest_ip'])
#         counts[key] = counts.get(key, 0) + 1
#     for (src, dst), count in counts.items():
#         if count > 10:
#             yield src, dst, count
# 
# def post_with_retry(url, payload, retries=3, delay=2):
#     for attempt in range(retries):
#         try:
#             resp = requests.post(url, json=payload, timeout=3)
#             if resp.status_code == 200:
#                 return True
#         except Exception as e:
#             if attempt == retries - 1:
#                 print(f"[ZeekListener] Failed to send alert after {retries} attempts: {e}")
#             else:
#                 time.sleep(delay)
#     return False
# 
# def start_zeek_listener(config):
#     agent_id = config.get('AGENT_ID', 'unknown')
#     zeek_log_path = config.get('ZEEK_LOG_PATH', '/var/log/zeek/current/')
#     controller_ip = config.get('CONTROLLER_IP', '127.0.0.1')
#     controller_port = config.get('CONTROLLER_ALERT_PORT', '5051')
#     alert_url = f"http://{controller_ip}:{controller_port}/api/zeek-alert"
#     conn_log = os.path.join(zeek_log_path, 'conn.log')
#     seen = set()
#     offset = 0
#     # Load offset if exists
#     if os.path.exists(OFFSET_FILE):
#         try:
#             with open(OFFSET_FILE, 'r') as f:
#                 offset = int(f.read().strip())
#         except Exception:
#             offset = 0
#     while True:
#         if not os.path.exists(conn_log):
#             time.sleep(5)
#             continue
#         with open(conn_log, 'r') as f:
#             f.seek(offset)
#             lines = f.readlines()
#             offset = f.tell()
#         # Save offset
#         with open(OFFSET_FILE, 'w') as f:
#             f.write(str(offset))
#         conn_entries = [parse_conn_log(l) for l in lines if not l.startswith('#')]
#         conn_entries = [e for e in conn_entries if e]
#         for src, dst, count in detect_beaconing(conn_entries):
#             alert_id = f"{src}->{dst}:{count}"
#             if alert_id in seen:
#                 continue
#             seen.add(alert_id)
#             alert = {
#                 "agent_id": agent_id,
#                 "event_type": "zeek_conn_alert",
#                 "description": f"Suspicious repeated connections: {count} from {src} to {dst}",
#                 "source_ip": src,
#                 "dest_ip": dst,
#                 "timestamp": datetime.utcnow().isoformat()
#             }
#             post_with_retry(alert_url, alert)
#         time.sleep(10)
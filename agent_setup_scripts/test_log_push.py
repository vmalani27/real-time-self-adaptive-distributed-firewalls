import random
import time
from central_engine import log_collector

AGENT_IDS = ['agent1', 'agent2']
TOOLS = ['zeek', 'suricata']
ALERT_TYPES = ['scan', 'dos', 'malware', 'policy']
SEVERITIES = ['low', 'medium', 'high', 'critical']

for i in range(10):
    payload = {
        'timestamp': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'agent_id': random.choice(AGENT_IDS),
        'tool': random.choice(TOOLS),
        'src_ip': f'192.168.1.{random.randint(2, 254)}',
        'src_port': random.randint(1024, 65535),
        'dest_ip': f'10.0.0.{random.randint(2, 254)}',
        'dest_port': random.randint(1, 1024),
        'protocol': random.choice(['tcp', 'udp', 'icmp']),
        'alert_type': random.choice(ALERT_TYPES),
        'severity': random.choice(SEVERITIES),
        'message': f'Test log message {i}'
    }
    log_collector.append_log(payload)
    print(f"Pushed log: {payload}")
    time.sleep(0.2) 
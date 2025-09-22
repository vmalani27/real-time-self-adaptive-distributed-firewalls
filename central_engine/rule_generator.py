import time
import re
from utils.constants import DEFAULT_RULE_FORMAT
from utils.helpers import validate_rule, load_env_config, get_config_value
import os

# Load configuration
config = load_env_config('central_engine/config.yaml')

def is_valid_ip(ip):
    pattern = r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"
    if not re.match(pattern, ip):
        return False
    return all(0 <= int(part) <= 255 for part in ip.split('.'))

def is_valid_port(port):
    return isinstance(port, int) and 1 <= port <= 65535

def load_whitelist():
    whitelist_path = get_config_value('WHITELIST_CONFIG_PATH', 'central_engine/whitelist.conf', config)
    if not os.path.exists(whitelist_path):
        return set()
    with open(whitelist_path, 'r') as f:
        return set(line.strip() for line in f if line.strip() and not line.startswith('#'))

def generate_nft_rule(anomaly_dict):
    src_ip = anomaly_dict.get('source_ip')
    dst_port = anomaly_dict.get('dest_port')
    attack_type = anomaly_dict.get('attack_type')
    whitelist = load_whitelist()
    if src_ip in whitelist:
        print(f"[rule_generator] Skipping rule for whitelisted IP: {src_ip}")
        return {'rule_str': None, 'metadata': {'source_ip': src_ip, 'whitelisted': True}}
    if not (is_valid_ip(src_ip) and is_valid_port(dst_port)):
        raise ValueError('Invalid IP or port')
    rule_str = f"nft add rule inet filter input ip saddr {src_ip} tcp dport {dst_port} drop"
    metadata = {
        'source_ip': src_ip,
        'dest_port': dst_port,
        'attack_type': attack_type,
        'timestamp': int(time.time())
    }
    return {'rule_str': rule_str, 'metadata': metadata}

def map_alert_to_rule(alert):
    """Maps a high-level anomaly alert to an nftables-compatible rule string."""
    # Try to extract relevant fields
    src_ip = alert.get('source_ip')
    dest_ip = alert.get('dest_ip')
    event_type = alert.get('event_type', '')
    description = alert.get('description', '')
    whitelist = load_whitelist()
    # Default: block source IP
    if src_ip and is_valid_ip(src_ip):
        if src_ip in whitelist:
            print(f"[rule_generator] Skipping rule for whitelisted IP: {src_ip}")
            return {'rule_str': None, 'metadata': {'source_ip': src_ip, 'whitelisted': True}}
        rule_str = f"nft add rule inet filter input ip saddr {src_ip} drop"
    else:
        rule_str = None
    # If Suricata alert with dest_port, block src_ip:dest_port
    dest_port = alert.get('dest_port') or alert.get('dest_port') or None
    if dest_port:
        try:
            port = int(dest_port)
            if is_valid_port(port) and src_ip and is_valid_ip(src_ip):
                if src_ip in whitelist:
                    print(f"[rule_generator] Skipping rule for whitelisted IP: {src_ip}")
                    return {'rule_str': None, 'metadata': {'source_ip': src_ip, 'whitelisted': True}}
                rule_str = f"nft add rule inet filter input ip saddr {src_ip} tcp dport {port} drop"
        except Exception:
            pass
    # If Zeek beaconing, block src_ip to dest_ip
    if event_type == 'zeek_conn_alert' and src_ip and dest_ip and is_valid_ip(src_ip) and is_valid_ip(dest_ip):
        if src_ip in whitelist:
            print(f"[rule_generator] Skipping rule for whitelisted IP: {src_ip}")
            return {'rule_str': None, 'metadata': {'source_ip': src_ip, 'whitelisted': True}}
        rule_str = f"nft add rule inet filter input ip saddr {src_ip} ip daddr {dest_ip} drop"
    # Metadata for traceability
    metadata = {
        'source_ip': src_ip,
        'dest_ip': dest_ip,
        'event_type': event_type,
        'description': description,
        'timestamp': int(time.time())
    }
    return {'rule_str': rule_str, 'metadata': metadata} 
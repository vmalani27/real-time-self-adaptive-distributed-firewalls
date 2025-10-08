import re
import hashlib
import json
import os
from typing import Dict, Any

def validate_rule(rule):
    """Validates a rule before applying. Checks for nftables structure and denies dangerous characters/commands."""
    if not isinstance(rule, str):
        return False
    # Basic nftables rule structure: must start with 'nft add rule'
    if not rule.strip().startswith('nft add rule'):
        return False
    # Deny dangerous shell characters
    if re.search(r'[;&|`$><]', rule):
        return False
    # Deny commands that could flush/delete tables
    dangerous_cmds = [
        'flush', 'delete table', 'delete chain', 'reset', 'shutdown', 'reboot', 'mkfs', 'rm -rf', 'wget', 'curl', 'python', 'bash', 'sh', 'os.system', 'subprocess', 'eval', 'exec'
    ]
    for cmd in dangerous_cmds:
        if cmd in rule:
            return False
    # Only allow alphanumerics, spaces, and basic punctuation
    if not re.match(r'^[a-zA-Z0-9\s\-\./:_]+$', rule):
        return False
    return True

def hash_log_entry(entry):
    """Hashes a log entry for tamper-evidence. Accepts dict or str, returns SHA-256 hex digest."""
    if isinstance(entry, dict):
        entry_str = json.dumps(entry, sort_keys=True)
    else:
        entry_str = str(entry)
    return hashlib.sha256(entry_str.encode('utf-8')).hexdigest()

def load_env_config(config_file_path: str = None) -> Dict[str, Any]:
    """
    Load configuration from .env file and config.yaml with .env taking priority.
    
    Args:
        config_file_path: Optional path to config.yaml file
    
    Returns:
        Dictionary with configuration values
    """
    config = {}
    
    # First, try to load from .env file
    env_file_paths = ['.env', 'central_engine/.env', 'agent/.env']
    
    for env_path in env_file_paths:
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip()] = value.strip().strip('"').strip("'")
                print(f"[Config] Loaded .env from: {env_path}")
                break
            except Exception as e:
                print(f"[Config] Error reading {env_path}: {e}")
    
    # Then load from environment variables (these override .env)
    for key, value in os.environ.items():
        config[key] = value
    
    # YAML/config.yaml fallback support removed - configuration is read from .env files and environment variables only.
    
    # Set defaults for missing values
    defaults = {
        # Common Configuration
        'API_KEY': 'changeme',
        'CONTROLLER_IP': '127.0.0.1',
        'CONTROLLER_ALERT_PORT': '5051',
        'API_SERVER_PORT': '8000',
    # WebSocket support removed; no WS_PORT default
        'LOG_DIR': '../logs',
        'NETWORK_INTERFACE': 'eth0',
        'DEBUG_MODE': 'false',
        'VERBOSE_LOGGING': 'false',
        
        # Central Engine Defaults
        'ENABLE_QUARANTINE': 'true',
        'ALERT_CACHE_TTL': '300',
        'QUARANTINE_CHECK_INTERVAL': '180',
        'MAX_RULES_PER_AGENT': '1000',
        'RULE_EXPIRY_HOURS': '24',
        'ENABLE_RULE_DEDUPLICATION': 'true',
        'ENABLE_ZEEK_INTEGRATION': 'true',
        'ENABLE_SURICATA_INTEGRATION': 'true',
        'MAX_CONCURRENT_DISPATCHES': '10',
        'BATCH_RULE_SIZE': '50',
        'WHITELIST_CONFIG_PATH': 'central_engine/whitelist.conf',
        'RULE_LOG_FILE': '../logs/rules.csv',
        
        # Agent Defaults
        'AGENT_ID': 'agent1',
        'AGENT_NAME': 'firewall_agent',
        'AGENT_REST_PORT': '5001',
    # Agent WebSocket port deprecated
        'CONTROLLER_URL': 'http://127.0.0.1:8000/ack',
    # Zeek integration deprecated
        'SURICATA_LOG_PATH': '/var/log/suricata/eve.json',
        'LOCAL_LOG_DIR': '/var/log/firewall_agent/',
        'NFT_TABLE_NAME': 'firewall_agent',
        'NFT_CHAIN_NAME': 'input_filter',
        'ENABLE_RULE_VALIDATION': 'true',
        'MAX_RULES_CACHE': '500',
    # Zeek integration deprecated
        'SURICATA_POLL_INTERVAL': '3',
        'LOG_BATCH_SIZE': '100',
        'ENABLE_LOG_ROTATION': 'true',
        'MAX_LOG_SIZE_MB': '10',
        'MONITOR_INTERFACE': 'eth0',
        'ENABLE_PACKET_CAPTURE': 'false',
        'ENABLE_RULE_BACKUP': 'true',
        'BACKUP_RETENTION_DAYS': '7',
        'TAMPER_DETECTION': 'true',
        'MAX_CONCURRENT_RULES': '100',
        'RULE_APPLICATION_TIMEOUT': '30',
        'HEARTBEAT_INTERVAL': '60',
        'TEST_MODE': 'false'
    }
    
    for key, default_value in defaults.items():
        if key not in config:
            config[key] = default_value
    
    print(f"[Config] Final config loaded with {len(config)} parameters")
    if config.get('DEBUG_MODE', '').lower() == 'true':
        print(f"[Config] Debug mode - config keys: {list(config.keys())}")
    
    return config

def get_config_value(key: str, default: Any = None, config: Dict[str, Any] = None) -> Any:
    """
    Get a configuration value with type conversion.
    
    Args:
        key: Configuration key
        default: Default value if key not found
        config: Configuration dict (loads if None)
    
    Returns:
        Configuration value with appropriate type
    """
    if config is None:
        config = load_env_config()
    
    value = config.get(key, default)
    
    # Convert string representations to appropriate types
    if isinstance(value, str):
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            pass
    
    return value 
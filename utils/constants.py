DEFAULT_RULE_FORMAT = "nft add rule inet filter input ..."
DEFAULT_PORT_RANGE = (1, 65535)
RULE_TIMEOUT = 30  # seconds
QUARANTINE_RULE_TEMPLATE = "nft add rule inet firewall forward ip saddr {ip} drop"
QUARANTINE_CHECK_INTERVAL = 180  # seconds (3 minutes)
HIGH_RISK_KEYWORDS = ["Malware", "Beaconing", "Ransomware", "C2", "Botnet"] 
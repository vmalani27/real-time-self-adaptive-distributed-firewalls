import requests
import time
import json
## import websockets
## import asyncio
from central_engine import rule_logger
from utils.helpers import load_env_config, get_config_value

# Load configuration once at module level
config = load_env_config()

def dispatch_rule(rule_dict):
    # Get agent configuration from env variables
    agent_ip = get_config_value('AGENT_1_IP', '127.0.0.1', config)
    agent_port = get_config_value('AGENT_1_PORT', '5001', config)
    api_key = get_config_value('API_KEY', 'changeme', config)
    
    agent_url = f"http://{agent_ip}:{agent_port}/apply-rule"
    headers = {'x-api-key': api_key, 'Content-Type': 'application/json'}
    
    for attempt in range(2):
        try:
            resp = requests.post(agent_url, json=rule_dict, headers=headers, timeout=5)
            return resp.status_code, resp.text
        except Exception as e:
            if attempt == 1:
                return 500, str(e)
            time.sleep(1)

def send_rule_to_agent(agent_ip, rule):
    """Sends a rule to an agent via REST API."""
    pass

# WebSocket dispatch support removed. Dispatcher uses REST via dispatch_rule().
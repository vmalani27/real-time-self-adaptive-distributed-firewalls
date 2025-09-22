import requests
import yaml
import time
import json
import websockets
import asyncio
from central_engine import rule_logger
from utils.helpers import load_env_config, get_config_value

# Load configuration once at module level
config = load_env_config('central_engine/config.yaml')

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
    """Sends a rule to an agent via REST API or WebSocket."""
    pass

def dispatch_rule_ws(rule_obj):
    # Get agent configuration from env variables
    agent_ip = get_config_value('AGENT_1_IP', '127.0.0.1', config)
    agent_ws_port = get_config_value('AGENT_1_WS_PORT', '9000', config)
    
    ws_url = f"ws://{agent_ip}:{agent_ws_port}/ws/rule"
    
    async def send_ws():
        try:
            async with websockets.connect(ws_url, ping_interval=None) as ws:
                await ws.send(json.dumps(rule_obj))
                try:
                    ack = await asyncio.wait_for(ws.recv(), timeout=5)
                    rule_logger.log_rule({'ws_status': 'success', 'ack': ack, **rule_obj})
                    print('WebSocket rule push success:', ack)
                    return True
                except asyncio.TimeoutError:
                    rule_logger.log_rule({'ws_status': 'no_ack', **rule_obj})
                    print('WebSocket rule push: no ACK, closing')
                    return True
        except Exception as e:
            print('WebSocket rule push failed:', e)
            return False
    try:
        result = asyncio.get_event_loop().run_until_complete(send_ws())
        if not result:
            print('Falling back to REST dispatch')
            status, resp = dispatch_rule(rule_obj)
            rule_logger.log_rule({'rest_status': status, 'rest_resp': resp, **rule_obj})
            return status, resp
        return 200, 'WebSocket push success'
    except Exception as e:
        print('WebSocket dispatch error:', e)
        status, resp = dispatch_rule(rule_obj)
        rule_logger.log_rule({'rest_status': status, 'rest_resp': resp, **rule_obj})
        return status, resp 

def terminate_ws_connection(ip):
    # TODO: Implement actual WebSocket termination logic for agent with given IP
    print(f"[Dispatcher] Terminating WebSocket connection for {ip}") 
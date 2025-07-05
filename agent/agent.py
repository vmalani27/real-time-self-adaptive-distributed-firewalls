from fastapi import FastAPI, Request, Header, HTTPException
import os
from agent import nft_manager
import time
from agent.ws_receiver import router as ws_router
import threading
import yaml

app = FastAPI()
app.include_router(ws_router)
API_KEY = os.environ.get('API_KEY', 'changeme')

def load_config():
    config = {}
    # Load from .env if present
    if os.path.exists('.env'):
        with open('.env') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    config[k.strip()] = v.strip()
    # Fallback to config.yaml
    if not config.get('AGENT_ID') or not config.get('ZEEK_LOG_PATH') or not config.get('SURICATA_LOG_PATH'):
        if os.path.exists('central_engine/config.yaml'):
            with open('central_engine/config.yaml') as f:
                yml = yaml.safe_load(f)
                agent = yml.get('agents', [{}])[0]
                if not config.get('AGENT_ID') and agent.get('id'):
                    config['AGENT_ID'] = agent['id']
                if not config.get('ZEEK_LOG_PATH') and agent.get('zeek_log_path'):
                    config['ZEEK_LOG_PATH'] = agent['zeek_log_path']
                if not config.get('SURICATA_LOG_PATH') and agent.get('suricata_log_path'):
                    config['SURICATA_LOG_PATH'] = agent['suricata_log_path']
    return config

config = load_config()

@app.post('/apply-rule')
async def apply_rule(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')
    data = await request.json()
    rule = data.get('rule_str')
    result = nft_manager.apply_rule(rule)
    return {
        'status': result['status'],
        'message': result['message'],
        'timestamp': int(time.time())
    }

# Start log watcher threads
try:
    from agent.log_watchers.zeek_listener import start_zeek_listener
    from agent.log_watchers.suricata_alerts import start_suricata_alerts
    zeek_thread = threading.Thread(target=start_zeek_listener, args=(config,), daemon=True)
    suricata_thread = threading.Thread(target=start_suricata_alerts, args=(config,), daemon=True)
    zeek_thread.start()
    suricata_thread.start()
except ImportError:
    print('Log watcher modules not found. Skipping log monitoring.')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001) 
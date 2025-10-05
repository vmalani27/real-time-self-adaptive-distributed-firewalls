from fastapi import FastAPI, Request, Header, HTTPException
import os
from agent import nft_manager
import time
## from agent.ws_receiver import router as ws_router
import threading
from dotenv import load_dotenv

app = FastAPI()
## app.include_router(ws_router)

load_dotenv('agent.env')
API_KEY = os.getenv('API_KEY', 'changeme')
AGENT_REST_PORT = int(os.getenv('AGENT_REST_PORT', '5001'))

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
    app.run(host='0.0.0.0', port=AGENT_REST_PORT)
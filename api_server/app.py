from fastapi import FastAPI, Request, Header, HTTPException
import yaml
import central_engine.dispatcher as dispatcher
import central_engine.rule_logger as rule_logger
from central_engine.trigger_engine import is_quarantined
from utils.helpers import load_env_config, get_config_value

# Load configuration from environment variables
config = load_env_config('central_engine/config.yaml')
API_KEY = get_config_value('API_KEY', 'changeme', config)

app = FastAPI()

@app.post('/push-rule')
async def push_rule(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')
    data = await request.json()
    src_ip = data.get('metadata', {}).get('source_ip')
    if src_ip and is_quarantined(src_ip):
        # Only allow explicit allow rules (future work)
        return {'status': 'blocked', 'response': f'Agent {src_ip} is quarantined. Rule push not allowed.'}
    status, resp = dispatcher.dispatch_rule(data)
    return {'status': status, 'response': resp}

@app.post('/ack')
async def ack(request: Request, x_api_key: str = Header(None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail='Unauthorized')
    data = await request.json()
    rule_logger.log_rule(data)
    return {'status': 'logged'} 
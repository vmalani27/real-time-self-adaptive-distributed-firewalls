from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import json
from agent import nft_manager
import requests
import os
from utils.helpers import load_env_config, get_config_value

router = APIRouter()

# Load configuration
config = load_env_config('central_engine/config.yaml')
API_KEY = get_config_value('API_KEY', 'changeme', config)
CONTROLLER_URL = get_config_value('CONTROLLER_URL', 'http://localhost:8000/ack', config)

@router.websocket('/ws/rule')
async def ws_rule(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_text()
        try:
            rule_obj = json.loads(data)
            rule_str = rule_obj.get('rule_str')
            if not rule_str:
                await websocket.close(code=4001)
                return
            result = nft_manager.apply_rule(rule_str)
            print('WS rule applied:', result)
            ack = {
                'rule': rule_str,
                'status': result['status'],
                'message': result['message']
            }
            headers = {'x-api-key': API_KEY}
            try:
                requests.post(CONTROLLER_URL, json=ack, headers=headers, timeout=5)
            except Exception:
                pass
            await websocket.send_text(json.dumps({'ack': result['status']}))
        except Exception:
            await websocket.close(code=4002)
    except WebSocketDisconnect:
        pass 
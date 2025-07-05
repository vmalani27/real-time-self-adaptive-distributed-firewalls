from fastapi import FastAPI, Request
import json
from central_engine import dispatcher, rule_logger, rule_generator
import hashlib
import time

app = FastAPI()

RECENT_ALERT_HASHES = set()
RECENT_ALERT_EXPIRY = {}
ALERT_CACHE_TTL = 300  # seconds

def alert_hash(alert):
    # Hash relevant fields for deduplication
    s = json.dumps({k: alert[k] for k in sorted(alert) if k in ('source_ip','dest_ip','event_type','description')}, sort_keys=True)
    return hashlib.sha256(s.encode()).hexdigest()

def cleanup_alert_cache():
    now = time.time()
    expired = [h for h, t in RECENT_ALERT_EXPIRY.items() if now - t > ALERT_CACHE_TTL]
    for h in expired:
        RECENT_ALERT_HASHES.discard(h)
        RECENT_ALERT_EXPIRY.pop(h, None)

@app.post('/api/zeek-alert')
async def zeek_alert(request: Request):
    alert = await request.json()
    cleanup_alert_cache()
    h = alert_hash(alert)
    if h in RECENT_ALERT_HASHES:
        return {'status': 'duplicate', 'resp': 'Alert already processed'}
    RECENT_ALERT_HASHES.add(h)
    RECENT_ALERT_EXPIRY[h] = time.time()
    rule_obj = rule_generator.map_alert_to_rule(alert)
    status, resp = dispatcher.dispatch_rule_ws(rule_obj)
    rule_logger.log_rule({'source': 'zeek', 'alert': alert, 'status': status, 'resp': resp})
    return {'status': status, 'resp': resp}

@app.post('/api/suricata-alert')
async def suricata_alert(request: Request):
    alert = await request.json()
    cleanup_alert_cache()
    h = alert_hash(alert)
    if h in RECENT_ALERT_HASHES:
        return {'status': 'duplicate', 'resp': 'Alert already processed'}
    RECENT_ALERT_HASHES.add(h)
    RECENT_ALERT_EXPIRY[h] = time.time()
    rule_obj = rule_generator.map_alert_to_rule(alert)
    status, resp = dispatcher.dispatch_rule_ws(rule_obj)
    rule_logger.log_rule({'source': 'suricata', 'alert': alert, 'status': status, 'resp': resp})
    return {'status': status, 'resp': resp} 
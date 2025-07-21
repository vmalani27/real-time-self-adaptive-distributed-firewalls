from fastapi import FastAPI, Request
import json
from central_engine import dispatcher, rule_logger, rule_generator
import hashlib
import time
import threading
import asyncio
from utils.constants import QUARANTINE_RULE_TEMPLATE, HIGH_RISK_KEYWORDS, QUARANTINE_CHECK_INTERVAL
from central_engine.dispatcher import terminate_ws_connection

app = FastAPI()

RECENT_ALERT_HASHES = set()
RECENT_ALERT_EXPIRY = {}
ALERT_CACHE_TTL = 300  # seconds

# Quarantine state: {ip: {"timestamp": ..., "reason": ..., "active": True}}
QUARANTINED_AGENTS = {}
QUARANTINE_LOCK = threading.Lock()

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

async def quarantine_agent(ip, reason):
    with QUARANTINE_LOCK:
        if ip in QUARANTINED_AGENTS and QUARANTINED_AGENTS[ip]["active"]:
            print(f"[Quarantine] {ip} already quarantined.")
            return False
        QUARANTINED_AGENTS[ip] = {"timestamp": int(time.time()), "reason": reason, "active": True}
    rule = QUARANTINE_RULE_TEMPLATE.format(ip=ip)
    # Securely execute nft command (dispatch to agent)
    rule_obj = {"rule_str": rule, "metadata": {"source_ip": ip, "reason": reason, "timestamp": int(time.time()), "quarantine": True}}
    status, resp = dispatcher.dispatch_rule_ws(rule_obj)
    rule_logger.log_rule({"source": "quarantine", "alert": {"source_ip": ip, "reason": reason}, "status": status, "resp": resp, "quarantine": True})
    # Terminate WebSocket connection for this agent
    terminate_ws_connection(ip)
    print(f"[Quarantine] {ip} quarantined for: {reason}")
    return True

def is_high_risk(alert):
    severity = alert.get("severity", 0)
    description = alert.get("description", "")
    if severity and int(severity) >= 3:
        return True
    for kw in HIGH_RISK_KEYWORDS:
        if kw.lower() in description.lower():
            return True
    return False

def is_quarantined(ip):
    with QUARANTINE_LOCK:
        return ip in QUARANTINED_AGENTS and QUARANTINED_AGENTS[ip]["active"]

def is_whitelisted(ip):
    # Use rule_generator's load_whitelist
    try:
        from central_engine.rule_generator import load_whitelist
        whitelist = load_whitelist()
        return ip in whitelist
    except Exception:
        return False

async def periodic_quarantine_check():
    while True:
        await asyncio.sleep(QUARANTINE_CHECK_INTERVAL)
        with QUARANTINE_LOCK:
            quarantined = [ip for ip, v in QUARANTINED_AGENTS.items() if v["active"]]
        for ip in quarantined:
            # Here, send REST request to agent to check infection status (stub for now)
            print(f"[Quarantine] Periodic check for {ip}")
            # TODO: Implement actual infection check logic
            # If infection cleared, set QUARANTINED_AGENTS[ip]["active"] = False (future work)

@app.on_event("startup")
def start_quarantine_scheduler():
    loop = asyncio.get_event_loop()
    loop.create_task(periodic_quarantine_check())

@app.post('/api/zeek-alert')
async def zeek_alert(request: Request):
    alert = await request.json()
    cleanup_alert_cache()
    h = alert_hash(alert)
    if h in RECENT_ALERT_HASHES:
        return {'status': 'duplicate', 'resp': 'Alert already processed'}
    RECENT_ALERT_HASHES.add(h)
    RECENT_ALERT_EXPIRY[h] = time.time()
    src_ip = alert.get('source_ip')
    if src_ip and is_whitelisted(src_ip):
        print(f"[trigger_engine] Skipping action for whitelisted IP: {src_ip}")
        rule_logger.log_rule({'source': 'zeek', 'alert': alert, 'skipped': True, 'reason': 'whitelisted'})
        return {'status': 'skipped', 'resp': f'{src_ip} is whitelisted'}
    if src_ip and is_high_risk(alert):
        await quarantine_agent(src_ip, alert.get('description', 'High severity alert'))
        return {'status': 'quarantined', 'resp': f'{src_ip} quarantined'}
    rule_obj = rule_generator.map_alert_to_rule(alert)
    if not rule_obj.get('rule_str'):
        rule_logger.log_rule({'source': 'zeek', 'alert': alert, 'skipped': True, 'reason': 'whitelisted'})
        return {'status': 'skipped', 'resp': f'{src_ip} is whitelisted'}
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
    src_ip = alert.get('source_ip')
    if src_ip and is_whitelisted(src_ip):
        print(f"[trigger_engine] Skipping action for whitelisted IP: {src_ip}")
        rule_logger.log_rule({'source': 'suricata', 'alert': alert, 'skipped': True, 'reason': 'whitelisted'})
        return {'status': 'skipped', 'resp': f'{src_ip} is whitelisted'}
    if src_ip and is_high_risk(alert):
        await quarantine_agent(src_ip, alert.get('description', 'High severity alert'))
        return {'status': 'quarantined', 'resp': f'{src_ip} quarantined'}
    rule_obj = rule_generator.map_alert_to_rule(alert)
    if not rule_obj.get('rule_str'):
        rule_logger.log_rule({'source': 'suricata', 'alert': alert, 'skipped': True, 'reason': 'whitelisted'})
        return {'status': 'skipped', 'resp': f'{src_ip} is whitelisted'}
    status, resp = dispatcher.dispatch_rule_ws(rule_obj)
    rule_logger.log_rule({'source': 'suricata', 'alert': alert, 'status': status, 'resp': resp})
    return {'status': status, 'resp': resp} 
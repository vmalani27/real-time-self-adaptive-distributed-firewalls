# self_adaptive_fw

A modular, Python-based self-adaptive distributed firewall controller for real-time network anomaly detection and automated rule enforcement across distributed endpoints.

## Architecture

- **Central Engine**: Detects anomalies, generates nftables rules, dispatches to agents (via REST or WebSocket), and logs all actions.
- **Agent**: Receives rules via REST or WebSocket, applies them using nft, and sends acknowledgments via REST. Also runs background log watchers for Zeek and Suricata alerts.
- **Monitoring**: Uses Zeek/Scapy to detect attacks (e.g., SYN flood) and triggers rule generation.
- **API Server**: FastAPI-based REST interface for rule push and agent ACKs.
- **Utils/Tests**: Common helpers, constants, and unit tests.

## Directory Structure

```
central_engine/
  main.py           # Main coordinator
  trie_engine.py    # Trie for IP/pattern matching
  rule_generator.py # Rule string generation
  dispatcher.py     # Rule dispatch to agents (REST & WebSocket)
  rule_logger.py    # Rule logging and rollback
  trigger_engine.py # Receives Zeek/Suricata alerts, triggers rules
  config.yaml       # Configuration (agent IPs, API keys, etc.)

api_server/
  app.py            # FastAPI server for rule push/ack

agent/
  agent.py          # FastAPI server for rule application (REST & WebSocket)
  nft_manager.py    # Applies nft rules securely
  ws_receiver.py    # WebSocket endpoint for rule push
  log_watchers/
    zeek_listener.py    # Watches Zeek logs for threats
    suricata_alerts.py  # Watches Suricata eve.json for alerts

monitoring/
  scapy_sniffer.py  # Scapy-based anomaly detection
  zeek_scripts/     # Zeek detection scripts

utils/
  helpers.py        # Common helpers
  constants.py      # Static data

tests/
  test_trie.py      # Trie unit tests
  test_rule_gen.py  # Rule generation tests
```

## Features

- Real-time anomaly detection (SYN flood, port scan, etc.)
- Trie-based efficient pattern/rule matching
- Automated nftables rule generation and dispatch
- RESTful and WebSocket agent communication with API key security
- Tamper-evident, append-only rule logging
- Rollback and versioning for firewall rules
- Zeek and Suricata log watchers for distributed threat detection
- Rule deduplication and robust alert delivery
- Unit tests for core logic

## Endpoints Overview

| Endpoint                     | Module                        | Purpose                                              |
| ---------------------------- | ----------------------------- | ---------------------------------------------------- |
| `/api/zeek-alert` (POST)     | central_engine/trigger_engine | Receives Zeek-based threat alerts from agents        |
| `/api/suricata-alert` (POST) | central_engine/trigger_engine | Receives Suricata-based threat alerts from agents    |
| `/apply-rule` (POST)         | agent/agent.py                | Agent applies nftables rule (REST fallback)          |
| `/ws/rule` (WebSocket)       | agent/ws_receiver.py          | Agent receives rules via WebSocket (preferred)       |
| `/ack` (POST)                | api_server/app.py             | Controller receives rule application acknowledgments |

## Testbed Setup Procedure

### 1. Install Dependencies

```bash
pip install -r requirements.txt
# For agent: pip install fastapi uvicorn websockets pyyaml requests
# For monitoring: pip install scapy
```

### 2. Configure the System

- Edit `central_engine/config.yaml` with agent IP, REST port, WebSocket port, Zeek/Suricata log paths, and API key.
- Set environment variables for agent/controller using `.env` (see `test.env` for example):

```
API_KEY=changeme
CONTROLLER_URL=http://127.0.0.1:8000/ack
AGENT_ID=agent1
ZEEK_LOG_PATH=/var/log/zeek/current/
SURICATA_LOG_PATH=/var/log/suricata/eve.json
CONTROLLER_IP=127.0.0.1
CONTROLLER_ALERT_PORT=5051
```

### 3. Start the Central Engine (Controller)

```bash
uvicorn central_engine.trigger_engine:app --host 0.0.0.0 --port 5051
# Or run main.py for other coordination tasks
```

### 4. Start the Agent

```bash
uvicorn agent.agent:app --host 0.0.0.0 --port 5001
# Or use the provided systemd service (see agent/daemon.service)
```

- The agent will automatically start background threads to watch Zeek and Suricata logs and send alerts to the controller.

### 5. Deploy Monitoring Tools

- **Zeek**: Configure Zeek to write logs to the path specified in `.env`/`config.yaml` (e.g., `/var/log/zeek/current/`).
- **Suricata**: Ensure Suricata writes `eve.json` to the path specified in `.env`/`config.yaml` (e.g., `/var/log/suricata/eve.json`).
- **Scapy**: Optionally run `monitoring/scapy_sniffer.py` for additional anomaly detection.

### 6. Run Tests

```bash
python -m unittest discover tests
```

## How the System Connects

- **Agent → Controller**: When Zeek or Suricata detects a threat, the agent's log watcher sends a POST to the controller's `/api/zeek-alert` or `/api/suricata-alert` endpoint.
- **Controller → Agent**: When a rule needs to be applied, the controller pushes it to the agent via WebSocket (`/ws/rule`). If that fails, it falls back to REST (`/apply-rule`).
- **Agent → Controller**: After applying a rule, the agent sends an acknowledgment to the controller's `/ack` endpoint.

## Security

- All rule and API inputs are validated (IP, port, etc.)
- REST and WebSocket endpoints require API key (configurable)
- No shell=True; all subprocess calls are sanitized
- Rule logs are append-only and tamper-evident
- TODO: Add token verification and origin checks for WebSocket

## Notes

- Requires Linux for nftables and packet capture.
- For production, use HTTPS/mTLS and secure API key storage.
- Extend monitoring/zeek_scripts for custom detection logic.
- Log watcher modules are started automatically by the agent and do not require separate processes.

## [2024-06-09] Update: Removal of Scapy from Central Engine

- The Scapy-based sniffer (`monitoring/scapy_sniffer.py`) has been removed from the project.
- The central engine no longer uses Scapy for packet capture or analysis.
- Zeek and Suricata are now the only monitoring and log generation tools, each running independently on every agent.
- Each agent maintains its own logs in `/var/log/zeek/current/` and `/var/log/suricata/`.
- The rule generation and dispatch pipeline is unaffected by this change.
- Communication between agents and the central engine (WebSockets primary, REST fallback) remains unchanged.
- For agent setup and testing, use the scripts in the new `agent_setup_scripts/` directory.

## Centralized Agent-wise CSV Log Archival (2024-06-09)

The central engine now supports robust, structured, and agent-wise CSV log archival for all incoming logs from agents (Zeek/Suricata). This enables:

- Clean segregation of logs by agent and tool
- Easy post-analysis, threat correlation, and forensics
- Preparation for dashboards and ML model training
- No heavy database overhead

### Log Structure

- **Location:** All logs are stored in the `logs/` directory at the project root (configurable via `central_engine/config.yaml` as `log_dir`).
- **Format:** One CSV file per agent per tool (e.g., `agent1_zeek.csv`, `agent2_suricata.csv`).
- **Fields:**
  - `timestamp, agent_id, tool, src_ip, src_port, dest_ip, dest_port, protocol, alert_type, severity, message`
- **Concurrency:** File locks are used to ensure safe concurrent writes.
- **Rotation:** Logs are currently append-only; rotation/clearing is a future scope.

### Module

- The `central_engine/log_collector.py` module handles incoming log payloads (JSON) over WebSockets or REST, parses them, and appends them to the appropriate CSV file.
- No disruption to the real-time rule generation and dispatch pipeline.

### Usage

- Agents send logs as JSON payloads to the central engine (WebSockets preferred, REST fallback).
- The central engine parses and archives these logs automatically.
- For testing, use the provided test script to simulate agent log pushes.

## Incident Response Quarantine Logic

When a Suricata or Zeek alert is received via `/api/suricata-alert` or `/api/zeek-alert`, the system will:

1. Parse the alert for `source_ip`, `severity`, and `description`.
2. If `severity >= 3` or the description matches high-risk keywords (Malware, Beaconing, etc):
   - Quarantine the agent by blocking its traffic with an nftables rule.
   - Log the quarantine action with timestamp, IP, and reason.
   - Terminate any active WebSocket connection for that agent.
   - Keep the REST connection open for periodic infection checks and log updates only.
   - Prevent duplicate quarantine rules.
3. A background scheduler will ping quarantined agents every 3–5 minutes to check infection status (future work for auto-unquarantine).
4. Other agents remain unaffected and continue normal operation.

### Quarantine Restrictions

- Quarantined agents cannot receive new rules (except explicit allow in future).
- Only log updates and infection checks are allowed during quarantine.
- All actions are append-only logged for audit.

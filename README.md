# self_adaptive_fw

A modular, Python-based self-adaptive distributed firewall controller for real-time network anomaly detection and automated rule enforcement across distributed endpoints.

## Architecture

- **Central Engine**: Detects anomalies, generates nftables rules, dispatches to agents via REST, and logs all actions.
- **Agent**: Receives rules via REST, applies them using nft, and sends acknowledgments via REST. Also runs background log watchers for Suricata alerts.
- **Monitoring**: Uses Scapy to detect attacks (e.g., SYN flood) and triggers rule generation.
- **API Server**: FastAPI-based REST interface for rule push and agent ACKs.
- **Utils/Tests**: Common helpers, constants, and unit tests.

## Directory Structure

```
central_engine/
  main.py           # Main coordinator
  trie_engine.py    # Trie for IP/pattern matching
  rule_generator.py # Rule string generation
  dispatcher.py     # Rule dispatch to agents (REST only)
  rule_logger.py    # Rule logging and rollback
  trigger_engine.py # Receives Suricata alerts, triggers rules
  config.yaml       # Configuration (agent IPs, API keys, etc.)

api_server/
  app.py            # FastAPI server for rule push/ack

agent/
  agent.py          # FastAPI server for rule application (REST only)
  nft_manager.py    # Applies nft rules securely
  # (WebSocket endpoint previously supported; now deprecated)
  log_watchers/
    # zeek_listener.py    # Watches Zeek logs for threats (deprecated)
    suricata_alerts.py  # Watches Suricata eve.json for alerts

monitoring/
  scapy_sniffer.py  # Scapy-based anomaly detection
  zeek_scripts/     # Zeek detection scripts (deprecated)

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
- RESTful agent communication with API key security
- Tamper-evident, append-only rule logging
- Automatic log rotation (per-agent, per-tool CSV logs rotate at 10MB)
- Rollback and versioning for firewall rules (now removes rule from agent, not just marks inactive)
- Whitelisting of IPs to prevent false positives
- Suricata log watcher for distributed threat detection
- Rule deduplication and robust alert delivery
- Unit tests for core logic

## Endpoints Overview

| Endpoint                     | Module                        | Purpose                                              |
| ---------------------------- | ----------------------------- | ---------------------------------------------------- |
| `/api/suricata-alert` (POST) | central_engine/trigger_engine | Receives Suricata-based threat alerts from agents    |
| `/apply-rule` (POST)         | agent/agent.py                | Agent applies nftables rule (REST only)              |
| `/ack` (POST)                | api_server/app.py             | Controller receives rule application acknowledgments |

## Testbed Setup Procedure

### 1. Install Dependencies

```bash
pip install -r requirements.txt
# For agent: pip install fastapi uvicorn pyyaml requests
# For monitoring: pip install scapy
```

### 2. Configure the System

- Edit `central_engine/config.yaml` with agent IP, REST port, Suricata log paths, and API key.
- Set environment variables for agent/controller using `.env` (see `test.env` for example):

```
API_KEY=changeme
CONTROLLER_URL=http://127.0.0.1:8000/ack
AGENT_ID=agent1
# ZEEK_LOG_PATH=/var/log/zeek/current/  # Deprecated
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

- The agent will automatically start background threads to watch Suricata logs and send alerts to the controller.

### 5. Deploy Monitoring Tools

- **Suricata**: Ensure Suricata writes `eve.json` to the path specified in `.env`/`config.yaml` (e.g., `/var/log/suricata/eve.json`).
- **Scapy**: Optionally run `monitoring/scapy_sniffer.py` for additional anomaly detection.

### 6. Run Tests

```bash
python -m unittest discover tests
```

## How the System Connects

- **Agent → Controller**: When Suricata detects a threat, the agent's log watcher sends a POST to the controller's `/api/suricata-alert` endpoint.
- **Controller → Agent**: When a rule needs to be applied, the controller pushes it to the agent via REST (`/apply-rule`).
- **Agent → Controller**: After applying a rule, the agent sends an acknowledgment to the controller's `/ack` endpoint.

## Security

- All rule and API inputs are validated (IP, port, etc.)
- REST endpoints require API key (configurable)
- No shell=True; all subprocess calls are sanitized
- Rule logs are append-only and tamper-evident
- Log entries are hashed for tamper-evidence (SHA-256)
- Firewall rules are validated for safety before application
- Whitelisted IPs are never blocked, even if detected as anomalous

## Whitelisting (False Positive Handling)

To prevent blocking of trusted or critical IPs, the system supports a simple whitelisting mechanism:

- Add IP addresses (one per line) to `central_engine/whitelist.conf`.
- Before generating or dispatching a block rule, the system checks if the source IP is whitelisted.
- If the IP is whitelisted, rule generation and enforcement are skipped, and a message is logged.
- Example whitelist.conf:
  ```
  # Whitelisted IP addresses
  192.168.1.100
  10.0.0.5
  ```

## Log Rotation

- Log files for each agent/tool (e.g., `agent1_suricata.csv`) are automatically rotated when they exceed 10MB.
- The old file is renamed to `.csv.1` and a new log file is started.
- This prevents unbounded log growth and ensures robust, long-term operation.

## Rollback Functionality

- The rollback feature now fully removes the last active rule from the agent by dispatching the corresponding nftables delete command.
- The rollback action is logged and marked as `rolled_back` in the rule log.

## Helper Functions

- `utils/helpers.py` provides:
  - `validate_rule(rule)`: Ensures nftables rules are safe and well-formed before application.
  - `hash_log_entry(entry)`: Returns a SHA-256 hash of a log entry (dict or string) for tamper-evidence.
- `agent/ack_sender.py`: `send_ack(status)` sends rule application status to the controller.
- `monitoring/log_shipper.py`: `ship_logs(log_file)` pushes logs to a central server (configurable).

## Centralized Agent-wise CSV Log Archival

The central engine now supports robust, structured, and agent-wise CSV log archival for all incoming logs from agents (Suricata). This enables:

- Clean segregation of logs by agent and tool
- Easy post-analysis, threat correlation, and forensics
- Preparation for dashboards and ML model training
- No heavy database overhead
- Automatic log rotation at 10MB per file

### Log Structure

- **Location:** All logs are stored in the `logs/` directory at the project root (configurable via `central_engine/config.yaml` as `log_dir`).
- **Format:** One CSV file per agent per tool (e.g., `agent1_suricata.csv`).
- **Fields:**
  - `timestamp, agent_id, tool, src_ip, src_port, dest_ip, dest_port, protocol, alert_type, severity, message`
- **Concurrency:** File locks are used to ensure safe concurrent writes.
- **Rotation:** Logs are currently append-only; rotation/clearing is a future scope.

### Module

- The `central_engine/log_collector.py` module handles incoming log payloads (JSON) over REST, parses them, and appends them to the appropriate CSV file.
- No disruption to the real-time rule generation and dispatch pipeline.

### Usage

- Agents send logs as JSON payloads to the central engine via REST.
- The central engine parses and archives these logs automatically.
- For testing, use the provided test script to simulate agent log pushes.

## Incident Response Quarantine Logic

When a Suricata alert is received via `/api/suricata-alert`, the system will:

1. Parse the alert for `source_ip`, `severity`, and `description`.
2. If `severity >= 3` or the description matches high-risk keywords (Malware, Beaconing, etc):
   - Quarantine the agent by blocking its traffic with an nftables rule.
   - Log the quarantine action with timestamp, IP, and reason.
   - Keep the REST connection open for periodic infection checks and log updates only.
   - Prevent duplicate quarantine rules.
3. A background scheduler will ping quarantined agents every 3–5 minutes to check infection status (future work for auto-unquarantine).
4. Other agents remain unaffected and continue normal operation.

### Quarantine Restrictions

- Quarantined agents cannot receive new rules (except explicit allow in future).
- Only log updates and infection checks are allowed during quarantine.
- All actions are append-only logged for audit.

## Changelog

### [2024-06-10] Major Robustness and Feature Update

- Implemented automatic log rotation for agent-wise CSV logs (10MB per file).
- Enhanced rollback: now removes rules from agents, not just marks as inactive.
- Added whitelisting mechanism (`central_engine/whitelist.conf`) to prevent blocking of trusted IPs.
- Improved rule validation and log hashing for security and tamper-evidence.
- Added helper functions for agent acknowledgment and log shipping.

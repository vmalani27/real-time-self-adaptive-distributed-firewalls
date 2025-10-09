#!/usr/bin/env bash
set -euo pipefail

# smoke_tests.sh
# Usage:
#   bash tests/smoke_tests.sh <CONTROLLER_IP> <CONTROLLER_PORT> <AGENT_IP> <AGENT_PORT> <API_KEY>
# Example:
#   bash tests/smoke_tests.sh 192.168.56.10 5051 192.168.56.11 5001 firewall_demo_key_2025

CTR_IP=${1:-127.0.0.1}
CTR_PORT=${2:-5051}
AGT_IP=${3:-127.0.0.1}
AGT_PORT=${4:-5001}
API_KEY=${5:-changeme}

CTR_URL="http://${CTR_IP}:${CTR_PORT}"
AGT_URL="http://${AGT_IP}:${AGT_PORT}"

echo "Controller: $CTR_URL"
echo "Agent:      $AGT_URL"

req() {
  echo "\n>>> $@" >&2
  eval "$@"
}

echo "\n1) Reachability checks"
req "curl -sS -I ${CTR_URL} || true"
req "curl -sS -I ${AGT_URL} || true"

echo "\n2) Agent direct apply-rule (valid rule)"
req "curl -sS -X POST '${AGT_URL}/apply-rule' -H 'Content-Type: application/json' -H 'x-api-key: ${API_KEY}' -d '{\"rule_str\":\"nft add rule inet filter input ip saddr 1.2.3.4 drop\"}' | jq . || true"

echo "\n3) Agent direct apply-rule (invalid rule)"
req "curl -sS -X POST '${AGT_URL}/apply-rule' -H 'Content-Type: application/json' -H 'x-api-key: ${API_KEY}' -d '{\"rule_str\":\"rm -rf /\"}' | jq . || true"

echo "\n4) Controller: submit normal Suricata alert (end-to-end dispatch)"
PAYLOAD='{\"source_ip\":\"10.0.0.55\",\"dest_ip\":\"8.8.8.8\",\"event_type\":\"alert\",\"description\":\"smoke test normal\",\"severity\":1}'
req "curl -sS -X POST '${CTR_URL}/api/suricata-alert' -H 'Content-Type: application/json' -d '${PAYLOAD}' | jq . || true"

echo "\n5) Deduplication test: send same payload twice"
PAYLOAD2='{\"source_ip\":\"10.0.0.77\",\"dest_ip\":\"8.8.4.4\",\"event_type\":\"alert\",\"description\":\"dup-test\",\"severity\":1}'
req "curl -sS -X POST '${CTR_URL}/api/suricata-alert' -H 'Content-Type: application/json' -d '${PAYLOAD2}' | jq . || true"
req "curl -sS -X POST '${CTR_URL}/api/suricata-alert' -H 'Content-Type: application/json' -d '${PAYLOAD2}' | jq . || true"

echo "\n6) Quarantine trigger (severity >= 3)"
PAYLOAD3='{\"source_ip\":\"10.0.0.99\",\"dest_ip\":\"1.2.3.4\",\"event_type\":\"alert\",\"description\":\"possible beaconing\",\"severity\":4}'
req "curl -sS -X POST '${CTR_URL}/api/suricata-alert' -H 'Content-Type: application/json' -d '${PAYLOAD3}' | jq . || true"

echo "\n7) Malformed payload test (should return error)"
req "curl -sS -X POST '${CTR_URL}/api/suricata-alert' -H 'Content-Type: application/json' -d '{not_json' || true"

echo "\nSmoke tests complete. Inspect controller and agent logs for dispatch and apply-rule activity." 

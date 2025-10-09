#!/usr/bin/env bash
set -euo pipefail

# smoke_tests.sh
# Usage:
#   bash tests/smoke_tests.sh <CONTROLLER_IP> <CONTROLLER_PORT> <AGENT_IP> <AGENT_PORT> <API_KEY>
# Example:
#   bash tests/smoke_tests.sh 192.168.56.10 5051 192.168.56.11 5001 firewall_demo_key_2025

CTR_IP=${1:-192.168.56.10}
CTR_PORT=${2:-5051}
AGT_IP=${3:-192.168.56.11}
AGT_PORT=${4:-5001}
API_KEY=${5:-changeme}

CTR_URL="http://${CTR_IP}:${CTR_PORT}"
AGT_URL="http://${AGT_IP}:${AGT_PORT}"

echo "Controller: $CTR_URL"
echo "Agent:      $AGT_URL"

print_header(){
  echo -e "\n>>> $1" >&2
}

post_json(){
  local url="$1"; shift
  local data="$1"; shift || true
  # Use curl directly with data variable to avoid eval/escaping problems
  if command -v jq >/dev/null 2>&1; then
    curl -sS -X POST "$url" -H 'Content-Type: application/json' -d "$data" | jq . || true
  else
    curl -sS -X POST "$url" -H 'Content-Type: application/json' -d "$data" || true
  fi
}

head_req(){
  local url="$1"
  curl -sS -I "$url" || true
}

echo "\n1) Reachability checks"
print_header "Controller HEAD"
head_req "${CTR_URL}"
print_header "Agent HEAD"
head_req "${AGT_URL}"

echo "\n2) Agent direct apply-rule (valid rule)"
print_header "Agent apply-rule (valid)"
post_json "${AGT_URL}/apply-rule" '{"rule_str":"nft add rule inet filter input ip saddr 1.2.3.4 drop"}' --

echo "\n3) Agent direct apply-rule (invalid rule)"
print_header "Agent apply-rule (invalid)"
post_json "${AGT_URL}/apply-rule" '{"rule_str":"rm -rf /"}' --

echo "\n4) Controller: submit normal Suricata alert (end-to-end dispatch)"
PAYLOAD='{"source_ip":"10.0.0.55","dest_ip":"8.8.8.8","event_type":"alert","description":"smoke test normal","severity":1}'
print_header "Controller suricata-alert (normal)"
post_json "${CTR_URL}/api/suricata-alert" "$PAYLOAD"

echo "\n5) Deduplication test: send same payload twice"
PAYLOAD2='{"source_ip":"10.0.0.77","dest_ip":"8.8.4.4","event_type":"alert","description":"dup-test","severity":1}'
print_header "Deduplication - first"
post_json "${CTR_URL}/api/suricata-alert" "$PAYLOAD2"
print_header "Deduplication - second"
post_json "${CTR_URL}/api/suricata-alert" "$PAYLOAD2"

echo "\n6) Quarantine trigger (severity >= 3)"
PAYLOAD3='{"source_ip":"10.0.0.99","dest_ip":"1.2.3.4","event_type":"alert","description":"possible beaconing","severity":4}'
print_header "Quarantine trigger"
post_json "${CTR_URL}/api/suricata-alert" "$PAYLOAD3"

echo "\n7) Malformed payload test (should return error)"
print_header "Malformed payload"
curl -sS -X POST "${CTR_URL}/api/suricata-alert" -H 'Content-Type: application/json' -d '{not_json' || true

echo "\nSmoke tests complete. Inspect controller and agent logs for dispatch and apply-rule activity." 

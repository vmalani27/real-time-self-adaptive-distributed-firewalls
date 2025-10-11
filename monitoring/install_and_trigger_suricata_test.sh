#!/bin/sh
"""
monitoring/install_and_trigger_suricata_test.sh

Small helper script to install a simple Suricata local rule, validate the Suricata configuration,
and provide a way to trigger an alert from another host. Intended to be run on the Suricata host
(usually the agent VM). Requires root privileges to write into /var/lib/suricata/rules and to
restart Suricata if desired.

Usage:
  sudo ./monitoring/install_and_trigger_suricata_test.sh

What it does:
  1. Creates /var/lib/suricata/rules/local.rules with a simple rule that matches HTTP traffic to
     host 192.168.56.100 (adjust the IP to a reachable test sender) or matches a custom payload.
  2. Runs `suricata -T -c /etc/suricata/suricata.yaml` to validate the config and rule load.
  3. Prints a curl command you can run from another machine to generate traffic that will trigger
     the rule and appear in Suricata's eve.json and (by extension) be picked up by the agent.

Notes:
  - Adjust TARGET_IP to the IP address of the system that will send the test HTTP request.
  - If your Suricata installation stores rules in a different directory, update RULE_DIR.
  - This script does not automatically restart Suricata; it validates the configuration. If you
    prefer automatic restart uncomment the restart lines (some systems prefer `systemctl reload`)
    and test carefully.
"""

set -e

RULE_DIR="/var/lib/suricata/rules"
LOCAL_RULE_FILE="$RULE_DIR/local.rules"
SURICATA_CFG="/etc/suricata/suricata.yaml"

# IP that will be used as the HTTP target in the rule.
# Replace this with the IP of the host where you'll run the trigger curl command.
TARGET_IP="192.168.56.100"

echo "== Suricata local rule installer and trigger helper =="
echo "Rule dir: $RULE_DIR"
echo "Local rule: $LOCAL_RULE_FILE"
echo "Suricata config: $SURICATA_CFG"
echo

if [ ! -d "$RULE_DIR" ]; then
  echo "Rule directory $RULE_DIR does not exist. Please check your Suricata installation." >&2
  exit 2
fi

echo "Writing test rule to $LOCAL_RULE_FILE"
cat > "$LOCAL_RULE_FILE" <<EOF
alert http any any -> $TARGET_IP any (msg:"SAFW-Test-HTTP-Alert"; sid:1000001; rev:1; classtype:attempted-recon;)
EOF

echo "Written. Validating Suricata configuration and rules..."
suricata -T -c "$SURICATA_CFG"
TEST_EXIT=$?
if [ $TEST_EXIT -ne 0 ]; then
  echo "Suricata test failed (exit $TEST_EXIT). Please review the output above and fix errors." >&2
  exit $TEST_EXIT
fi

echo
echo "Validation succeeded. To trigger the rule from another host, run (replace TARGET_IP accordingly):"
echo
echo "curl -v -H 'Host: example.test' http://$TARGET_IP/"
echo
echo "Then check Suricata's eve.json (default /var/log/suricata/eve.json) for a message with msg:\"SAFW-Test-HTTP-Alert\""
echo
echo "If you prefer Suricata to pick up the new rule immediately, reload or restart Suricata on this host."
echo "Examples (systemd):"
echo "  sudo systemctl reload suricata    # gentle reload if supported"
echo "  sudo systemctl restart suricata   # full restart"

echo
echo "Finished."

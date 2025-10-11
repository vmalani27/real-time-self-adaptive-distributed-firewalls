Monitoring helpers
==================

This folder contains small helper scripts to help test Suricata and packet capture integrations used by the agent.

install_and_trigger_suricata_test.sh
------------------------------------

- Purpose: write a simple `local.rules` entry, validate Suricata's configuration, and print a curl command
  you can run from another machine to trigger the rule.
- Usage: Run this script on the Suricata host (agent VM) with sudo:

  sudo ./monitoring/install_and_trigger_suricata_test.sh

- Notes:
  - Update the TARGET_IP variable inside the script to the IP of the machine that will send the trigger request.
  - The script validates the Suricata configuration but does not automatically restart Suricata unless
    you choose to do so. Use `systemctl reload suricata` or `systemctl restart suricata` to apply rules
    immediately.

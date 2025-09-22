#!/bin/bash

echo "📦 Setting up Self-Adaptive Firewall Agent for Testing..."

# Check if we're already in the project directory
if [ ! -f "./requirements.txt" ] && [ ! -f "./agent/agent.py" ]; then
  echo "❌ Error: Please run this script from the project root directory."
  echo "   Expected files: requirements.txt, agent/agent.py"
  exit 1
else
  echo "📁 Project files found in current directory."
fi

# Install required packages
sudo apt install -y python3 python3-pip git nftables curl jq net-tools \
    zeek suricata tmux wget build-essential libpcap-dev libnetfilter-queue-dev

# Install Python dependencies
pip3 install -r requirements.txt

# Configure Zeek and Suricata logs
mkdir -p /var/log/zeek/current/
mkdir -p /var/log/suricata/

touch /var/log/zeek/current/conn.log
touch /var/log/suricata/eve.json

# Enable nftables
sudo systemctl enable nftables
sudo systemctl start nftables

# Create systemd service for agent
echo "🛠️ Creating systemd service..."

sudo tee /etc/systemd/system/safw-agent.service > /dev/null <<EOF
[Unit]
Description=Self-Adaptive Firewall Agent
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/env uvicorn agent.agent:app --host 0.0.0.0 --port 5001
WorkingDirectory=$(pwd)
Restart=always
EnvironmentFile=$(pwd)/.env

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable safw-agent
sudo systemctl start safw-agent

echo "✅ Agent testing setup complete and running on port 5001" 
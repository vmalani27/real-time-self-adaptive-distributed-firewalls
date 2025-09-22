#!/bin/bash

# 📦 Setting up Self-Adaptive Firewall Agent...

echo "📦 Setting up Self-Adaptive Firewall Agent..."

# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3 python3-pip git nftables curl jq net-tools \
  zeek suricata tmux wget build-essential libpcap-dev libnetfilter-queue-dev

# Clone or copy project repo (only if not already in project directory)
if [ ! -f "./requirements.txt" ] && [ ! -f "./agent/agent.py" ]; then
  echo "📁 Project files not found. Cloning project repo..."
  if [ ! -d "./real-time-self-adaptive-distributed-firewalls" ]; then
    git clone https://github.com/vmalani27/real-time-self-adaptive-distributed-firewalls.git
  fi
  cd real-time-self-adaptive-distributed-firewalls || exit
else
  echo "📁 Project files found in current directory."
fi

# Install Python dependencies
pip3 install -r requirements.txt

# Set up .env (use test.env as base)
cp test.env .env

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

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable safw-agent
sudo systemctl start safw-agent

echo "✅ Agent setup complete and running on port 5001" 
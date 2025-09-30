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
# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment and install dependencies
echo "📦 Installing dependencies in virtual environment..."
source venv/bin/activate
pip install -r requirements.txt
deactivate

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

# Get absolute paths
PROJECT_DIR=$(pwd)
VENV_PYTHON="$PROJECT_DIR/venv/bin/python"
VENV_UVICORN="$PROJECT_DIR/venv/bin/uvicorn"

sudo tee /etc/systemd/system/safw-agent.service > /dev/null <<EOF
[Unit]
Description=Self-Adaptive Firewall Agent
After=network.target

[Service]
Type=simple
ExecStart=$VENV_UVICORN agent.agent:app --host 192.168.56.11 --port 5001
WorkingDirectory=$PROJECT_DIR
Restart=always
RestartSec=5
EnvironmentFile=$PROJECT_DIR/.env
User=kali
Group=kali
Environment=PATH=$PROJECT_DIR/venv/bin:/usr/local/bin:/usr/bin:/bin
Environment=PYTHONPATH=$PROJECT_DIR

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd, enable and start the service
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable safw-agent
sudo systemctl start safw-agent

echo "✅ Agent testing setup complete and running on port 5001" 
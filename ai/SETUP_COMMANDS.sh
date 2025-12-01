#!/bin/bash
# Commands to install and enable AI Runner on Ubuntu 22.04

# Create required directories
mkdir -p /root/hands-off/ai/tasks
mkdir -p /root/hands-off/ai/results
mkdir -p /root/hands-off/ai/processed
mkdir -p /root/hands-off-out/ai

# Install Python dependencies
pip3 install requests

# Copy the Python script
cp /root/hands-off-engine/ai/ai_runner.py /root/hands-off/ai/ai_runner.py
chmod +x /root/hands-off/ai/ai_runner.py

# Install systemd service
cp /root/hands-off-engine/ai/ai-runner.service /etc/systemd/system/ai-runner.service

# Edit the service file to add your API key
# nano /etc/systemd/system/ai-runner.service
# Set AI_RUNNER_API_KEY to your actual key
# Set AI_RUNNER_EXECUTE=1 when ready to execute commands

# Reload systemd
systemctl daemon-reload

# Enable service to start on boot
systemctl enable ai-runner

# Start the service
systemctl start ai-runner

# Check status
systemctl status ai-runner

# View logs
journalctl -u ai-runner -f

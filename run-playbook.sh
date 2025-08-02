#!/bin/bash

# Run the Amazon Linux 2023 setup playbook
# Usage: ./run-playbook.sh [target_ip] [ssh_key_path]

set -e

TARGET_IP=${1:-"127.0.0.1"}
SSH_KEY_PATH=${2:-"~/.ssh/id_rsa"}

echo "Setting up Amazon Linux 2023 development environment..."
echo "Target IP: $TARGET_IP"
echo "SSH Key: $SSH_KEY_PATH"
echo

# Install Ansible Galaxy requirements
echo "Installing Ansible Galaxy requirements..."
ansible-galaxy install -r requirements.yml

# Run the playbook
echo "Running playbook..."
ansible-playbook \
    -i inventory.yml \
    -e "target_ip=$TARGET_IP" \
    -e "ssh_key_path=$SSH_KEY_PATH" \
    playbook.yml

echo
echo "Setup complete! Remember to:"
echo "1. Reboot the target system: sudo reboot"
echo "2. Verify Node.js: node --version"
echo "3. Verify Docker: docker ps"
echo "4. Check services: systemctl status docker"
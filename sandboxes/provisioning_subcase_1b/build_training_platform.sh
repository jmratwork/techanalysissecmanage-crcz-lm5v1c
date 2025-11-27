#!/bin/bash
set -e

# Example provisioning steps for the training platform VM
apt-get update
apt-get install -y nginx
systemctl enable nginx

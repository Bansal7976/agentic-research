#!/usr/bin/env bash
# Run ON the Compute Engine VM (Debian) after SSH-ing in. See docs/10 for the
# gcloud commands that create the VM, firewall rule and service account.
set -euo pipefail

# 1. Install Docker + compose plugin
sudo apt-get update -y
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker "$USER"

# 2. Get the code (replace with YOUR repo URL after pushing to GitHub)
git clone https://github.com/Bansal7976/agentic-research.git
cd agentic-research

# 3. Configure secrets — paste real keys into .env
cp .env.example .env
echo ">>> EDIT .env NOW:  nano .env   (then re-run the last command below)"

# 4. Launch (restart:always not needed; compose restarts with --restart unless-stopped)
# Re-login first so the docker group applies, or prefix with: sg docker -c '...'
docker compose -f deploy/docker-compose.yml up --build -d
echo ">>> Done. Open http://VM_EXTERNAL_IP/  |  Stop the VM when not in use to save money!"

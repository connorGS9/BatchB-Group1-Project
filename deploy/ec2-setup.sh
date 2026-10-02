#!/bin/bash
# deploy/ec2-setup.sh
# One-time setup of a fresh Amazon Linux 2023 EC2 server for the bank app:
# installs Docker + Docker Compose + git, and adds 1 GB of swap (t3.micro only has 1 GB RAM).
# Run on the server:   bash deploy/ec2-setup.sh     then log out and back in.
set -euo pipefail

COMPOSE_VERSION="v5.5.1"
BUILDX_VERSION="v0.37.2"

echo "==> Installing Docker and git"
sudo dnf install -y docker git
sudo systemctl enable --now docker
sudo usermod -aG docker ec2-user          # lets ec2-user run docker without sudo (after re-login)

echo "==> Installing Docker Compose ${COMPOSE_VERSION} and Buildx ${BUILDX_VERSION}"
PLUGINS=/usr/local/lib/docker/cli-plugins
sudo mkdir -p "$PLUGINS"
sudo curl -fsSL "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-x86_64" -o "$PLUGINS/docker-compose"
sudo curl -fsSL "https://github.com/docker/buildx/releases/download/${BUILDX_VERSION}/buildx-${BUILDX_VERSION}.linux-amd64" -o "$PLUGINS/docker-buildx"
sudo chmod +x "$PLUGINS/docker-compose" "$PLUGINS/docker-buildx"

if [ ! -f /swapfile ]; then
  echo "==> Adding 1 GB swap"
  sudo dd if=/dev/zero of=/swapfile bs=1M count=1024 status=none
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile >/dev/null
  sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab >/dev/null
fi

docker --version
sudo docker compose version
echo "==> Done. Log out and back in (or open a new connection) so 'docker' works without sudo."

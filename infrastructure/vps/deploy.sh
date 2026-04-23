#!/usr/bin/env bash
set -euo pipefail

APP_DIR="/opt/llm-ops-v1"
SERVICE_NAME="agent.service"

sudo mkdir -p "$APP_DIR"
sudo rsync -av --delete ./ "$APP_DIR"/
cd "$APP_DIR"

uv sync --frozen
sudo cp infrastructure/vps/agent.service /etc/systemd/system/"$SERVICE_NAME"
sudo systemctl daemon-reload
sudo systemctl enable --now "$SERVICE_NAME"
sudo systemctl status "$SERVICE_NAME" --no-pager

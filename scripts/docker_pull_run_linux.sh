#!/usr/bin/env bash
set -euo pipefail

IMAGE="thanglong2807/be-cenvi:latest"
CONTAINER="cenvi_backend"
APP_DIR="${1:-$(pwd)}"

echo "[1/5] Pull image ${IMAGE}"
docker pull "${IMAGE}"

echo "[2/5] Stop old container (if exists)"
docker rm -f "${CONTAINER}" >/dev/null 2>&1 || true

echo "[3/5] Ensure required folders"
mkdir -p "${APP_DIR}/credentials" "${APP_DIR}/app/data"

echo "[4/5] Run container"
docker run -d \
  --name "${CONTAINER}" \
  -p 8100:8100 \
  --env-file "${APP_DIR}/.env" \
  -e DOCKER=true \
  -v "${APP_DIR}/credentials:/app/credentials:ro" \
  -v "${APP_DIR}/app/data:/app/app/data" \
  -v "${APP_DIR}/cenvi_audit.db:/app/cenvi_audit.db" \
  "${IMAGE}"

echo "[5/5] Show logs"
docker logs --tail 100 "${CONTAINER}"
echo "Deploy completed."
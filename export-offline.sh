#!/usr/bin/env bash
# 导出离线镜像包：把「已构建好的」前后端镜像 + 三个依赖服务镜像打成一个 tar
# 收包方在无外网环境执行 import-offline.sh 即可启动，无需联网构建
set -e
cd "$(dirname "$0")"

OUT="liveops-offline-$(date +%Y%m%d).tar"
IMAGES=("liveops-backend:latest" "liveops-frontend:latest" "mysql:8.0" "redis:7-alpine" "postgres:16")

echo "[1/2] 构建前后端镜像"
docker compose --profile ui build

echo "[2/2] 导出镜像 -> $OUT"
docker save "${IMAGES[@]}" -o "$OUT"

if command -v gzip >/dev/null 2>&1; then
  gzip -f "$OUT"
  echo "完成：$OUT.gz（约 1~2 GB，可直接拷贝给他人）"
else
  echo "完成：$OUT"
fi

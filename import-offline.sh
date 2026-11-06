#!/usr/bin/env bash
# 导入离线镜像包并启动（无需外网）
set -e
cd "$(dirname "$0")"

ARCHIVE="${1:-}"
if [ -z "$ARCHIVE" ]; then
  ARCHIVE=$(ls -t liveops-offline-*.tar.gz liveops-offline-*.tar 2>/dev/null | head -1)
fi
if [ -z "$ARCHIVE" ] || [ ! -f "$ARCHIVE" ]; then
  echo "未找到离线镜像包，请先执行 export-offline.sh，或传入包路径" >&2
  exit 1
fi

echo "[1/3] 导入镜像：$ARCHIVE"
case "$ARCHIVE" in
  *.gz) gunzip -c "$ARCHIVE" | docker load ;;
  *)    docker load -i "$ARCHIVE" ;;
esac

echo "[2/3] 检查 .env"
[ -f .env ] || cp .env.example .env

echo "[3/3] 启动容器（不重新构建）"
docker compose --profile ui up -d

echo ""
echo "  启动完成：http://localhost:8088"
echo "  演示账号：admin1 / host6   密码 123456"

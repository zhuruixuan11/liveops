#!/usr/bin/env bash
# LiveOps 一键启动（macOS / Linux / WSL）
set -e
cd "$(dirname "$0")"

echo "[1/4] 检查 .env"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "      已根据 .env.example 生成 .env（如需 AI 话术，请填写 LLM_API_KEY）"
else
  echo "      .env 已存在，跳过"
fi

echo "[2/4] 检查 Docker"
if ! docker info >/dev/null 2>&1; then
  echo "      Docker 未运行，请先启动 Docker Desktop / dockerd" >&2
  exit 1
fi

echo "[3/4] 构建并启动容器（首次约 3~5 分钟）"
docker compose --profile ui up -d --build

echo "[4/4] 等待服务就绪"
ok=0
for _ in $(seq 1 90); do
  if curl -fsS http://localhost:8088/api/health 2>/dev/null | grep -q '"ok"'; then
    ok=1
    break
  fi
  sleep 2
done

if [ "$ok" -eq 1 ]; then
  echo ""
  echo "  启动成功"
  echo "  老板端/主播端: http://localhost:8088"
  echo "  API 健康检查 : http://localhost:8088/api/health"
  echo "  演示账号     : admin1 / host6   密码 123456"
else
  echo "  服务尚未就绪，查看日志：docker compose --profile ui logs -f backend" >&2
  exit 1
fi

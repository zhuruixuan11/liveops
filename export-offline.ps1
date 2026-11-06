# 导出离线镜像包（Windows PowerShell）
$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

$out = "liveops-offline-$(Get-Date -Format 'yyyyMMdd').tar"

Write-Host "[1/2] 构建前后端镜像" -ForegroundColor Cyan
docker compose --profile ui build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/2] 导出镜像 -> $out" -ForegroundColor Cyan
docker save -o $out liveops-backend:latest liveops-frontend:latest mysql:8.0 redis:7-alpine postgres:16
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "完成：$out（约 1~2 GB，可直接拷贝给他人）" -ForegroundColor Green

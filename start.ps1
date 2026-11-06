# LiveOps 一键启动（Windows PowerShell）
$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "[1/4] 检查 .env" -ForegroundColor Cyan
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "      已根据 .env.example 生成 .env（如需 AI 话术，请填写 LLM_API_KEY）"
} else {
    Write-Host "      .env 已存在，跳过"
}

Write-Host "[2/4] 检查 Docker" -ForegroundColor Cyan
docker info *> $null
if ($LASTEXITCODE -ne 0) {
    Write-Host "      Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    exit 1
}

Write-Host "[3/4] 构建并启动容器（首次约 3~5 分钟）" -ForegroundColor Cyan
docker compose --profile ui up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[4/4] 等待服务就绪" -ForegroundColor Cyan
$ok = $false
for ($i = 0; $i -lt 90; $i++) {
    try {
        $r = Invoke-RestMethod -Uri "http://localhost:8088/api/health" -TimeoutSec 2
        if ($r.status -eq "ok") { $ok = $true; break }
    } catch { }
    Start-Sleep -Seconds 2
}

if ($ok) {
    Write-Host ""
    Write-Host "  启动成功" -ForegroundColor Green
    Write-Host "  老板端/主播端: http://localhost:8088"
    Write-Host "  API 健康检查 : http://localhost:8088/api/health"
    Write-Host "  演示账号     : admin1 / host6   密码 123456"
} else {
    Write-Host "  服务尚未就绪，查看日志：docker compose --profile ui logs -f backend" -ForegroundColor Red
    exit 1
}

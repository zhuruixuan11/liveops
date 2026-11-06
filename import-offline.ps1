# 导入离线镜像包并启动（Windows PowerShell，无需外网）
$ErrorActionPreference = "Stop"
Set-Location -Path (Split-Path -Parent $MyInvocation.MyCommand.Path)

$archive = $args[0]
if (-not $archive) {
    $archive = Get-ChildItem -Filter "liveops-offline-*.tar" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($archive) { $archive = $archive.FullName }
}
if (-not $archive -or -not (Test-Path $archive)) {
    Write-Host "未找到离线镜像包，请先执行 export-offline.ps1，或传入包路径" -ForegroundColor Red
    exit 1
}

Write-Host "[1/3] 导入镜像：$archive" -ForegroundColor Cyan
docker load -i $archive
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "[2/3] 检查 .env" -ForegroundColor Cyan
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

Write-Host "[3/3] 启动容器（不重新构建）" -ForegroundColor Cyan
docker compose --profile ui up -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host ""
Write-Host "  启动完成：http://localhost:8088" -ForegroundColor Green
Write-Host "  演示账号：admin1 / host6   密码 123456"

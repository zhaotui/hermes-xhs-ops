# Kimi WebBridge Windows 安装脚本
# 用法：powershell -ExecutionPolicy Bypass -File .\install-webbridge.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Kimi WebBridge 安装 ===" -ForegroundColor Cyan

# 1. 安装
Write-Host "1/4 下载安装..."
irm https://cdn.kimi.com/webbridge/install.ps1 | iex

# 2. 找到安装路径
$binDir = "$env:USERPROFILE\.kimi-webbridge\bin"
$exe = "$binDir\kimi-webbridge.exe"
if (-not (Test-Path $exe)) {
    Write-Host "❌ 未找到 $exe" -ForegroundColor Red
    exit 1
}
Write-Host "  安装位置: $exe"

# 3. 加入 PATH
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$binDir", "User")
    $env:Path = "$env:Path;$binDir"
    Write-Host "2/4 已加入 PATH: $binDir"
} else {
    Write-Host "2/4 PATH 已存在，跳过"
}

# 4. 重启服务（监听所有网卡，WSL2 才能访问）
Write-Host "3/4 重启服务（绑定 0.0.0.0:10086）..."

# 停止所有运行中的进程
Get-Process -Name "kimi-webbridge" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

# 清理残留 PID 文件
$pidFile = "$env:USERPROFILE\.kimi-webbridge\kimi-webbridge.pid"
if (Test-Path $pidFile) {
    Remove-Item $pidFile -Force
}

# 启动
& $exe start --addr 0.0.0.0:10086 2>&1 | Out-Null
Start-Sleep -Seconds 3

# 5. 验证
Write-Host "4/4 验证..."
$status = & $exe status 2>&1
Write-Host "  $status"

if ($LASTEXITCODE -eq 0 -and $status -match '"running":\s*true') {
    Write-Host "`n✅ 安装完成" -ForegroundColor Green
    Write-Host "  浏览器扩展请访问 https://www.kimi.com/zh-cn/features/webbridge 加载"
} else {
    Write-Host "`n⚠️ 服务可能未正常启动" -ForegroundColor Yellow
    Write-Host "  手动排查: kimi-webbridge status"
    Write-Host "  查看日志: $env:USERPROFILE\.kimi-webbridge\logs\daemon.log"
}

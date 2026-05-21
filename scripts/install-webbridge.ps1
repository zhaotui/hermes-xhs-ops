# Kimi WebBridge Windows 安装脚本
# 用法：PowerShell 管理员运行 .\install-webbridge.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Kimi WebBridge 安装 ===" -ForegroundColor Cyan

# 1. 安装
Write-Host "1/5 下载安装..."
irm https://cdn.kimi.com/webbridge/install.ps1 | iex

# 2. 找到安装路径
$binDir = "$env:USERPROFILE\.kimi-webbridge\bin"
$exe = "$binDir\kimi-webbridge.exe"
if (-not (Test-Path $exe)) {
    Write-Host "❌ 未找到 $exe" -ForegroundColor Red
    exit 1
}
Write-Host "  安装位置: $exe"

# 3. 加入 PATH（安装脚本默认不加）
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($userPath -notlike "*$binDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$userPath;$binDir", "User")
    $env:Path = "$env:Path;$binDir"
    Write-Host "2/5 已加入 PATH: $binDir"
} else {
    Write-Host "2/5 PATH 已存在，跳过"
}

# 4. 处理已有进程（PID 冲突）
Write-Host "3/5 检查运行状态..."
$existing = Get-Process -Name "kimi-webbridge" -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "  已有进程 (PID $($existing.Id))，先停止..."
    Stop-Process -Name "kimi-webbridge" -Force
    Start-Sleep -Seconds 2
}

# 5. 启动（监听所有网卡，WSL2 才能访问）
Write-Host "4/5 启动服务..."
Start-Process -FilePath $exe -ArgumentList "start", "--addr", "0.0.0.0" -WindowStyle Hidden
Start-Sleep -Seconds 3

# 6. 验证
Write-Host "5/5 验证..."
$status = & $exe status 2>&1
Write-Host "  $status"

if ($status -match "running") {
    Write-Host "`n✅ 安装完成" -ForegroundColor Green
    Write-Host "  浏览器扩展请访问 https://www.kimi.com/zh-cn/features/webbridge 加载"
} else {
    Write-Host "`n⚠️ 服务可能未正常启动，请检查 $env:USERPROFILE\.kimi-webbridge\logs\daemon.log" -ForegroundColor Yellow
}

#!/bin/bash
set -e

# ── XHS Ops 一键安装 ──
# 用法: bash install.sh [WebBridge IP]
# 示例: bash install.sh 172.26.240.1

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

echo "XHS Ops 安装中..."

# 1. 检测 WebBridge IP
IP="${1:-}"
if [ -z "$IP" ]; then
    IP=$(ip route 2>/dev/null | awk '/default/ {print $3; exit}')
    if [ -z "$IP" ]; then
        IP=$(ip route show default 2>/dev/null | awk '{print $3; exit}')
    fi
fi
if [ -z "$IP" ]; then
    echo -e "${RED}无法自动检测 Windows IP。请手动指定：${NC}"
    echo "  bash install.sh 你的IP"
    exit 1
fi

echo "  WebBridge IP: $IP"

# 2. 设环境变量
if ! grep -q "WEBBRIDGE_BASE" ~/.bashrc 2>/dev/null; then
    echo "export WEBBRIDGE_BASE=\"http://${IP}:10086\"" >> ~/.bashrc
    echo "  已写入 ~/.bashrc"
fi
export WEBBRIDGE_BASE="http://${IP}:10086"

# 3. 软链接 Plugin
sudo ln -sf "$(pwd)" /usr/local/lib/hermes-agent/plugins/xhs
echo "  插件已注册"

# 4. 软链接 Skills
mkdir -p ~/.hermes/skills/xhs
for d in skills/*/; do
    ln -sf "$(pwd)/${d}" ~/.hermes/skills/xhs/ 2>/dev/null
done
echo "  Skills 已注册"

# 5. 部署 cron 脚本
mkdir -p ~/.hermes/scripts
cp -f scripts/scan_report.py ~/.hermes/scripts/scan_report.py
echo "  定时脚本已部署"

# 6. 创建 cron
if hermes cron list 2>/dev/null | grep -q "xhs-scan"; then
    echo "  cron 已存在，跳过"
else
    hermes cron create --name xhs-scan --script scan_report.py --no-agent "*/15 * * * *" 2>/dev/null || true
    echo "  自循环已启动"
fi

echo ""
echo -e "${GREEN}安装完成 ✅${NC}"
echo "  报告目录: ~/.hermes/data/xhs-ops/reports/"

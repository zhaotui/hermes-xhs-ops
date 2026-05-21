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
if ! grep -q "XHS_PROJECT" ~/.bashrc 2>/dev/null; then
    echo "export XHS_PROJECT=\"$(pwd)\"" >> ~/.bashrc
    echo "  已写入 ~/.bashrc"
fi
if ! grep -q "WEBBRIDGE_BASE" ~/.bashrc 2>/dev/null; then
    echo "export WEBBRIDGE_BASE=\"http://${IP}:10086\"" >> ~/.bashrc
    echo "  已写入 ~/.bashrc"
fi
export XHS_PROJECT="$(pwd)"
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

echo ""
echo -e "${GREEN}安装完成 ✅${NC}"
echo "  后续操作（cron、自循环等）交给 Hermes 处理"

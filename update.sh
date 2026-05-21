#!/bin/bash
# ── XHS Ops 更新脚本 ──
# 拉取最新代码，重启 gateway

set -e
cd ~/.hermes/plugins/xhs
sed -i 's/\r$//' install.sh 2>/dev/null || true

echo "XHS Ops 更新中..."
git pull
hermes gateway restart 2>/dev/null && echo "✅ 已更新并重载" || echo "⚠️ 代码已更新，请手动重启 gateway"

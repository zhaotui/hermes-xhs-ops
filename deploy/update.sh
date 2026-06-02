#!/bin/bash
# ── XHS Ops 更新脚本 ──
# git pull 最新代码，重启 gateway

set -e

GIT_URL="https://github.com/zhaotui/hermes-xhs-ops.git"
BRANCH="opensource"
INSTALL_DIR="$HOME/.hermes/plugins/xhs"

echo "XHS Ops 更新中..."

cd "$INSTALL_DIR"
git pull "$GIT_URL" "$BRANCH"

# 修复换行符
sed -i 's/\r$//' "$INSTALL_DIR/deploy/install.sh" 2>/dev/null || true
sed -i 's/\r$//' "$INSTALL_DIR/deploy/update.sh" 2>/dev/null || true

hermes gateway restart 2>/dev/null && echo "✅ 已更新并重载" || echo "⚠️ 代码已更新，请手动重启 gateway"

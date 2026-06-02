#!/bin/bash
set -e

# ── XHS Ops 一键安装 ──
# 用法: bash install.sh [WebBridge IP]
# 用 git clone/pull + 账号密码拉取

GIT_URL="https://github.com/zhaotui/hermes-xhs-ops.git"
BRANCH="opensource"
INSTALL_DIR="$HOME/.hermes/plugins/xhs"

# 检查 git
if ! command -v git &>/dev/null; then
    echo "需要 git，请先安装 git"
    exit 1
fi

# 0. 如果不在仓库内，git clone 到 Hermes 插件目录
if [ ! -f "plugin.yaml" ]; then
    echo "拉取 xhs-ops..."

    if [ -d "$INSTALL_DIR/.git" ]; then
        # 已有仓库，git pull 更新
        echo "  已有安装，git pull 更新..."
        cd "$INSTALL_DIR"
        git pull "$GIT_URL" "$BRANCH"
    else
        # 全新 clone
        if [ -d "$INSTALL_DIR" ]; then
            echo "  已有安装，覆盖更新..."
            rm -rf "$INSTALL_DIR"
        fi

        mkdir -p "$(dirname "$INSTALL_DIR")"
        git clone --depth 1 -b "$BRANCH" "$GIT_URL" "$INSTALL_DIR"
    fi

    cd "$INSTALL_DIR"
    sed -i 's/\r$//' deploy/install.sh 2>/dev/null || true
    exec bash deploy/install.sh "$@"
fi

# 确保在仓库根目录
cd "$(dirname "$0")/.." 2>/dev/null || true

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

# 3. 软链接 Skills
mkdir -p ~/.hermes/skills/xhs
for d in skills/*/; do
    ln -sf "$(pwd)/${d}" ~/.hermes/skills/xhs/ 2>/dev/null
done
echo "  Skills 已注册"

# 4. 重启 gateway 让 Hermes 识别新插件
hermes gateway restart 2>/dev/null && echo "  Gateway 已重载" || true
sleep 2

# 5. 启用 xhs 插件 + 加入 CLI 平台
hermes plugins enable xhs 2>/dev/null || true
python3 -c "
import yaml, os
p = os.path.expanduser('~/.hermes/config.yaml')
with open(p) as f: c = yaml.safe_load(f)
cli = c.setdefault('platform_toolsets', {}).setdefault('cli', [])
if 'xhs' not in cli:
    cli.append('xhs')
    with open(p, 'w') as f: yaml.dump(c, f, default_flow_style=False, allow_unicode=True)
    print('  xhs 已加入 CLI 平台')
" 2>/dev/null || echo "  跳过工具集配置"

# 验证
sleep 1
if hermes tools list 2>/dev/null | grep -q xhs; then
    echo "  ✅ xhs 工具集已识别"
else
    echo "  ⚠️ xhs 工具集未识别，请手动检查 hermes tools list"
fi

echo ""
echo -e "${GREEN}安装完成 ✅${NC}"
echo "  后续操作（cron、自循环等）交给 Hermes 处理"

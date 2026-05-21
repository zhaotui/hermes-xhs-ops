#!/bin/bash
set -e

# ── XHS Ops 一键安装 ──
# 用法: bash install.sh [WebBridge IP]
# 可以直接运行（自动 clone 仓库），也可以在仓库内运行

REPO_URL="http://192.168.8.251:8080/hr/xhs-ops"

# 0. 如果不在仓库内，先 clone，然后用仓库内的 install.sh 继续
if [ ! -f "plugin.yaml" ]; then
    echo "未检测到项目文件，正在 clone 仓库..."
    git clone "$REPO_URL" ~/xhs-ops
    cd ~/xhs-ops
    sed -i 's/\r$//' install.sh 2>/dev/null || true
    exec bash install.sh "$@"
fi

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

# 3. 软链接 Plugin — 自动检测 Hermes 插件目录
PLUGIN_DIR=""
for d in \
    "$HOME/.hermes/plugins" \
    "/usr/local/lib/hermes-agent/plugins" \
    "$(python3 -c "import site; print(site.getsitepackages()[0])" 2>/dev/null)/hermes_agent/plugins" \
    ; do
    if [ -d "$d" ] || mkdir -p "$d" 2>/dev/null; then
        PLUGIN_DIR="$d"
        break
    fi
done
if [ -z "$PLUGIN_DIR" ]; then
    PLUGIN_DIR="$HOME/.hermes/plugins"
    mkdir -p "$PLUGIN_DIR"
fi
ln -sf "$(pwd)" "$PLUGIN_DIR/xhs" 2>/dev/null || sudo ln -sf "$(pwd)" "$PLUGIN_DIR/xhs"
echo "  插件已注册 → $PLUGIN_DIR/xhs"

# 重启 gateway 让 Hermes 识别新插件
hermes gateway restart 2>/dev/null && echo "  Gateway 已重载" || true
sleep 2

# 4. 软链接 Skills
mkdir -p ~/.hermes/skills/xhs
for d in skills/*/; do
    ln -sf "$(pwd)/${d}" ~/.hermes/skills/xhs/ 2>/dev/null
done
echo "  Skills 已注册"

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

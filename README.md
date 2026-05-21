# XHS Ops — 小红书运营插件

一个完整的 Hermes Plugin 项目，6 个工具 + 6 个技能 + 脚本（发帖、扫评论、回复、收集、删帖、自循环、tab 管理）。

## 项目结构

```
xhs/                       ← Plugin 根目录
├── plugin.yaml
├── __init__.py             ← register() 入口
├── client.py               ← WebBridge HTTP 底层客户端
├── tools.py                ← 6 个工具实现（handler + schema）
├── skills/                 ← Skills（Hermes 自动加载）
│   ├── xhs-publish-post/   → 发布笔记
│   ├── xhs-read-comments/  → 读评论
│   ├── xhs-reply-comment/  → 回复评论
│   ├── xhs-collect-info/   → 分类收集信息
│   ├── xhs-delete-post/    → 删帖清理
│   ├── xhs-auto-pilot/     → 自循环运营（定时调度）
│   └── xhs-tab-manager/    → 浏览器 tab 感知与管理
├── scripts/
│   ├── publish_auto.py     → 发布脚本（step-by-step 浏览器自动化）
│   ├── scan_report.py      → 扫描报告脚本（cron --script 调用）
│   └── tab_manager.py      → tab 管理模块（list/ensure/close）
└── README.md
```

## 工具

| 工具 | 功能 | 参数 |
|------|------|------|
| `xhs_publish_post` | 发布长文 | title, body, visibility, images, location, template, … |
| `xhs_read_comments` | 笔记管理→详情页读评论 | note_index |
| `xhs_view_note_detail` | 打开笔记详情页 | note_index |
| `xhs_reply_comment` | 在详情页回复评论 | reply_text |
| `xhs_collect_info` | 分类评论保存 JSONL | comments_json, goal |
| `xhs_delete_post` | 删帖（按可见范围） | visibility=private/public/all |

## 脚本

| 脚本 | 用途 | 调用方式 |
|------|------|---------|
| `publish_auto.py` | 浏览器自动化发帖 | `--stdin-json` |
| `scan_report.py` | 扫评论+收集→报告 | `python3 scripts/scan_report.py` |
| `tab_manager.py` | tab 管理（list/ensure/close） | `from tab_manager import …` |

## 报告

扫描报告保存在 `/root/.hermes/data/xhs-ops/reports/`，收集数据保存在 `/root/.hermes/data/xhs-ops/records.jsonl`。

## 安装

### 1. 确认基础环境

你需要有一台 Windows 电脑，上面运行着 **Kimi WebBridge**（浏览器扩展）。这台电脑上还要安装 **WSL2**，Hermes Agent 跑在 WSL2 里面。

先确认 Hermes 装好了：

```bash
hermes --version   # 有版本号就行
```

确认 WebBridge 能连通。在 WSL2 终端里执行：

```bash
# 找到 Windows 主机的 IP
ip route | awk '/default/ {print $3}'

# 测试连通（把 172.xx 换成上一步拿到的 IP）
curl http://172.26.240.1:10086/status
# 看到 {"running":true, "extension_connected":true} 就对了
```

如果 `curl` 不通，检查：
- Windows 防火墙是否拦截了 10086 端口
- Kimi WebBridge 扩展是否已安装并在浏览器里启用
- 浏览器是否已打开一个小红书页面（WebBridge 需要至少一个 tab）

### 2. 下载项目

```bash
cd ~
git clone <你的仓库地址> xhs-ops
cd xhs-ops
```

项目目录就是 `/root/xhs-ops`，后续所有路径都基于它。

### 3. 配置 WebBridge 地址

告诉 client.py 该往哪连。两种方式任选一种：

**方式 A：环境变量（推荐，全局生效）**
```bash
echo 'export WEBBRIDGE_BASE="http://172.26.240.1:10086"' >> ~/.bashrc
source ~/.bashrc
# 把 IP 换成你第一步拿到的值
```

**方式 B：每次手动**（不推荐）
```bash
export WEBBRIDGE_BASE="http://172.26.240.1:10086"
```

### 4. 注册 Hermes Plugin

让 Hermes 启动时自动加载项目里的 6 个工具（发帖、读评论、回复等）：

```bash
# 把项目目录软链接到 Hermes 插件目录
sudo ln -sf /root/xhs-ops /usr/local/lib/hermes-agent/plugins/xhs
```

验证：
```bash
ls /usr/local/lib/hermes-agent/plugins/xhs/
# 应该看到 client.py、tools.py、scripts/ 等文件
```

### 5. 注册 Skills

Skills 是给 AI 看的操作手册，告诉它每个任务怎么执行：

```bash
# 创建 skills 目录
mkdir -p ~/.hermes/skills/xhs

# 软链接所有 skill
ln -sf /root/xhs-ops/skills/xhs-publish-post   ~/.hermes/skills/xhs/
ln -sf /root/xhs-ops/skills/xhs-read-comments  ~/.hermes/skills/xhs/
ln -sf /root/xhs-ops/skills/xhs-reply-comment  ~/.hermes/skills/xhs/
ln -sf /root/xhs-ops/skills/xhs-collect-info   ~/.hermes/skills/xhs/
ln -sf /root/xhs-ops/skills/xhs-delete-post    ~/.hermes/skills/xhs/
ln -sf /root/xhs-ops/skills/xhs-auto-pilot     ~/.hermes/skills/xhs/
ln -sf /root/xhs-ops/skills/xhs-tab-manager    ~/.hermes/skills/xhs/
```

> 用软链接的好处：以后你在项目里改了 skill 文件，Hermes 读到的是最新的，不用再复制。

### 6. 部署定时脚本

`scan_report.py` 是自循环的核心——它每 15 分钟自动扫评论、分类、生成报告。Hermes cron 要求脚本放在 `~/.hermes/scripts/` 下：

```bash
cp /root/xhs-ops/scripts/scan_report.py ~/.hermes/scripts/scan_report.py
```

### 7. 验证安装

跑一遍健康检查，确认整个链路通：

```bash
cd /root/xhs-ops
python3 -c "
import sys
sys.path.insert(0, '.')
from client import _health_check
print('WebBridge:', '✅ 在线' if _health_check() else '❌ 连不上')
"
```

如果输出 `✅ 在线`，安装成功。

### 8. 启动自循环

创建 cron 任务，每 15 分钟自动扫描一次：

```bash
hermes cron create \
  --name "xhs-scan" \
  --script "scan_report.py" \
  --no-agent \
  "*/15 * * * *"
```

- `--name "xhs-scan"`：任务名字，方便管理
- `--script "scan_report.py"`：要执行的脚本
- `--no-agent`：直接跑脚本输出结果，不经过 AI（干净快速）
- `"*/15 * * * *"`：每 15 分钟跑一次

查看任务状态：
```bash
hermes cron list          # 看所有定时任务
hermes cron status        # 看调度器是否在运行
```

查看报告：
```bash
ls /root/.hermes/data/xhs-ops/reports/     # 报告文件列表
cat /root/.hermes/data/xhs-ops/reports/scan_*.md | tail -20   # 看最新报告
```

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `_health_check()` 返回 False | WebBridge 没连上 | 检查防火墙、扩展是否启用、浏览器有没有打开 |
| cron 不执行 | gateway 没跑 | `hermes gateway status`，没有就 `hermes gateway start` |
| 脚本报 import 错误 | 路径不对 | 确认第 4 步软链接正确，`python3` 在项目根目录执行 |
| 报告里没数据 | 没有评论或笔记 | 去小红书发一篇公开笔记，等人评论后再看 |

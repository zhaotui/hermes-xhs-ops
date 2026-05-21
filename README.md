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

### 前置条件

- **Hermes Agent** 已安装
- **Kimi WebBridge** 运行在 Windows 端（`http://<IP>:10086`）
- WSL2 环境，浏览器已登录小红书创作者

### 步骤

```bash
# 1. 克隆
git clone <repo-url> /opt/xhs-ops && cd /opt/xhs-ops

# 2. WebBridge 地址
export WEBBRIDGE_BASE="http://你的Windows IP:10086"

# 3. 软链接 Plugin + Skills
ln -sf /opt/xhs-ops /usr/local/lib/hermes-agent/plugins/xhs
mkdir -p ~/.hermes/skills/xhs
for d in skills/*/; do ln -sf /opt/xhs-ops/"$d" ~/.hermes/skills/xhs/; done

# 4. 部署定时脚本
cp scripts/scan_report.py ~/.hermes/scripts/

# 5. 验证
python3 -c "import sys; sys.path.insert(0,'/opt/xhs-ops'); from client import _health_check; print(_health_check())"

# 6. 启动自循环
hermes cron create --name "xhs-scan" --script "scan_report.py" --no-agent "*/15 * * * *"
```

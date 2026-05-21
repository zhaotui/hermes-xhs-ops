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

扫描报告保存在 `~/.hermes/data/xhs-ops/reports/`，收集数据保存在 `~/.hermes/data/xhs-ops/records.jsonl`。

## 前置

1. 装 **Kimi WebBridge**：[kimi.com/webbridge](https://www.kimi.com/zh-cn/features/webbridge)
   - 浏览器扩展：Chrome 商店安装或手动加载
   - 桥接服务：Mac / WSL2 跑 `curl -fsSL https://cdn.kimi.com/webbridge/install.sh \| bash`，Windows 原生参考页面指引
2. Hermes Agent 已安装
3. 浏览器登录小红书，保持一个页面打开

## 安装

```bash
git clone http://192.168.8.251:8080/hr/xhs-ops ~/xhs-ops && cd ~/xhs-ops && bash install.sh
```

脚本自动检测 WebBridge IP、注册插件和技能、部署定时任务。也可以手动指定 IP：

```bash
bash install.sh 172.26.240.1
```

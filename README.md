
<!--
  xhs-ops — Hermes 小红书运营插件 README
-->

# xhs-ops

小红书自动化运营插件，基于 Hermes Agent + Kimi WebBridge。支持多账号管理、自动发布、评论监控、信息收集、定时运营。

> 第一次使用需手动扫码登录小红书，后续通过登录态快照一键切换，无需重复验证。

## 核心能力

- ✅ 多账号管理：保存/恢复登录态（cookie + localStorage），一键切换账号
- ✅ 自动发布笔记：支持长文、图文、排版模板，指定可见范围
- ✅ 自动读评论：从笔记管理页进入详情页，提取全部评论
- ✅ 自动回复评论：在详情页对指定评论进行回复
- ✅ 评论分类收集：正向信号 → 写入 JSONL，其余丢弃，支持去重
- ✅ 安全删帖：仅删除"仅自己可见"帖，先识别后删除，绝不盲删
- ✅ 自动运营：Hermes cron 定时调度，扫描评论 + 发布 + 清理
- ✅ 运营报告：每次操作自动生成 Markdown 报告，可回溯

### 和同类项目的区别

| | xhs-ops (本项目) | xiaohongshu-ops-skill |
|---|---|---|
| 运行平台 | Hermes Agent | OpenClaw |
| 浏览器操控 | Kimi WebBridge (HTTP API) | CDP 直连 |
| 多账号 | ✅ 登录态快照切换 | ❌ 单账号 |
| 定时调度 | ✅ Hermes cron | ❌ |
| 数据收集 | ✅ JSONL 结构化存储 | ❌ |
| AI 辅助创作 | ❌ (可使用 Hermes 本身) | ✅ 选题/分析/复刻 |

---

## 快速开始

### 一、安装

**1. 安装 Kimi WebBridge**（浏览器扩展 + 桥接服务）

Chrome 扩展从 [Chrome 商店](https://www.kimi.com/zh-cn/features/webbridge) 安装，然后装桥接服务：

```bash
# Mac
curl -fsSL https://cdn.kimi.com/webbridge/install.sh | bash

# Windows
# PowerShell 管理员运行:
irm https://cdn.kimi.com/webbridge/install.ps1 | iex
```

**2. 安装 xhs-ops 插件**

```bash
git clone https://github.com/your-org/xhs-ops ~/.hermes/plugins/xhs
cd ~/.hermes/plugins/xhs && bash deploy/install.sh
```

**3. 配置账号**

启动 Hermes 对话，执行：

```
xhs_account_manager(action="detect")                          # 检测当前登录昵称
xhs_account_manager(action="add", key="main", nickname="你的昵称")  # 新增账号
xhs_account_manager(action="save_state", key="main")          # 保存登录态
```

### 二、日常使用

在 Hermes 对话中直接说人话即可：

| 你说 | Hermes 执行 |
|------|-----------|
| "帮我发一篇小红书" | 引导填写标题正文 → 自动发布 |
| "扫描一下评论" | 读取最新评论 → 分类收集 → 输出报告 |
| "回复最新评论" | 检查未回复的评论 → 逐条回复 |
| "切换账号" | 列出账号 → 切换登录态 |
| "清理测试帖" | 识别仅自己可见帖 → 删除 |

### 三、定时运营

```bash
# 每 15 分钟扫描评论
hermes cron create --name xhs-scan \
  --skill xhs-read-comments --skill xhs-collect-info --skill xhs-report \
  "*/15 * * * *" "扫描评论、分类、输出报告"

# 每周清理测试帖
hermes cron create --name xhs-cleanup \
  --skill xhs-delete-post --skill xhs-report \
  "0 3 * * 0" "删除仅自己可见帖，输出报告"
```

---

## 工具列表

| 工具 | 功能 |
|------|------|
| `xhs_account_manager` | 多账号管理、登录态保存/恢复/切换 |
| `xhs_publish_post` | 发布长文笔记 |
| `xhs_read_comments` | 读笔记评论 |
| `xhs_view_note_detail` | 打开笔记详情页 |
| `xhs_reply_comment` | 回复评论 |
| `xhs_collect_info` | 评论分类收集 → JSONL |
| `xhs_delete_post` | 安全删帖 |

---

## 仓库结构

```
xhs-ops/
├── plugin.yaml             # Hermes 插件声明
├── __init__.py             # 插件入口，注册所有工具
├── client.py               # WebBridge HTTP 客户端
├── tools.py                # 7 个工具实现
├── skills/                 # AI 操作指南（Skills）
│   ├── xhs-publish-post/   # 发布笔记流程
│   ├── xhs-read-comments/  # 读评论流程
│   ├── xhs-reply-comment/  # 回复评论流程
│   ├── xhs-collect-info/   # 评论分类收集规则
│   ├── xhs-delete-post/    # 安全删帖流程
│   ├── xhs-account-manager/# 多账号管理
│   ├── xhs-auto-pilot/     # 定时运营调度
│   ├── xhs-tab-manager/    # 浏览器 tab 管理
│   ├── xhs-report/         # 报告格式规范
│   └── kimi-webbridge/     # WebBridge 使用指南
├── scripts/
│   ├── publish_auto.py     # 浏览器发帖自动化
│   └── tab_manager.py      # tab 管理模块
├── deploy/
│   ├── install.sh          # 一键安装
│   ├── install-webbridge.ps1  # Windows WebBridge 安装
│   └── update.sh           # 更新代码
└── README.md
```

---

## 数据存储

```
~/.hermes/data/xhs-ops/
├── accounts.json           # 账号配置
├── account-states/         # 登录态快照
├── records.jsonl           # 收集的用户信息
└── reports/                # 运营报告
```

---

## 环境要求

| 组件 | 说明 |
|------|------|
| Windows 10/11 或 macOS | 浏览器运行环境 |
| WSL2（Windows） | Hermes Agent 运行环境 |
| Chrome | 带 Kimi WebBridge 扩展 |
| Kimi WebBridge | 浏览器自动化桥接 (端口 10086) |
| Hermes Agent | AI 调度引擎 |

---

## 已知限制

- Cookie 通过 CDP `Network.setCookies` 设置，标签页关闭后需重新切换
- 电脑休眠/锁屏会导致 WebBridge 失效，生产环境需设电源"永不"
- 小红书有发布频率限制，大量发布需分批

---

## 交流群

**小红书 MCP 互助群**

> ⚠️ 重要：在群里问问题之前，请一定要先仔细看完 README 文档以及查看 [Issues](https://github.com/zhaotui/hermes-xhs-ops/issues)。

扫码加入微信群：

<img src="./assets/wechat-group.jpg" alt="微信群" width="200" />

---

## License

MIT

# XHS Ops — 小红书运营插件

一个完整的 Hermes Plugin 项目，6 个工具 + 9 个技能 + 脚本（发帖、扫评论、回复、收集、删帖、自循环、报告、tab 管理、WebBridge 指南）。

## 项目结构

```
xhs/                       ← Plugin 根目录
├── plugin.yaml
├── __init__.py             ← register() 入口
├── client.py               ← WebBridge HTTP 底层客户端
├── tools.py                ← 6 个工具实现（handler + schema）
├── skills/                 ← Skills（Hermes 自动加载）
│   ├── kimi-webbridge/     → WebBridge 使用指南
│   ├── xhs-publish-post/   → 发布笔记
│   ├── xhs-read-comments/  → 读评论
│   ├── xhs-reply-comment/  → 回复评论
│   ├── xhs-collect-info/   → 分类收集信息
│   ├── xhs-delete-post/    → 删帖清理
│   ├── xhs-auto-pilot/     → 自循环运营（定时调度）
│   ├── xhs-tab-manager/    → 浏览器 tab 感知与管理
│   └── xhs-report/         → 报告规范与存储
├── scripts/
│   ├── publish_auto.py     → 发布脚本（step-by-step 浏览器自动化）
│   └── tab_manager.py      → tab 管理模块（list/ensure/close）
├── install.sh              ← 一键安装
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
| `tab_manager.py` | tab 管理（list/ensure/close） | `from tab_manager import …` |

## 报告

扫描报告保存在 `~/.hermes/data/xhs-ops/reports/`，收集数据保存在 `~/.hermes/data/xhs-ops/records.jsonl`。

## 前置

1. 装 **Kimi WebBridge**：浏览器扩展从 [Chrome 商店](https://www.kimi.com/zh-cn/features/webbridge) 安装，然后装桥接服务：
   - **Mac**：`curl -fsSL https://cdn.kimi.com/webbridge/install.sh | bash`
   - **Windows**：PowerShell 执行 `irm https://cdn.kimi.com/webbridge/install.ps1 | iex`
2. Hermes Agent 已安装
3. 浏览器登录小红书，保持一个页面打开

## Kimi WebBridge 路径

Windows 安装脚本会把 WebBridge 装到当前用户目录：

```powershell
$env:USERPROFILE\.kimi-webbridge
```

常见可执行文件路径：

```powershell
$env:USERPROFILE\.kimi-webbridge\bin\kimi-webbridge.exe
```

检查是否存在：

```powershell
$BinPath = "$env:USERPROFILE\.kimi-webbridge\bin\kimi-webbridge.exe"
Test-Path $BinPath
Get-Item $BinPath
```

查看状态：

```powershell
& "$env:USERPROFILE\.kimi-webbridge\bin\kimi-webbridge.exe" status
```

如果已加入 PATH：

```powershell
Get-Command kimi-webbridge -All
where.exe kimi-webbridge
kimi-webbridge status
```

从端口反查正在运行的进程路径：

```powershell
$pid = (Get-NetTCPConnection -LocalPort 10086 -State Listen).OwningProcess
Get-Process -Id $pid | Select-Object Id, ProcessName, Path
```

查看日志：

```powershell
Get-Content "$env:USERPROFILE\.kimi-webbridge\logs\daemon.log" -Tail 100
```

Hermes 在 WSL 中访问 Windows WebBridge：

```bash
WEBBRIDGE_BASE="http://$(ip route | awk '/default/ {print $3; exit}'):10086"
curl -s "$WEBBRIDGE_BASE/status"
```

## 安装

**1. Windows 端 — 装 WebBridge**

```powershell
.\scripts\install-webbridge.ps1
```

**2. WSL2 端 — 装 xhs 插件**

```bash
git clone http://192.168.8.251:8080/hr/xhs-ops ~/xhs-ops && cd ~/xhs-ops && sed -i 's/\r$//' install.sh && bash install.sh
```

也可以手动指定 WebBridge IP：

```bash
bash install.sh 172.26.240.1
```

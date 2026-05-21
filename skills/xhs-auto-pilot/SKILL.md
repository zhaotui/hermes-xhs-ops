---
name: xhs-auto-pilot
description: 小红书自驱动运营——cron 链式调度，自动发帖/扫评论/回帖/收集信息，24 小时无人值守。
---

# XHS Auto Pilot

> 基于 Hermes cron 的小红书自循环运营系统。
> 扫描通过 `scan_report.py` 脚本完成，发帖通过 `publish_auto.py` 脚本完成。

## 前置条件

- Windows 不锁屏不休眠
- Kimi WebBridge 运行中
- 浏览器已登录小红书
- Hermes gateway 运行中

## 依赖

| 组件 | 用途 |
|------|------|
| `scan_report.py` | 报告调度（默认扫评论，支持扩展新任务） |
| `publish_auto.py` | 浏览器自动化发帖 |
| `xhs-read-comments` | 笔记管理页→详情页读评论 |
| `xhs-collect-info` | 分类收集评论 → JSONL |
| `xhs-reply-comment` | 自动回复评论 |
| `xhs-delete-post` | 清理测试帖 |

## 调度架构

```
┌─────────────┐     ┌──────────────────┐
│ scan cron   │────▶│ scan_report.py   │
│ 每 15 分钟   │     │ → 报告 + JSONL   │
└─────────────┘     └──────────────────┘

┌─────────────┐     ┌──────────────────┐
│ post cron   │────▶│ publish_auto.py  │
│ 每天 1 次    │     │ → 发布 private    │
└─────────────┘     └──────────────────┘
```

## 搭建

```bash
# 扫评论（每 15 分钟）
hermes cron create --name xhs-scan --script scan_report.py --no-agent "*/15 * * * *"

# 发帖（每天上午 10 点）— 暂不开启
# hermes cron create --name xhs-post --script publish_auto.py --no-agent "0 10 * * *"
```

## 查看报告

```bash
ls ~/.hermes/data/xhs-ops/reports/
cat ~/.hermes/data/xhs-ops/reports/scan_*.md | tail -30
```

## 陷阱

- 电脑休眠/锁屏会导致 WebBridge 失效 → 电源设置"永不"
- session 统一用 `xhs`，不跨 session
- `scan_report.py` 存报告到 `~/.hermes/data/xhs-ops/reports/`
- 收集数据存到 `~/.hermes/data/xhs-ops/records.jsonl`

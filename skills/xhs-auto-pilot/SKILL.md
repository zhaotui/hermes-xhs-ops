---
name: xhs-auto-pilot
description: 小红书自驱动运营——cron 链式调度，自动发帖/扫评论/回帖/收集信息，24 小时无人值守。
---

# XHS Auto Pilot

> 基于 Hermes cron 的小红书自循环运营系统。
> 具体任务由 AI 执行，报告按 `xhs-report` 技能规范生成。

## 前置条件

- Windows 不锁屏不休眠
- Kimi WebBridge 运行中
- 浏览器已登录小红书
- Hermes gateway 运行中

## 依赖

| 组件 | 用途 |
|------|------|
| `xhs-publish-post` | 发布笔记 |
| `xhs-read-comments` | 笔记管理页→详情页读评论 |
| `xhs-collect-info` | 分类收集评论 → JSONL |
| `xhs-reply-comment` | 自动回复评论 |
| `xhs-delete-post` | 清理测试帖 |
| `xhs-report` | 报告格式与存储规范 |
| `publish_auto.py` | 浏览器自动化发帖 |

## 调度架构

```
┌─────────────┐     ┌──────────────────┐
│ scan cron   │────▶│ AI 扫评论 + 收集  │
│ 每 N 分钟    │     │ → xhs-report 报告 │
└─────────────┘     └──────────────────┘

┌─────────────┐     ┌──────────────────┐
│ post cron   │────▶│ publish_auto.py  │
│ 每天 1 次    │     │ → 发布            │
└─────────────┘     └──────────────────┘
```

## 查看报告

```bash
ls ~/.hermes/data/xhs-ops/reports/
```

## 陷阱

- 电脑休眠/锁屏会导致 WebBridge 失效 → 电源设置"永不"
- session 统一用 `xhs`
- 报告和收集数据按 `xhs-report` 规范存储

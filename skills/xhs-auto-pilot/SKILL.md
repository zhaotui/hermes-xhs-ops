---
name: xhs-auto-pilot
description: 小红书自驱动运营——用户定计划，AI 搭建 cron + 执行，每次定时任务自动输出报告。
---

# XHS Auto Pilot

> 用户只需说"每 X 分钟扫评论"、"每天发一篇帖"。
> AI 负责搭建 cron、执行任务、每次自动按 `xhs-report` 规范生成报告。

## 核心规则

1. **每次定时执行必须输出报告**，保存到 `~/.hermes/data/xhs-ops/reports/`
2. 报告格式按 `xhs-report` 技能规范
3. 这是自动行为，用户不需要显式要求

## 依赖

| 组件 | 用途 |
|------|------|
| `xhs-publish-post` | 发布笔记 |
| `xhs-read-comments` | 读评论 |
| `xhs-collect-info` | 收集信息 → JSONL |
| `xhs-reply-comment` | 回复评论 |
| `xhs-delete-post` | 清理测试帖 |
| `xhs-report` | 报告格式与存储 |
| `xhs-tab-manager` | tab 管理 |
| `publish_auto.py` | 浏览器发帖 |

## 使用方式

用户说计划，AI 做：
```bash
# 用户："每15分钟扫评论"
hermes cron create --name xhs-scan --skill xhs-read-comments --skill xhs-collect-info --skill xhs-report "*/15 * * * *" "读评论、分类、输出报告"

# 用户："每天10点发一篇生活帖"
hermes cron create --name xhs-post --skill xhs-publish-post --skill xhs-report "0 10 * * *" "生成生活帖发布，输出报告"

# 用户："每周清测试帖"
hermes cron create --name xhs-cleanup --skill xhs-delete-post --skill xhs-report "0 3 * * 0" "删除仅自己可见帖，输出报告"
```

## 查看报告

```bash
ls ~/.hermes/data/xhs-ops/reports/
```

## 陷阱

- 电脑休眠/锁屏 WebBridge 失效 → 电源"永不"
- session 统一用 `xhs`
- 每次 cron 执行完毕必须生成报告

---
name: xhs-report
description: 小红书运营报告规范——每次用户要求输出报告时按此格式生成，统一存储到固定位置。
---

# XHS Report

> 报告不是固化脚本，而是**由用户提出内容、AI 执行生成**。格式和存储位置是固定的。

## 存储位置

所有报告保存到 `~/.hermes/data/xhs-ops/reports/`，文件名格式 `{内容}_{YYYYMMDD_HHMMSS}.md`。

## 报告格式

```markdown
# {标题} — {时间戳 UTC}

## {分节标题}
{内容行}

## {分节标题}
{内容行}
```

- 标题由用户提出的内容决定（如"评论扫描"、"数据汇总"）
- 时间戳用 UTC
- 按需分节

## 执行方式

用户说"输出XX报告"时：
1. 通过 execute_code 执行浏览器操作或数据处理
2. 按上述格式生成报告
3. 保存到 `~/.hermes/data/xhs-ops/reports/`
4. 把报告内容展示给用户

## 查看历史报告

```bash
ls ~/.hermes/data/xhs-ops/reports/
cat ~/.hermes/data/xhs-ops/reports/report_*.md | tail -50
```

---
name: xhs-collect-info
description: 根据规则分类评论，收集用户主动提供的信息，保存到本地 JSONL。
---

# XHS Collect Info

> **依赖 Plugin:** `xhs` (提供 `xhs_collect_info` 工具)

## 输入

```json
{
  "goal": "任务目标",
  "comments_json": "[{\"authorName\":\"...\",\"text\":\"...\"}]",
  "positive_signals": "感兴趣,想了解,怎么报名",
  "negative_signals": "无关闲聊,表情,单纯问候"
}
```

## 流程

1. 从 `xhs_read_comments` 拿到评论 JSON
2. **调 `xhs_collect_info(comments_json=..., goal=..., ...)`** — 自动分类、去重、保存到 `/root/.hermes/data/xhs-ops/records.jsonl`
3. 输出收集结果

## 输出

```
本次收集到 X 条有效信息：
1. 用户：【name】 评论：【text】 分类：【useful/maybe_useful】
本地文件：/root/.hermes/data/xhs-ops/records.jsonl
```

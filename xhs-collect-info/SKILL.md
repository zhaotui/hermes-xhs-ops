---
name: xhs-collect-info
description: Classify Xiaohongshu comments, collect user-provided information, save records locally, and output collected results.
---

# XHS Collect Info

Use this skill only for classifying comments and saving user-provided information.

## Input

```json
{
  "goal": "任务目标",
  "comments": [
    {
      "authorName": "昵称",
      "timeText": "时间",
      "text": "评论原文"
    }
  ],
  "collectFields": ["联系方式", "需求", "城市"],
  "positiveSignals": ["感兴趣", "想了解", "怎么报名"],
  "negativeSignals": ["无关闲聊", "表情", "单纯问候"],
  "localOutputFile": "/root/.hermes/data/xhs-ops/records.jsonl"
}
```

## Classify And Collect

Use the task's own rules:

```text
positiveSignals -> useful
negativeSignals -> ignore
collectFields -> fields to extract
```

General rule:

```text
useful: user shows interest, asks details, or provides requested info
maybe_useful: related but missing information
ignore: emoji, greeting only, unrelated chat
```

Only collect information voluntarily written in the comment. Do not open profiles.

Common fields:

```text
联系方式: 微信, 手机号, 邮箱, QQ
城市/地点
需求/问题
经验/背景
报名信息
反馈/建议
```

Save useful and maybe-useful records to:

```text
/root/.hermes/data/xhs-ops/records.jsonl
```

Record shape:

```json
{
  "type": "xhs_collected_info",
  "goal": "任务目标",
  "platform": "xiaohongshu",
  "sourceType": "comment",
  "authorName": "昵称",
  "sourceText": "评论原文",
  "classification": "useful",
  "fields": {},
  "status": "new",
  "capturedAt": "ISO-8601 datetime"
}
```

Deduplicate by:

```text
goal + authorName + sourceText
```

## Reply Suggestions

For each useful or maybe-useful comment, include a suggested reply.

If enough information was collected:

```text
收到，我先记录下来了～
```

If useful but missing fields:

```text
收到，可以再补充一下{缺失字段}，我好记录完整～
```

## Output

Always end with:

```text
本次收集到 X 条有效信息：

1. 用户：
   评论：
   分类：
   收集字段：
   建议回复：
   状态：

本地文件：/root/.hermes/data/xhs-ops/records.jsonl
```

If none:

```text
本次没有收集到新的有效信息。
```

## Hard Rules

- Do not collect profile bio, followers, likes, or unrelated data.
- Do not invent collected information.

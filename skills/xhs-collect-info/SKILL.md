---
name: xhs-collect-info
description: 根据规则分类评论，收集用户主动提供的信息，保存到本地 JSONL。
---

# XHS Collect Info

> 实际通过 AI 分析评论 JSON + 本地文件写入完成（`xhs_collect_info` plugin tool 尚未实现）。

## 输入

```json
{
  "goal": "任务目标",
  "comments_json": "[{\"authorName\":\"...\",\"text\":\"...\",\"timeText\":\"...\"}]",
  "positive_signals": "感兴趣,想了解,怎么报名",
  "negative_signals": "无关闲聊,表情,单纯问候"
}
```

## 流程

1. 从 `xhs-read-comments` 拿到评论 JSON
2. AI 根据 positive/negative signals 逐条分类评论
3. 去重后保存到 `~/.hermes/data/xhs-ops/records.jsonl`（JSONL 格式）

## 分类逻辑（Python）

```python
def classify(text, positive_signals="感兴趣,想了解,怎么报名,联系,微信,电话,咨询",
                     negative_signals="你好,你好啊,哈喽,hi,在吗,表情,打卡"):
    for kw in positive_signals.split(","):
        if kw in text:
            return "useful"
    for kw in negative_signals.split(","):
        if kw in text:
            return "useless"
    return "maybe_useful"
```

## 保存格式

每行一条 JSONL 记录：
```json
{"authorName": "...", "text": "...", "timeText": "...", "classification": "useful|maybe_useful|useless", "collected_at": "ISO8601"}
```

## 输出

```
本次收集到 X 条有效信息：
1. 用户：【name】 评论：【text】 分类：【useful/maybe_useful/useless】
本地文件：~/.hermes/data/xhs-ops/records.jsonl
```

## 陷阱

- classification 三类：`useful`（命中 positive）、`useless`（命中 negative）、`maybe_useful`（均未命中）
- 追加写入（`"a"` mode），不会覆盖历史记录
- 需确保 `~/.hermes/data/xhs-ops/` 目录存在

---
name: xhs-collect-info
description: 根据规则分类评论，收集用户主动提供的信息，保存到本地 JSONL。
---

# XHS Collect Info

> 通过 `xhs_collect_info` plugin tool 完成。分类规则：positive 命中 → useful，其余 → ignore（不保存）。

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

1. 从 `xhs-read-comments` 拿到评论 JSON
2. Tool 逐条分类：positive 关键词命中 → `useful`，其余 → `ignore`
3. 去重后追加写入 `~/.hermes/data/xhs-ops/records.jsonl`

## 分类逻辑

```python
def classify(text):
    for s in positive_signals:
        if s in text:
            return "useful"
    return "ignore"  # 不保存
```

## 保存格式

每行一条 JSONL：
```json
{"type":"xhs_collected_info","goal":"...","platform":"xiaohongshu","sourceType":"comment","authorName":"...","sourceText":"...","classification":"useful","fields":{},"status":"new","capturedAt":"2026-05-21T..."}
```

## 输出

```
本次收集到 X 条有效信息：
1. 【authorName】: text [useful]
本地文件：~/.hermes/data/xhs-ops/records.jsonl
```

## 陷阱

- 分类两类：`useful`（命中 positive）和 `ignore`（其余，不写入文件）
- 追加写入，去重基于 (goal, authorName, sourceText) 三元组
- 目录自动创建

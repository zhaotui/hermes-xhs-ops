# XHS Ops — 小红书运营插件 + Skills

## 架构

```
plugin/                        ← Plugin（Python，注册 5 个工具到 Hermes）
  ├── plugin.yaml
  ├── __init__.py
  ├── client.py                → WebBridge HTTP 客户端
  └── tools.py                 → 工具实现

kimi-webbridge/                ← Skill（WebBridge 使用指南 + 代码片段库）

xhs-read-comments/             ← Skill（业务流程：何时调哪个工具）
xhs-reply-comment/             ← Skill
xhs-collect-info/              ← Skill
xhs-publish-post/              ← Skill
```

## 安装

```bash
# Skills（软链接）
ln -s /mnt/c/Users/yxkj/Desktop/work/xhs ~/.hermes/skills/xhs

# Plugin（软链接）
ln -s /mnt/c/Users/yxkj/Desktop/work/xhs/plugin /usr/local/lib/hermes-agent/plugins/xhs

# 启用
hermes plugins enable xhs
```

## Plugin 工具

| 工具 | 功能 | 状态 |
|------|------|------|
| `xhs_read_comments()` | 打开通知页，提取评论 | ✅ |
| `xhs_view_note_detail(note_index)` | 打开笔记前端详情页 | ✅ |
| `xhs_reply_comment(reply_text)` | 在详情页回复评论 | ✅ |
| `xhs_collect_info(...)` | 分类评论，保存 JSONL | ✅ |
| `xhs_publish_post(title, body)` | 发布笔记 | ⚠️ 待实现 |

## Skill 作用

Plugin 提供工具 → AI 直接调。Skill 提供**业务指南**（什么时候调、什么顺序、注意什么陷阱）。

## 完整流程

```
1. xhs_read_comments()          → 拿到评论列表
2. xhs_view_note_detail(N)      → 打开详情页查看完整上下文
3. xhs_reply_comment("回复")    → 回复评论
4. xhs_collect_info(...)        → 分类收集信息，保存到 JSONL
```

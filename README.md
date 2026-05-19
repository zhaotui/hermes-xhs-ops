# XHS Ops — 小红书运营插件

一个完整的 Hermes Plugin 项目，5 个工具 + 配套 Skills。

## 项目结构

```
xhs/                       ← Plugin 根目录（可直接 install）
├── plugin.yaml            ← 插件元数据
├── __init__.py             ← register() 入口
├── client.py               ← WebBridge HTTP 客户端
├── tools.py                ← 5 个工具实现
├── skills/                 ← 配套 Skills（业务编排指南）
│   ├── kimi-webbridge/     → WebBridge 使用指南 + 代码片段
│   ├── xhs-read-comments/  → 读评论 → 看详情
│   ├── xhs-reply-comment/  → 回复评论
│   ├── xhs-collect-info/   → 分类收集信息
│   └── xhs-publish-post/   → 发布笔记
└── README.md
```

## 安装

```bash
# Plugin（一条命令）
hermes plugins install https://github.com/xxx/xhs-ops.git
hermes plugins enable xhs

# Skills（手动）
git clone https://github.com/xxx/xhs-ops.git ~/xhs-ops
ln -s ~/xhs-ops/skills ~/.hermes/skills/xhs
```

## 工具

| 工具 | 功能 |
|------|------|
| `xhs_read_comments()` | 打开通知页，提取评论 |
| `xhs_view_note_detail(note_index)` | 打开笔记前端详情页 |
| `xhs_reply_comment(reply_text)` | 在详情页回复评论 |
| `xhs_collect_info(...)` | 分类评论，保存 JSONL |
| `xhs_publish_post(title, body)` | 发布笔记（待实现） |

## 流程示例

```
xhs_read_comments() → 拿到评论
xhs_view_note_detail(2) → 看详情
xhs_reply_comment("感谢") → 回复
xhs_collect_info(comments_json, goal) → 收集信息
```

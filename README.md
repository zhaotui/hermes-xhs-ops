# XHS Ops Skills

这是给 Hermes 使用的小红书通用运营 skills，已拆成 4 个独立 skill。

## 安装方式（软链接）

已通过软链接映射到 Hermes skills 目录，无需复制：

```bash
ln -s /mnt/c/Users/yxkj/Desktop/work/xhs ~/.hermes/skills/xhs
```

新增 skill 子目录后执行 `/reload-skills` 即可。

## Skills

| Skill | 功能 | 依赖 |
|-------|------|------|
| `xhs-read-comments` | 读取通知页评论 + 进入笔记详情页 | WebBridge |
| `xhs-collect-info` | 分类评论、收集信息、保存记录 | 无（纯数据处理） |
| `xhs-reply-comment` | 在笔记详情页回复评论 | WebBridge |
| `xhs-publish-post` | 发布小红书长文 | WebBridge |

## 已验证的完整流程

### 读取评论 + 查看详情

```
通知页（评论和@） → 提取评论 JSON → 笔记管理页 → 点封面图（PointerEvent）
→ 新标签打开详情页 → find_tab 绑定 → 查看完整评论和回复状态
```

### 回复评论

```
笔记详情页 → 找目标评论的"回复"按钮（按垂直位置排序取最后）
→ 点击 → P.content-input 填入文本 → 点"发送" → 验证回复位置
```

### 收集信息

```
读取评论 JSON → 按正/负向信号分类 → 去重 → 保存 JSONL → 输出摘要
```

## 重要陷阱

- **仅自己可见**的笔记无法打开前端详情页，只有已发布的笔记可以。
- 通知页不显示你是否已回复，必须进详情页确认。
- 封面图点击需要 PointerEvent + MouseEvent 联合 dispatch，普通 click 不生效。
- 新标签不在 session 追踪范围内，必须用 `find_tab` 查找并绑定。
- 每个评论都有"回复"文字，必须按位置选最后一个。
- evaluate 传中文/特殊字符用文件 + python3 构造 JSON，不要直接写 curl -d。

## WebBridge

```bash
# WSL 中动态获取 Windows 网关 IP
WEBBRIDGE_BASE="http://$(ip route | awk '/default/ {print $3; exit}'):10086"
curl -s "$WEBBRIDGE_BASE/status"
```

## 给 Hermes 的任务模板

### 读评论 + 进详情

```text
@xhs-read-comments

通过 kimi-webbridge 打开小红书通知页，读取"评论和@"里的评论。
如有新评论，进入笔记管理页，点封面图打开详情页查看完整上下文。

不要做复杂网络诊断。只检查 WebBridge status。
```

### 回复评论

```text
@xhs-reply-comment

在笔记详情页回复指定评论。注意：回复在详情页操作，不是通知页。

用户：【昵称】
回复内容：【回复文本】
```

### 收集信息

```text
@xhs-collect-info

根据评论判断哪些有用，只收集评论里用户主动提供的信息。

任务目标：【目标】
评论列表：【粘贴 @xhs-read-comments 输出的 JSON】
收集字段：联系方式、需求、城市
正向信号：感兴趣、想了解、怎么报名
负向信号：无关闲聊、表情、单纯问候
```

### 发布笔记

```text
@xhs-publish-post

通过 kimi-webbridge 发布一篇小红书长文。

任务目标：【目标】
可见范围：仅自己可见
```

# XHS Ops Skills

这是给 Hermes 使用的小红书通用运营 skills，已拆成 4 个独立 skill。

## Skills

```text
C:\Users\yxkj\Desktop\work\xhs\xhs-publish-post\SKILL.md
C:\Users\yxkj\Desktop\work\xhs\xhs-read-comments\SKILL.md
C:\Users\yxkj\Desktop\work\xhs\xhs-collect-info\SKILL.md
C:\Users\yxkj\Desktop\work\xhs\xhs-reply-comment\SKILL.md
```

WSL 路径：

```text
/mnt/c/Users/yxkj/Desktop/work/xhs/xhs-publish-post/SKILL.md
/mnt/c/Users/yxkj/Desktop/work/xhs/xhs-read-comments/SKILL.md
/mnt/c/Users/yxkj/Desktop/work/xhs/xhs-collect-info/SKILL.md
/mnt/c/Users/yxkj/Desktop/work/xhs/xhs-reply-comment/SKILL.md
```

如果 Hermes 需要安装到默认 skills 目录，可以复制：

```bash
mkdir -p /root/.hermes/skills/xhs-publish-post
mkdir -p /root/.hermes/skills/xhs-read-comments
mkdir -p /root/.hermes/skills/xhs-collect-info
mkdir -p /root/.hermes/skills/xhs-reply-comment
cp /mnt/c/Users/yxkj/Desktop/work/xhs/xhs-publish-post/SKILL.md /root/.hermes/skills/xhs-publish-post/SKILL.md
cp /mnt/c/Users/yxkj/Desktop/work/xhs/xhs-read-comments/SKILL.md /root/.hermes/skills/xhs-read-comments/SKILL.md
cp /mnt/c/Users/yxkj/Desktop/work/xhs/xhs-collect-info/SKILL.md /root/.hermes/skills/xhs-collect-info/SKILL.md
cp /mnt/c/Users/yxkj/Desktop/work/xhs/xhs-reply-comment/SKILL.md /root/.hermes/skills/xhs-reply-comment/SKILL.md
```

WebBridge 建议这样启动：

```bash
kimi-webbridge start --addr 0.0.0.0:10086
```

Hermes 在 WSL 中访问：

```bash
WEBBRIDGE_BASE="http://$(ip route | awk '/default/ {print $3; exit}'):10086"
echo "$WEBBRIDGE_BASE"
```

## 给 Hermes 的任务模板

```text
@xhs-publish-post

通过 kimi-webbridge 发布一篇小红书长文。

不要做复杂网络诊断。
先执行固定命令：
WEBBRIDGE_BASE="http://$(ip route | awk '/default/ {print $3; exit}'):10086"
只检查 $WEBBRIDGE_BASE/status。
如果不通就停止并告诉我 WebBridge 不通。

任务目标：
【在这里写目标】

要求：
1. 生成小红书长文内容。
2. 发布帖子，可见范围：仅自己可见。
```

```text
@xhs-read-comments

通过 kimi-webbridge 打开小红书通知页，读取“评论和@”里的评论。

不要做复杂网络诊断。
先执行固定命令：
WEBBRIDGE_BASE="http://$(ip route | awk '/default/ {print $3; exit}'):10086"
只检查 $WEBBRIDGE_BASE/status。
如果不通就停止并告诉我 WebBridge 不通。

要求：
1. 打开 https://www.xiaohongshu.com/notification。
2. 读取“评论和@”里的评论。
3. 输出评论 JSON 和中文摘要。
```

```text
@xhs-collect-info

根据评论判断哪些有用，只收集评论里用户主动提供的信息。

任务目标：
【在这里写目标】

评论列表：
【粘贴 @xhs-read-comments 输出的 JSON】

希望收集的信息：
- 联系方式
- 需求
- 城市

正向信号：
- 感兴趣
- 想了解
- 怎么报名

负向信号：
- 无关闲聊
- 表情
- 单纯问候

要求：
1. 保存到 /root/.hermes/data/xhs-ops/records.jsonl。
2. 输出本次收集到的信息。
3. 为有用但缺信息的评论生成建议回复。
```

```text
@xhs-reply-comment

通过 kimi-webbridge 回复指定评论。

不要做复杂网络诊断。
先执行固定命令：
WEBBRIDGE_BASE="http://$(ip route | awk '/default/ {print $3; exit}'):10086"
只检查 $WEBBRIDGE_BASE/status。
如果不通就停止并告诉我 WebBridge 不通。

用户：
【昵称】

评论：
【评论原文】

回复：
【回复内容】
```

---
name: ehr-xhs-publish
description: 从 EHR IndexedDB 读取待发布职位，格式化后发布到小红书，发布成功删除记录。
---

# EHR → 小红书 职位发布

从 `ehr.tenops.com` 的 IndexedDB (`ehr_xhs_publish/jobs`) 读取待发布职位，自动发布到小红书。

## 前置条件

- EHR 前端已通过 `saveXhsPublishJob()` 写入职位数据
- kimi-webbridge daemon 运行中
- 小红书已登录（浏览器 session）

## 数据结构（IndexedDB）

```typescript
interface XhsPublishJob {
  id: string;          // 职位 ID
  jobName: string;     // 职位名称 → 标题
  standardRole: string;// 标准岗位
  department: string;  // 部门
  salary: string;      // 薪资
  location: string;    // 省份-城市
  locationFull: string;// 完整地址
  headcount: number;   // 需求人数
  priority: string;    // 优先级
  jd: string;          // 职位描述 → 正文
  tags: string[];      // 标签
  creator: string;     // 创建人
  createdAt: string;   // 创建时间
}
```

数据库：`ehr_xhs_publish`，Store：`jobs`，keyPath：`id`

## 执行流程

### Step 1: 导航到 EHR

```bash
WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
WEBBRIDGE="http://${WIN_HOST}:10086/command"

# 打开 EHR
curl -s -X POST "$WEBBRIDGE" \
  -H 'Content-Type: application/json' \
  -d '{"action":"navigate","args":{"url":"https://ehr.tenops.com/","newTab":true},"session":"ehr-xhs"}'
```

### Step 2: 读取所有待发布职位

使用 evaluate 读 IndexedDB：

```js
(async () => {
  const result = await new Promise((resolve, reject) => {
    const req = indexedDB.open('ehr_xhs_publish', 2);
    req.onsuccess = (e) => {
      const tx = e.target.result.transaction('jobs', 'readonly');
      const getAll = tx.objectStore('jobs').getAll();
      getAll.onsuccess = () => resolve(getAll.result);
      getAll.onerror = () => reject(getAll.error);
    };
    req.onerror = () => resolve([]);
  });
  return JSON.stringify(result);
})()
```

返回 `XhsPublishJob[]`。

### Step 3: 按创建人匹配发布账号

读取 `accounts.json`，将 job 的 `creator` 与账号的 `linked_creator` 匹配，找到对应发布账号。

```python
xhs_account_manager(action="list")
# 返回 accounts 列表，每个 account 有 linked_creator 字段
# job.creator == account.linked_creator → 用这个账号发布
```

匹配规则：
- `creator` 精准匹配 `linked_creator` → 直接用该账号
- 多个账号匹配同一 creator → 优先用 `current`，其次第一个
- 无匹配 → 暂停，告知用户"XX 没有关联账号"，让用户指定或关联

匹配到账号后切换：
```python
xhs_account_manager(action="switch", key="matched_key")
```

### Step 4: 逐条发布

对每条 job 调用 `xhs_publish_post`：

- **title**: `【招聘】{jobName}`（≤30字，超出截断）
- **body**: 见下方模板
- **visibility**: `public`（需要确认）

正文模板：
```
📍 {location}  |  💰 {salary}  |  🏢 {department}

📋 {jd}

---
#招聘 #求职 #{location_city} #{department}
```

### Step 5: 删除已发布记录

```js
(async () => {
  const req = indexedDB.open('ehr_xhs_publish', 2);
  req.onsuccess = (e) => {
    const tx = e.target.result.transaction('jobs', 'readwrite');
    tx.objectStore('jobs').delete('JOB_ID');
    tx.oncomplete = () => e.target.result.close();
  };
})()
```

### Step 6: 失败处理

发布失败时保留记录，输出错误原因，继续处理下一条。

## 调用方式

用户手动触发或配置 cron 定时执行。

### 一键执行（推荐）

```bash
# 1. 读取待发布职位
JOBS=$(bash ~/.hermes/skills/xhs/ehr-xhs-publish/../../scripts/ehr-read-jobs.sh 2>/dev/null)
echo "$JOBS" | python3 -c "import json,sys; print(f'{len(json.load(sys.stdin))} 条待发布')"

# 2. 格式化并逐条发布
echo "$JOBS" | python3 scripts/ehr-format-job.py | python3 -c "
import json, sys
for item in json.load(sys.stdin):
    print(json.dumps(item, ensure_ascii=False))
"  # 这里 Hermes 会逐条调用 xhs_publish_post

# 3. 发布成功后删除
bash scripts/ehr-delete-job.sh <job_id>
```

### Cron 示例

```bash
*/10 * * * * bash /mnt/c/Users/yxkj/Desktop/work/xhs/scripts/ehr-read-jobs.sh | python3 /mnt/c/Users/yxkj/Desktop/work/xhs/scripts/ehr-format-job.py
```

## 文件清单

| 文件 | 用途 |
|------|------|
| `SKILL.md` | 本文档，完整工作流 |
| `scripts/ehr-read-jobs.sh` | npm 读 IndexedDB，输出 JSON |
| `scripts/ehr-delete-job.sh` | 删除指定 ID 的记录 |
| `scripts/ehr-format-job.py` | 职位数据 → 小红书发布参数 |

## 注意事项

- IndexedDB 是 per-origin，必须在 `ehr.tenops.com` 域下操作
- webbridge `evaluate` JS 内的中文须用文件+python3 JSON 传参方式
- 每次操作后检查 `indexedDB.databases()` 确认数据状态
- 小红书发布有频率限制，大量职位需分批

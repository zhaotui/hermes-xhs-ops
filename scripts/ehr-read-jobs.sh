#!/usr/bin/env bash
# EHR IndexedDB → 小红书 发布辅助脚本
# 用法: bash ehr-publish.sh
# 功能: 读取 ehr.tenops.com IndexedDB 中所有待发布职位，输出 JSON

set -euo pipefail

WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
WEBBRIDGE="http://${WIN_HOST}:10086/command"
SESSION="ehr-xhs"

# -------- 1. 导航到 EHR --------
echo ">>> 导航到 EHR..." >&2
curl -s -X POST "$WEBBRIDGE" \
  -H 'Content-Type: application/json' \
  -d "{\"action\":\"find_tab\",\"args\":{\"url\":\"ehr.tenops.com\",\"active\":true},\"session\":\"$SESSION\"}" > /dev/null 2>&1 || {
  curl -s -X POST "$WEBBRIDGE" \
    -H 'Content-Type: application/json' \
    -d "{\"action\":\"navigate\",\"args\":{\"url\":\"https://ehr.tenops.com/\",\"newTab\":true},\"session\":\"$SESSION\"}" > /dev/null 2>&1
}

sleep 2

# -------- 2. 读取 IndexedDB --------
echo ">>> 读取待发布职位..." >&2

cat > /tmp/ehr-read-jobs.js << 'JSEOF'
(async () => {
  const jobs = await new Promise((resolve) => {
    const req = indexedDB.open('ehr_xhs_publish', 2);
    req.onsuccess = (e) => {
      const db = e.target.result;
      if (!db.objectStoreNames.contains('jobs')) {
        db.close();
        return resolve([]);
      }
      const tx = db.transaction('jobs', 'readonly');
      const getAll = tx.objectStore('jobs').getAll();
      getAll.onsuccess = () => { db.close(); resolve(getAll.result); };
      getAll.onerror = () => { db.close(); resolve([]); };
    };
    req.onerror = () => resolve([]);
  });
  return JSON.stringify(jobs);
})()
JSEOF

CODE=$(cat /tmp/ehr-read-jobs.js)
RESP=$(curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'$SESSION'}))" "$CODE")")

# 提取数据
JOBS=$(echo "$RESP" | python3 -c "
import json, sys
data = json.load(sys.stdin)
if data.get('ok') and data.get('data',{}).get('type') == 'string':
    print(data['data']['value'])
else:
    print('[]')
")

echo "$JOBS"

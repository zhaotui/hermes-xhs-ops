#!/usr/bin/env bash
# 删除 EHR IndexedDB 中已发布的职位
# 用法: bash ehr-delete-job.sh <job_id>

set -euo pipefail
JOB_ID="${1:?请提供职位ID}"

WIN_HOST=$(ip route | awk '/default/ {print $3; exit}')
WEBBRIDGE="http://${WIN_HOST}:10086/command"
SESSION="ehr-xhs"

# 确保在 EHR 页面
curl -s -X POST "$WEBBRIDGE" \
  -H 'Content-Type: application/json' \
  -d "{\"action\":\"find_tab\",\"args\":{\"url\":\"ehr.tenops.com\",\"active\":true},\"session\":\"$SESSION\"}" > /dev/null 2>&1

cat > /tmp/ehr-delete.js << JSEOF
(async () => {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open('ehr_xhs_publish', 2);
    req.onsuccess = (e) => {
      const db = e.target.result;
      const tx = db.transaction('jobs', 'readwrite');
      tx.objectStore('jobs').delete('${JOB_ID}');
      tx.oncomplete = () => { db.close(); resolve('deleted'); };
      tx.onerror = () => reject(tx.error);
    };
    req.onerror = () => reject(req.error);
    setTimeout(() => reject(new Error('timeout')), 5000);
  });
})()
JSEOF

CODE=$(cat /tmp/ehr-delete.js)
curl -s -X POST "$WEBBRIDGE" -H 'Content-Type: application/json' \
  -d "$(python3 -c "import json,sys; print(json.dumps({'action':'evaluate','args':{'code':sys.argv[1]},'session':'$SESSION'}))" "$CODE")"

echo "Deleted job: $JOB_ID"

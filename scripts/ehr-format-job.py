#!/usr/bin/env python3
"""将 EHR 职位数据格式化为小红书发布参数"""

import json
import sys

def format_job(job: dict) -> dict:
    """输入: IndexedDB 中的一条 job 记录，输出: xhs_publish_post 参数"""
    
    job_name = job.get("jobName", "")
    title = f"【招聘】{job_name}"
    if len(title) > 30:
        title = title[:27] + "..."
    
    location = job.get("location", "")
    salary = job.get("salary", "")
    department = job.get("department", "")
    jd = job.get("jd", "")
    location_full = job.get("locationFull", "")
    city = location.split("-")[-1] if "-" in location else location
    
    body = f"""📍 {location}  |  💰 {salary}  |  🏢 {department}

📋 {jd}

---
#招聘 #求职 #{city} #{department}"""
    
    return {
        "title": title,
        "body": body,
        "visibility": "public",
        "content_type": f"招聘-{job_name}",
        "source_type": f"EHR({job.get('id', '')})",
    }

if __name__ == "__main__":
    data = json.load(sys.stdin)
    
    if isinstance(data, list):
        result = [{"id": job.get("id"), "params": format_job(job)} for job in data]
    else:
        result = {"id": data.get("id"), "params": format_job(data)}
    
    print(json.dumps(result, ensure_ascii=False, indent=2))

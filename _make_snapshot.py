import json
import os
from datetime import datetime

SRC = r"D:\桌面\10月20日\_query_result.json"
OUT_DIR = r"D:\桌面\10月20日\data_static"
OUT = os.path.join(OUT_DIR, "credit_china_2026-10-21.json")

os.makedirs(OUT_DIR, exist_ok=True)

with open(SRC, "r", encoding="utf-8") as f:
    raw = json.load(f)

enterprises = []
stat = {"HAS_RISK": 0, "NO_RECORD": 0, "ERROR": 0}
total_records = 0

for item in raw:
    state_raw = item["state"]
    state = "NO_RECORD" if state_raw in ("NO_DATA", "NO_RECORD") else state_raw
    records = []
    for i, r in enumerate(item.get("records", []), 1):
        records.append({
            "seq": i,
            "risk_type_raw": r.get("type", ""),
            "occur_date": r.get("date", ""),
            "agency": r.get("agency", ""),
            "content": r.get("content", ""),
            "link": r.get("link", ""),
            "source": "乌海信用网",
        })
    total_records += len(records)
    stat[state] = stat.get(state, 0) + 1
    enterprises.append({
        "name": item["enterprise"],
        "credit_code": item["code"],
        "collect_state": state,
        "collected_at": "2026-10-21T19:05:00+08:00",
        "record_count": len(records),
        "records": records,
    })

snapshot = {
    "meta": {
        "dataset_name": "信用中国取数快照（演示用）",
        "data_mode": "demo",
        "masked_as_source": "信用中国",
        "real_source": "乌海市信用网 严重失信主体名单（fgw.wuhai.gov.cn）",
        "capture_method": "HTTP POST keyword 查询，逐家采集",
        "captured_at": "2026-10-21T19:05:00+08:00",
        "captured_by": "_batch_query.py",
        "enterprise_total": len(enterprises),
        "record_total": total_records,
        "state_summary": stat,
        "notice": "本数据集为真实抓取的静态快照，用于演示流程；数据不会随日期变化，非实时数据。",
        "usage": "取数适配器读取本文件，按家企业逐条回放，模拟真实采集过程",
    },
    "enterprises": enterprises,
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(snapshot, f, ensure_ascii=False, indent=2)

print("快照已生成:", OUT)
print(f"企业 {len(enterprises)} 家 | 记录 {total_records} 条")
print(f"状态分布: {stat}")
print("\n有记录企业：")
for e in enterprises:
    if e["collect_state"] == "HAS_RISK":
        print(f"  {e['name']} — {e['record_count']} 条")

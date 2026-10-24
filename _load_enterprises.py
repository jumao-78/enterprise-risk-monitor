import csv
import os
from datetime import date

import pymysql

BASE = r"D:\桌面\10月20日"
REAL_CSV = BASE + r"\企业名单_真实.csv"
DEMO_CSV = BASE + r"\企业名单_演示.csv"
TODAY = date(2026, 10, 21)

DB = dict(host="127.0.0.1", port=3307, user="riskmonitor",
          password=os.environ.get("DB_PASSWORD", "<本地 MySQL 口令>"),
          charset="utf8mb4", autocommit=False)

SQL = """
INSERT INTO enterprise (name, credit_code, industry, tag, enabled, join_date, remark)
VALUES (%s,%s,%s,%s,%s,%s,%s)
ON DUPLICATE KEY UPDATE
  name=VALUES(name), industry=VALUES(industry), tag=VALUES(tag), remark=VALUES(remark)
"""


def load(dbname, csv_path):
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    conn = pymysql.connect(database=dbname, **DB)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM risk_record")
        rc = cur.fetchone()[0]
        if rc:
            raise SystemExit(f"{dbname} 已有 {rc} 条风险记录，拒绝清空企业表")
        cur.execute("DELETE FROM enterprise")
        for r in rows:
            cur.execute(SQL, (
                r["企业名称"].strip(), r["统一社会信用代码"].strip(),
                r["行业"].strip(), r["分组标签"].strip(),
                1 if r["启用"].strip() == "是" else 0, TODAY,
                r.get("数据来源", "").strip() or r.get("备注", "").strip(),
            ))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM enterprise")
        n = cur.fetchone()[0]
        cur.execute("SELECT name, credit_code, industry FROM enterprise ORDER BY id LIMIT 3")
        sample = cur.fetchall()
    conn.close()
    print(f"[{dbname}] 导入 {n} 家（CSV {len(rows)} 行）")
    for s in sample:
        print(f"    {s[0]} | {s[1]} | {s[2]}")


load("risk_monitor", REAL_CSV)
load("risk_monitor_demo", DEMO_CSV)

print("\n=== 两库企业数核对 ===")
for db in ("risk_monitor", "risk_monitor_demo"):
    conn = pymysql.connect(database=db, **DB)
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*), SUM(enabled) FROM enterprise")
        total, enabled = cur.fetchone()
    conn.close()
    print(f"  {db}: 共 {total} 家，启用 {enabled} 家")

print("LOAD_OK")

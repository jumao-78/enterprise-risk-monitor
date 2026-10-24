import csv
import json
import re
import time
import urllib.parse
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
URL = "https://fgw.wuhai.gov.cn/xywh/blackList.jspx"
CSV = r"D:\桌面\10月20日\企业名单_真实.csv"
OUT = r"D:\桌面\10月20日\_query_result.json"


def query(keyword):
    data = urllib.parse.urlencode({"keyword": keyword, "pageNo": "1"}).encode()
    req = urllib.request.Request(
        URL, data=data, method="POST",
        headers={"User-Agent": UA,
                 "Content-Type": "application/x-www-form-urlencoded",
                 "Referer": URL})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", errors="ignore")


def parse(html):
    m = re.search(r"<table[\s\S]*?</table>", html, re.I)
    if not m:
        return [], "NO_DATA"
    rows = []
    for r in re.findall(r"<tr[\s\S]*?</tr>", m.group(0), re.I):
        c = [re.sub(r"<[^>]+>", "", x).replace("&nbsp;", " ").strip()
             for x in re.findall(r"<t[dh][^>]*>([\s\S]*?)</t[dh]>", r, re.I)]
        if len(c) >= 5 and "统一社会信用代码" not in c[1]:
            rows.append({"name": c[0], "code": c[1], "type": c[2],
                         "date": c[3], "agency": c[4]})
    if rows:
        return rows, "HAS_RISK"
    return [], "NO_DATA"


with open(CSV, "r", encoding="utf-8-sig", newline="") as f:
    targets = list(csv.DictReader(f))

print(f"共 {len(targets)} 家，开始查询（间隔 2.5s）\n")
results = []
stat = {"HAS_RISK": 0, "NO_DATA": 0, "ERROR": 0}

for i, row in enumerate(targets, 1):
    name = row["企业名称"].strip()
    code = row["统一社会信用代码"].strip()
    try:
        html = query(code if code else name)
        records, state = parse(html)
    except Exception as e:
        records, state = [], "ERROR"
        print(f"  [{i:02d}] {name} -> ERROR {type(e).__name__}")
    else:
        mark = "命中" if state == "HAS_RISK" else "无记录"
        print(f"  [{i:02d}] {name[:22]:<24} -> {mark} {len(records)} 条")
        for r in records:
            print(f"        {r['type']} | {r['date']} | {r['agency']}")
    stat[state] = stat.get(state, 0) + 1
    results.append({"enterprise": name, "code": code, "state": state,
                    "records": records, "source": "乌海信用网"})
    time.sleep(2.5)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print("\n" + "=" * 60)
print(f"命中 {stat['HAS_RISK']} 家 / 无记录 {stat['NO_DATA']} 家 / 错误 {stat['ERROR']} 家")
print(f"风险记录总条数: {sum(len(r['records']) for r in results)}")
print("结果已保存:", OUT)

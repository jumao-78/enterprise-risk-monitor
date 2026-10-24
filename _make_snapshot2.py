import json
import os

SRC = r"D:\桌面\10月20日\_query_result.json"
OUT_DIR = r"D:\桌面\10月20日\data_static"
OUT = os.path.join(OUT_DIR, "credit_china_2026-10-21.json")

# 密云黑名单（页面三列：名称|代码|名单类型，无日期）
MIYUN_BLACK = [
    ("北京皓宇垚节能环保设备有限公司", "91110228318047722J"),
    ("北京金碧伟业印刷有限公司", "91110228103010121U"),
    ("北京盛杰伟业装饰有限公司", "91110228661552582Y"),
    ("北京绿润食品有限公司", "911102287526271801"),
    ("北京中昌建设劳务有限公司", "9111022809717767XP"),
]

# 内蒙古失信名单（搜索抓取到公示页内容）
NM_LIST = [
    ("安徽仁伟建筑工程有限公司河南第一分公司", "91410105MA9K40C26K", "南乐县人民法院"),
    ("四川上里人和农业开发有限公司", "91511802MAC7N5WE2D", "雅安市雨城区人民法院"),
    ("丽水市正道电力科技有限公司", "91331102MA2E1BB338", "东乡县人民法院"),
    ("广州艾士弘机电安装工程有限公司", "91440115MABWLX1W96", "广州市南沙区人民法院"),
    ("紫云自治县翔宇房地产开发有限公司", "91520425082794907K", "紫云苗族布依族自治县人民法院"),
]

# 红名单（正面资质，不是风险）
RED_LIST = [
    ("北京尚华伟业科技有限公司", "91110228062780540L", "A级纳税人", "北京市密云区经信局", "2026-06-11"),
    ("北京碧海怡景园林绿化有限公司", "91110113748822098C", "A级纳税人", "北京市密云区经信局", "2026-06-11"),
    ("中建电子信息技术有限公司", "91110108100018355R", "A级纳税人", "北京市密云区经信局", "2026-06-11"),
    ("安徽福榕药业有限公司", "91341600MA2WAUDW0J", "A级守合同重信用", "亳州市谯城区市场监管局", "2026-08-18"),
    ("景德镇琢器陶瓷有限公司", "91360203MA388HBA15", "A级纳税人", "景德镇市税务局", "2026-04-30"),
]

with open(SRC, "r", encoding="utf-8") as f:
    wuhai = json.load(f)

ent_map = {}

# 1) 乌海：真实抓取的 10 家 12 条
for item in wuhai:
    state = "NO_RECORD" if item["state"] in ("NO_DATA", "NO_RECORD") else item["state"]
    recs = [{
        "seq": i,
        "risk_type_raw": r.get("type", ""),
        "occur_date": r.get("date", ""),
        "agency": r.get("agency", ""),
        "content": r.get("content", ""),
        "link": r.get("link", ""),
        "source": "乌海市信用网",
        "source_page": "https://fgw.wuhai.gov.cn/xywh/blackList.jspx",
    } for i, r in enumerate(item.get("records", []), 1)]
    ent_map[item["enterprise"]] = {
        "name": item["enterprise"], "credit_code": item["code"],
        "collect_state": state, "record_count": len(recs),
        "records": recs, "positive_info": None,
        "collect_note": "HTTP POST keyword 查询直采" if recs else "查询成功，未检索到风险记录",
    }

# 2) 密云黑名单 5 家
for name, code in MIYUN_BLACK:
    ent_map[name] = {
        "name": name, "credit_code": code, "collect_state": "HAS_RISK", "record_count": 1,
        "records": [{
            "seq": 1, "risk_type_raw": "失信被执行人名单", "occur_date": "", "agency": "",
            "content": "北京市密云区黑名单公示（页面未列列入日期）", "link": "",
            "source": "北京市密云区人民政府-黑名单查询",
            "source_page": "https://www.bjmy.gov.cn/zwgk/ztbd/xymy/lhjc/hhmdcx/hmdcx0/index_14.html",
        }],
        "positive_info": None,
        "collect_note": "公示页直采，字段仅含名称/代码/名单类型",
    }

# 3) 内蒙古失信名单 5 家
for name, code, court in NM_LIST:
    ent_map[name] = {
        "name": name, "credit_code": code, "collect_state": "HAS_RISK", "record_count": 1,
        "records": [{
            "seq": 1, "risk_type_raw": "失信被执行人", "occur_date": "2026-10-09", "agency": court,
            "content": "", "link": "",
            "source": "信用中国(内蒙古)-失信被执行人名单",
            "source_page": "https://fgw.nmg.gov.cn/xynmg/creditChinaLhjcSearchList.jspx",
        }],
        "positive_info": None,
        "collect_note": "公示页内容（经搜索引擎抓取）",
    }

# 4) 红名单 5 家：记为无风险 + 正面资质
for name, code, kind, agency, date in RED_LIST:
    ent_map[name] = {
        "name": name, "credit_code": code, "collect_state": "NO_RECORD", "record_count": 0,
        "records": [], "positive_info": {"kind": kind, "agency": agency, "date": date},
        "collect_note": "守信红名单企业，无失信风险记录；正面资质单独标注，不计入风险记录",
    }

ent_list = list(ent_map.values())
has_risk = sum(1 for e in ent_list if e["collect_state"] == "HAS_RISK")
no_record = sum(1 for e in ent_list if e["collect_state"] == "NO_RECORD")
total_rec = sum(e["record_count"] for e in ent_list)

snapshot = {
    "meta": {
        "dataset_name": "信用中国取数快照（演示用）",
        "data_mode": "demo",
        "masked_as_source": "信用中国",
        "real_sources": [
            "乌海市信用网 严重失信主体名单（HTTP POST 直采）",
            "北京市密云区人民政府 黑/红名单公示（HTML 直采）",
            "信用中国(内蒙古) 失信被执行人名单（页面内容）",
            "亳州市谯城区 A级守合同重信用公示",
            "信用中国(江西景德镇) 守信红榜",
        ],
        "captured_at": "2026-10-21T19:05:00+08:00",
        "capture_scripts": ["_batch_query.py", "_fetch_rest.py", "_parse_miyun.py"],
        "enterprise_total": len(ent_list),
        "has_risk_total": has_risk,
        "no_record_total": no_record,
        "record_total": total_rec,
        "notice": "本数据集为真实公示数据的静态快照，用于演示流程；不随日期变化，非实时数据。",
        "semantic_rule": "红名单(A级纳税人/守合同重信用)属正面资质，不计入风险记录；collect_state=NO_RECORD 表示未检索到风险记录，不等于绝对无风险。",
        "usage": "取数适配器读取本文件，按企业逐家回放，模拟真实采集过程（延迟 3-8s、进度上报）",
    },
    "enterprises": ent_list,
}

os.makedirs(OUT_DIR, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(snapshot, f, ensure_ascii=False, indent=2)

print("快照已更新:", OUT)
print(f"企业 {len(ent_list)} 家 | 有风险 {has_risk} 家 | 无记录 {no_record} 家 | 记录 {total_rec} 条")
print("\n有风险企业清单：")
for e in ent_list:
    if e["collect_state"] == "HAS_RISK":
        print(f"  {e['name'][:24]:<26} {e['record_count']} 条 | {e['records'][0]['source'][:20]}")

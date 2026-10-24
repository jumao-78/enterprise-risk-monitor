import csv
import re
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

PAGES = {
    "密云-黑名单": "https://www.bjmy.gov.cn/zwgk/ztbd/xymy/lhjc/hhmdcx/hmdcx0/index_14.html",
    "密云-红名单": "https://www.bjmy.gov.cn/zwgk/ztbd/xymy/lhjc/hhmdcx/hmdcx/index_334.html",
    "内蒙古-失信名单": "https://fgw.nmg.gov.cn/xynmg/creditChinaLhjcSearchList.jspx?category=local_sxbzxrmd&name=%E5%A4%B1%E4%BF%A1%E8%A2%AB%E6%89%A7%E8%A1%8C%E4%BA%BA%E5%90%8D%E5%8D%95&navPage=3",
    "亳州-守合同重信用": "https://www.bzqc.gov.cn/XxgkContent/show/3003343.html",
    "景德镇-红榜": "https://credit.jdz.gov.cn/cms/creditpublic/toHongmingdan.action",
}

# 未命中的 15 家
TARGETS = {
    "北京皓宇垚节能环保设备有限公司": "91110228318047722J",
    "北京金碧伟业印刷有限公司": "91110228103010121U",
    "北京盛杰伟业装饰有限公司": "91110228661552582Y",
    "北京绿润食品有限公司": "911102287526271801",
    "北京中昌建设劳务有限公司": "9111022809717767XP",
    "安徽仁伟建筑工程有限公司河南第一分公司": "91410105MA9K40C26K",
    "四川上里人和农业开发有限公司": "91511802MAC7N5WE2D",
    "丽水市正道电力科技有限公司": "91331102MA2E1BB338",
    "广州艾士弘机电安装工程有限公司": "91440115MABWLX1W96",
    "紫云自治县翔宇房地产开发有限公司": "91520425082794907K",
    "北京尚华伟业科技有限公司": "91110228062780540L",
    "北京碧海怡景园林绿化有限公司": "91110113748822098C",
    "中建电子信息技术有限公司": "91110108100018355R",
    "安徽福榕药业有限公司": "91341600MA2WAUDW0J",
    "景德镇琢器陶瓷有限公司": "91360203MA388HBA15",
}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        raw = r.read()
    for enc in ("utf-8", "gbk", "gb18030"):
        try:
            return raw.decode(enc), enc
        except UnicodeDecodeError:
            pass
    return raw.decode("utf-8", errors="ignore"), "ignore"


def extract_pairs(html):
    text = re.sub(r"<[^>]+>", "|", html)
    text = text.replace("&nbsp;", " ").replace("\n", "|")
    pairs = []
    for name, code in TARGETS.items():
        if name in text:
            pairs.append((name, code, "名称命中"))
        elif code in text:
            pairs.append((name, code, "代码命中"))
    return pairs


all_hit = {}
for page, url in PAGES.items():
    print("=" * 66)
    print(page)
    try:
        html, enc = fetch(url)
    except Exception as e:
        print("  抓取失败:", type(e).__name__, str(e)[:100])
        continue
    print(f"  HTML={len(html)} 编码={enc}")
    hits = extract_pairs(html)
    if hits:
        for n, c, how in hits:
            print(f"  ✓ {n} [{how}]")
            all_hit[n] = {"code": c, "page": page, "how": how}
    else:
        print("  本页未命中目标企业")

print("\n" + "=" * 66)
print(f"命中 {len(all_hit)} / {len(TARGETS)} 家")
missing = [n for n in TARGETS if n not in all_hit]
if missing:
    print("仍未命中：")
    for m in missing:
        print("  -", m)

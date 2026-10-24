import re
import urllib.request

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

PAGES = {
    "黑名单": "https://www.bjmy.gov.cn/zwgk/ztbd/xymy/lhjc/hhmdcx/hmdcx0/index_14.html",
    "红名单": "https://www.bjmy.gov.cn/zwgk/ztbd/xymy/lhjc/hhmdcx/hmdcx/index_334.html",
}
NAMES = ["北京皓宇垚节能环保设备有限公司", "北京金碧伟业印刷有限公司",
         "北京盛杰伟业装饰有限公司", "北京绿润食品有限公司",
         "北京中昌建设劳务有限公司", "北京尚华伟业科技有限公司",
         "北京碧海怡景园林绿化有限公司", "中建电子信息技术有限公司"]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode("utf-8", errors="ignore")


for label, url in PAGES.items():
    html = fetch(url)
    # 去掉 script/style，保留结构
    body = re.sub(r"<(script|style)[\s\S]*?</\1>", "", html, flags=re.I)
    print("=" * 70)
    print(label, "HTML=", len(body))
    for name in NAMES:
        idx = body.find(name)
        if idx < 0:
            continue
        seg = body[max(0, idx - 400): idx + 500]
        plain = re.sub(r"<[^>]+>", "|", seg)
        plain = re.sub(r"[|\s]+", "|", plain).strip("|")
        print(f"\n  【{name}】")
        print("   ", plain[:320])

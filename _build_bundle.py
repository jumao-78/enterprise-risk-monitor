# -*- coding: utf-8 -*-
"""把 proto/ 下的 4 个原型页合并为单个可分发 HTML。
每页保留各自的 <style> / 结构 / <script>，在独立文档中运行，外层提供统一侧栏与顶栏。
"""
import json
import re
from pathlib import Path

WS = Path(r"D:/桌面/10月20日")
SRC = WS / "proto"
OUT = WS / "企业风险监测_原型汇总.html"

PAGES = [
    ("overview", "01-总览.html", "总览"),
    ("tasks",    "03-取数任务.html", "取数·任务"),
    ("detail",   "02-风险明细.html", "风险明细"),
    ("ai",       "04-AI与邮件.html", "AI 与邮件"),
    ("config",   "05-配置.html",     "配置"),
    ("setting",  "06-系统设置.html", "系统设置"),
]
NAME2KEY = {fn: key for key, fn, _ in PAGES}

SVG = {
    "overview": '<rect x="1.7" y="1.7" width="5" height="5" rx="1.4"/><rect x="9.3" y="1.7" width="5" height="5" rx="1.4"/><rect x="1.7" y="9.3" width="5" height="5" rx="1.4"/><rect x="9.3" y="9.3" width="5" height="5" rx="1.4"/>',
    "tasks":    '<path d="M8 1.8v7.4M8 9.2 4.9 6.1M8 9.2l3.1-3.1M2.2 11.4v1.6c0 .7.6 1.2 1.2 1.2h9.2c.7 0 1.2-.6 1.2-1.2v-1.6"/>',
    "detail":   '<path d="M2.4 3.6h8.4M2.4 8h11.2M2.4 12.4h6.6"/><circle cx="13.1" cy="3.6" r="1.2"/>',
    "ai":       '<rect x="1.8" y="3.2" width="12.4" height="9.6" rx="1.8"/><path d="m2.4 4.4 5.6 3.9 5.6-3.9"/>',
    "config":   '<path d="M2.5 4.8h11M2.5 8h11M2.5 11.2h11"/><circle cx="6" cy="4.8" r="1.6" fill="#fff"/><circle cx="10.6" cy="8" r="1.6" fill="#fff"/><circle cx="5" cy="11.2" r="1.6" fill="#fff"/>',
    "setting":  '<circle cx="8" cy="8" r="2.3"/><path d="M8 1.6v1.7M8 12.7v1.7M1.6 8h1.7M12.7 8h1.7M3.5 3.5l1.2 1.2M11.3 11.3l1.2 1.2M12.5 3.5l-1.2 1.2M4.7 11.3l-1.2 1.2"/>',
}


def ico(name, size=16):
    return ('<svg width="%d" height="%d" viewBox="0 0 16 16" fill="none" stroke="currentColor" '
            'stroke-width="1.4">%s</svg>') % (size, size, SVG[name])


ROUTER = """
<style>
/* 动画兜底：部分环境（省电模式 / 低帧率 / 无头渲染）不推进动画时钟，
   2 秒后强制回到终态，保证图表与折线一定完整可见。 */
.anim-done .bar,
.anim-done .line,
.anim-done .dot{animation:none!important; opacity:1!important; transform:none!important; stroke-dashoffset:0!important}
</style>
<script>
(function(){
  document.addEventListener('click', function(e){
    var t = e.target, a = null;
    while(t && t !== document){
      if(t.getAttribute && t.getAttribute('data-nav')){ a = t; break; }
      t = t.parentNode;
    }
    if(!a) return;
    e.preventDefault();
    try{ parent.WB_NAV(a.getAttribute('data-nav')); }catch(err){}
  });
  setTimeout(function(){
    document.documentElement.className += ' anim-done';
  }, 2000);
})();
</script>
"""


def extract(fn):
    html = (SRC / fn).read_text(encoding="utf-8")
    styles = re.findall(r"<style>(.*?)</style>", html, re.S)
    body = html.split("<body>", 1)[1]
    i = body.index('<main class="wrap">')
    j = body.index("</main>", i)
    content = body[i:j + len("</main>")]
    rest = body[j + len("</main>"):]
    k = rest.index("<script")
    tail = rest[:k]
    tail = re.sub(r"^\s*</div>\s*</div>", "", tail, count=1)
    scripts = re.findall(r"<script[^>]*>.*?</script>", rest[k:], re.S)
    return styles, content, tail, scripts


def build_doc(key, fn, title):
    styles, content, tail, scripts = extract(fn)
    # 跨页链接改为 data-nav，交给外层壳路由
    for name, k2 in NAME2KEY.items():
        content = content.replace('href="%s"' % name, 'href="#" data-nav="%s"' % k2)
        tail = tail.replace('href="%s"' % name, 'href="#" data-nav="%s"' % k2)
    # 纯占位锚点不再触发滚动
    content = content.replace('href="#"', 'href="javascript:void 0"')
    tail = tail.replace('href="#"', 'href="javascript:void 0"')
    doc = (
        '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<title>企业风险监测 · %s</title>\n<style>\n%s\n</style>\n'
        '</head>\n<body>\n%s\n%s\n%s\n'
        '%s\n</body>\n</html>'
    ) % (title, "\n".join(styles), content, tail, "\n".join(scripts), ROUTER)
    return doc


NAV_ITEMS = "".join(
    '\n      <a class="item%s" data-page="%s" title="%s">%s\n        %s%s\n      </a>'
    % (
        " on" if key == "overview" else "",
        key,
        title,
        ico(key),
        title,
        {"overview": ' <span class="dot d-part" title="部分完成"></span>',
         "detail":   ' <span class="dot d-part" title="部分完成"></span>',
         "ai":       ' <span class="dot d-wait" title="待分析"></span>'}.get(key, ""),
    )
    for key, _, title in PAGES
)

PARENT = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>企业风险监测 · 原型汇总</title>
<style>
:root{
  --sans:"Inter","Segoe UI Variable Text","Segoe UI","Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;
  --bg:#F5F6F8; --card:#FFFFFF;
  --line:#EDEFF3; --line-2:#E3E6EB;
  --text:#16181D; --text-2:#5B6270; --text-3:#8A9099; --text-4:#AAB0B9;
  --shadow:0 1px 2px rgba(17,24,39,.04);
  --amber:#B45309;
}
*{box-sizing:border-box}
html,body{margin:0;padding:0;height:100%}
html{scrollbar-width:none; -ms-overflow-style:none}
::-webkit-scrollbar{width:0;height:0}
body{background:var(--bg); color:var(--text); font-family:var(--sans); font-size:13px; line-height:1.5;
  -webkit-font-smoothing:antialiased; font-variant-numeric:tabular-nums; overflow:hidden}
button{font-family:inherit; color:inherit}
.app{display:flex; height:100vh; height:100dvh; overflow:hidden}

/* 侧栏 */
.side{width:228px; flex:0 0 228px; background:var(--card); border-right:1px solid var(--line);
  padding:13px 11px; display:flex; flex-direction:column; height:100vh; height:100dvh;
  overflow-y:auto; overflow-x:hidden; transition:width .18s ease, flex-basis .18s ease}
.brand{display:flex; align-items:center; gap:9px; padding:5px 8px 14px}
.brand .mark{width:26px;height:26px;border-radius:7px;background:#16181D;display:grid;place-items:center;flex:0 0 26px}
.brand .name{font-size:13.5px; font-weight:600; letter-spacing:-.01em; white-space:nowrap}
.brand .collapse{margin-left:auto; background:none;border:0;padding:0;cursor:pointer;display:flex;align-items:center;
  color:var(--text-4);transition:transform .18s,color .12s}
.brand .collapse:hover{color:var(--text-2)}
.grp{font-size:11.5px; color:var(--text-4); padding:9px 9px 5px; white-space:nowrap}
.nav{display:flex; flex-direction:column; gap:1px}
.item{display:flex; align-items:center; gap:9px; height:32px; padding:0 9px; border-radius:7px;
  color:var(--text-2); font-size:12.5px; cursor:pointer; text-decoration:none; user-select:none; white-space:nowrap}
.item svg{flex:0 0 16px; color:var(--text-3)}
.item:hover{background:#F7F8FA; color:var(--text)}
.item.on{background:#F2F3F5; color:var(--text); font-weight:500}
.item.on svg{color:var(--text)}
.item.disabled{color:var(--text-4); cursor:default}
.item.disabled:hover{background:none; color:var(--text-4)}
.item .dot{margin-left:auto; width:6px;height:6px;border-radius:50%}
.d-ok{background:#22A45D} .d-part{background:#E29A2D} .d-wait{background:#C6CAD1}
.side-foot{margin-top:auto; padding-top:8px}
.srcs{display:flex; flex-direction:column; gap:1px}
.srcrow{display:flex; align-items:center; gap:9px; height:28px; padding:0 9px; font-size:12px; color:var(--text-2); white-space:nowrap}
.srcrow .sq{width:7px;height:7px;border-radius:2px;flex:0 0 7px}
.srcrow span{margin-left:auto; font-size:11px; color:var(--text-4)}
.demo-card{border:1px solid #F3E3C8; background:#FFFCF6; border-radius:9px; padding:9px 10px; margin:12px 0 10px}
.demo-card .t{display:flex; align-items:center; gap:6px; font-size:11.5px; font-weight:600; color:var(--amber)}
.demo-card .t i{width:6px;height:6px;border-radius:50%;background:#E29A2D}
.demo-card p{margin:4px 0 0; font-size:11px; color:var(--text-3); line-height:1.55}
.demo-card a{display:inline-block;margin-top:5px;font-size:11px;color:var(--text-2);text-decoration:none;border-bottom:1px solid var(--line-2)}
.user{display:flex; align-items:center; gap:9px; padding:9px 5px 3px; border-top:1px solid var(--line)}
.user .av{width:26px;height:26px;border-radius:50%;background:#E9EBEF;display:grid;place-items:center;font-size:11px;color:var(--text-2);flex:0 0 26px}
.user .nm{font-size:12px; font-weight:500; line-height:1.3; white-space:nowrap}
.user .em{font-size:10.5px; color:var(--text-4); line-height:1.3; white-space:nowrap}

/* 侧栏收起 */
.app.collapsed .side{width:68px;flex-basis:68px;padding:13px 11px}
.app.collapsed .brand{gap:5px;padding:5px 4px 14px}
.app.collapsed .brand .name{display:none}
.app.collapsed .brand .collapse{margin-left:auto;transform:rotate(180deg)}
.app.collapsed .grp{display:none}
.app.collapsed .item{justify-content:center;padding:0;font-size:0;position:relative}
.app.collapsed .item .dot{position:absolute;top:8px;right:11px;margin:0}
.app.collapsed .srcs{display:none}
.app.collapsed .demo-card{display:none}
.app.collapsed .user{justify-content:center;padding:9px 0 3px}
.app.collapsed .user > span:last-child{display:none}

/* 顶栏 */
.main{flex:1; min-width:0; display:flex; flex-direction:column; height:100vh; height:100dvh; overflow:hidden}
.top{height:54px; flex:0 0 54px; background:var(--card); border-bottom:1px solid var(--line);
  display:flex; align-items:center; gap:12px; padding:0 22px; z-index:10}
.crumb{display:flex; align-items:center; gap:8px; font-size:12.5px; color:var(--text-3)}
.crumb b{color:var(--text); font-weight:500}
.top .right{margin-left:auto; display:flex; align-items:center; gap:9px}
.search{display:flex; align-items:center; gap:7px; height:32px; width:258px;
  border:1px solid var(--line-2); border-radius:8px; padding:0 10px; color:var(--text-4); background:var(--card)}
.search:focus-within{border-color:#CBD2DA}
.search input{border:0; outline:0; background:none; font:inherit; color:var(--text); width:100%}
.search input::placeholder{color:var(--text-4)}
.icon-btn{width:32px;height:32px;border:1px solid var(--line-2); border-radius:8px; background:var(--card);
  display:grid;place-items:center; color:var(--text-2); cursor:pointer; position:relative}
.icon-btn:hover{background:#F7F8FA}
.icon-btn .pip{position:absolute; top:6px; right:7px; width:5px;height:5px;border-radius:50%;background:#E29A2D;border:1.5px solid #fff}
.av-top{width:28px;height:28px;border-radius:50%;background:#E9EBEF;display:grid;place-items:center;font-size:11px;color:var(--text-2)}

/* 页面容器 */
.host{position:relative; flex:1; min-height:0; background:var(--bg)}
.frame{position:absolute; inset:0; width:100%; height:100%; border:0; display:none; background:var(--bg)}
.frame.on{display:block}

:focus-visible{outline:2px solid #16181D; outline-offset:2px; border-radius:5px}

@media (max-width:900px){
  .app{flex-direction:column}
  .side{width:100%; flex:0 0 auto; height:auto; flex-direction:row; align-items:center; gap:4px;
    padding:7px 8px; border-right:0; border-bottom:1px solid var(--line); overflow-x:auto; overflow-y:hidden}
  .side::-webkit-scrollbar{height:0}
  .brand{padding:0 4px 0 0}
  .brand .name,.brand .collapse,.grp,.side-foot{display:none!important}
  .nav{flex-direction:row; gap:2px}
  .item{height:30px; padding:0 10px}
  .item .dot{display:none}
  .app.collapsed .side{width:100%; flex-basis:auto}
  .app.collapsed .item{font-size:12.5px; padding:0 10px; justify-content:flex-start}
  .main{height:auto; flex:1; min-height:0}
  .top{height:48px; flex:0 0 48px; padding:0 14px}
  .search{display:none}
}
</style>
</head>
<body>
<div class="app" id="app">

  <aside class="side">
    <div class="brand">
      <span class="mark">
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none"><rect x="1.5" y="2" width="11" height="2.2" fill="#fff"/><rect x="1.5" y="6" width="7.5" height="2.2" fill="#fff"/><rect x="1.5" y="10" width="9.5" height="2.2" fill="#fff"/></svg>
      </span>
      <span class="name">企业风险监测</span>
      <button class="collapse" id="sideToggle" aria-label="收起侧栏" title="收起侧栏">
        <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="1.5" y="2.5" width="13" height="11" rx="2"/><path d="M6 2.5v11"/></svg>
      </button>
    </div>

    <div class="grp">监测面板</div>
    <nav class="nav" id="nav">__NAV__
    </nav>

    <div class="side-foot">
      <div class="grp" style="padding-top:0">数据源</div>
      <div class="srcs">
        <div class="srcrow"><i class="sq d-ok"></i>信用中国<span>25/25</span></div>
        <div class="srcrow"><i class="sq d-part"></i>企查查<span>23/25</span></div>
      </div>
      <div class="demo-card">
        <div class="t"><i></i>演示快照</div>
        <p>2026-10-21　25 家企业　22 条记录<br>非实时抓取</p>
        <a href="javascript:void 0">查看数据来源</a>
      </div>
      <div class="user">
        <span class="av">值</span>
        <span>
          <div class="nm">值班账号</div>
          <div class="em">risk_monitor_demo</div>
        </span>
      </div>
    </div>
  </aside>

  <div class="main">
    <header class="top">
      <div class="crumb" id="crumb">
        <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="1.7" y="1.7" width="5" height="5" rx="1.4"/><rect x="9.3" y="1.7" width="5" height="5" rx="1.4"/><rect x="1.7" y="9.3" width="5" height="5" rx="1.4"/><rect x="9.3" y="9.3" width="5" height="5" rx="1.4"/></svg>
        <b id="crumbText">总览</b>
      </div>
      <div class="right">
        <label class="search" title="输入企业名后回车，自动跳到风险明细并检索">
          <svg width="14" height="14" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="7.2" cy="7.2" r="4.6"/><path d="m10.7 10.7 3 3"/></svg>
          <input id="gsearch" placeholder="搜索企业，回车跳转风险明细">
        </label>
        <a class="icon-btn" href="m.html" target="_blank" rel="noopener" aria-label="手机版预览" title="手机版预览">
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><rect x="4.4" y="1.4" width="7.2" height="13.2" rx="2"/><path d="M7 12.6h2"/></svg>
        </a>
        <button class="icon-btn" aria-label="帮助" title="原型说明">
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><circle cx="8" cy="8" r="6.3"/><path d="M6.3 6.2c.1-.9.8-1.5 1.7-1.5.9 0 1.7.6 1.7 1.5 0 1.2-1.7 1.3-1.7 2.6"/><circle cx="8" cy="11.3" r=".8" fill="currentColor" stroke="none"/></svg>
        </button>
        <button class="icon-btn" aria-label="通知">
          <span class="pip"></span>
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.4"><path d="M8 1.9a4.1 4.1 0 0 0-4.1 4.1c0 3.3-1.3 4.3-1.3 4.3h10.8s-1.3-1-1.3-4.3A4.1 4.1 0 0 0 8 1.9Z"/><path d="M6.6 12.7a1.5 1.5 0 0 0 2.8 0"/></svg>
        </button>
        <span class="av-top">值</span>
      </div>
    </header>

    <div class="host" id="host">
      <iframe class="frame" id="f-overview" title="总览" loading="eager"></iframe>
      <iframe class="frame" id="f-tasks" title="取数·任务"></iframe>
      <iframe class="frame" id="f-detail" title="风险明细"></iframe>
      <iframe class="frame" id="f-ai" title="AI 与邮件"></iframe>
      <iframe class="frame" id="f-config" title="配置"></iframe>
      <iframe class="frame" id="f-setting" title="系统设置"></iframe>
    </div>
  </div>
</div>

<script id="docsJson" type="application/json">__DOCS__</script>
<script>
(function(){
  /* 手机版入口透传分享码，否则会 403 */
  (function(){
    var ml = document.querySelector('a[href="m.html"]');
    if(ml && location.search) ml.href = 'm.html' + location.search;
  })();
  var DOCS = JSON.parse(document.getElementById('docsJson').textContent);
  var KEYS = ['overview','tasks','detail','ai','config','setting'];
  var TITLES = {overview:'总览', tasks:'取数·任务', detail:'风险明细', ai:'AI 与邮件', config:'配置', setting:'系统设置'};
  var CRUMB_ICO = {
    overview:'<rect x="1.7" y="1.7" width="5" height="5" rx="1.4"/><rect x="9.3" y="1.7" width="5" height="5" rx="1.4"/><rect x="1.7" y="9.3" width="5" height="5" rx="1.4"/><rect x="9.3" y="9.3" width="5" height="5" rx="1.4"/>',
    tasks:'<path d="M8 1.8v7.4M8 9.2 4.9 6.1M8 9.2l3.1-3.1M2.2 11.4v1.6c0 .7.6 1.2 1.2 1.2h9.2c.7 0 1.2-.6 1.2-1.2v-1.6"/>',
    detail:'<path d="M2.4 3.6h8.4M2.4 8h11.2M2.4 12.4h6.6"/><circle cx="13.1" cy="3.6" r="1.2"/>',
    ai:'<rect x="1.8" y="3.2" width="12.4" height="9.6" rx="1.8"/><path d="m2.4 4.4 5.6 3.9 5.6-3.9"/>',
    config:'<path d="M2.5 4.8h11M2.5 8h11M2.5 11.2h11"/><circle cx="6" cy="4.8" r="1.6" fill="#fff"/><circle cx="10.6" cy="8" r="1.6" fill="#fff"/><circle cx="5" cy="11.2" r="1.6" fill="#fff"/>',
    setting:'<circle cx="8" cy="8" r="2.3"/><path d="M8 1.6v1.7M8 12.7v1.7M1.6 8h1.7M12.7 8h1.7M3.5 3.5l1.2 1.2M11.3 11.3l1.2 1.2M12.5 3.5l-1.2 1.2M4.7 11.3l-1.2 1.2"/>'
  };
  var app = document.getElementById('app'),
      navItems = [].slice.call(document.querySelectorAll('.item[data-page]')),
      crumbIco = document.querySelector('#crumb svg'),
      crumbText = document.getElementById('crumbText'),
      loaded = {}, current = null;

  function load(key){
    if(loaded[key]) return;
    var f = document.getElementById('f-' + key);
    if(!f || !DOCS[key]) return;
    loaded[key] = true;
    f.srcdoc = DOCS[key];
  }

  function show(key){
    if(!TITLES[key]) key = 'overview';
    current = key;
    load(key);
    KEYS.forEach(function(k){
      var f = document.getElementById('f-' + k);
      if(f) f.classList.toggle('on', k === key);
    });
    navItems.forEach(function(it){ it.classList.toggle('on', it.dataset.page === key); });
    crumbText.textContent = TITLES[key];
    if(crumbIco) crumbIco.innerHTML = CRUMB_ICO[key];
    try{ localStorage.setItem('wbPage', key); }catch(e){}
    try{ if(history.replaceState) history.replaceState(null, '', '#' + key); }catch(e){}
    document.title = '企业风险监测 · ' + TITLES[key];
  }

  window.WB_NAV = function(key){ show(key); };

  navItems.forEach(function(it){
    it.addEventListener('click', function(){ show(it.dataset.page); });
    it.addEventListener('keydown', function(e){
      if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); show(it.dataset.page); }
    });
    it.setAttribute('tabindex', '0');
  });

  /* 侧栏收起 */
  var btn = document.getElementById('sideToggle');
  function setCol(on){
    app.classList.toggle('collapsed', on);
    var lbl = on ? '展开侧栏' : '收起侧栏';
    btn.setAttribute('aria-label', lbl); btn.title = lbl;
    try{ localStorage.setItem('sideCollapsed', on ? '1' : '0'); }catch(e){}
  }
  btn.addEventListener('click', function(){ setCol(!app.classList.contains('collapsed')); });

  /* 全局搜索 -> 风险明细 */
  var gs = document.getElementById('gsearch');
  gs.addEventListener('keydown', function(e){
    if(e.key !== 'Enter') return;
    var v = gs.value.trim();
    if(!v) return;
    show('detail');
    setTimeout(function(){
      try{
        var d = document.getElementById('f-detail').contentDocument;
        var q = d.getElementById('q');
        if(q){
          q.value = v;
          q.dispatchEvent(new Event('input', { bubbles: true }));
          var fl = d.querySelector('.filters');
          if(fl && fl.scrollIntoView) fl.scrollIntoView({ behavior:'smooth', block:'center' });
        }
      }catch(err){}
    }, 260);
  });

  /* 初始页：hash > 上次访问 > 总览；其余页面空闲加载 */
  var init = (location.hash || '').replace('#','');
  if(!TITLES[init]){
    try{ init = localStorage.getItem('wbPage') || 'overview'; }catch(e){ init = 'overview'; }
  }
  show(init);
  setTimeout(function(){
    KEYS.forEach(load);
  }, 400);

  try{ if(localStorage.getItem('sideCollapsed') === '1') setCol(true); }catch(e){}
})();
</script>
</body>
</html>
"""


def main():
    docs = {key: build_doc(key, fn, title) for key, fn, title in PAGES}
    payload = json.dumps(docs, ensure_ascii=False).replace("</", "<\\/")
    html = (PARENT
            .replace("__NAV__", NAV_ITEMS)
            .replace("__DOCS__", payload))
    OUT.write_text(html, encoding="utf-8")
    print("written:", OUT)
    print("size: %.1f KB" % (OUT.stat().st_size / 1024))
    for k, v in docs.items():
        print("  page %-9s %.1f KB" % (k, len(v.encode('utf-8')) / 1024))


if __name__ == "__main__":
    main()

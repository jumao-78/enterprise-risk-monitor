#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把 proto/ 下 6 个页面打包成单文件演示包 proto/index.html

做法：每个页面完整 HTML 放进 <template>，运行时赋给 iframe.srcdoc。
- 单文件、零外部依赖，双击或放到任意静态服务器都能打开
- 每个页面仍是独立文档，CSS / 全局变量 / id 互不污染
- 注入一段桥接脚本：页面内左侧导航点击改为 postMessage，由外壳切页
"""
import re, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent
PROTO = ROOT / "proto"

PAGES = [
    ("01-总览.html",    "总览"),
    ("03-取数任务.html", "取数 · 任务"),
    ("02-风险明细.html", "风险明细"),
    ("04-AI与邮件.html", "AI 与邮件"),
    ("05-配置.html",    "配置"),
    ("06-系统设置.html", "系统设置"),
]

# 侧栏导航 → 页序（用于页内跳转）
NAV_MAP = {name: i for i, (name, _) in enumerate(PAGES)}

BRIDGE = """
<script>
(function(){
  var MAP = %s;
  document.addEventListener('click', function(e){
    var a = e.target.closest && e.target.closest('.side .item');
    if(!a) return;
    var href = (a.getAttribute('href') || '').split('/').pop();
    if(Object.prototype.hasOwnProperty.call(MAP, href)){
      e.preventDefault();
      try{ parent.postMessage({go: MAP[href]}, '*'); }catch(err){}
    }
  }, true);
})();
</script>
""" % str(NAV_MAP).replace("'", '"')


def prep(html: str) -> str:
    """注入桥接脚本；去掉 <template> 里会提前闭合的字样"""
    if "</body>" in html:
        html = html.replace("</body>", BRIDGE + "</body>", 1)
    else:
        html += BRIDGE
    # 理论上不会有，但保险
    html = html.replace("</template", "<\\/template")
    return html


def main():
    chunks_tpl, chunks_js = [], []
    for i, (name, label) in enumerate(PAGES):
        p = PROTO / name
        html = prep(p.read_text(encoding="utf-8"))
        chunks_tpl.append(f'<template id="p{i}">{html}</template>')

    shell = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>企业风险监测 · 演示包</title>
<style>
  *{{box-sizing:border-box}}
  html,body{{height:100%;margin:0;background:#F5F6F8;
    font-family:"Inter","Segoe UI Variable Text","Segoe UI","Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;
    -webkit-font-smoothing:antialiased}}
  #fr{{width:100%;height:100%;border:0;display:block;background:#F5F6F8}}

  .dock{{position:fixed;left:50%;bottom:20px;transform:translateX(-50%);
    display:flex;align-items:center;gap:4px;padding:5px 7px;border-radius:20px;
    background:rgba(22,24,29,.9);backdrop-filter:blur(10px) saturate(1.2);
    box-shadow:0 12px 34px rgba(17,24,39,.3), 0 0 0 1px rgba(255,255,255,.06);
    color:#fff;z-index:9;user-select:none;transition:opacity .25s,transform .25s}}
  .dock:hover{{background:rgba(22,24,29,.96)}}

  .nav{{width:26px;height:26px;border:0;border-radius:50%;background:rgba(255,255,255,.1);
    color:#fff;font-size:14px;line-height:1;cursor:pointer;display:grid;place-items:center;padding:0;
    transition:background .15s}}
  .nav:hover{{background:rgba(255,255,255,.22)}}
  .nav:disabled{{opacity:.25;cursor:default;background:rgba(255,255,255,.06)}}

  .now{{display:flex;align-items:baseline;gap:7px;padding:0 8px;font-size:12px;white-space:nowrap}}
  .now .i{{font-variant-numeric:tabular-nums;color:rgba(255,255,255,.55);font-size:11px}}
  .now b{{font-weight:500;letter-spacing:.01em}}

  .sep{{width:1px;height:14px;background:rgba(255,255,255,.18);margin:0 4px}}
  .dots{{display:flex;align-items:center;gap:3px}}
  .dot{{width:6px;height:6px;border:0;border-radius:3px;background:rgba(255,255,255,.28);
    cursor:pointer;padding:0;transition:width .2s,background .2s}}
  .dot:hover{{background:rgba(255,255,255,.55)}}
  .dot[aria-current="true"]{{width:16px;background:#fff}}

  .tip{{position:fixed;left:50%;bottom:62px;transform:translateX(-50%);
    font-size:11.5px;color:#fff;background:rgba(22,24,29,.72);padding:5px 11px;border-radius:7px;
    opacity:0;transition:opacity .3s;pointer-events:none;z-index:9}}
  .tip.on{{opacity:1}}

  @media print{{.dock,.tip{{display:none}}#fr{{height:auto}}}}
</style>
</head>
<body>

<iframe id="fr" title="企业风险监测演示"></iframe>

<div class="dock" id="dock">
  <button class="nav" id="prev" aria-label="上一页">‹</button>
  <div class="now"><span class="i" id="num">1/6</span><b id="nm">总览</b></div>
  <button class="nav" id="next" aria-label="下一页">›</button>
  <span class="sep"></span>
  <div class="dots" id="dots"></div>
</div>

<div class="tip" id="tip">← → 翻页　·　1–6 直达</div>

{chr(10).join(chunks_tpl)}

<script>
(function(){{
  var NAMES = {[l for _, l in PAGES]!r};
  var fr = document.getElementById('fr');
  var dock = document.getElementById('dock');
  var num = document.getElementById('num');
  var nm = document.getElementById('nm');
  var dots = document.getElementById('dots');
  var cur = 0;

  NAMES.forEach(function(n, i){{
    var b = document.createElement('button');
    b.className = 'dot';
    b.setAttribute('data-i', i);
    b.title = n;
    b.setAttribute('aria-label', n);
    dots.appendChild(b);
  }});

  function render(){{
    var nodes = dots.querySelectorAll('.dot');
    for(var i = 0; i < nodes.length; i++){{
      nodes[i].setAttribute('aria-current', i === cur ? 'true' : 'false');
    }}
    num.textContent = (cur + 1) + '/' + NAMES.length;
    nm.textContent = NAMES[cur];
    document.getElementById('prev').disabled = cur === 0;
    document.getElementById('next').disabled = cur === NAMES.length - 1;
    document.title = '企业风险监测 · ' + NAMES[cur];
  }}

  function go(i){{
    if(i < 0 || i >= NAMES.length) return;
    cur = i;
    var tpl = document.getElementById('p' + i);
    fr.srcdoc = tpl.innerHTML;
    render();
    try{{ location.hash = 'p' + (i + 1); }}catch(e){{}}
  }}

  document.getElementById('prev').addEventListener('click', function(){{ go(cur - 1); }});
  document.getElementById('next').addEventListener('click', function(){{ go(cur + 1); }});
  dots.addEventListener('click', function(e){{
    var b = e.target.closest('.dot');
    if(b) go(+b.getAttribute('data-i'));
  }});

  /* 页内左侧导航 → 切页 */
  window.addEventListener('message', function(e){{
    var d = e.data;
    if(d && typeof d.go === 'number') go(d.go);
  }});

  /* 键盘：← → 翻页，1–6 直达，Home / End 跳首尾 */
  document.addEventListener('keydown', function(e){{
    if(e.target && /input|textarea|select/i.test(e.target.tagName)) return;
    if(e.key === 'ArrowLeft'){{ e.preventDefault(); go(cur - 1); }}
    else if(e.key === 'ArrowRight'){{ e.preventDefault(); go(cur + 1); }}
    else if(e.key === 'Home'){{ e.preventDefault(); go(0); }}
    else if(e.key === 'End'){{ e.preventDefault(); go(NAMES.length - 1); }}
    else if(/^[1-6]$/.test(e.key)){{ e.preventDefault(); go(+e.key - 1); }}
  }});

  var tip = document.getElementById('tip');
  tip.classList.add('on');
  setTimeout(function(){{ tip.classList.remove('on'); }}, 2800);

  /* 支持 #p3 直接定位 */
  var h = (location.hash || '').match(/^#p([1-6])$/);
  go(h ? (+h[1] - 1) : 0);
}})();
</script>
</body>
</html>
"""

    out = PROTO / "index.html"
    out.write_text(shell, encoding="utf-8")
    kb = out.stat().st_size / 1024
    print(f"built {out}  {kb:.0f} KB")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Collapses the Next.js static export into a single self-contained HTML file.
Run: python3 build-single.py
Output: recovery-demo.html
"""
import re
import os

ROOT = os.path.dirname(os.path.abspath(__file__))

def read(rel_href):
    # Strip leading ./ and query strings
    path = rel_href.lstrip('./')
    path = path.split('?')[0]
    return open(os.path.join(ROOT, path), encoding='utf-8').read()

# Read from the pristine Next.js export (index.orig.html). index.html itself
# is a BUILD OUTPUT (see bottom of file) so the host serves our enhanced,
# self-contained page at "/" -- reading from it would double-inject on rebuild.
with open(os.path.join(ROOT, 'index.orig.html'), encoding='utf-8') as f:
    html = f.read()

# 0. Patch stale pre-rendered HTML in index.html so it matches our JS changes.
#    React hydrates server-side HTML in place; if the HTML is stale the user
#    sees old UI until JS loads. We fix the most visible mismatches here.
#    - Remove the "Run engine" button (we merged it into Start simulation)
#    - Update soft/hard chip colours from legacy green/red to indigo/amber
html = re.sub(
    r'<button[^>]*class="[^"]*btn-primary[^"]*"[^>]*>'
    r'<svg[^>]*>.*?</svg>Run engine</button>',
    '', html, flags=re.DOTALL)
html = html.replace('color:#4cb782', 'color:#5e6ad2')
html = html.replace('background:#4cb782', 'background:#5e6ad2')
html = html.replace('color:#eb5757;', 'color:#f2994a;')
html = html.replace('background:#eb5757', 'background:#f2994a')

# 1. Remove <link rel="preload"> tags (not needed when everything is inline)
html = re.sub(r'<link rel="preload"[^>]*/>', '', html)

# 2. Inline CSS: <link rel="stylesheet" href="./..."> → <style>...</style>
def inline_css(m):
    href = m.group(1)
    if href.startswith('http'):
        return m.group(0)   # keep external (e.g. Google Fonts)
    css = read(href)
    return f'<style>{css}</style>'

html = re.sub(r'<link rel="stylesheet" href="([^"]+)"[^/]*/>', inline_css, html)

# 3. Inline JS: <script src="./..."></script> → <script>...</script>
# Escape </script> inside JS to avoid breaking the HTML parser
def safe_js(content):
    return content.replace('</script>', r'<\/script>')

def inline_js(m):
    attrs, src = m.group(1), m.group(2)
    if src.startswith('http'):
        return m.group(0)   # keep external CDN scripts
    content = safe_js(read(src))
    extra = ' nomodule' if 'noModule' in attrs or 'nomodule' in attrs else ''
    return f'<script{extra}>{content}</script>'

html = re.sub(r'<script([^>]*) src="(\./[^"]+)"[^>]*></script>', inline_js, html)

# Remove rr-booting opacity so our body overlay is always visible
html = html.replace('<style>html.rr-booting body{opacity:0}</style>', '', 1)
html = re.sub(r'<script>document\.documentElement\.classList\.add\("rr-booting"\);.*?</script>', '', html, flags=re.DOTALL)

# Widen section-to-section gap in Recovery Overview to 48px, keeping the
# header-to-first-section gap at the default 24px (space-y-6 only applies
# a uniform gap, so override the 3rd+ children specifically).
html = html.replace('</head>', '<style>main.space-y-6>div:nth-child(2){margin-top:32px!important}main.space-y-6>div:nth-child(n+3){margin-top:40px!important}</style></head>', 1)

ONBOARDING = """<script>
(function(){
  // Landing + onboarding respect the persisted theme (no toggle here yet).
  var _L = (function(){ try{ return localStorage.getItem('rrTheme')!=='dark'; }catch(e){ return true; } })();
  function OL(a){ return (_L?'rgba(15,23,42,':'rgba(255,255,255,')+a+')'; }
  var BRAND='#006DF9',
      BG    = _L?'#f6f7f9':'#08090a',
      CARD  = _L?'#ffffff':'#0f1117',
      PANEL = _L?'#ffffff':'#13181f',
      BORDER= _L?'rgba(15,23,42,0.10)':'rgba(255,255,255,0.08)',
      TEXT  = _L?'#1a1f36':'#f7f8f8',
      GRAY  = _L?'#5b6270':'#8a8f98',
      GRAY2 = _L?'#8b93a0':'#62666d';

  var SUN_SVG = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/></svg>';
  var MOON_SVG = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9z"/></svg>';
  window.rrApplyTheme = function(light){
    try{ localStorage.setItem('rrTheme', light?'light':'dark'); }catch(e){}
    document.documentElement.classList.toggle('rr-light', !!light);
    if(window.rrFixGradients){ window.rrFixGradients(); setTimeout(window.rrFixGradients, 60); }
    if(window.rrOnThemeChange) window.rrOnThemeChange(!!light);
  };

  // React's hydration resets <html>'s className, wiping the rr-light class the
  // boot script added. Re-enforce the persisted theme and keep it enforced.
  function rrEnsureTheme(){
    var want; try{ want = localStorage.getItem('rrTheme')!=='dark'; }catch(e){ want=true; }
    var has = document.documentElement.classList.contains('rr-light');
    if(want && !has) document.documentElement.classList.add('rr-light');
    else if(!want && has) document.documentElement.classList.remove('rr-light');
  }
  rrEnsureTheme();
  try{ new MutationObserver(rrEnsureTheme).observe(document.documentElement, {attributes:true, attributeFilter:['class']}); }catch(e){}

  function addExitBtn(){
    var profile = document.querySelector('.border-t.p-3.flex.items-center');
    if(!profile){ setTimeout(addExitBtn, 100); return; }
    var gear = profile.querySelector('.lucide-settings');
    if(gear) gear.remove();
    // Theme toggle
    if(!profile.querySelector('#rr-theme-btn')){
      var tbtn = document.createElement('button');
      tbtn.id = 'rr-theme-btn';
      tbtn.title = 'Toggle light / dark';
      tbtn.style.cssText = 'background:none;border:none;cursor:pointer;padding:4px;color:#8a8f98;display:flex;align-items:center;flex-shrink:0';
      var syncIcon = function(){ tbtn.innerHTML = document.documentElement.classList.contains('rr-light') ? MOON_SVG : SUN_SVG; };
      syncIcon();
      tbtn.onmouseenter = function(){ tbtn.style.color = document.documentElement.classList.contains('rr-light') ? '#1a1f36' : TEXT; };
      tbtn.onmouseleave = function(){ tbtn.style.color = '#8a8f98'; };
      tbtn.onclick = function(){ window.rrApplyTheme(!document.documentElement.classList.contains('rr-light')); syncIcon(); };
      profile.appendChild(tbtn);
    }
    if(profile.querySelector('#rr-exit-btn')) return;
    var exit = document.createElement('button');
    exit.id = 'rr-exit-btn';
    exit.title = 'Back to landing';
    exit.style.cssText = 'background:none;border:none;cursor:pointer;padding:4px;color:'+GRAY2+';display:flex;align-items:center;flex-shrink:0';
    exit.innerHTML = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>';
    exit.onmouseenter = function(){ exit.style.color=TEXT; };
    exit.onmouseleave = function(){ exit.style.color=GRAY2; };
    exit.onclick = function(){ localStorage.removeItem('rrSetupV2'); try{ sessionStorage.removeItem('rrInApp'); }catch(e){} location.reload(); };
    profile.appendChild(exit);
  }

  // React re-renders the sidebar profile bar on view switches (and once
  // more during its own hydration correction pass, which replaces the
  // <aside> element itself) wiping our injected buttons. Observing that
  // specific <aside> node is fragile -- once React swaps it out, our
  // observer keeps watching a detached node and never fires again.
  // Observe document.body instead: it's never replaced, so the observer
  // survives every re-render, including the hydration swap.
  function watchExitBtn(){
    new MutationObserver(function(){ addExitBtn(); }).observe(document.body, {childList:true, subtree:true});
    addExitBtn();
  }

  // Recovery Flow / stat cards paint depth via React inline gradients that end
  // in dark stops (#0d0e10 / #000 / #08090a). On a light surface those read as
  // harsh metallic sweeps. Neutralise the dark stops in light mode (storing the
  // original so dark can be restored); CSS can't reach gradient colour stops.
  // In light mode, React inline styles that were designed for a dark surface
  // read wrong on white: gradient dark stops become metallic sweeps, white-
  // overlay borders/backgrounds vanish, and the neutral gray/near-white inline
  // text colours are off. CSS can't reach inline styles, so sweep + rewrite
  // them here (storing originals so dark restores exactly).
  var _DARKSTOP = /rgba\((?:13,\s*14,\s*16|0,\s*0,\s*0|8,\s*9,\s*10),\s*([0-9.]+)\)/g;
  var _WHITEPILL = /border-radius:\s*999px/;
  // Neutral inline text colours (React serialises hex as rgb) -> light-mode.
  var _INK = [
    [/rgb\(247,\s*248,\s*248\)/g, '#1a1f36'],  // #f7f8f8 primary
    [/rgb\(226,\s*228,\s*233\)/g, '#1f2937'],  // #e2e4e9 bright label/title text
    [/rgb\(197,\s*200,\s*205\)/g, '#2f3646'],  // #c5c8cd
    [/rgb\(163,\s*168,\s*179\)/g, '#4b5563'],  // #a3a8b3
    [/rgb\(138,\s*143,\s*152\)/g, '#5b6270'],  // #8a8f98 secondary
    [/rgb\(98,\s*102,\s*109\)/g,  '#8b93a0']   // #62666d muted
  ];
  window.rrFixInline = function(){
    var light = document.documentElement.classList.contains('rr-light');
    document.querySelectorAll('[style*="gradient"], [style*="rgba(255, 255, 255"], [style*="rgb(247, 248, 248)"], [style*="rgb(226, 228, 233)"], [style*="rgb(197, 200, 205)"], [style*="rgb(163, 168, 179)"], [style*="rgb(138, 143, 152)"], [style*="rgb(98, 102, 109)"], [style*="rgb(8, 9, 10)"], [style*="rgb(10, 11, 13)"], [style*="rgb(13, 14, 16)"], [style*="rgb(15, 16, 18)"], [style*="rgb(19, 19, 22)"], [style*="transition: color"], [data-rr-obg]').forEach(function(e){
      var s = e.getAttribute('style') || '';
      if(light){
        if(!e.dataset.rrObg) e.dataset.rrObg = s;
        var fixed = s.replace(_DARKSTOP, function(_m, a){ return 'rgba(15,23,42,' + Math.min(0.05, parseFloat(a) * 0.1).toFixed(3) + ')'; });
        // Solid (no-alpha) dark app-bg / surface colours in inline styles
        // (gradients and flat backgrounds, e.g. the Recovery Simulation result
        // canvas and its invoice badge) -> light equivalents.
        fixed = fixed
          .replace(/rgb\(8,\s*9,\s*10\)/g, '#ffffff')     // #08090a app bg
          .replace(/rgb\(10,\s*11,\s*13\)/g, '#f6f7f9')   // #0a0b0d
          .replace(/rgb\(13,\s*14,\s*16\)/g, '#ffffff')   // #0d0e10 surface
          .replace(/rgb\(15,\s*16,\s*18\)/g, '#ffffff')   // #0f1012
          .replace(/rgb\(19,\s*19,\s*22\)/g, '#ffffff');  // #131316
        if(_WHITEPILL.test(fixed) && /background(?:-color)?:\s*rgba\(255,\s*255,\s*255/.test(fixed)){
          // toggle track: solid off-track + defined border + readable opacity
          fixed = fixed.replace(/(background(?:-color)?:\s*)rgba\(255,\s*255,\s*255,\s*[0-9.]+\)/g, '$1#e2e5ea')
                       .replace(/opacity:\s*0?\.\d+/g, 'opacity:0.85');
          if(!/(^|;)\s*border:/.test(fixed)) fixed += ';border:1px solid #c3c9d2';
        } else {
          // generic: white-overlay background -> faint slate; border -> visible slate
          fixed = fixed.replace(/(background(?:-color)?:\s*)rgba\(255,\s*255,\s*255,\s*([0-9.]+)\)/g,
                     function(_m, pre, a){ return pre + 'rgba(15,23,42,' + Math.min(0.04, parseFloat(a)).toFixed(3) + ')'; })
                   .replace(/(border(?:-[a-z]+)?(?:-color)?:\s*[0-9a-z ]*?)rgba\(255,\s*255,\s*255,\s*([0-9.]+)\)/g,
                     function(_m, pre, a){ return pre + 'rgba(15,23,42,' + Math.min(0.09, parseFloat(a) * 1.3 + 0.025).toFixed(3) + ')'; });
        }
        for(var i=0;i<_INK.length;i++) fixed = fixed.replace(_INK[i][0], _INK[i][1]);
        // Colour-transitioning labels (e.g. active booster titles) turn white on
        // their dark-mode active state -> invisible on white. Map their white
        // text to emphasised dark. Scoped to `transition: color` so white-on-
        // accent buttons are untouched.
        if(/transition:\s*color/.test(fixed)){
          fixed = fixed.replace(/(color:\s*)(#ffffff|#fff|rgb\(255,\s*255,\s*255\)|white)(?=\s*;|\s*$)/gi, '$1#1a1f36');
        }
        // Recovery Simulation's result-panel wrapper (identified by its own
        // light-converted gradient bg) sits directly under the filter section,
        // which already has its own border-bottom right above -- its border-top
        // is a redundant second line that stacks into a heavy double divider.
        if(fixed.indexOf('linear-gradient(#ffffff 0%, #f6f7f9 100%)') > -1){
          fixed = fixed.replace(/border-top:[^;]*;?/, '');
        }
        // Mono uppercase section labels (e.g. "RECOVERY TIMELINE", "RECOVERY
        // SIGNALS") use their own inline-style convention (ui-monospace,
        // uppercase, letter-spacing:2px) instead of the plain h3 convention
        // every other section header in the app uses (e.g. "Failure
        // Breakdown": text-[13px] font-semibold, dark, normal case, no
        // divider line). Replace the whole style outright to match exactly,
        // and hide the trailing divider these mono headers pair with.
        if(/letter-spacing:\s*2px/.test(fixed) && /ui-monospace/.test(fixed)){
          fixed = 'font-size:13px;font-weight:600;color:'+TEXT;
        }
        if(/^flex:\s*1[^;]*;\s*height:\s*1px;\s*background:/.test(fixed) && !/display:\s*none/.test(fixed)){
          fixed = fixed + ';display:none';
        }
        if(fixed !== s) e.setAttribute('style', fixed);
      } else if(e.dataset.rrObg){
        e.setAttribute('style', e.dataset.rrObg); delete e.dataset.rrObg;
      }
    });
    // Recovery ML status pill ("Idle" / "Scoring") uses a literal bg-black/30
    // -- a dark overlay meant for a dark canvas, reads as a heavy gray blob on
    // white. Idle is also just noise in the default state, so hide it there;
    // Scoring gets a light-friendly accent pill instead of black.
    document.querySelectorAll('[class*="bg-black/30"]').forEach(function(e){
      var isIdle = e.textContent.trim() === 'Idle';
      if(light){
        if(isIdle){ e.style.display = 'none'; return; }
        e.style.display = '';
        e.style.background = 'rgba(0,109,249,0.08)';
        e.style.borderColor = 'rgba(0,109,249,0.15)';
      } else {
        e.style.display = '';
        e.style.background = '';
        e.style.borderColor = '';
      }
    });
    // Recovery Simulation's native page header (h2 "Recovery Simulation" +
    // its subtitle <p>) uses a smaller type scale (14px/12px) than every
    // other tab's header (Recovery Overview, Live Flow both 20px/13px).
    // Normalise it to match so headers read consistently across tabs.
    (function(){
      var xres = document.evaluate("//h2[text()='Recovery Simulation']", document, null, XPathResult.ANY_TYPE, null);
      var h2 = xres.iterateNext();
      if(h2){
        h2.style.fontSize = '20px';
        h2.style.fontWeight = '600';
        var p = h2.parentElement && h2.parentElement.nextElementSibling;
        if(p && p.tagName === 'P') p.style.fontSize = '13px';
      }
    })();
    // Recovery Simulation: the "Invoice amount" picker is redundant (the
    // amount is fixed per the fail-invoice preview above it) -- hide its
    // whole labelled block. Found by its label text since it shares a
    // generic wrapper className with every other filter block.
    (function(){
      var xres = document.evaluate("//div[text()='Invoice amount']", document, null, XPathResult.ANY_TYPE, null);
      var label = xres.iterateNext();
      if(label && label.parentElement) label.parentElement.style.display = 'none';
    })();
    // Recovery Simulation: "Failure class" is two individually-bordered
    // buttons; every other tab group in the app (e.g. Live Flow's scenario
    // bar) uses a single pill container with a borderless active/inactive
    // tab inside it. Reapply that same treatment here so the two match.
    (function(){
      var btns = Array.prototype.filter.call(document.querySelectorAll('button'), function(b){
        var t = b.textContent.trim();
        return t === 'Soft Declines' || t === 'Hard Declines';
      });
      if(btns.length !== 2 || btns[0].parentElement !== btns[1].parentElement) return;
      var wrap = btns[0].parentElement;
      wrap.style.background = light ? 'rgba(15,23,42,0.04)' : 'rgba(255,255,255,0.04)';
      wrap.style.border = '1px solid ' + (light ? 'rgba(15,23,42,0.10)' : 'rgba(255,255,255,0.08)');
      wrap.style.borderRadius = '10px';
      wrap.style.padding = '3px';
      wrap.style.gap = '3px';
      btns.forEach(function(b){
        var active = /006DF9/.test(b.className);
        b.style.border = 'none';
        b.style.borderRadius = '7px';
        b.style.setProperty('height', '30px', 'important');
        b.style.setProperty('background', active ? (light ? '#ffffff' : 'rgba(255,255,255,0.08)') : 'transparent', 'important');
        b.style.setProperty('color', active ? '#006DF9' : (light ? '#5b6270' : '#8a8f98'), 'important');
        b.style.boxShadow = active ? (light ? '0 1px 2px rgba(15,23,42,.08)' : '0 1px 4px rgba(0,0,0,.4)') : 'none';
        b.style.fontWeight = active ? '600' : '400';
      });
    })();
    // SVG marker/tooltip fills use the `fill` attribute, not CSS -- e.g. the
    // Recovery Timeline's peak-marker circles (#0d1712, a dark card surface)
    // read as a harsh black blob on white.
    document.querySelectorAll('[fill="#0d1712"], [data-rr-ofill]').forEach(function(e){
      if(light){
        if(!e.dataset.rrOfill) e.dataset.rrOfill = e.getAttribute('fill');
        if(e.dataset.rrOfill === '#0d1712') e.setAttribute('fill', '#ffffff');
      } else if(e.dataset.rrOfill){
        e.setAttribute('fill', e.dataset.rrOfill); delete e.dataset.rrOfill;
      }
    });
    // SVG gridlines use the `stroke` attribute with a white-overlay value
    // designed for a dark chart bg (e.g. Recovery Timeline's horizontal
    // gridlines) -- invisible on white.
    document.querySelectorAll('[stroke^="rgba(255,255,255"], [data-rr-ostroke]').forEach(function(e){
      if(light){
        if(!e.dataset.rrOstroke) e.dataset.rrOstroke = e.getAttribute('stroke');
        var orig = e.dataset.rrOstroke;
        var m = orig && orig.match(/^rgba\(255,255,255,([0-9.]+)\)$/);
        if(m) e.setAttribute('stroke', 'rgba(15,23,42,' + Math.min(0.05, parseFloat(m[1]) * 0.8 + 0.012).toFixed(3) + ')');
      } else if(e.dataset.rrOstroke){
        e.setAttribute('stroke', e.dataset.rrOstroke); delete e.dataset.rrOstroke;
      }
    });
  };
  window.rrFixGradients = window.rrFixInline;  // back-compat alias
  function watchGradients(){
    var main = document.querySelector('main');
    if(!main){ setTimeout(watchGradients, 100); return; }
    var t; new MutationObserver(function(){ window.rrFixInline(); clearTimeout(t); t = setTimeout(window.rrFixInline, 80); })
      .observe(main, {childList:true, subtree:true, attributes:true, attributeFilter:['style','class']});
    window.rrFixInline();
  }

  // Show the landing page on every fresh URL entry. We only jump straight to
  // the dashboard when the user has entered the app within this tab session
  // (set on skip/complete/explore below), so reopening the URL always lands
  // on the hero first.
  var _inApp = (function(){ try{ return sessionStorage.getItem('rrInApp')==='1'; }catch(e){ return false; } })();
  if(localStorage.getItem('rrSetupV2') && _inApp){
    addExitBtn(); watchExitBtn(); watchGradients();
    setTimeout(window.rrFixGradients, 50);
    setTimeout(window.rrFixGradients, 200);
    setTimeout(window.rrFixGradients, 500);
    setTimeout(window.rrFixGradients, 1000);
    window.addEventListener('load', window.rrFixGradients);
    return;
  }

  /* ── helpers ── */
  function el(tag, css, html){ var e=document.createElement(tag); if(css)e.style.cssText=css; if(html)e.innerHTML=html; return e; }
  function btn(text, css, onclick){ var b=el('button', css); b.textContent=text; b.onclick=onclick; return b; }
  function genId(){ return Math.random().toString(36).substring(2,10); }

  /* ── overlay shell ── */
  var shell = el('div','position:fixed;top:0;left:0;width:100%;height:100%;z-index:2147483647;background:'+BG+';display:flex;flex-direction:column;font-family:Inter,system-ui,sans-serif;overflow:hidden;box-sizing:border-box');

  /* ── state ── */
  var stepIndex = -1; // -1 = landing
  var state = {
    payProc:'', payApiKey:'sk_live_demo_a1b2c3', paySvk:'whsec_demo_x7y8z9', payLabel:'', payWebhook:'', payConnected:false,
    billProc:'', billApiKey:'sk_live_bill_d4e5f6', billSvk:'whsec_bill_u1v2w3', billLabel:'', billWebhook:'', billConnected:false,
    retryAfter:'3', retryMax:'15'
  };

  var PAY_PROCS = [{id:'stripe',name:'Stripe'},{id:'adyen',name:'Adyen'},{id:'vantiv',name:'Worldpay Vantiv'},{id:'hyperswitch',name:'Hyperswitch'}];
  var BILL_PROCS = [{id:'chargebee',name:'Chargebee',group:'Billing Processors'},{id:'recurly',name:'Recurly',group:'Billing Processors'},{id:'stripe_billing',name:'Stripe Billing',group:'In house'},{id:'custom_billing',name:'Custom Billing',group:'In house'}];
  var STEPS = ['payment-select','payment-webhook','billing-select','billing-setup','billing-retries','review'];
  var GROUPS = [
    {key:'processor',label:'Connect Processor',icon:'inbox',steps:['payment-select','payment-webhook'],subs:['Select a Processor','Setup Webhook']},
    {key:'billing',label:'Add Billing Processor',icon:'puzzle',steps:['billing-select','billing-setup','billing-retries'],subs:['Select Billing platform','Billing Processor Set-up','Configure Retries']},
    {key:'review',label:'Review Details',icon:'flag',steps:['review'],subs:[]}
  ];

  var GROUP_ICONS = {
    inbox:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>',
    puzzle:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>',
    flag:'<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"/><line x1="4" y1="22" x2="4" y2="15"/></svg>',
    check:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>'
  };

  /* ── render ── */
  function render(){
    shell.innerHTML = '';
    if(stepIndex === -1){ renderLanding(); } else { renderWizard(); }
  }

  /* ── landing ── */
  function renderLanding(){
    // keyframes for the landing motion (injected once)
    if(!document.getElementById('rr-landing-anim')){
      var st = document.createElement('style'); st.id = 'rr-landing-anim';
      st.textContent = '@keyframes rrFadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}';
      document.head.appendChild(st);
    }
    shell.style.padding = '0';
    // soft gradient backdrop — no glow blobs, dot texture, or lines
    shell.style.background = _L
      ? 'radial-gradient(1100px 560px at 18% -12%, rgba(0,109,249,0.10), transparent 60%), radial-gradient(950px 520px at 84% 112%, rgba(51,153,255,0.12), transparent 60%), linear-gradient(180deg,#fbfcfe 0%,#eef3fb 100%)'
      : 'radial-gradient(1100px 560px at 18% -12%, rgba(0,109,249,0.20), transparent 60%), radial-gradient(950px 520px at 84% 112%, rgba(37,99,235,0.14), transparent 60%), linear-gradient(180deg,#08090a 0%,#0b1120 100%)';
    var wrap = el('div','position:relative;z-index:1;flex:1;display:flex;flex-direction:column;overflow:hidden;padding:24px;box-sizing:border-box');
    // margin:auto centres the column vertically when it fits, yet lets it
    // scroll (instead of clipping the top) on short viewports.
    var content = el('div','margin:auto;display:flex;flex-direction:column;align-items:center;width:100%');
    var logo = el('div','position:absolute;top:26px;right:32px;z-index:2;display:flex;align-items:center;color:'+TEXT+';animation:rrFadeUp .6s ease both');
    logo.innerHTML = '__RR_LOGO_SVG__';
    // hero illustration — custom composition instead of a baked PNG: the same
    // invoice enters failed on the left, passes through the Juspay retry
    // engine, and exits recovered on the right.
    var art = el('div','position:relative;width:100%;max-width:640px;margin:0 auto 34px;animation:rrFadeUp .6s ease .08s both');
    // the panel's washes mirror the story: a red tint under the failed card,
    // green under the recovered one, and a blue glow radiating from the engine
    var panel = el('div','position:relative;border-radius:22px;padding:120px 34px;box-sizing:border-box;background:'
      +(_L
        ? 'radial-gradient(300px 200px at 16% 66%, rgba(239,68,68,0.06), transparent 70%), radial-gradient(300px 200px at 86% 34%, rgba(34,197,94,0.08), transparent 70%), radial-gradient(380px 260px at 50% 42%, rgba(0,109,249,0.13), transparent 72%), linear-gradient(180deg,#e7f0fe,#d5e5fc)'
        : 'radial-gradient(300px 200px at 16% 66%, rgba(239,68,68,0.10), transparent 70%), radial-gradient(300px 200px at 86% 34%, rgba(34,197,94,0.10), transparent 70%), radial-gradient(380px 260px at 50% 42%, rgba(0,109,249,0.22), transparent 72%), linear-gradient(180deg,#0d1522,#101b2e)')
      +';border:1px solid '+(_L?'rgba(15,23,42,0.04)':OL(0.06))+';overflow:hidden');
    // ghost side sheets cropped by the panel edges, for depth
    panel.appendChild(el('div','position:absolute;left:-36px;top:50%;transform:translateY(-52%);width:92px;height:168px;border-radius:14px;background:'+(_L?'rgba(252,253,255,0.55)':OL(0.04))));
    panel.appendChild(el('div','position:absolute;right:-36px;top:50%;transform:translateY(-46%);width:92px;height:168px;border-radius:14px;background:'+(_L?'rgba(252,253,255,0.55)':OL(0.04))));
    // concentric halo rings radiating from the engine tile
    var rings = el('div','position:absolute;left:50%;top:calc(50% - 11px);width:0;height:0;pointer-events:none');
    [150,230,310].forEach(function(d,i){
      rings.appendChild(el('div','position:absolute;left:'+(-d/2)+'px;top:'+(-d/2)+'px;width:'+d+'px;height:'+d+'px;border-radius:50%;border:1px solid '+(_L?'rgba(0,109,249,'+(0.15-0.045*i).toFixed(3)+')':'rgba(96,165,250,'+(0.17-0.05*i).toFixed(3)+')')));
    });
    panel.appendChild(rings);
    // connecting arrows (drawn behind the cards)
    var AR = _L ? 'rgba(0,109,249,0.45)' : 'rgba(96,165,250,0.55)';
    var arrows = el('div','position:absolute;top:0;left:0;width:100%;height:100%;pointer-events:none');
    arrows.innerHTML =
      '<svg width="100%" height="100%" viewBox="0 0 640 224" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg">'
      +'<defs><marker id="rr-arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="'+AR+'"/></marker></defs>'
      +'<path d="M218 138 C 246 138, 240 104, 264 104" fill="none" stroke="'+AR+'" stroke-width="2" marker-end="url(#rr-arr)"/>'
      +'<path d="M376 104 C 402 104, 396 84, 420 84" fill="none" stroke="'+AR+'" stroke-width="2" marker-end="url(#rr-arr)"/>'
      +'</svg>';
    panel.appendChild(arrows);
    // invoice cards — same invoice, before and after the engine
    var hcCss = 'width:182px;box-sizing:border-box;background:'+(_L?'#ffffff':'#131a26')+';border:1px solid '+(_L?'rgba(15,23,42,0.06)':OL(0.08))+';border-radius:13px;padding:13px 14px;box-shadow:0 12px 28px '+(_L?'rgba(37,99,235,0.14)':'rgba(0,0,0,0.4)')+';text-align:left;position:relative;';
    var lc = el('div', hcCss+'transform:translateY(20px)');
    lc.innerHTML =
      '<div style="display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:8px"><span style="font-size:10.5px;font-weight:600;color:'+GRAY+'">INV-2041 · Stripe</span><span style="font-size:9.5px;font-weight:700;color:#ef4444;background:rgba(239,68,68,0.10);border-radius:999px;padding:2px 8px">Failed</span></div>'
      +'<div style="font-size:16px;font-weight:700;letter-spacing:-0.01em;color:'+TEXT+'">$197.00</div>'
      +'<div style="font-size:9.8px;color:'+GRAY2+';margin-top:3px">Insufficient funds · Visa ··4242</div>';
    var eng = el('div','display:flex;flex-direction:column;align-items:center;gap:10px;flex-shrink:0;position:relative');
    var tile = el('div','display:flex;align-items:center;justify-content:center;width:104px;height:104px;border-radius:26px;background:'+(_L?'#ffffff':'#0f1826')+';border:1px solid '+(_L?'rgba(15,23,42,0.05)':OL(0.08))+';box-shadow:0 18px 40px '+(_L?'rgba(37,99,235,0.18)':'rgba(0,0,0,0.5)')+', 0 0 0 10px '+(_L?'rgba(252,253,255,0.4)':OL(0.03)));
    tile.innerHTML = '__RR_MARK_SVG__';
    var engLbl = el('div','font-size:9.5px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:'+(_L?'#7186a3':GRAY2));
    engLbl.textContent = 'Smart retry engine';
    eng.appendChild(tile); eng.appendChild(engLbl);
    var rc = el('div', hcCss+'transform:translateY(-18px)');
    rc.innerHTML =
      '<div style="display:flex;align-items:center;justify-content:space-between;gap:6px;margin-bottom:8px"><span style="font-size:10.5px;font-weight:600;color:'+GRAY+';white-space:nowrap">INV-2041 · Stripe</span><span style="font-size:9.5px;font-weight:700;color:#16a34a;background:rgba(34,197,94,0.12);border-radius:999px;padding:2px 7px;white-space:nowrap;flex-shrink:0">Recovered</span></div>'
      +'<div style="font-size:16px;font-weight:700;letter-spacing:-0.01em;color:'+TEXT+'">$197.00</div>'
      +'<div style="font-size:9.8px;color:'+GRAY2+';margin-top:3px">Paid · retry #2 · Visa ··4242</div>';
    var heroRow = el('div','position:relative;display:flex;align-items:center;justify-content:space-between;gap:18px');
    heroRow.appendChild(lc); heroRow.appendChild(eng); heroRow.appendChild(rc);
    panel.appendChild(heroRow);
    art.appendChild(panel);
    // header + sub-header sit below the illustration, on a wider text column
    var h1 = el('h1','font-size:40px;font-weight:700;color:'+TEXT+';letter-spacing:-0.03em;line-height:1.15;margin:0 0 30px;text-align:center');
    h1.innerHTML = 'Recover failed payments with <span style="background:linear-gradient(90deg,'+BRAND+',#33A0FF);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent">intelligent retries</span>';
    var cta = btn('Try the live demo →','padding:14px 36px;border-radius:10px;border:none;background:'+BRAND+';color:#fff;font-size:15px;font-weight:600;cursor:pointer;font-family:inherit;box-shadow:0 8px 20px rgba(0,109,249,0.25);transition:transform .15s ease,box-shadow .15s ease',
      function(){ stepIndex=0; render(); });
    cta.onmouseenter = function(){ cta.style.transform='translateY(-1px)'; cta.style.boxShadow='0 12px 28px rgba(0,109,249,0.35)'; };
    cta.onmouseleave = function(){ cta.style.transform=''; cta.style.boxShadow='0 8px 20px rgba(0,109,249,0.25)'; };
    var eyebrow = el('div','font-size:11px;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:'+GRAY2+';margin-bottom:14px');
    eyebrow.textContent = 'Revenue Recovery';
    var inner = el('div','display:flex;flex-direction:column;align-items:center;text-align:center;max-width:620px;animation:rrFadeUp .6s ease .16s both');
    inner.appendChild(eyebrow); inner.appendChild(h1); inner.appendChild(cta);
    content.appendChild(art); content.appendChild(inner);
    wrap.appendChild(content);
    shell.appendChild(wrap);
    shell.appendChild(logo);
  }

  /* ── wizard ── */
  function renderWizard(){
    // card wrapper — inset from edges on all sides (reset the landing gradient)
    shell.style.background = BG;
    shell.style.padding = '32px';
    var card = el('div','display:flex;flex-direction:column;width:100%;height:100%;border-radius:16px;border:1px solid '+BORDER+';overflow:hidden;box-sizing:border-box');

    // top bar — split bg: left=dark (stepper), right=lighter (content)
    var topbar = el('div','display:flex;align-items:stretch;flex-shrink:0;border-bottom:1px solid '+BORDER);
    var topLeft = el('div','display:flex;align-items:center;gap:12px;padding:24px 32px 20px;width:280px;flex-shrink:0;background:'+(_L?'#ffffff':BG)+';box-sizing:border-box');
    var backBtn = btn('','display:flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:8px;border:none;background:none;color:'+TEXT+';cursor:pointer',
      function(){ stepIndex > 0 ? (stepIndex--, render()) : (stepIndex=-1, render()); });
    backBtn.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>';
    var title = el('span','font-size:16px;font-weight:700;color:'+TEXT);
    title.textContent = 'Revenue Recovery';
    topLeft.appendChild(backBtn); topLeft.appendChild(title);
    var topRight = el('div','flex:1;background:#13181f');
    topbar.appendChild(topLeft); topbar.appendChild(topRight);

    // body
    var body = el('div','display:flex;flex:1;min-height:0;');

    // stepper panel (dark) — followed by a separator and a "go with default
    // setup" action so it reads as part of the setup flow, not a stray link
    // floating in the header.
    var stepperPanel = el('div','width:280px;flex-shrink:0;padding:24px 32px 32px;background:'+(_L?'#ffffff':BG)+';display:flex;flex-direction:column');
    renderStepper(stepperPanel);
    var skipSep = el('div','height:1px;background:'+BORDER+';margin:28px 0 20px');
    var skipBg = _L ? CARD : 'rgba(255,255,255,0.035)';
    var skipBgHover = _L ? '#f4f6f9' : 'rgba(255,255,255,0.07)';
    var skipBtn = document.createElement('button');
    skipBtn.style.cssText = 'display:flex;align-items:center;gap:10px;width:100%;padding:11px 12px;border-radius:11px;border:1px solid '+BORDER+';background:'+skipBg+';cursor:pointer;font-family:inherit;text-align:left;box-sizing:border-box;transition:background .15s ease;box-shadow:'+(_L?'0 1px 2px rgba(2,6,23,0.05)':'none');
    skipBtn.innerHTML =
      '<span style="display:flex;align-items:center;justify-content:center;width:28px;height:28px;border-radius:999px;background:rgba(0,109,249,0.10);color:'+BRAND+';flex-shrink:0">'
      +'<svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" stroke="none"><path d="M2.5 5.6v12.8c0 .8.9 1.3 1.6.9l9.2-6.4c.6-.4.6-1.4 0-1.8L4.1 4.7c-.7-.4-1.6.1-1.6.9z"/><path d="M12.5 5.6v12.8c0 .8.9 1.3 1.6.9l9.2-6.4c.6-.4.6-1.4 0-1.8l-9.2-6.4c-.7-.4-1.6.1-1.6.9z"/></svg>'
      +'</span>'
      +'<span style="flex:1;font-size:12.5px;font-weight:600;color:'+TEXT+';white-space:nowrap">Go with default setup</span>'
      +'<span style="color:'+GRAY2+';flex-shrink:0;display:flex"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg></span>';
    skipBtn.onclick = function(){ openDefaultSetupModal(); };
    skipBtn.onmouseenter = function(){ skipBtn.style.background = skipBgHover; };
    skipBtn.onmouseleave = function(){ skipBtn.style.background = skipBg; };
    stepperPanel.appendChild(skipSep); stepperPanel.appendChild(skipBtn);

    // content panel (lighter bg for depth)
    var contentPanel = el('div','flex:1;background:#13181f;border-left:1px solid '+BORDER+';padding:32px 40px;overflow-y:auto');
    renderStep(contentPanel);

    body.appendChild(stepperPanel); body.appendChild(contentPanel);
    card.appendChild(topbar); card.appendChild(body);
    shell.appendChild(card);
  }

  /* ── default-setup confirmation modal ── */
  function openDefaultSetupModal(){
    var defaults = [
      {label:'Payment processor', value:'Stripe'},
      {label:'Billing processor', value:'Chargebee'},
      {label:'Retry policy', value:'Retry after 3 days · up to 15 attempts'}
    ];
    var backdrop = el('div','position:fixed;inset:0;z-index:2147483647;background:rgba(8,9,10,0.55);display:flex;align-items:center;justify-content:center;padding:24px;box-sizing:border-box');
    backdrop.onclick = function(e){ if(e.target === backdrop) close(); };
    var box = el('div','width:100%;max-width:400px;background:'+CARD+';border:1px solid '+BORDER+';border-radius:14px;padding:28px;box-sizing:border-box;box-shadow:0 24px 60px rgba(0,0,0,0.35)');
    box.onclick = function(e){ e.stopPropagation(); };

    var h = el('h2','font-size:17px;font-weight:700;color:'+TEXT+';margin:0 0 6px');
    h.textContent = 'Use default setup';
    var sub = el('p','font-size:13px;color:'+GRAY+';line-height:1.55;margin:0 0 20px');
    sub.textContent = "We'll configure the demo with these defaults. You can change any of this later from settings.";
    box.appendChild(h); box.appendChild(sub);

    var list = el('div','border:1px solid '+BORDER+';border-radius:10px;overflow:hidden;margin-bottom:22px');
    defaults.forEach(function(d, i){
      var row = el('div','display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 14px'+(i?';border-top:1px solid '+BORDER:''));
      var l = el('span','font-size:12.5px;color:'+GRAY);
      l.textContent = d.label;
      var v = el('span','font-size:12.5px;font-weight:600;color:'+TEXT+';text-align:right');
      v.textContent = d.value;
      row.appendChild(l); row.appendChild(v);
      list.appendChild(row);
    });
    box.appendChild(list);

    var actions = el('div','display:flex;align-items:center;gap:10px');
    var cancelBtn = btn('Cancel','flex:1;padding:11px 16px;border-radius:9px;border:1px solid '+BORDER+';background:none;color:'+TEXT+';font-size:13.5px;font-weight:600;cursor:pointer;font-family:inherit',
      function(){ close(); });
    var confirmBtn = btn('Continue to demo →','flex:1;padding:11px 16px;border-radius:9px;border:none;background:'+BRAND+';color:#fff;font-size:13.5px;font-weight:600;cursor:pointer;font-family:inherit',
      function(){
        localStorage.setItem('rrSetupV2','1');
        try{ sessionStorage.setItem('rrInApp','1'); }catch(e){}
        try{ localStorage.setItem('rrView','overview'); localStorage.removeItem('rrActiveTab'); }catch(e){}
        location.reload();
      });
    actions.appendChild(cancelBtn); actions.appendChild(confirmBtn);
    box.appendChild(actions);

    function close(){ backdrop.remove(); document.removeEventListener('keydown', onKey); }
    function onKey(e){ if(e.key === 'Escape') close(); }
    document.addEventListener('keydown', onKey);

    backdrop.appendChild(box);
    document.body.appendChild(backdrop);
  }

  function renderStepper(container){
    var currentKey = STEPS[stepIndex];
    GROUPS.forEach(function(group, gi){
      var lastIdx = Math.max.apply(null, group.steps.map(function(s){ return STEPS.indexOf(s); }));
      var isActive = group.steps.indexOf(currentKey) !== -1;
      var isDone = lastIdx < stepIndex;
      var isFirst = gi === 0;

      // group row
      var row = el('div','display:flex;align-items:stretch;cursor:'+(isDone?'pointer':'default'));
      if(isDone) row.onclick = function(){ stepIndex = STEPS.indexOf(group.steps[0]); render(); };

      var rail = el('div','width:46px;display:flex;align-items:center;justify-content:center;flex-shrink:0;position:relative');
      if(!isFirst){
        var lineTop = el('span','position:absolute;left:50%;width:1px;margin-left:-0.5px;background:'+BORDER+';top:0;height:50%');
        rail.appendChild(lineTop);
      }
      // no trailing line after the last group — it would dangle below the icon
      if(gi < GROUPS.length-1 || (isActive && group.subs.length)){
        var lineBot = el('span','position:absolute;left:50%;width:1px;margin-left:-0.5px;background:'+BORDER+';bottom:0;height:50%');
        rail.appendChild(lineBot);
      }

      var dot = el('span','display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:999px;border:1.5px solid '+BORDER+';background:'+CARD+';color:'+(isActive?GRAY:GRAY2)+';position:relative;z-index:1;flex-shrink:0');
      dot.innerHTML = isDone ? GROUP_ICONS.check : GROUP_ICONS[group.icon];
      if(isDone) dot.style.color = BRAND;
      rail.appendChild(dot);

      var info = el('div','display:flex;align-items:center;flex:1;padding-left:14px;min-height:64px');
      var label = el('span','font-size:13.5px;font-weight:600;color:'+(isActive||isDone?TEXT:GRAY2)+';flex:1');
      label.textContent = group.label;
      info.appendChild(label);
      if(group.subs.length){
        var chevron = el('span','color:'+GRAY2);
        chevron.innerHTML = isActive
          ? '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="18 15 12 9 6 15"/></svg>'
          : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
        info.appendChild(chevron);
      }
      row.appendChild(rail); row.appendChild(info);
      container.appendChild(row);

      // substeps if active
      if(isActive && group.subs.length){
        group.steps.forEach(function(stepKey, si){
          var idx = STEPS.indexOf(stepKey);
          var isSubActive = idx === stepIndex;
          var isSubDone = idx < stepIndex;
          var subRow = el('div','display:flex;align-items:stretch;cursor:'+(isSubDone?'pointer':'default'));
          if(isSubDone) subRow.onclick = function(){ stepIndex=idx; render(); };

          var subRail = el('div','width:46px;display:flex;align-items:center;justify-content:center;flex-shrink:0;position:relative');
          var st = el('span','position:absolute;left:50%;width:1px;margin-left:-0.5px;background:'+BORDER+';top:0;height:50%');
          subRail.appendChild(st);
          if(!(gi === GROUPS.length-1 && si === group.steps.length-1)){
            var sb = el('span','position:absolute;left:50%;width:1px;margin-left:-0.5px;background:'+BORDER+';bottom:0;height:50%');
            subRail.appendChild(sb);
          }

          var subDot;
          if(isSubActive){
            subDot = el('span','display:flex;align-items:center;justify-content:center;width:20px;height:20px;border-radius:999px;background:rgba(0,109,249,0.15);position:relative;z-index:1;flex-shrink:0');
            subDot.innerHTML = '<span style="width:10px;height:10px;border-radius:999px;background:'+BRAND+';display:block"></span>';
          } else if(isSubDone){
            subDot = el('span','width:11px;height:11px;border-radius:999px;background:'+BORDER+';position:relative;z-index:1;flex-shrink:0;display:block');
          } else {
            subDot = el('span','width:13px;height:13px;border-radius:999px;background:'+CARD+';border:1.5px solid '+BORDER+';position:relative;z-index:1;flex-shrink:0;display:block');
          }
          subRail.appendChild(subDot);

          var subInfo = el('div','display:flex;align-items:center;flex:1;padding-left:14px;min-height:40px');
          var subLabel = el('span','font-size:11.5px;font-weight:'+(isSubActive?600:500)+';color:'+(isSubActive?BRAND:GRAY2));
          subLabel.textContent = group.subs[si];
          subInfo.appendChild(subLabel);
          subRow.appendChild(subRail); subRow.appendChild(subInfo);
          container.appendChild(subRow);
        });
      }
    });
  }

  function renderStep(outerContainer){
    outerContainer.innerHTML = '';
    var container = el('div','max-width:440px;width:100%');
    outerContainer.appendChild(container);
    var step = STEPS[stepIndex];

    function header(title, sub){
      var h = el('div','margin-bottom:24px');
      var t = el('h2','font-size:20px;font-weight:700;color:'+TEXT+';letter-spacing:-0.01em;margin:0 0 6px');
      t.textContent = title;
      var s = el('p','font-size:13.5px;color:'+GRAY+';margin:0');
      s.textContent = sub;
      h.appendChild(t); h.appendChild(s); return h;
    }

    function primaryBtn(text, disabled, onclick){
      var b = el('button','width:100%;padding:12px 18px;border-radius:10px;border:none;font-size:13.5px;font-weight:600;color:#fff;cursor:'+(disabled?'not-allowed':'pointer')+';background:'+(disabled?'rgba(0,109,249,0.4)':BRAND)+';font-family:inherit;transition:background 0.15s');
      b.textContent = text;
      b.disabled = disabled;
      b.onclick = onclick;
      return b;
    }

    function inputEl(val, placeholder, type, onchange){
      var i = el('input','width:100%;padding:10px 12px;background:'+CARD+';border:1px solid '+BORDER+';border-radius:9px;font-size:13px;color:'+TEXT+';outline:none;font-family:inherit;box-sizing:border-box');
      i.value = val; i.placeholder = placeholder; i.type = type||'text';
      i.onfocus = function(){ i.style.borderColor=BRAND; i.style.boxShadow='0 0 0 3px rgba(0,109,249,0.15)'; };
      i.onblur = function(){ i.style.borderColor='rgba(255,255,255,0.08)'; i.style.boxShadow='none'; };
      i.oninput = function(){ onchange(i.value); };
      return i;
    }

    function field(label, val, placeholder, type, onchange){
      var wrap = el('div','margin-bottom:16px');
      var lbl = el('label','display:block;font-size:12.5px;font-weight:600;color:'+TEXT+';margin-bottom:6px');
      lbl.innerHTML = label + ' <span style="color:#e11d48">*</span>';
      wrap.appendChild(lbl); wrap.appendChild(inputEl(val, placeholder, type, onchange));
      return wrap;
    }

    function fieldWithHint(label, val, placeholder, hint, onchange){
      var wrap = el('div','margin-bottom:16px');
      var lbl = el('label','display:block;font-size:12.5px;font-weight:600;color:'+TEXT+';margin-bottom:6px');
      lbl.innerHTML = label + ' <span style="color:#e11d48">*</span>';
      var row = el('div','position:relative');
      var inp = inputEl(val, placeholder, 'text', onchange);
      inp.style.paddingRight = '80px';
      var suf = el('span','position:absolute;right:12px;top:50%;transform:translateY(-50%);font-size:12px;color:'+GRAY2+';pointer-events:none');
      suf.textContent = hint;
      row.appendChild(inp); row.appendChild(suf);
      wrap.appendChild(lbl); wrap.appendChild(row);
      var note = el('p','font-size:11.5px;color:'+GRAY2+';margin:6px 0 0');
      note.textContent = placeholder === '3' ? 'Number of failed attempts by the billing processor before retries triggered' : 'Maximum number of retry attempts allowed per invoice.';
      wrap.appendChild(note);
      return wrap;
    }

    function infoBox(text){
      var b = el('div','display:flex;align-items:flex-start;gap:10px;background:rgba(0,109,249,0.08);border:1px solid rgba(0,109,249,0.18);border-radius:11px;padding:13px 15px;margin-bottom:20px');
      b.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="'+BRAND+'" stroke-width="2" style="flex-shrink:0;margin-top:1px"><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></svg>';
      var t = el('p','font-size:12.5px;color:rgba(0,109,249,0.9);line-height:1.55;margin:0');
      t.textContent = text;
      b.appendChild(t); return b;
    }

    function webhookField(url){
      var wrap = el('div','background:'+CARD+';border:1px solid '+BORDER+';border-radius:10px;padding:12px 14px;display:flex;align-items:center;gap:10px;margin-bottom:16px');
      var urlText = el('span','font-size:12px;color:'+GRAY+';flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-family:monospace');
      urlText.textContent = url;
      var copyBtn = el('button','background:rgba(0,109,249,0.12);border:none;color:'+BRAND+';font-size:12px;font-weight:600;padding:5px 12px;border-radius:6px;cursor:pointer;flex-shrink:0;font-family:inherit');
      copyBtn.textContent = 'Copy';
      copyBtn.onclick = function(){ navigator.clipboard.writeText(url).catch(function(){}); copyBtn.textContent='Copied!'; setTimeout(function(){ copyBtn.textContent='Copy'; }, 1500); };
      wrap.appendChild(urlText); wrap.appendChild(copyBtn);
      return wrap;
    }

    function processorDropdown(list, selected, onSelect, grouped){
      var wrap = el('div','position:relative;margin-bottom:24px');
      var lbl = el('label','display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;color:'+TEXT+';margin-bottom:8px');
      lbl.innerHTML = (grouped ? 'Select Billing Processor' : 'Select a processor') + ' <span style="color:#e11d48">*</span>';
      wrap.appendChild(lbl);

      var trigger = el('button','display:flex;align-items:center;width:100%;padding:10px 12px;gap:10px;background:'+CARD+';border:1px solid '+BORDER+';border-radius:9px;cursor:pointer;font-family:inherit;text-align:left');
      var sel = list.find(function(c){ return c.id===selected; });
      trigger.innerHTML = (sel ? '<span style="width:22px;height:22px;border-radius:6px;background:rgba(0,109,249,0.15);color:'+BRAND+';font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0">'+sel.name[0]+'</span>' : '')
        +'<span style="flex:1;font-size:13px;color:'+(sel?TEXT:GRAY2)+'">'+(sel?sel.name:'Select Processor')+'</span>'
        +'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="'+GRAY2+'" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';

      var dropdown = el('div','position:fixed;background:#13181f;border:1px solid '+BORDER+';border-radius:11px;box-shadow:0 16px 32px -8px rgba(0,0,0,0.7);padding:4px 0;z-index:2147483646;display:none');

      function buildItems(){
        dropdown.innerHTML = '';
        if(grouped){
          var groups = [];
          list.forEach(function(c){ if(groups.indexOf(c.group)===-1) groups.push(c.group); });
          groups.forEach(function(g){
            var gl = el('div','padding:8px 12px 4px;font-size:11px;color:'+GRAY2+';font-weight:600');
            gl.textContent = g;
            dropdown.appendChild(gl);
            list.filter(function(c){ return c.group===g; }).forEach(function(c){ dropdown.appendChild(itemEl(c)); });
          });
        } else {
          list.forEach(function(c){ dropdown.appendChild(itemEl(c)); });
        }
      }

      function itemEl(c){
        var row = el('button','display:flex;align-items:center;width:100%;padding:9px 12px;gap:10px;background:none;border:none;cursor:pointer;font-family:inherit');
        row.style.textAlign = 'left';
        row.innerHTML = '<span style="width:22px;height:22px;border-radius:6px;background:rgba(0,109,249,0.15);color:'+BRAND+';font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0">'+c.name[0]+'</span>'
          +'<span style="flex:1;font-size:13px;color:'+TEXT+'">'+c.name+'</span>'
          +'<span style="width:16px;height:16px;border-radius:999px;border:'+(c.id===selected?'5px solid '+BRAND:'1.5px solid '+BORDER)+';flex-shrink:0;display:block"></span>';
        row.onmouseenter = function(){ row.style.background='rgba(255,255,255,0.04)'; };
        row.onmouseleave = function(){ row.style.background='none'; };
        row.onclick = function(){ onSelect(c.id); dropdown.style.display='none'; trigger.style.borderColor='rgba(255,255,255,0.08)'; buildTrigger(c); };
        return row;
      }

      function buildTrigger(c){
        trigger.innerHTML = (c ? '<span style="width:22px;height:22px;border-radius:6px;background:rgba(0,109,249,0.15);color:'+BRAND+';font-size:11px;font-weight:700;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0">'+c.name[0]+'</span>' : '')
          +'<span style="flex:1;font-size:13px;color:'+(c?TEXT:GRAY2)+'">'+(c?c.name:'Select Processor')+'</span>'
          +'<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="'+GRAY2+'" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
      }

      buildItems();
      trigger.onclick = function(){
        var open = dropdown.style.display==='block';
        if(!open){
          var r = trigger.getBoundingClientRect();
          dropdown.style.top = (r.bottom+6)+'px';
          dropdown.style.left = r.left+'px';
          dropdown.style.width = r.width+'px';
          buildItems();
        }
        dropdown.style.display = open ? 'none' : 'block';
        trigger.style.borderColor = open ? 'rgba(255,255,255,0.08)' : BRAND;
      };
      document.addEventListener('click', function handler(e){ if(!wrap.contains(e.target)&&!dropdown.contains(e.target)){ dropdown.style.display='none'; trigger.style.borderColor='rgba(255,255,255,0.08)'; document.removeEventListener('click',handler); } });

      wrap.appendChild(trigger);
      shell.appendChild(dropdown);
      return wrap;
    }

    /* ── step renders ── */
    if(step === 'payment-select'){
      container.appendChild(header('Connect your payment processor','Start by selecting one processor. You can add more later.'));
      container.appendChild(processorDropdown(PAY_PROCS, state.payProc, function(id){
        state.payProc = id;
        var p = PAY_PROCS.find(function(c){ return c.id===id; });
        if(p && !state.payLabel) state.payLabel = 'Production '+p.name;
        render();
      }));
      container.appendChild(primaryBtn('Continue', !state.payProc, function(){ stepIndex++; render(); }));
    }

    else if(step === 'payment-webhook'){
      container.appendChild(header('Connect your payment processor','Choose a processor to begin. You can connect others later.'));
      if(!state.payConnected){
        var h3 = el('h3','font-size:14px;font-weight:700;color:'+TEXT+';margin:0 0 16px');
        h3.textContent = 'Enter credentials to connect your processor';
        container.appendChild(h3);
        container.appendChild(field('API Key', state.payApiKey, 'sk_live_...', 'password', function(v){ state.payApiKey=v; }));
        container.appendChild(field('Source Verification Key', state.paySvk, 'whsec_...', 'password', function(v){ state.paySvk=v; }));
        container.appendChild(field('Connector label', state.payLabel, 'Production Stripe', 'text', function(v){ state.payLabel=v; }));
        container.appendChild(primaryBtn('Connect', !(state.payApiKey && state.paySvk && state.payLabel), function(){
          if(!state.payWebhook) state.payWebhook = 'https://rr.hyperswitch.io/webhooks/payments/'+genId();
          state.payConnected = true; render();
        }));
      } else {
        container.appendChild(webhookField(state.payWebhook));
        container.appendChild(infoBox('Configure this webhook URL in your payment processor\\'s dashboard to receive payment events (e.g. payment.failed, payment.succeeded).'));
        container.appendChild(primaryBtn('Continue', false, function(){ stepIndex++; render(); }));
      }
    }

    else if(step === 'billing-select'){
      container.appendChild(header('Choose your Billing Platform','Choose one processor for now. You can connect more processors later.'));
      container.appendChild(processorDropdown(BILL_PROCS, state.billProc, function(id){
        state.billProc = id;
        var p = BILL_PROCS.find(function(c){ return c.id===id; });
        if(p && !state.billLabel) state.billLabel = 'Production '+p.name;
        render();
      }, true));
      container.appendChild(primaryBtn('Next', !state.billProc, function(){ stepIndex++; render(); }));
    }

    else if(step === 'billing-setup'){
      var billName = (BILL_PROCS.find(function(c){ return c.id===state.billProc; })||{}).name||'Billing';
      container.appendChild(header('Choose your Billing Platform','Choose one processor for now. You can connect more processors later.'));
      if(!state.billConnected){
        var bh3 = el('h3','font-size:14px;font-weight:700;color:'+TEXT+';margin:0 0 16px');
        bh3.textContent = 'Enter credentials to connect your processor';
        container.appendChild(bh3);
        container.appendChild(field(billName+' API Key', state.billApiKey, 'sk_live_...', 'password', function(v){ state.billApiKey=v; }));
        container.appendChild(field('Source Verification Key', state.billSvk, 'whsec_...', 'password', function(v){ state.billSvk=v; }));
        container.appendChild(field('Connector Label', state.billLabel, 'Production Chargebee', 'text', function(v){ state.billLabel=v; }));
        container.appendChild(primaryBtn('Connect', !(state.billApiKey && state.billSvk && state.billLabel), function(){
          if(!state.billWebhook) state.billWebhook = 'https://rr.hyperswitch.io/webhooks/billing/'+genId();
          state.billConnected = true; render();
        }));
      } else {
        container.appendChild(webhookField(state.billWebhook));
        container.appendChild(infoBox('Configure this webhook URL in your billing processor to receive invoice events (e.g. invoice.generated, payment.triggered).'));
        container.appendChild(primaryBtn('Continue', false, function(){ stepIndex++; render(); }));
      }
    }

    else if(step === 'billing-retries'){
      container.appendChild(header('Configure Retry Logic','Set how and when you\\'d like retries to be attempted. You can modify this later.'));
      var rh3 = el('h3','font-size:14px;font-weight:700;color:'+TEXT+';margin:0 0 16px');
      rh3.textContent = 'Retry Settings';
      container.appendChild(rh3);
      container.appendChild(fieldWithHint('Start Retry After', state.retryAfter, '3', 'Attempts', function(v){ state.retryAfter=v; }));
      container.appendChild(fieldWithHint('Max Retry Attempts', state.retryMax, '15', 'Attempts', function(v){ state.retryMax=v; }));
      container.appendChild(primaryBtn('Next', false, function(){ stepIndex++; render(); }));
    }

    else if(step === 'review'){
      container.appendChild(header('Connection Successful','Explore all the Revenue Recovery metrics in the dashboard.'));
      var rows = [
        {icon:'<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>', label:'Billing platform connection successful'},
        {icon:'<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="22 12 16 12 14 15 10 15 8 12 2 12"/><path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/></svg>', label:'Payment processor connection successful'}
      ];
      rows.forEach(function(r){
        var row = el('div','display:flex;align-items:center;gap:14px;padding:16px 18px;border:1px solid '+BORDER+';border-radius:12px;background:'+CARD+';margin-bottom:12px');
        var icon = el('span','display:flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:9px;background:rgba(255,255,255,0.05);color:'+GRAY+';flex-shrink:0');
        icon.innerHTML = r.icon;
        var lbl2 = el('span','flex:1;font-size:13.5px;font-weight:500;color:'+TEXT);
        lbl2.textContent = r.label;
        var badge = el('span','display:flex;align-items:center;gap:6px;font-size:12.5px;font-weight:600;color:#34d399');
        badge.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg> Completed';
        row.appendChild(icon); row.appendChild(lbl2); row.appendChild(badge);
        container.appendChild(row);
      });
      container.appendChild(primaryBtn('Start exploring', false, function(){
        localStorage.setItem('rrSetupV2','1');
        try{ sessionStorage.setItem('rrInApp','1'); }catch(e){}
        try{ localStorage.setItem('rrView','overview'); localStorage.removeItem('rrActiveTab'); }catch(e){}
        location.reload();
      }));
    }
  }

  setTimeout(function(){ document.body.appendChild(shell); render(); }, 50);
})();
</script>"""
# Theme-aware onboarding: rewrite hardcoded dark colours in the body (past the
# theme-setup block) to the derived vars/helpers, same technique as Live Flow.
_onb_marker = "  GRAY2 = _L?'#8b93a0':'#62666d';\n"
_onb_head, _onb_body = ONBOARDING.split(_onb_marker, 1)
_onb_body = re.sub(r'rgba\(255,255,255,([0-9.]+)\)', r"'+OL(\1)+'", _onb_body)
_onb_body = _onb_body.replace('#13181f', "'+PANEL+'")
ONBOARDING = _onb_head + _onb_marker + _onb_body

# Inline the Juspay wordmark, made theme-aware: the "Juspay" text ships as
# fill="white" (built for a dark bg) so it would vanish on our light default —
# map it to currentColor (driven by the logo container's colour), and drop the
# secondary word's light-grey to a neutral that reads on both themes. Collapse
# whitespace so the markup is safe inside a single-quoted JS string.
_logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'juspay-logo.svg')
with open(_logo_path, 'r', encoding='utf-8') as _lf:
    _logo_svg = _lf.read()
_logo_svg = _logo_svg.replace('fill="white"', 'fill="currentColor"').replace('#CBCACF', '#8a8f98')
_logo_svg = re.sub(r'\s+', ' ', _logo_svg).strip()
# give it a consistent render height regardless of the file's intrinsic px size
_logo_svg = _logo_svg.replace('<svg width="228" height="25"', '<svg width="228" height="25" style="height:20px;width:auto;display:block"', 1)
ONBOARDING = ONBOARDING.replace('__RR_LOGO_SVG__', _logo_svg)

# Extract just the circular Juspay mark (the two blue paths) from the wordmark
# for the hero illustration's engine tile.
_mark_paths = re.findall(r'<path[^>]+fill="#(?:2B8EFF|0561E2)"[^>]*/>', _logo_svg)
_mark_svg = '<svg width="44" height="44" viewBox="0 0 22.8 22.8" fill="none" xmlns="http://www.w3.org/2000/svg">' + ''.join(_mark_paths) + '</svg>'
ONBOARDING = ONBOARDING.replace('__RR_MARK_SVG__', _mark_svg)

html = html.replace('</body>', ONBOARDING + '</body>', 1)


SIMULATION_VIEW = r"""<script>
(function(){
  var BG,CARD,BORDER,TEXT,GRAY,GRAY2,BRAND,STAGE,INVBG,TERMBG,CHIPBG,PILLBG;
  // Overlay helper: subtle white tints in dark, subtle dark-slate tints in light.
  function OL(a){ return (document.documentElement.classList.contains('rr-light')?'rgba(15,23,42,':'rgba(255,255,255,')+a+')'; }
  function rrLiveTheme(){
    var L=document.documentElement.classList.contains('rr-light');
    BG=L?'#f6f7f9':'#08090a'; CARD=L?'#ffffff':'#0f1117';
    BORDER=L?'rgba(15,23,42,0.10)':'rgba(255,255,255,0.08)';
    TEXT=L?'#1a1f36':'#f7f8f8'; GRAY=L?'#5b6270':'#8a8f98'; GRAY2=L?'#8b93a0':'#62666d';
    BRAND='#006DF9';
    STAGE=L?'#ffffff':'#0b0d11'; INVBG=L?'#ffffff':'#10131a';
    TERMBG=L?'#0e1524':'#05070b'; CHIPBG=L?'#ffffff':'#16191f'; PILLBG=L?'#eef0f2':'#0c0e13';
  }
  rrLiveTheme();

  var CHANNELS = {
    cBP: 'M290,415 L790,415',
    cBR: 'M430,527 C320,552 165,545 165,497',
    cPR: 'M915,495 C915,540 762,552 650,527'
  };
  var PORTS = [
    {cx:290,cy:415},{cx:790,cy:415},
    {cx:430,cy:527},{cx:165,cy:497},
    {cx:915,cy:495},{cx:650,cy:527}
  ];
  var INVOICE_ID = 'INV-2024-0001', INVOICE_AMOUNT = '$49.00';
  var BUDGET_TOTAL = 1000, RETRY_COST = 10;

  var TONE_COLORS = {
    idle:       {bg:'rgba(255,255,255,0.06)', color:'#8a8f98'},
    info:       {bg:'rgba(0,109,249,0.15)',   color:'#5b9bff'},
    listen:     {bg:'rgba(0,109,249,0.15)',   color:'#5b9bff'},
    processing: {bg:'rgba(0,109,249,0.15)',   color:'#5b9bff'},
    failed:     {bg:'rgba(239,68,68,0.15)',   color:'#ef4444'},
    success:    {bg:'rgba(16,185,129,0.15)',  color:'#10b981'},
    recovered:  {bg:'rgba(16,185,129,0.15)', color:'#10b981'},
    scheduled:  {bg:'rgba(245,158,11,0.15)', color:'#f59e0b'},
    captured:   {bg:'rgba(8,145,178,0.15)',  color:'#0891b2'},
    halted:     {bg:'rgba(239,68,68,0.15)',   color:'#ef4444'},
    classified: {bg:'rgba(245,158,11,0.15)', color:'#f59e0b'},
    switching:  {bg:'rgba(245,158,11,0.15)', color:'#f59e0b'},
    received:   {bg:'rgba(16,185,129,0.15)', color:'#10b981'},
    sent:       {bg:'rgba(0,109,249,0.15)',   color:'#5b9bff'},
    retrying:   {bg:'rgba(0,109,249,0.15)',   color:'#5b9bff'},
    partial:    {bg:'rgba(8,145,178,0.15)',   color:'#0891b2'},
    created:    {bg:'rgba(0,109,249,0.15)',   color:'#5b9bff'}
  };

  function getTone(t){ return TONE_COLORS[t] || TONE_COLORS.idle; }

  function formatTime(){
    var n=new Date();
    return [n.getHours(),n.getMinutes(),n.getSeconds()].map(function(x){return String(x).padStart(2,'0');}).join(':');
  }
  function futureDate(d){
    var dt=new Date(); dt.setDate(dt.getDate()+d);
    return dt.toLocaleDateString('en-US',{month:'short',day:'numeric'});
  }
  function el(tag,css,html){ var e=document.createElement(tag); if(css)e.style.cssText=css; if(html!==undefined)e.innerHTML=html; return e; }
  function statusPill(tone,text,small){
    var t=getTone(tone);
    var s=el('span','display:inline-block;font-weight:600;border-radius:999px;background:'+t.bg+';color:'+t.color+';white-space:nowrap;'+(small?'font-size:9.5px;padding:2px 8px':'font-size:11.5px;padding:5px 12px'));
    s.textContent=text; return s;
  }

  /* ── Simulation State ── */
  var state={
    phase:'idle', active:null,
    billStatus:'Idle', billTone:'idle',
    procStatus:'Idle', procTone:'idle',
    invoiceStatus:'No invoice', invoiceTone:'idle',
    external:[], internal:[],
    log:[], scenario:'soft_decline',
    cprMuted:true, escalated:false,
    declineType:null, errorCode:null, activeCardIndex:0,
    accountUpdated:false, expiredRevealed:false,
    retryHardDeclines:false, budgetBalance:BUDGET_TOTAL
  };
  var cancelFlag=false, retryHardFlag=false;

  /* ── DOM refs ── */
  var els={
    panel:null, stageWrap:null, stage:null, chip:null,
    paths:{cBP:null,cBR:null,cPR:null},
    billCard:null, procCard:null, extRetry:null, ledger:null,
    streamLog:null, streamHeader:null,
    startBtn:null, budgetEl:null, hardToggleEl:null, hardToggleKnob:null,
    scenarioBar:null, hardPanel:null
  };
  var paymentName='Stripe', billingName='Chargebee';

  function hidePanel(){
    if(els.panel) els.panel.style.display='none';
    cancelFlag=true;
  }

  function showPanel(){
    if(!els.panel) buildPanel();
    els.panel.style.display='flex';
  }

  /* ── Build Panel ── */
  function buildPanel(){
    // Cover the main content area (everything except sidebar)
    // Use position:fixed covering full viewport minus sidebar (~216px)
    var p = el('div','position:fixed;top:0;right:0;bottom:0;z-index:999;background:'+BG+';display:flex;flex-direction:column;font-family:Inter,system-ui,sans-serif;overflow-y:auto;padding:48px 24px 24px 40px;box-sizing:border-box');
    p.id = 'rr-sim3-panel';

    // Determine sidebar width dynamically
    var sidebar = document.querySelector('aside') || document.querySelector('[class*="sidebar"]') || document.querySelector('[class*="w-54"]');
    var sideW = sidebar ? sidebar.offsetWidth : 216;
    p.style.left = sideW + 'px';
    els.panel = p;

    // Content wrapper capped like dashboard main (max-w-[1400px])
    var inner = el('div','width:100%;max-width:1400px;display:flex;flex-direction:column;flex:none');
    els.panelInner = inner;

    // Header row
    var header = el('div','flex-shrink:0;padding:0 0 18px;display:flex;align-items:center;justify-content:space-between;gap:16px');

    var titleGroup = el('div');
    var title = el('div','font-size:20px;font-weight:600;color:'+TEXT+';letter-spacing:-0.01em');
    title.textContent = 'Live Flow';
    var subtitle = el('div','font-size:13px;color:'+GRAY+';margin-top:3px');
    subtitle.textContent = 'Watch a failed invoice travel from your billing engine to recovery, live.';
    titleGroup.appendChild(title); titleGroup.appendChild(subtitle);

    var resetBtn = el('button','');
    resetBtn.className = 'btn-secondary text-[13px] font-medium px-4 py-2 rounded-lg disabled:opacity-40 disabled:cursor-not-allowed';
    resetBtn.style.cssText = 'flex-shrink:0';
    resetBtn.textContent = 'Reset';
    resetBtn.disabled = true;
    resetBtn.onclick = function(){
      if(resetBtn.disabled) return;
      cancelFlag=true;          // stop any in-flight run before it can re-render stale state
      retryHardFlag=false;
      resetSimState('idle');
    };
    els.resetBtn = resetBtn;

    var startBtn = el('button','padding:10px 22px;border-radius:9px;border:none;background:'+BRAND+';color:#fff;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;flex-shrink:0;display:flex;align-items:center;gap:6px;box-shadow:0 2px 8px rgba(0,102,255,.3)');
    startBtn.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg><span>Start</span>';
    startBtn.onclick = function(){ if(state.phase!=='running') runSim(); };
    els.startBtn = startBtn;

    var btnGroup = el('div','display:flex;align-items:center;gap:10px;flex-shrink:0');
    btnGroup.appendChild(resetBtn); btnGroup.appendChild(startBtn);
    header.appendChild(titleGroup); header.appendChild(btnGroup);
    inner.appendChild(header);

    // Container card holding the whole flow (matches Recovery Simulation section)
    var containerCard = el('div','flex:none;height:calc(100vh - 140px);min-height:440px;display:flex;flex-direction:column;border:1px solid '+BORDER+';border-radius:12px;overflow:hidden;background:#0b0d11');

    // Control bar: scenario tabs + badges
    var ctrlBar = el('div','flex-shrink:0;display:flex;align-items:flex-end;justify-content:space-between;gap:8px;padding:14px 20px;border-bottom:1px solid '+BORDER+';overflow:hidden');

    var tabsGroup = el('div','min-width:0');
    var tabsLabel = el('div','font-size:10.5px;text-transform:uppercase;letter-spacing:0.05em;color:'+GRAY+';margin-bottom:6px');
    tabsLabel.textContent = 'Scenario';
    var tabsWrap = el('div','display:flex;align-items:center;gap:3px;background:rgba(255,255,255,0.04);border:1px solid '+BORDER+';border-radius:10px;padding:3px;min-width:0;overflow-x:auto');
    var scenarios=[
      {id:'soft_decline',label:'Soft Decline'},
      {id:'card_switching',label:'Card Switching'},
      {id:'account_update',label:'Account Update'},
      {id:'partial_auth',label:'Partial Auth'},
      {id:'hard_decline',label:'Hard Decline'}
    ];
    scenarios.forEach(function(sc){
      var tb = el('button','font-size:11.5px;height:30px;padding:0 12px;border-radius:7px;border:none;cursor:pointer;font-family:inherit;white-space:nowrap;display:inline-flex;align-items:center;justify-content:center;transition:background 0.15s,color 0.15s;flex-shrink:0');
      tb.textContent = sc.label;
      tb.dataset.scid = sc.id;
      tb.onclick = function(){
        if(state.phase==='running') return;
        state.scenario = sc.id;
        state.activeCardIndex = 0;
        state.accountUpdated = false;
        state.expiredRevealed = false;
        updateScenarioTabs();
        updateHardPanel();
        if(els.invoiceCard) renderInvoiceCard(els.invoiceCard);
        updateChannelGeometry();
      };
      tabsWrap.appendChild(tb);
    });
    els.scenarioBar = tabsWrap;

    // Hard decline toggle panel (hidden unless hard_decline)
    var hardPanel = el('div','display:none;align-items:center;gap:8px;padding:5px 10px;border-radius:8px');
    hardPanel.id = 'rr-hard-panel';
    els.hardPanel = hardPanel;

    var budgetEl = el('span','font-size:11.5px;font-weight:800;color:'+TEXT+';white-space:nowrap;letter-spacing:-0.01em');
    budgetEl.textContent = '$'+BUDGET_TOTAL.toLocaleString();
    els.budgetEl = budgetEl;

    var divider = el('div','width:1px;height:14px;background:rgba(253,186,116,0.4);flex-shrink:0');
    var hardLabel = el('span','font-size:11px;font-weight:600;color:#C2410C;white-space:nowrap');
    hardLabel.textContent = 'Retry Hard Declines';

    var toggleWrap = el('div','width:30px;height:16px;border-radius:8px;background:#374151;position:relative;cursor:pointer;transition:background 0.2s;flex-shrink:0');
    var knob = el('div','position:absolute;top:2px;left:2px;width:12px;height:12px;border-radius:6px;background:#fff;transition:left 0.18s;box-shadow:0 1px 3px rgba(0,0,0,.4)');
    toggleWrap.appendChild(knob);
    els.hardToggleEl = toggleWrap;
    els.hardToggleKnob = knob;
    toggleWrap.onclick = function(){
      if(state.phase!=='running' || state.declineType!=='hard') return;
      state.retryHardDeclines = !state.retryHardDeclines;
      retryHardFlag = state.retryHardDeclines;
      updateHardToggle();
    };

    hardPanel.appendChild(budgetEl); hardPanel.appendChild(divider);
    hardPanel.appendChild(hardLabel); hardPanel.appendChild(toggleWrap);
    els.hardPanel = hardPanel;

    // Badges
    var badgesGroup = el('div','min-width:0;flex-shrink:0');
    var badgesLabel = el('div','font-size:10.5px;text-transform:uppercase;letter-spacing:0.05em;color:'+GRAY+';margin-bottom:6px');
    badgesLabel.textContent = 'Integrations';
    var badgesWrap = el('div','display:flex;align-items:center;gap:8px;flex-shrink:0');
    [{label:'Payment',name:paymentName},{label:'Billing',name:billingName}].forEach(function(b){
      var badge = el('span','display:inline-flex;align-items:center;gap:4px;box-sizing:border-box;height:38px;background:rgba(255,255,255,0.05);border:1px solid '+BORDER+';border-radius:999px;padding:0 14px;font-size:10.5px;color:'+GRAY+';white-space:nowrap');
      badge.innerHTML = '<span>'+b.label+':</span><b style="color:'+TEXT+'">'+b.name+'</b><span style="color:#10b981">&#10003;</span>';
      badgesWrap.appendChild(badge);
    });
    badgesGroup.appendChild(badgesLabel); badgesGroup.appendChild(badgesWrap);

    var rightCtrl = el('div','display:flex;align-items:flex-end;gap:8px');
    rightCtrl.appendChild(hardPanel); rightCtrl.appendChild(badgesGroup);

    tabsGroup.appendChild(tabsLabel); tabsGroup.appendChild(tabsWrap);
    ctrlBar.appendChild(tabsGroup); ctrlBar.appendChild(rightCtrl);
    containerCard.appendChild(ctrlBar);

    // Body: stage (70%) + stream (30%)
    var body = el('div','flex:1;min-height:0;display:flex;overflow:hidden');

    // Stage
    var stageWrap = el('div','flex:1;min-width:0;min-height:0;position:relative;overflow:hidden;background:'+CARD+';background-image:radial-gradient(circle, rgba(255,255,255,0.06) 1.2px, transparent 1.2px);background-size:16px 16px');
    els.stageWrap = stageWrap;

    var stage = el('div','position:relative;width:1080px;height:770px;transform-origin:top left');
    els.stage = stage;

    // SVG channels
    var svgEl = document.createElementNS('http://www.w3.org/2000/svg','svg');
    svgEl.setAttribute('width','1080'); svgEl.setAttribute('height','770');
    svgEl.setAttribute('viewBox','0 0 1080 770');
    svgEl.style.cssText='position:absolute;inset:0;pointer-events:none';

    // Glow filter for lit channels
    var NS='http://www.w3.org/2000/svg';
    var defs=document.createElementNS(NS,'defs');
    defs.innerHTML='<filter id="rr-glow" x="-50%" y="-50%" width="200%" height="200%">'
      +'<feGaussianBlur stdDeviation="3.5"/></filter>';
    svgEl.appendChild(defs);

    els.basePaths={};
    els.glowPaths={};
    els.trackPaths={};
    Object.entries(CHANNELS).forEach(function(entry){
      var id=entry[0], d=entry[1];
      // Soft wide underlay track
      var track=document.createElementNS(NS,'path');
      track.setAttribute('d',d); track.setAttribute('fill','none');
      track.setAttribute('stroke','rgba(255,255,255,0.03)'); track.setAttribute('stroke-width','6');
      track.setAttribute('stroke-linecap','round');
      svgEl.appendChild(track);
      els.trackPaths[id]=track;

      // Base pipe
      var base=document.createElementNS(NS,'path');
      base.setAttribute('d',d); base.setAttribute('fill','none');
      base.setAttribute('stroke','rgba(255,255,255,0.14)'); base.setAttribute('stroke-width','1.5');
      base.setAttribute('stroke-linecap','round');
      base.style.transition='stroke 0.6s ease, opacity 0.6s ease, stroke-dasharray 0.6s ease';
      base.id='rr-base-'+id;
      svgEl.appendChild(base);
      els.basePaths[id]=base;

      // Glow layer — blurred wide stroke lit during transmission
      var glow=document.createElementNS(NS,'path');
      glow.setAttribute('d',d); glow.setAttribute('fill','none');
      glow.setAttribute('stroke','none'); glow.setAttribute('stroke-width','6');
      glow.setAttribute('stroke-linecap','round');
      glow.setAttribute('filter','url(#rr-glow)');
      glow.style.opacity='0';
      glow.style.transition='opacity 0.25s ease';
      svgEl.appendChild(glow);
      els.glowPaths[id]=glow;

      // Flow overlay — marching dots
      var flow=document.createElementNS(NS,'path');
      flow.setAttribute('d',d); flow.setAttribute('fill','none');
      flow.setAttribute('stroke','none'); flow.setAttribute('stroke-width','2.5');
      flow.setAttribute('stroke-linecap','round');
      flow.style.opacity='0';
      flow.id='rr-flow-'+id;
      svgEl.appendChild(flow);
      els.paths[id]=flow;
    });

    // Ports — ring + core, on an overlay SVG so knots render above the cards
    var portSvg=document.createElementNS(NS,'svg');
    portSvg.setAttribute('width','1080'); portSvg.setAttribute('height','770');
    portSvg.setAttribute('viewBox','0 0 1080 770');
    portSvg.style.cssText='position:absolute;inset:0;pointer-events:none;z-index:5';
    els.portEls=[];
    PORTS.forEach(function(pt){
      var ring=document.createElementNS(NS,'circle');
      ring.setAttribute('cx',pt.cx); ring.setAttribute('cy',pt.cy); ring.setAttribute('r','4.5');
      ring.setAttribute('fill',CARD);
      ring.setAttribute('stroke','rgba(255,255,255,0.28)');
      ring.setAttribute('stroke-width','1.2');
      portSvg.appendChild(ring);
      var core=document.createElementNS(NS,'circle');
      core.setAttribute('cx',pt.cx); core.setAttribute('cy',pt.cy); core.setAttribute('r','1.8');
      core.setAttribute('fill','rgba(255,255,255,0.45)');
      portSvg.appendChild(core);
      els.portEls.push({ring:ring,core:core});
    });
    els.portSvg=portSvg;
    // Context drop-line: invoice anchor feeds the flow (dashed, behind cards)
    var ctxLine=document.createElementNS(NS,'path');
    ctxLine.setAttribute('d','M540,297 L540,316');
    ctxLine.setAttribute('fill','none');
    ctxLine.setAttribute('stroke','rgba(255,255,255,0.16)');
    ctxLine.setAttribute('stroke-width','1.5');
    ctxLine.setAttribute('stroke-dasharray','2 5');
    ctxLine.setAttribute('stroke-linecap','round');
    svgEl.appendChild(ctxLine);
    els.ctxLine=ctxLine;

    stage.appendChild(svgEl);
    updateChannelMutes();

    // Territory labels — zone context above each card group (ref: role pills)
    [
      {x:40,  y:389, label:'Merchant side', color:'#9b72e4'},
      {x:790, y:389, label:'Card network',  color:'#22d3ee'},
      {x:390, y:560, label:'Hyperswitch',   color:'#5b9bff'}
    ].forEach(function(t){
      var tl=el('div','position:absolute;font-size:8.5px;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;padding:3px 9px;border-radius:5px;background:rgba(255,255,255,0.04);border:1px solid '+BORDER);
      tl.style.left=t.x+'px'; tl.style.top=t.y+'px'; tl.style.color=t.color;
      tl.textContent=t.label;
      stage.appendChild(tl);
    });

    // Chip
    var chip=el('div','position:absolute;top:0;left:0;display:flex;align-items:center;gap:5px;padding:4px 9px;background:#16191f;border:1px solid rgba(255,255,255,0.2);border-radius:999px;font-size:10px;font-weight:600;color:'+TEXT+';white-space:nowrap;opacity:0;pointer-events:none;transform:translate(-300px,-300px);z-index:9;box-shadow:0 8px 20px -6px rgba(0,0,0,0.6)');
    els.chip=chip; stage.appendChild(chip);

    // Component cards
    els.billCard = buildBillingCard();
    els.invoiceCard = buildInvoiceCard();
    els.procCard = buildProcCard();
    els.extRetry = buildExtRetryPanel();
    els.ledger = buildLedgerPanel();
    stage.appendChild(els.billCard);
    stage.appendChild(els.invoiceCard);
    stage.appendChild(els.procCard);
    stage.appendChild(els.extRetry);
    stage.appendChild(els.ledger);
    stage.appendChild(els.portSvg);

    stageWrap.appendChild(stage);
    body.appendChild(stageWrap);

    // Message stream
    var stream = buildMessageStream();
    body.appendChild(stream);

    containerCard.appendChild(body);
    inner.appendChild(containerCard);
    p.appendChild(inner);
    document.body.appendChild(p);
    updateChannelGeometry();

    // ResizeObserver for scale
    updateStageScale();
    var ro = new ResizeObserver(updateStageScale);
    ro.observe(stageWrap);

    // CSS keyframe for ccflow animation
    if(!document.getElementById('rr-ccflow-style')){
      var styleEl = document.createElement('style');
      styleEl.id = 'rr-ccflow-style';
      styleEl.textContent = '@keyframes ccflow{to{stroke-dashoffset:-18}}';
      document.head.appendChild(styleEl);
    }

    updateScenarioTabs();
    updateHardPanel();
  }

  function updateChannelGeometry(){
    // Anchor channel endpoints & ports exactly on the rendered card edges
    var b=els.billCard, p=els.procCard, l=els.ledger;
    if(!b||!p||!l||!els.trackPaths) return;
    if(!b.offsetHeight) return; // panel hidden — offsets unreliable
    var bRight=b.offsetLeft+b.offsetWidth,  bBot=b.offsetTop+b.offsetHeight,  bMidX=b.offsetLeft+b.offsetWidth/2;
    var pLeft=p.offsetLeft,                 pBot=p.offsetTop+p.offsetHeight,  pMidX=p.offsetLeft+p.offsetWidth/2;
    var laneY=Math.round((b.offsetTop+b.offsetHeight/2 + p.offsetTop+p.offsetHeight/2)/2);
    var lLeft=l.offsetLeft, lRight=l.offsetLeft+l.offsetWidth, lMidY=l.offsetTop+l.offsetHeight/2;
    var D={
      cBP:'M'+bRight+','+laneY+' L'+pLeft+','+laneY,
      cBR:'M'+lLeft+','+lMidY+' C'+(lLeft-100)+','+lMidY+' '+bMidX+','+(bBot+45)+' '+bMidX+','+bBot,
      cPR:'M'+pMidX+','+pBot+' C'+pMidX+','+(pBot+50)+' '+(lRight+100)+','+lMidY+' '+lRight+','+lMidY
    };
    Object.keys(D).forEach(function(id){
      [els.trackPaths[id],els.basePaths[id],els.glowPaths[id],els.paths[id]].forEach(function(path){
        if(path) path.setAttribute('d',D[id]);
      });
    });
    // Context stack follows the invoice's rendered height
    var inv=els.invoiceCard;
    if(inv){
      inv.style.top=Math.max(4, 346-inv.offsetHeight)+'px';
      if(els.ctxLine) els.ctxLine.setAttribute('d','M540,349 L540,356');
    }
    var pts=[[bRight,laneY],[pLeft,laneY],[lLeft,lMidY],[bMidX,bBot],[pMidX,pBot],[lRight,lMidY]];
    (els.portEls||[]).forEach(function(pe,i){
      if(!pts[i]) return;
      pe.ring.setAttribute('cx',pts[i][0]); pe.ring.setAttribute('cy',pts[i][1]);
      pe.core.setAttribute('cx',pts[i][0]); pe.core.setAttribute('cy',pts[i][1]);
    });
  }

  function updateChannelMutes(){
    // Recovery channels stay dashed & faint until handoff
    if(!els.basePaths) return;
    ['cBR','cPR'].forEach(function(id){
      var b=els.basePaths[id];
      if(!b) return;
      var t=els.trackPaths&&els.trackPaths[id];
      if(state.cprMuted){
        b.setAttribute('stroke-dasharray','3 6');
        b.setAttribute('stroke','rgba(255,255,255,0.10)');
        b.style.opacity='1';
        if(t) t.style.opacity='0';
      } else {
        b.setAttribute('stroke-dasharray','');
        b.style.opacity='1';
        b.setAttribute('stroke','rgba(0,109,249,0.35)');
        if(t) t.style.opacity='1';
      }
    });
  }

  function updateStageScale(){
    if(!els.stageWrap || !els.stage) return;
    var w=els.stageWrap.clientWidth, h=els.stageWrap.clientHeight;
    if(!w||!h) return;
    var sc=Math.min(1, w/1080, h/770)*0.94;
    var scaledH=770*sc, topOffset=Math.max(0,(h-scaledH)/2);
    var scaledW=1080*sc, leftOffset=Math.max(0,(w-scaledW)/2);
    els.stage.style.transform='scale('+sc+')';
    els.stage.style.marginTop=topOffset+'px';
    els.stage.style.marginLeft=leftOffset+'px';
  }

  function updateScenarioTabs(){
    if(!els.scenarioBar) return;
    var tabs=els.scenarioBar.querySelectorAll('button');
    tabs.forEach(function(tb){
      var active = tb.dataset.scid===state.scenario;
      var _tL=document.documentElement.classList.contains('rr-light');
      tb.style.background = active ? (_tL?'#ffffff':'rgba(255,255,255,0.08)') : 'transparent';
      tb.style.color = active ? BRAND : GRAY;
      tb.style.fontWeight = active ? '600' : '400';
      tb.style.boxShadow = active ? (_tL?'0 1px 2px rgba(15,23,42,.08)':'0 1px 4px rgba(0,0,0,.4)') : 'none';
    });
  }

  function updateHardPanel(){
    if(!els.hardPanel) return;
    els.hardPanel.style.display = state.scenario==='hard_decline' ? 'flex' : 'none';
    var enabled = state.scenario==='hard_decline' && state.declineType==='hard' && state.phase==='running';
    els.hardPanel.style.opacity = enabled ? '1' : '0.45';
    var isOn = state.retryHardDeclines;
    els.hardPanel.style.background = isOn ? 'rgba(253,186,116,0.08)' : 'rgba(239,68,68,0.08)';
    els.hardPanel.style.border = '1px solid '+(isOn?'rgba(253,186,116,0.3)':'rgba(239,68,68,0.3)');
    if(els.hardToggleEl) els.hardToggleEl.style.background = isOn ? '#F97316' : '#374151';
    if(els.hardToggleKnob) els.hardToggleKnob.style.left = isOn ? '16px' : '2px';
    if(els.budgetEl) els.budgetEl.textContent = '$'+state.budgetBalance.toLocaleString();
  }

  function updateStartBtn(){
    if(!els.startBtn) return;
    var running=state.phase==='running', done=state.phase==='done';
    els.startBtn.style.background = running ? 'rgba(0,109,249,0.5)' : BRAND;
    els.startBtn.style.cursor = running ? 'default' : 'pointer';
    var icon = done ? '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.9"/></svg>'
                    : running ? '' : '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>';
    var label = running ? 'Running…' : done ? 'Replay flow' : 'Start';
    els.startBtn.innerHTML = icon + '<span>'+label+'</span>';
    if(els.resetBtn) els.resetBtn.disabled = state.phase==='idle';
  }

  /* ── Component Card Builders ── */
  function cardBox(position){
    var c=el('div','position:absolute;background:'+CARD+';border:1px solid '+BORDER+';border-radius:12px;padding:14px 15px;transition:border-color 0.25s,box-shadow 0.25s');
    c.style.left=position.left+'px'; c.style.top=position.top+'px'; c.style.width=position.width+'px';
    return c;
  }
  function activateCard(c,on){
    c.style.borderColor = on ? 'rgba(0,109,249,0.4)' : BORDER;
    c.style.boxShadow = on ? '0 0 0 3px rgba(0,109,249,0.1),0 8px 24px -8px rgba(0,109,249,0.2)' : 'none';
  }

  function nodeHeader(c, opts){
    // Typed node card: tinted header strip (icon + title + type chip), then body row
    var strip=el('div','display:flex;align-items:center;gap:8px;margin:-14px -15px 11px;padding:9px 13px;border-bottom:1px solid '+BORDER+';border-radius:11px 11px 0 0');
    strip.style.background=opts.mutedTitle?'rgba(255,255,255,0.02)':(opts.tint||'rgba(255,255,255,0.03)');
    var icon=el('div','width:22px;height:22px;border-radius:6px;flex-shrink:0;display:flex;align-items:center;justify-content:center');
    icon.style.background=opts.iconBg; icon.innerHTML=opts.iconSvg;
    var name=el('div','flex:1;min-width:0;font-size:12px;font-weight:700;color:'+(opts.mutedTitle?GRAY2:TEXT)+';letter-spacing:-0.01em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis');
    name.textContent=opts.title;
    strip.appendChild(icon); strip.appendChild(name);
    if(opts.typeChip){
      var chip=el('span','flex-shrink:0;font-size:8px;font-weight:800;letter-spacing:0.09em;text-transform:uppercase;padding:2px 7px;border-radius:5px');
      chip.style.color=opts.mutedTitle?GRAY2:(opts.chipColor||GRAY);
      chip.style.background=opts.mutedTitle?'rgba(255,255,255,0.04)':(opts.chipBg||'rgba(255,255,255,0.06)');
      chip.style.border='1px solid '+(opts.mutedTitle?BORDER:(opts.chipBorder||BORDER));
      chip.textContent=opts.typeChip;
      strip.appendChild(chip);
    }
    c.appendChild(strip);
    if(!opts.provider && !opts.pill) return;
    // Body row: provider + status pill
    var bodyRow=el('div','display:flex;align-items:center;justify-content:space-between;gap:8px');
    var prov=el('div','font-size:10.5px;color:'+(opts.mutedTitle?'rgba(255,255,255,0.18)':GRAY2)+';min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap');
    prov.textContent=opts.provider;
    bodyRow.appendChild(prov);
    if(opts.pill) bodyRow.appendChild(opts.pill);
    c.appendChild(bodyRow);
  }

  function attemptDots(items){
    // n8n-style progress dots — one per attempt, tinted by tone
    var wrap=el('div','display:flex;align-items:center;gap:5px');
    items.forEach(function(item){
      var t=getTone(item.tone);
      var d=el('span','width:7px;height:7px;border-radius:50%;flex-shrink:0;transition:background 0.3s');
      d.style.background=t.color;
      d.style.boxShadow='0 0 6px '+t.color+'55';
      wrap.appendChild(d);
    });
    return wrap;
  }

  function buildBillingCard(){
    var c=cardBox({left:40,top:415,width:250});
    c.id='rr-bill-card';
    renderBillingCard(c); return c;
  }
  function renderBillingCard(c){
    c.innerHTML='';
    nodeHeader(c,{
      title:'Billing Engine', provider:null,
      tint:'rgba(105,65,198,0.10)',
      typeChip:'Source', chipColor:'#9b72e4', chipBg:'rgba(105,65,198,0.12)', chipBorder:'rgba(105,65,198,0.3)',
      iconBg:'rgba(105,65,198,0.15)',
      iconSvg:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#9b72e4" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>'
    });
    // Latest emitted invoice as a mini "sheet" with perforated edge
    var sheetFace=el('div','margin-top:2px;padding:8px 10px;border-radius:7px;background:rgba(255,255,255,0.025);border:1px solid '+BORDER);
    var sheetTop=el('div','display:flex;align-items:center;justify-content:space-between;gap:8px');
    var invId=el('span','font-size:10px;font-family:monospace;color:'+(state.invoiceStatus==='No invoice'?GRAY2:TEXT)+';font-weight:600');
    invId.textContent=state.invoiceStatus==='No invoice'?'awaiting cycle…':'#'+INVOICE_ID;
    sheetTop.appendChild(invId);
    sheetTop.appendChild(statusPill(state.billTone,state.billStatus,true));
    sheetFace.appendChild(sheetTop);
    var perf=el('div','margin:7px -10px 6px;border-top:1px dashed rgba(255,255,255,0.1)');
    sheetFace.appendChild(perf);
    var provRow=el('div','display:flex;align-items:center;gap:5px;font-size:9.5px;color:'+GRAY2);
    provRow.innerHTML='<span style="width:12px;height:12px;border-radius:3px;background:rgba(105,65,198,0.2);color:#9b72e4;font-size:7.5px;font-weight:800;display:inline-flex;align-items:center;justify-content:center">'+billingName[0]+'</span>Billed via '+billingName+' · monthly';
    sheetFace.appendChild(provRow);
    c.appendChild(sheetFace);
  }

  function buildInvoiceCard(){
    var c=cardBox({left:390,top:8,width:300});
    c.id='rr-invoice-card';
    c.style.padding='0';
    c.style.overflow='hidden';
    c.style.background='#10131a';
    c.style.border='1px dashed rgba(255,255,255,0.18)';
    c.style.boxShadow=document.documentElement.classList.contains('rr-light')?'0 4px 16px -8px rgba(15,23,42,0.12)':'0 12px 32px -12px rgba(0,0,0,0.6)';
    renderInvoiceCard(c); return c;
  }
  function renderInvoiceCard(c){
    var invD=getBillingInvoice();
    c.innerHTML='';
    var recovered=state.invoiceTone==='recovered';
    c.style.transition='border-color 0.8s ease';
    c.style.border=recovered?'1px solid rgba(255,255,255,0.08)':'1px dashed rgba(255,255,255,0.18)';

    // Header band — tinted, invoice no. + status (ref 02)
    var band=el('div','transition:background 0.8s ease;padding:12px 15px;background:'+(recovered?'rgba(16,185,129,0.07)':'rgba(0,109,249,0.07)')+';border-bottom:1px '+(recovered?'solid rgba(255,255,255,0.08)':'dashed rgba(255,255,255,0.12)')+';display:flex;align-items:center;justify-content:space-between;gap:8px');
    var bandLeft=el('div');
    var lbl=el('div','font-size:9px;font-weight:700;color:'+GRAY2+';text-transform:uppercase;letter-spacing:0.09em');
    lbl.textContent='Invoice';
    var invId=el('div','font-size:11px;color:'+TEXT+';font-family:monospace;letter-spacing:0.02em;margin-top:2px;font-weight:600');
    invId.textContent='#'+invD.id;
    bandLeft.appendChild(lbl); bandLeft.appendChild(invId);
    band.appendChild(bandLeft);
    band.appendChild(statusPill(state.invoiceTone,state.invoiceStatus,true));
    c.appendChild(band);

    var body=el('div','padding:14px 15px 15px');

    // Amount row — prominent, cycle text right beside it (ref 03)
    var amtRow=el('div','display:flex;align-items:baseline;gap:8px');
    var amt=el('span','font-size:20px;font-weight:800;color:'+TEXT+';letter-spacing:-0.02em');
    amt.textContent=invD.amount;
    var cycle=el('span','font-size:10.5px;color:'+GRAY2);
    cycle.textContent='Monthly subscription';
    amtRow.appendChild(amt); amtRow.appendChild(cycle);
    body.appendChild(amtRow);

    // Meta grid — label-over-value pairs
    var meta=el('div','display:flex;gap:24px;margin-top:16px');
    function metaCol(k,v){
      var col=el('div','flex:1;min-width:0');
      var kEl=el('div','font-size:9px;font-weight:700;color:'+GRAY2+';text-transform:uppercase;letter-spacing:0.09em');
      kEl.textContent=k;
      var vEl=el('div','font-size:11px;color:'+GRAY+';font-weight:500;margin-top:5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis');
      vEl.textContent=v;
      col.appendChild(kEl); col.appendChild(vEl); return col;
    }
    meta.appendChild(metaCol('Customer','john.doe@acme.io'));
    meta.appendChild(metaCol('Account','cus_Np8x42'));
    body.appendChild(meta);

    // Payment method section — scenario-aware cards (ref 01)
    body.appendChild(el('div','margin:18px 0;border-top:1px '+(recovered?'solid rgba(255,255,255,0.08)':'dashed rgba(255,255,255,0.12)')));
    var pmLbl=el('div','font-size:9px;font-weight:700;color:'+GRAY2+';text-transform:uppercase;letter-spacing:0.09em;margin:0 0 10px');
    pmLbl.textContent='Cards attached';
    body.appendChild(pmLbl);
    (invD.cards||[]).forEach(function(card,i){
      var isActive=i===(invD.activeCard||0);
      var showExp=card.expired && card.expiredRevealed;
      var netBg=card.network==='MC'?'linear-gradient(135deg,#c0392b,#e67e22)':'linear-gradient(135deg,#1e3a8a,#2563EB)';
      var netName=card.network==='MC'?'Mastercard':'Visa';
      var cardRow=el('div','display:flex;align-items:center;gap:10px;padding:8px 10px;border-radius:9px;transition:all 0.35s ease;margin-bottom:8px');
      cardRow.style.background=isActive?'rgba(37,99,235,0.1)':'rgba(255,255,255,0.03)';
      cardRow.style.border='1px solid '+(isActive?'rgba(37,99,235,0.25)':BORDER);
      cardRow.style.opacity=isActive?'1':'0.55';
      // Network chip — mini card with stripe
      var netEl=el('div','width:34px;height:22px;border-radius:4px;flex-shrink:0;position:relative;overflow:hidden;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 6px rgba(0,0,0,0.35)');
      netEl.style.background=netBg;
      netEl.innerHTML='<span style="font-size:7px;font-weight:900;color:#fff;letter-spacing:0.3px;position:relative;z-index:1">'+card.network+'</span>'
        +'<span style="position:absolute;top:0;left:0;right:0;height:7px;background:rgba(255,255,255,0.14)"></span>';
      // Number + labeled expiry, two lines
      var mid=el('div','flex:1;min-width:0');
      var numLine=el('div','display:flex;align-items:baseline;gap:6px');
      var netTxt=el('span','font-size:11px;font-weight:600;color:'+TEXT); netTxt.textContent=netName;
      var last4=el('span','font-size:11px;font-weight:600;color:'+TEXT+';font-family:monospace;letter-spacing:0.04em'); last4.textContent='•••• '+card.last4;
      numLine.appendChild(netTxt); numLine.appendChild(last4);
      var expLine=el('div','font-size:9.5px;color:'+(showExp?'#ef4444':GRAY2)+';margin-top:2px');
      expLine.textContent='Expires '+card.expiry;
      mid.appendChild(numLine); mid.appendChild(expLine);
      // Status badge
      var badge2=el('span','flex-shrink:0;font-size:9px;font-weight:700;padding:3px 8px;border-radius:5px;letter-spacing:0.05em;text-transform:uppercase');
      if(showExp){ badge2.style.background='rgba(239,68,68,0.15)'; badge2.style.color='#ef4444'; badge2.style.border='1px solid rgba(239,68,68,0.3)'; badge2.textContent='Expired'; }
      else if(isActive){ badge2.style.background='rgba(37,99,235,0.15)'; badge2.style.color='#5b9bff'; badge2.style.border='1px solid rgba(37,99,235,0.25)'; badge2.textContent='Active'; }
      else { badge2.style.background='rgba(255,255,255,0.05)'; badge2.style.color=GRAY2; badge2.style.border='1px solid '+BORDER; badge2.textContent='Backup'; }
      cardRow.appendChild(netEl); cardRow.appendChild(mid); cardRow.appendChild(badge2);
      body.appendChild(cardRow);
    });
    c.appendChild(body);
  }
  function getBillingInvoice(){
    var base={id:INVOICE_ID,amount:INVOICE_AMOUNT};
    if(state.scenario==='card_switching') return Object.assign({},base,{cards:[{network:'VISA',last4:'4242',expiry:'12/26'},{network:'MC',last4:'8888',expiry:'09/27'}],activeCard:state.activeCardIndex});
    if(state.scenario==='account_update'){
      var cards=state.accountUpdated?[{network:'VISA',last4:'4242',expiry:'06/23',expired:true,expiredRevealed:state.expiredRevealed},{network:'VISA',last4:'7890',expiry:'03/28'}]:[{network:'VISA',last4:'4242',expiry:'06/23',expired:true,expiredRevealed:state.expiredRevealed}];
      return Object.assign({},base,{cards:cards,activeCard:state.accountUpdated?1:0});
    }
    return Object.assign({},base,{cards:[{network:'VISA',last4:'4242',expiry:'12/26'}],activeCard:0});
  }

  function buildProcCard(){
    var c=cardBox({left:790,top:415,width:250});
    c.id='rr-proc-card';
    renderProcCard(c); return c;
  }
  function renderProcCard(c){
    c.innerHTML='';
    nodeHeader(c,{
      title:'Payment Processor', provider:null,
      tint:'rgba(34,211,238,0.08)',
      typeChip:'Processor', chipColor:'#22d3ee', chipBg:'rgba(34,211,238,0.10)', chipBorder:'rgba(34,211,238,0.3)',
      iconBg:'rgba(34,211,238,0.10)',
      iconSvg:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#22d3ee" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>'
    });
    // Terminal metaphor: card slot groove + monospace display readout
    var toneColor={idle:GRAY2,processing:'#5b9bff',failed:'#ef4444',success:'#10b981',captured:'#0891b2'}[state.procTone]||GRAY2;
    var _pL=document.documentElement.classList.contains('rr-light');
    var screen=el('div','padding:8px 10px;border-radius:7px;background:'+(_pL?'#f1f3f6':'#05070b')+';border:1px solid '+(_pL?'rgba(15,23,42,0.10)':'rgba(255,255,255,0.07)')+';box-shadow:'+(_pL?'inset 0 1px 3px rgba(15,23,42,0.06)':'inset 0 2px 8px rgba(0,0,0,0.6)'));
    var line1=el('div','font-size:9px;font-family:monospace;color:'+GRAY2+';letter-spacing:0.03em');
    line1.textContent=paymentName.toUpperCase()+' · TERMINAL';
    var line2=el('div','font-size:10px;font-family:monospace;font-weight:600;margin-top:4px;letter-spacing:0.02em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis');
    line2.style.color=toneColor;
    line2.style.textShadow=state.procTone!=='idle'?'0 0 8px '+toneColor+'66':'none';
    line2.textContent='> '+state.procStatus;
    screen.appendChild(line1); screen.appendChild(line2);
    c.appendChild(screen);
  }

  function buildExtRetryPanel(){
    // Out-of-loop context ticker — narrates merchant external retries
    var c=el('div','position:absolute;left:540px;top:360px;transform:translateX(-50%);display:flex;align-items:center;gap:8px;padding:6px 14px;border-radius:999px;background:'+(document.documentElement.classList.contains('rr-light')?'#ffffff':'#0c0e13')+';border:1px solid '+BORDER+';white-space:nowrap;z-index:2;transition:border-color 0.4s,opacity 0.4s');
    c.id='rr-ext-retry';
    renderExtRetry(c); return c;
  }
  function renderExtRetry(c){
    c.innerHTML='';
    var n=state.external.length;
    var dotColor, text, textColor, borderColor;
    if(state.escalated){
      dotColor='#38bdf8';
      text='Unrecovered after 3 external retries · handed off to Hyperswitch';
      textColor='#38bdf8'; borderColor='rgba(56,189,248,0.35)';
      c.style.opacity='1';
    } else if(n>0){
      dotColor='#f59e0b';
      text='Merchant attempting external retries · '+n+' of 3 failed';
      textColor='#f59e0b'; borderColor='rgba(245,158,11,0.35)';
      c.style.opacity='1';
    } else {
      var _xL=document.documentElement.classList.contains('rr-light');
      dotColor=_xL?'#94a3b8':'#64748b';
      text='Merchant external retries · not started';
      textColor=_xL?'#64748b':'#94a3b8'; borderColor=_xL?'rgba(15,23,42,0.14)':BORDER;
      c.style.opacity='0.9';
    }
    c.style.borderColor=borderColor;
    var dot=el('span','width:7px;height:7px;border-radius:50%;flex-shrink:0');
    dot.style.background=dotColor;
    if(n>0&&!state.escalated) dot.style.boxShadow='0 0 8px '+dotColor;
    c.appendChild(dot);
    var txt=el('span','font-size:9.5px;font-weight:600;letter-spacing:0.02em');
    txt.style.color=textColor;
    txt.textContent=text;
    c.appendChild(txt);
    if(n>0&&!state.escalated) c.appendChild(attemptDots(state.external));
  }

  function buildLedgerPanel(){
    var c=cardBox({left:390,top:585,width:300});
    c.id='rr-ledger';
    renderLedger(c); return c;
  }
  function renderLedger(c){
    c.innerHTML='';
    var muted=state.cprMuted;
    c.style.opacity='1';
    c.style.background=CARD;

    // Hero hub treatment — brand glow when active
    c.style.border='1px solid '+(muted?BORDER:'rgba(0,109,249,0.35)');
    c.style.boxShadow=muted?'none':'0 0 0 3px rgba(0,109,249,0.07), 0 12px 36px -12px rgba(0,109,249,0.35)';

    nodeHeader(c,{
      title:'Revenue Recovery',
      provider:muted?'Awaiting handoff from merchant':'Hyperswitch internal retries',
      mutedTitle:muted,
      tint:'rgba(0,109,249,0.10)',
      typeChip:'Engine', chipColor:'#5b9bff', chipBg:'rgba(0,109,249,0.14)', chipBorder:'rgba(0,109,249,0.35)',
      iconBg:muted?'rgba(255,255,255,0.04)':'rgba(0,109,249,0.16)',
      iconSvg:'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="'+(muted?GRAY2:'#5b9bff')+'" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 .49-3.9"/></svg>'
    });

    if(!muted){
      // Decline analysis — classification + error code readout
      var DB={
        hard:   {label:'Hard Decline', color:'#ef4444'},
        expired:{label:'Card Expired', color:'#ef4444'},
        soft:   {label:'Soft Decline', color:'#ef4444'}
      };
      var db=state.declineType?DB[state.declineType]:null;
      if(db){
      // Neutral container; only the values carry the tone color. Fade in gently once.
      var grid=el('div','display:flex;gap:18px;margin-top:11px;padding:8px 11px;border-radius:8px;background:rgba(255,255,255,0.03);border:1px solid '+BORDER);
      if(!state.anaRevealed){
        state.anaRevealed=true;
        grid.style.opacity='0';
        grid.style.transition='opacity 0.8s ease';
        requestAnimationFrame(function(){ requestAnimationFrame(function(){ grid.style.opacity='1'; }); });
      }
      function anaCol(k,vText,vColor,mono){
        var col=el('div','flex:1;min-width:0');
        var kEl=el('div','font-size:8px;font-weight:800;letter-spacing:0.1em;text-transform:uppercase;color:'+GRAY2);
        kEl.textContent=k;
        var vEl=el('div','font-weight:700;margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'+(mono?'font-family:monospace;letter-spacing:0.01em;font-size:9.5px':'font-size:10.5px'));
        vEl.style.color=vColor;
        vEl.textContent=vText;
        col.appendChild(kEl); col.appendChild(vEl); return col;
      }
      grid.appendChild(anaCol('Decline type', db.label, db.color, false));
      grid.appendChild(anaCol('Error code', state.errorCode||'—', db.color, true));
      c.appendChild(grid);
      }
      var foot=el('div','display:flex;align-items:center;justify-content:space-between;gap:8px;margin-top:12px;padding-top:10px;border-top:1px solid '+BORDER);
      if(state.internal.length===0){
        var idle=el('span','font-size:10.5px;color:rgba(255,255,255,0.18)'); idle.textContent='No retries scheduled yet';
        foot.appendChild(idle);
      } else {
        var last=state.internal[state.internal.length-1];
        var leftG=el('div','display:flex;align-items:center;gap:8px');
        leftG.appendChild(attemptDots(state.internal));
        var cnt=el('span','font-size:10.5px;color:'+GRAY2);
        cnt.textContent=state.internal.length+' internal '+(state.internal.length===1?'retry':'retries');
        leftG.appendChild(cnt);
        foot.appendChild(leftG);
        foot.appendChild(statusPill(last.tone,last.status,true));
      }
      c.appendChild(foot);
    }
  }

  function buildMessageStream(){
    var s=el('div','flex:0 0 27%;min-width:0;min-height:0;overflow:hidden;display:flex;flex-direction:column;background:'+CARD+';border-left:1px solid '+BORDER);

    var hdrEl=el('div','display:flex;align-items:center;gap:8px;padding:14px 18px 12px;border-bottom:1px solid '+BORDER+';flex-shrink:0');
    var dot=el('div','width:10px;height:10px;border-radius:50%;background:#3a3f4a;flex-shrink:0');
    var hdrText=el('span','font-size:10.5px;font-weight:700;color:'+TEXT+';letter-spacing:0.07em;flex:1');
    hdrText.textContent='AWAITING START';
    var hdrBadge=el('span','font-size:10px;font-weight:600;color:#3a3f4a;background:rgba(255,255,255,0.06);padding:2px 8px;border-radius:999px');
    hdrBadge.textContent='IDLE';
    hdrEl.appendChild(dot); hdrEl.appendChild(hdrText); hdrEl.appendChild(hdrBadge);
    els.streamHeader={el:hdrEl,dot:dot,text:hdrText,badge:hdrBadge};

    var logWrap=el('div','flex:1;min-height:0;overflow-y:auto;overflow-x:hidden;padding:18px 16px');
    var emptyMsg=el('div','font-size:11px;color:'+GRAY2+';text-align:center;padding-top:28px');
    emptyMsg.textContent='No events yet — press Start.';
    logWrap.appendChild(emptyMsg);
    els.streamLog=logWrap;

    s.appendChild(hdrEl); s.appendChild(logWrap);
    return s;
  }

  function updateStreamHeader(){
    if(!els.streamHeader) return;
    var sh=els.streamHeader;
    var dotColor=state.phase==='running'?'#4D90FF':state.phase==='done'?'#10b981':'#3a3f4a';
    var label=state.phase==='running'?'LIVE':state.phase==='done'?'COMPLETE':'IDLE';
    var text=state.phase==='running'?'REVENUE RECOVERY IS ATTEMPTING RETRIES':state.phase==='done'?'RETRIES COMPLETED':'AWAITING START';
    sh.dot.style.background=dotColor;
    sh.dot.style.boxShadow=state.phase!=='idle'?'0 0 8px '+dotColor+'66':'none';
    sh.text.textContent=text;
    sh.badge.style.color=dotColor;
    sh.badge.style.background=dotColor+'18';
    sh.badge.textContent=label;
  }

  function addLogEntry(route, label, status, tone){
    state.log.push({time:formatTime(),route:route,label:label,status:status,tone:tone});
    renderLog();
  }
  function renderLog(){
    if(!els.streamLog) return;
    els.streamLog.innerHTML='';
    if(state.log.length===0){
      var em=el('div','font-size:11px;color:'+GRAY2+';text-align:center;padding-top:28px');
      em.textContent='No events yet — press Start.'; els.streamLog.appendChild(em); return;
    }
    var DOT_COLORS={listen:'#4D90FF',idle:'#5e6573',failed:'#EF4444',success:'#10B981',scheduled:'#F59E0B',processing:'#4D90FF',recovered:'#10B981',received:'#10B981',sent:'#4D90FF',retrying:'#4D90FF',partial:'#0891B2',created:'#4D90FF',classified:'#F59E0B',switching:'#F59E0B',halted:'#EF4444'};
    var BADGE_COLORS={listen:{bg:'rgba(0,102,255,0.12)',color:'#5b9bff'},idle:{bg:'rgba(255,255,255,0.06)',color:'#8a8f98'},failed:{bg:'rgba(239,68,68,0.12)',color:'#ef4444'},success:{bg:'rgba(16,185,129,0.12)',color:'#10b981'},scheduled:{bg:'rgba(245,158,11,0.12)',color:'#f59e0b'},processing:{bg:'rgba(0,102,255,0.12)',color:'#5b9bff'},recovered:{bg:'rgba(16,185,129,0.12)',color:'#10b981'},received:{bg:'rgba(16,185,129,0.12)',color:'#10b981'},sent:{bg:'rgba(0,102,255,0.12)',color:'#5b9bff'},retrying:{bg:'rgba(0,102,255,0.12)',color:'#5b9bff'},partial:{bg:'rgba(8,145,178,0.12)',color:'#0891b2'},created:{bg:'rgba(0,102,255,0.12)',color:'#5b9bff'},classified:{bg:'rgba(245,158,11,0.12)',color:'#f59e0b'},switching:{bg:'rgba(245,158,11,0.12)',color:'#f59e0b'},halted:{bg:'rgba(239,68,68,0.12)',color:'#ef4444'}};
    state.log.forEach(function(entry,i){
      var isLast=i===state.log.length-1;
      var dot=DOT_COLORS[entry.tone]||'#5e6573';
      var badge=BADGE_COLORS[entry.tone]||{bg:'rgba(255,255,255,0.06)',color:'#8a8f98'};
      var row=el('div','display:flex;position:relative;padding-left:36px;padding-bottom:'+(isLast?'0':'22px'));
      if(!isLast){
        var line=el('div','position:absolute;left:19.5px;top:12px;bottom:2px;width:0;border-left:1px dashed rgba(255,255,255,0.14)');
        row.appendChild(line);
      }
      var dotEl=el('div','position:absolute;left:16px;top:4px;width:9px;height:9px;border-radius:50%;background:'+dot+';box-shadow:0 0 6px '+dot+'88;z-index:1');
      row.appendChild(dotEl);
      var content=el('div','flex:1;min-width:0');
      var topLine=el('div','display:flex;align-items:center;gap:6px;margin-bottom:4px');
      var num=el('span','font-size:10px;color:'+GRAY2+';font-variant-numeric:tabular-nums'); num.textContent='#'+String(i+1).padStart(2,'0');
      var route2=el('span','font-size:10.5px;color:'+GRAY+';flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap'); route2.textContent=entry.route;
      var time=el('span','font-size:10px;color:'+GRAY2+';white-space:nowrap'); time.textContent=entry.time;
      topLine.appendChild(num); topLine.appendChild(route2); topLine.appendChild(time);
      var botLine=el('div','display:flex;align-items:center;gap:6px;flex-wrap:wrap');
      var statusEl=el('span','font-size:10.5px;font-weight:600;padding:2px 8px;border-radius:4px;white-space:nowrap');
      statusEl.style.background=badge.bg; statusEl.style.color=badge.color; statusEl.textContent=entry.status;
      var labelEl=el('span','font-size:10.5px;color:'+GRAY2+';overflow-wrap:anywhere'); labelEl.textContent=entry.label;
      botLine.appendChild(statusEl); botLine.appendChild(labelEl);
      content.appendChild(topLine); content.appendChild(botLine);
      row.appendChild(content);
      els.streamLog.appendChild(row);
    });
    els.streamLog.scrollTop=els.streamLog.scrollHeight;
  }

  /* ── Chip animation ── */
  function flyChip(channelId, reverse, color, label){
    return new Promise(function(resolve){
      var stage=els.stage, chip=els.chip, path=els.paths[channelId];
      var glow=els.glowPaths?els.glowPaths[channelId]:null;
      if(!stage||!chip||!path){ setTimeout(resolve,320); return; }
      var len=path.getTotalLength();
      path.setAttribute('stroke',color);
      path.style.strokeDasharray='1 8';
      path.style.opacity='1';
      path.style.animation='ccflow 0.9s linear infinite';
      path.style.animationDirection=reverse?'reverse':'normal';
      if(glow){ glow.setAttribute('stroke',color); glow.style.opacity='0.28'; }
      chip.innerHTML='<span style="width:6px;height:6px;border-radius:50%;background:'+color+';flex:none;display:inline-block"></span><span>'+label+'</span>';
      chip.style.borderColor=color;
      chip.style.boxShadow='0 8px 22px -6px '+color+'88';
      chip.style.opacity='1';
      var cw=chip.offsetWidth||90, ch=chip.offsetHeight||28;
      var dur=1600, t0=performance.now(), done=false;
      function finish(){
        if(done) return; done=true;
        chip.style.opacity='0';
        setTimeout(function(){
          path.style.opacity='0'; path.style.animation=''; path.setAttribute('stroke','none');
          if(glow){ glow.style.opacity='0'; }
        },220);
        resolve();
      }
      function frame(n){
        if(done||cancelFlag){ if(!done)finish(); return; }
        var p=Math.min(1,(n-t0)/dur);
        var e=p<0.5?2*p*p:1-Math.pow(-2*p+2,2)/2;
        var at=reverse?1-e:e;
        var pt=path.getPointAtLength(at*len);
        chip.style.transform='translate('+(pt.x-cw/2)+'px,'+(pt.y-ch/2)+'px)';
        if(p<1) requestAnimationFrame(frame); else finish();
      }
      requestAnimationFrame(frame);
      setTimeout(finish, dur+280);
    });
  }

  function tick(ms){
    return new Promise(function(resolve){
      setTimeout(function(){ cancelFlag?resolve('cancelled'):resolve(); }, ms);
    });
  }

  function updateCards(){
    if(els.billCard) renderBillingCard(els.billCard);
    if(els.invoiceCard) renderInvoiceCard(els.invoiceCard);
    if(els.procCard) renderProcCard(els.procCard);
    if(els.extRetry) renderExtRetry(els.extRetry);
    if(els.ledger) renderLedger(els.ledger);
    activateCard(els.billCard, state.active==='bill');
    activateCard(els.procCard, state.active==='proc');
    if(els.ledger){
      var recActive=!state.cprMuted&&state.active==='rec';
      if(recActive){
        els.ledger.style.borderColor='rgba(0,109,249,0.6)';
        els.ledger.style.boxShadow='0 0 0 3px rgba(0,109,249,0.14), 0 12px 36px -12px rgba(0,109,249,0.5)';
      }
      // otherwise renderLedger already applied hero/muted styling
    }
    updateChannelGeometry();
    updateChannelMutes();
    updateHardPanel();
    updateStreamHeader();
    updateStartBtn();
    renderLog();
  }

  /* ── Main simulation run ── */
  function resetSimState(phase){
    state.phase=phase; state.active=null;
    state.log=[]; state.external=[]; state.internal=[];
    state.billStatus='Idle'; state.billTone='idle';
    state.procStatus='Idle'; state.procTone='idle';
    state.invoiceStatus='No invoice'; state.invoiceTone='idle';
    state.cprMuted=true; state.escalated=false;
    state.declineType=null; state.errorCode=null; state.anaRevealed=false; state.activeCardIndex=0;
    state.accountUpdated=false; state.expiredRevealed=false;
    state.retryHardDeclines=false; state.budgetBalance=BUDGET_TOTAL;
    updateCards();
  }

  async function runSim(){
    cancelFlag=false; retryHardFlag=false;
    resetSimState('running');
    if((await tick(300))==='cancelled') return;

    // 1 — Billing Engine generates invoice
    state.active='bill'; state.billTone='info'; state.billStatus='Invoice raised';
    state.invoiceTone='info'; state.invoiceStatus='Open';
    addLogEntry('Billing Engine','invoice '+INVOICE_ID+' generated · '+INVOICE_AMOUNT,'created','listen');
    updateCards();
    if((await tick(600))==='cancelled') return;

    // 2 — External retries: Billing → Processor (3 attempts, all fail)
    var EXT_TOTAL=3;
    for(var ei=1;ei<=EXT_TOTAL;ei++){
      state.active='bill'; state.procTone='processing'; state.procStatus='Attempt #'+ei+' · processing…';
      updateCards();
      await flyChip('cBP',false,'#5e6573','attempt #'+ei);
      if(cancelFlag) return;
      addLogEntry('Billing → Processor','external attempt #'+ei+' · '+INVOICE_AMOUNT,'sent','idle');
      state.active='proc'; updateCards();
      if((await tick(500))==='cancelled') return;
      state.procTone='failed'; state.procStatus='Declined · attempt #'+ei;
      updateCards();
      await flyChip('cBP',true,'#EF4444','failed');
      if(cancelFlag) return;
      addLogEntry('Processor → Billing','attempt #'+ei+' declined','failed','failed');
      state.external.push({label:'External retry #'+ei,sub:'Merchant · Billing Engine',amount:INVOICE_AMOUNT,status:'Failed',tone:'failed'});
      state.invoiceTone='failed'; state.invoiceStatus='Past due';
      state.active='bill'; updateCards();
      if((await tick(350))==='cancelled') return;
    }

    // 3 — Hand off to Revenue Recovery
    state.billTone='info'; state.billStatus='Escalating…'; state.escalated=true; state.cprMuted=false;
    updateCards();
    if((await tick(300))==='cancelled') return;
    await flyChip('cBR',true,'#0066FF','handoff to recovery');
    if(cancelFlag) return;
    addLogEntry('Billing → Recovery',EXT_TOTAL+' external retries exhausted · handoff','received','listen');
    state.active='rec'; updateCards();
    if((await tick(400))==='cancelled') return;

    // 4 — Internal retries (scenario-aware)
    var sc=state.scenario;
    var isHard=sc==='hard_decline', isCardSwitch=sc==='card_switching';
    var isAcctUpdate=sc==='account_update', isPartialAuth=sc==='partial_auth';
    var PARTIAL_SCHEDULE=isPartialAuth?{3:15,5:20,6:14}:{};
    var recoveredSoFar=0;
    var INT_TOTAL=isCardSwitch?3:isHard?3:isPartialAuth?6:2;

    for(var ii=1;ii<=INT_TOTAL;ii++){
      var date=futureDate(ii*2);
      var idx=ii-1;
      state.internal.push({label:'Recovery retry #'+ii,sub:'Scheduled '+date,amount:INVOICE_AMOUNT,status:'Scheduled',tone:'scheduled'});
      state.active='rec';
      addLogEntry('Recovery · internal','scheduled retry #'+ii+' for '+date,'scheduled','scheduled');
      updateCards();
      if((await tick(600))==='cancelled') return;

      state.internal[idx]={label:'Recovery retry #'+ii,sub:'Scheduled '+date,amount:INVOICE_AMOUNT,status:'Processing',tone:'processing'};
      state.procTone='processing'; state.procStatus='Recovery retry #'+ii+'…';
      if(isHard){ state.budgetBalance=Math.max(0,state.budgetBalance-RETRY_COST); }
      updateCards();
      await flyChip('cPR',true,'#0066FF','recovery retry #'+ii);
      if(cancelFlag) return;
      addLogEntry('Recovery → Processor','recovery retry #'+ii,'retrying','listen');
      state.active='proc'; updateCards();
      if((await tick(650))==='cancelled') return;

      var isPartialResult=isPartialAuth&&PARTIAL_SCHEDULE[ii]!==undefined;
      var succeeded=isCardSwitch?(ii===3):(isHard?(ii===3):(!isPartialAuth&&ii===INT_TOTAL));

      if(isPartialResult){
        var partialAmt=PARTIAL_SCHEDULE[ii];
        recoveredSoFar+=partialAmt;
        var isLastPartial=recoveredSoFar>=49;
        state.procTone=isLastPartial?'success':'captured';
        state.procStatus='Partial auth · $'+partialAmt+' authorized';
        updateCards();
        await flyChip('cPR',false,'#0891B2','partial $'+partialAmt);
        if(cancelFlag) return;
        addLogEntry('Processor → Recovery','partial.authorized · $'+partialAmt+' of '+INVOICE_AMOUNT,'partial','captured');
        state.internal[idx]={label:'Recovery retry #'+ii,sub:'Captured '+date,amount:'$'+partialAmt,status:'$'+partialAmt+' partial',tone:'captured'};
        state.active='rec';
        if(isLastPartial){ state.invoiceTone='recovered'; state.invoiceStatus='Recovered'; }
        else { state.invoiceTone='captured'; state.invoiceStatus='$'+recoveredSoFar+' / '+INVOICE_AMOUNT; }
        updateCards();
        if((await tick(400))==='cancelled') return;
      } else if(!succeeded){
        state.procTone='failed'; state.procStatus='Declined · attempt #'+ii;
        updateCards();
        await flyChip('cPR',false,'#EF4444','failed');
        if(cancelFlag) return;
        addLogEntry('Processor → Recovery','payment.failed webhook','failed','failed');
        state.internal[idx]={label:'Recovery retry #'+ii,sub:'Attempted '+date,amount:INVOICE_AMOUNT,status:'Failed',tone:'failed'};
        state.active='rec'; updateCards();
        if((await tick(400))==='cancelled') return;

        if(ii===1){
          var dtype=isHard?'hard':isAcctUpdate?'expired':'soft';
          var ERR_CODES={soft_decline:'INSUFFICIENT_FUNDS',card_switching:'DO_NOT_HONOR',account_update:'EXPIRED_CARD',partial_auth:'PARTIAL_AUTH_ONLY',hard_decline:'STOLEN_CARD'};
          state.declineType=dtype;
          state.errorCode=ERR_CODES[sc]||'DO_NOT_HONOR';
          addLogEntry('Recovery · analysis','Classified as '+(isHard?'Hard Decline':isAcctUpdate?'Card Expired':'Soft Decline')+' · '+state.errorCode,'classified',isHard?'failed':'scheduled');
          updateCards();
          if((await tick(500))==='cancelled') return;

          if(isHard){
            state.invoiceTone='failed'; state.invoiceStatus='Paused'; updateCards();
            addLogEntry('Recovery · safeguard','⏸ Hard decline · retry paused · enable “Retry Hard Declines” budget to continue','halted','failed');
            updateHardPanel();
            while(!retryHardFlag){ if(cancelFlag) return; await tick(300); }
            addLogEntry('Recovery · safeguard','⚠ Retry budget enabled · network penalty risk acknowledged · proceeding…','classified','scheduled');
            if((await tick(500))==='cancelled') return;
          }

          if(isAcctUpdate){
            state.expiredRevealed=true; updateCards();
            addLogEntry('Recovery · account updater','Searching for updated card details…','scheduled','scheduled');
            if((await tick(800))==='cancelled') return;
            state.accountUpdated=true; updateCards();
            addLogEntry('Recovery · account updater','Found new card •••• 7890 (Visa) · Exp 03/28','received','success');
            state.billStatus='New card found · retrying…'; updateCards();
            if((await tick(500))==='cancelled') return;
          }
        }

        if(isCardSwitch&&ii===2){
          if((await tick(300))==='cancelled') return;
          state.activeCardIndex=1; updateCards();
          addLogEntry('Recovery · card switch','Switching to backup card •••• 8888 (Mastercard)','switching','scheduled');
          state.billStatus='Card switched · retrying…'; updateCards();
          if((await tick(600))==='cancelled') return;
        }
      } else {
        var cardLabel=isCardSwitch?'Mastercard •••• 8888':isHard?'hard decline resolved':'primary card';
        state.procTone='success'; state.procStatus='Payment succeeded ✓'; updateCards();
        await flyChip('cPR',false,'#10B981','succeeded');
        if(cancelFlag) return;
        addLogEntry('Processor → Recovery','payment.succeeded · '+cardLabel,'recovered','success');
        state.internal[idx]={label:'Recovery retry #'+ii,sub:'Captured '+date,amount:INVOICE_AMOUNT,status:'Succeeded',tone:'success'};
        state.active='rec'; updateCards();
        if((await tick(450))==='cancelled') return;
      }
    }

    // 5 — Mark paid
    await flyChip('cBR',false,'#10B981','mark paid (API)');
    if(cancelFlag) return;
    addLogEntry('Recovery → Billing','PATCH invoice → paid (API)','sent','success');
    state.active=null; state.billTone='success'; state.billStatus='Paid ✓';
    state.invoiceTone='recovered'; state.invoiceStatus='Recovered';
    state.phase='done'; updateCards();
  }

  window.rrAddSimulationNav = function(){
    var allBtns=document.querySelectorAll('nav button');
    var simBtn=null;
    for(var i=0;i<allBtns.length;i++){
      if(allBtns[i].textContent.trim().indexOf('Recovery Simulation')===0){ simBtn=allBtns[i]; break; }
    }
    if(!simBtn) return;
    var navContainer=simBtn.parentNode;
    if(navContainer.querySelector('#rr-sim3-nav')) return;

    try{
      var rrCfg=JSON.parse(localStorage.getItem('rrConfig')||'{}');
      if(rrCfg.payName) paymentName=rrCfg.payName;
      if(rrCfg.billName) billingName=rrCfg.billName;
    }catch(e){}

    // Clone the real button structure exactly (icon box, gap, padding) so
    // spacing matches pixel-for-pixel instead of approximating with our own markup.
    var ACTIVE_CLS='w-full flex items-center gap-2.5 px-2 rounded-md text-[12.5px] transition-colors bg-white/[0.06] text-[#f7f8f8]';
    var INACTIVE_CLS='w-full flex items-center gap-2.5 px-2 rounded-md text-[12.5px] transition-colors text-[#8a8f98] hover:bg-white/[0.03] hover:text-[#f7f8f8]';
    var navItem=simBtn.cloneNode(true);
    navItem.id='rr-sim3-nav';
    navItem.className=INACTIVE_CLS;
    navItem.style.cssText=simBtn.style.cssText; // matches the inline padding-top/bottom the real buttons use
    var navSvg=navItem.querySelector('svg');
    if(navSvg) navSvg.innerHTML='<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>';
    var navSpan=navItem.querySelector('span');
    if(navSpan) navSpan.textContent='Live Flow';

    // React owns these buttons' className — never overwrite it directly (if a
    // click is a no-op for React's own state, it won't reconcile our change
    // back, leaving the button permanently stuck). Use !important inline
    // style instead, which sits outside React's diffing entirely and is
    // trivially reversible by just removing the property.
    function maskActiveLook(b){
      b.style.setProperty('background','transparent','important');
      b.style.setProperty('color','#8a8f98','important');
    }
    function unmaskActiveLook(b){
      b.style.removeProperty('background');
      b.style.removeProperty('color');
    }

    var existingBtns=navContainer.querySelectorAll('button');
    existingBtns.forEach(function(b){
      b.addEventListener('click',function(){
        if(els.panel) els.panel.style.display='none';
        cancelFlag=true;
        unmaskActiveLook(b);
        navItem.className=INACTIVE_CLS; // only one tab is ever active at a time
        try{ localStorage.setItem('rrActiveTab', b.textContent.trim().indexOf('Recovery Simulation')===0 ? 'simulation' : 'overview'); }catch(e){}
      });
    });

    function activateLiveFlow(){
      existingBtns.forEach(maskActiveLook);
      navItem.className=ACTIVE_CLS;
      if(!els.panel) buildPanel();
      els.panel.style.display='flex';
      try{ localStorage.setItem('rrActiveTab','liveflow'); }catch(e){}
    }
    navItem.onclick=activateLiveFlow;

    navContainer.appendChild(navItem);

    // Restore Live Flow immediately on load if it was the last active tab —
    // same persistence the real nav items get via rrView.
    try{ if(localStorage.getItem('rrActiveTab')==='liveflow') activateLiveFlow(); }catch(e){}
  };

  // Rebuild the Live Flow panel on theme switch so its inline-styled colours refresh.
  window.rrOnThemeChange = function(){
    rrLiveTheme();
    if(els.panel){
      var open = els.panel.style.display!=='none';
      cancelFlag = true;
      els.panel.remove(); els.panel=null; els.signalsWrap=null;
      if(open){ buildPanel(); els.panel.style.display='flex'; }
    }
  };

  if(localStorage.getItem('rrSetupV2')) setTimeout(window.rrAddSimulationNav, 300);
})();
</script>"""
# Make the Live Flow theme-aware: rewrite hardcoded dark colours in the JS body
# (everything after the theme-setup block) to the theme-derived vars/helpers.
# Applied only past the `rrLiveTheme();` init line so the definitions themselves
# aren't mangled. Each target lives inside a single-quoted JS string, so wrapping
# with `'+VAR+'` closes and reopens the string cleanly.
_sv_marker = '  rrLiveTheme();\n'
_sv_head, _sv_body = SIMULATION_VIEW.split(_sv_marker, 1)
_sv_body = re.sub(r'rgba\(255,255,255,([0-9.]+)\)', r"'+OL(\1)+'", _sv_body)
for _h, _v in [('#0b0d11', 'STAGE'), ('#10131a', 'INVBG'), ('#05070b', 'TERMBG'),
               ('#16191f', 'CHIPBG'), ('#0c0e13', 'PILLBG')]:
    _sv_body = _sv_body.replace(_h, "'+" + _v + "+'")
SIMULATION_VIEW = _sv_head + _sv_marker + _sv_body

html = html.replace('</body>', SIMULATION_VIEW + '</body>', 1)

# ============================================================
#  LIGHT THEME  —  override layer for the compiled dark dashboard
#  A `html.rr-light` root class remaps the neutral surface/text scale
#  and flips white-opacity overlays to subtle black ones. Accent colours
#  (indigo/blue/green/red/cyan/orange) are left untouched — they read on
#  both themes. Generated from the classes actually present in `html`.
# ============================================================
# Semantic CSS-variable layer (drives .surface, .grid-bg consumers, var() users).
_VARS_LIGHT = {
    '--bg': '#f6f7f9',            # app / content background (light gray)
    '--bg-elevated': '#ffffff',  # cards
    '--surface': '#ffffff',      # panels / canvases
    '--surface-2': '#eef0f2',    # hover surface
    '--border': 'rgba(15,23,42,.10)',
    '--border-strong': 'rgba(15,23,42,.17)',
    '--text': '#1a1f36',
    '--text-secondary': '#5b6270',
    '--text-muted': '#8b93a0',
    # accents (--accent/--success/--warning/--error) intentionally unchanged
}
# Hardcoded arbitrary-class scale, kept consistent with the variables above.
_NEUTRAL = {
    '#08090a': '#f6f7f9',  # app / content background
    '#0a0b0d': '#ffffff',  # sidebar
    '#0c0d0f': '#ffffff',
    '#0d0e10': '#ffffff',  # cards / surfaces
    '#0f1012': '#ffffff',
    '#131316': '#ffffff',  # surface
    '#18181b': '#eef0f2',  # surface-2 (hover)
    '#3f4147': '#ccd1d7',  # mid gray (toggle tracks, dividers)
    '#f7f8f8': '#1a1f36',  # primary text / headings  (brightest -> darkest)
    '#c5c8cd': '#2f3646',
    '#a3a8b3': '#4b5563',
    '#8a8f98': '#5b6270',
    '#62666d': '#8b93a0',  # dimmest gray
}
_PROP = {
    'bg': 'background-color', 'text': 'color', 'border': 'border-color',
    'ring': '--tw-ring-color', 'fill': 'fill', 'stroke': 'stroke',
}

def _esc(cls):
    return re.sub(r'([\[\]#./])', r'\\\1', cls)

_theme_rules = []
# 1) variable overrides
_theme_rules.append('html.rr-light{' + ''.join('{}:{};'.format(k, v) for k, v in _VARS_LIGHT.items()) + '}')
# 2) grid-bg lines flip white->black so they stay visible on light surfaces
_theme_rules.append('html.rr-light .grid-bg{background-image:linear-gradient(rgba(15,23,42,.035) 1px,transparent 0),linear-gradient(90deg,rgba(15,23,42,.035) 1px,transparent 0)}')
# 2b) Live Recovery Pipeline canvas paints a dark gradient via a React inline
# style; override it by its unique class hook.
_theme_rules.append('html.rr-light .min-h-\\[230px\\]{background:linear-gradient(#ffffff,#f6f7f9)!important}')
# 2c) .btn-secondary:hover hardcodes a dark fill (#1f1f23); on light its text
# (var(--text), already dark) becomes unreadable. Give it a light hover fill.
_theme_rules.append('html.rr-light .btn-secondary:hover{background:#e9ebef!important}')
# 2d) Recovery Simulation's "Error type" <select> relies on the browser's
# native chevron, which sits inconsistently close to the edge depending on
# platform. Force a custom, precisely centred chevron in both themes.
_theme_rules.append(
    'select.rounded-md.px-3{appearance:none;-webkit-appearance:none;'
    'background-image:url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'14\' height=\'14\' viewBox=\'0 0 24 24\' fill=\'none\' stroke=\'%238a8f98\' stroke-width=\'2\'%3E%3Cpolyline points=\'6 9 12 15 18 9\'/%3E%3C/svg%3E");'
    'background-repeat:no-repeat;background-position:right 10px center;padding-right:30px!important;height:38px!important;box-sizing:border-box!important}'
)
# 3) hardcoded arbitrary color classes
for _prefix, _cssprop in _PROP.items():
    for _dark, _light in _NEUTRAL.items():
        _cls = '{}-[{}]'.format(_prefix, _dark)
        if _cls in html:
            _theme_rules.append('html.rr-light .{}{{{}:{}!important}}'.format(_esc(_cls), _cssprop, _light))
# Some colours appear cased upper in class names (e.g. #006DF9) — accents, skip.
# 3b) gradient stops (from-[#..]/to-[#..]) for neutral colours — e.g. the dark
# bottom-fade footer on the Recovery Flow card.
for _prefix in ('from', 'to'):
    for _dark, _light in _NEUTRAL.items():
        _cls = '{}-[{}]'.format(_prefix, _dark)
        if _cls in html:
            _theme_rules.append('html.rr-light .{}{{--tw-gradient-{}:{} var(--tw-gradient-{}-position)!important}}'.format(_esc(_cls), _prefix, _light, _prefix))

# White-opacity overlays -> subtle black overlays. Dark-on-light reads stronger,
# so background lifts get a lighter alpha while borders get a touch heavier for
# visibility on white.
for _m in sorted(set(re.findall(r'(?:bg|border|text|ring)-white/\[0?\.[0-9]+\]', html))):
    _kind = _m.split('-')[0]
    _alpha = float(re.search(r'\[([0-9.]+)\]', _m).group(1))
    if _kind == 'border':
        _a, _prop = min(0.14, _alpha * 1.6 + 0.02), 'border-color'
    elif _kind == 'bg':
        _a, _prop = _alpha * 0.85, 'background-color'
    else:
        _a, _prop = _alpha, 'color'
    _theme_rules.append('html.rr-light .{}{{{}:rgba(0,0,0,{:.3f})!important}}'.format(_esc(_m), _prop, _a))

# body background flip + colour-scheme hint for form controls/scrollbars
_theme_rules.append('html.rr-light body{background:#ffffff;color-scheme:light}')

_THEME_CSS = '<style id="rr-theme-light">' + ''.join(_theme_rules) + '</style>'
# Apply the persisted theme before first paint to avoid a flash.
_THEME_BOOT = '<script>try{if(localStorage.getItem("rrTheme")!=="dark")document.documentElement.classList.add("rr-light")}catch(e){}</script>'
html = html.replace('</head>', _THEME_CSS + _THEME_BOOT + '</head>', 1)

# Write the built page to BOTH names:
#  - recovery-demo.html: kept for the local preview server / direct links
#  - index.html: what the static host (Vercel) serves at "/", so the deployed
#    site gets our enhanced page with no rewrite needed
for name in ('recovery-demo.html', 'index.html'):
    out = os.path.join(ROOT, name)
    with open(out, 'w', encoding='utf-8') as f:
        f.write(html)

size_kb = os.path.getsize(os.path.join(ROOT, 'recovery-demo.html')) / 1024
print(f"✓  recovery-demo.html + index.html  ({size_kb:.0f} KB)")

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

with open(os.path.join(ROOT, 'index.html'), encoding='utf-8') as f:
    html = f.read()

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

out = os.path.join(ROOT, 'recovery-demo.html')
with open(out, 'w', encoding='utf-8') as f:
    f.write(html)

size_kb = os.path.getsize(out) / 1024
print(f"✓  recovery-demo.html  ({size_kb:.0f} KB)")

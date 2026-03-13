#!/usr/bin/env python3
"""Render daily report Markdown to a modern responsive HTML page."""

import datetime
import os
import sys

import markdown

# --- 1. Setup ---
if len(sys.argv) > 1:
    date = sys.argv[1]
    date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
else:
    date_obj = datetime.date.today()
    date = date_obj.strftime("%Y-%m-%d")

date_display = date_obj.strftime("%Y年%m月%d日")
report_path = f"reports/daily_briefings/Morning_Report_{date}.md"

try:
    with open(report_path, encoding="utf-8") as f:
        content = f.read()
except FileNotFoundError:
    print(f"Report not found: {report_path}", file=sys.stderr)
    sys.exit(1)

html_body = markdown.markdown(content, extensions=["tables", "fenced_code"])

# Determine if this is an archive page (not today)
today = datetime.date.today().strftime("%Y-%m-%d")
is_archive = date != today
archive_base = "archive" if not is_archive else ".."
back_link_html = ""
if is_archive:
    back_link_html = '<a class="btn btn-outline-light btn-sm" href="../index.html">返回今日</a>'

# --- 2. HTML Template ---
page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DailyPulse · {date_display}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
<script>const ARCHIVE_BASE = "{archive_base}";</script>
<style>
  :root {{
    --dp-bg: #eef2f7;
    --dp-card: #ffffff;
    --dp-text: #1f2937;
    --dp-muted: #6b7280;
    --dp-accent: #2563eb;
    --dp-border: #e5e7eb;
    --dp-hero: linear-gradient(135deg, #111827 0%, #1f3b8a 52%, #2563eb 100%);
    --dp-serif: "Noto Serif SC", serif;
    --dp-sans: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  }}

  @media (prefers-color-scheme: dark) {{
    :root {{
      --dp-bg: #0f172a;
      --dp-card: #111827;
      --dp-text: #f3f4f6;
      --dp-muted: #94a3b8;
      --dp-accent: #60a5fa;
      --dp-border: #334155;
      --dp-hero: linear-gradient(135deg, #020617 0%, #0f172a 48%, #1d4ed8 100%);
    }}
  }}

  body {{
    font-family: var(--dp-sans);
    background: radial-gradient(circle at top right, rgba(37,99,235,0.08), transparent 40%), var(--dp-bg);
    color: var(--dp-text);
    min-height: 100vh;
  }}

  .hero {{
    background: var(--dp-hero);
    color: #fff;
    padding: 2.25rem 0 1.75rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }}

  .hero-brand {{
    letter-spacing: 0.14em;
    text-transform: uppercase;
    opacity: 0.8;
    font-size: 0.72rem;
    font-weight: 600;
  }}

  .hero-title {{
    margin-top: 0.5rem;
    font-family: var(--dp-serif);
    font-size: clamp(1.75rem, 3.8vw, 2.5rem);
    font-weight: 700;
    line-height: 1.25;
  }}

  .hero-meta {{
    margin-top: 0.95rem;
    display: flex;
    gap: 0.55rem;
    flex-wrap: wrap;
    align-items: center;
  }}

  .hero-chip {{
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    border-radius: 999px;
    padding: 0.34rem 0.8rem;
    background: rgba(255,255,255,0.14);
    border: 1px solid rgba(255,255,255,0.22);
    font-size: 0.84rem;
  }}

  .app-wrap {{
    margin-top: 1.1rem;
    margin-bottom: 2.2rem;
  }}

  .panel {{
    background: var(--dp-card);
    border: 1px solid var(--dp-border);
    border-radius: 14px;
    box-shadow: 0 10px 28px rgba(2, 6, 23, 0.04);
  }}

  .sidebar-panel {{
    position: sticky;
    top: 1rem;
  }}

  .sidebar-title {{
    font-size: 0.74rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--dp-muted);
    font-weight: 700;
  }}

  .nav-item-link {{
    border: 0;
    border-left: 3px solid transparent;
    border-radius: 0.5rem;
    color: var(--dp-muted);
    transition: all .15s ease;
    font-size: 0.93rem;
  }}

  .nav-item-link:hover {{
    background: color-mix(in srgb, var(--dp-accent) 8%, transparent);
    color: var(--dp-text);
  }}

  .nav-item-link.active {{
    border-left-color: var(--dp-accent);
    color: var(--dp-text);
    background: color-mix(in srgb, var(--dp-accent) 12%, transparent);
    font-weight: 600;
  }}

  .section {{
    margin-bottom: 2rem;
    scroll-margin-top: 1rem;
  }}

  .section-head {{
    font-family: var(--dp-serif);
    font-size: clamp(1.18rem, 2.2vw, 1.58rem);
    margin-bottom: 1rem;
    padding-bottom: 0.7rem;
    border-bottom: 2px solid var(--dp-border);
  }}

  .summary-card {{
    border-radius: 12px;
    border-left: 4px solid var(--dp-accent);
    background: linear-gradient(135deg, color-mix(in srgb, var(--dp-accent) 10%, transparent), color-mix(in srgb, #22c55e 10%, transparent));
    color: var(--dp-text);
  }}

  .article-card {{
    border-radius: 12px;
    border: 1px solid var(--dp-border);
    background: var(--dp-card);
    margin-bottom: 1rem;
    transition: transform .15s ease, box-shadow .15s ease;
  }}

  .article-card:hover {{
    transform: translateY(-2px);
    box-shadow: 0 12px 24px rgba(2, 6, 23, 0.08);
  }}

  .article-title a {{
    color: inherit;
    text-decoration: none;
  }}

  .article-title a:hover {{
    color: var(--dp-accent);
  }}

  .meta-row {{ display: flex; flex-wrap: wrap; align-items: center; gap: 0.4rem; margin-bottom: 0.15rem; }}
  .meta-source {{ font-size: 0.82rem; font-weight: 600; color: var(--dp-text); }}
  .meta-badge {{
    display: inline-flex; align-items: center;
    border-radius: 999px; padding: 0.1rem 0.5rem;
    font-size: 0.72rem; font-weight: 600;
    background: color-mix(in srgb, var(--dp-accent) 15%, transparent);
    color: var(--dp-accent); border: 1px solid color-mix(in srgb, var(--dp-accent) 30%, transparent);
  }}
  .meta-secondary {{ font-size: 0.76rem; color: var(--dp-muted); }}

  .article-quote {{
    border-left: 3px solid var(--dp-accent);
    padding-left: 0.8rem;
    color: var(--dp-text);
    margin-top: 0.5rem;
  }}

  .article-summary {{
    color: var(--dp-muted);
  }}

  .mobile-nav-btn {{
    border-color: rgba(255,255,255,0.28);
    color: #fff;
  }}

  .mobile-nav-btn:hover {{
    background: rgba(255,255,255,0.15);
    color: #fff;
  }}

  .quick-nav-fab {{
    position: fixed;
    right: 1rem;
    bottom: calc(1rem + env(safe-area-inset-bottom, 0px));
    z-index: 1085;
    border-radius: 999px;
    box-shadow: 0 12px 24px rgba(2, 6, 23, 0.28);
    border: 1px solid rgba(255,255,255,0.2);
    background: color-mix(in srgb, var(--dp-accent) 88%, #111827 12%);
    color: #fff;
    font-weight: 600;
    letter-spacing: 0.01em;
    padding: 0.5rem 0.85rem;
  }}

  .quick-nav-fab:hover {{
    color: #fff;
    background: color-mix(in srgb, var(--dp-accent) 78%, #111827 22%);
  }}

  .history-menu-scroll {{
    max-height: 300px;
    overflow-y: auto;
  }}

  @media (max-width: 991.98px) {{
    .app-wrap {{ margin-top: 0.85rem; }}
    .hero {{ padding: 1.5rem 0 1.1rem; }}
    body {{ padding-bottom: 4.5rem; }}
    .quick-nav-fab {{ display: inline-flex; align-items: center; gap: 0.35rem; }}
  }}

  @media (min-width: 992px) {{
    .quick-nav-fab {{ display: none; }}
  }}
</style>
</head>
<body>

<header class="hero">
  <div class="container-xxl">
    <div class="hero-brand">DailyPulse</div>
    <h1 class="hero-title">🌍 国际时事日报</h1>
    <div class="hero-meta">
      <span class="hero-chip">📅 {date_display}</span>
      {back_link_html}
      <div class="dropdown">
        <button class="btn btn-sm btn-outline-light dropdown-toggle" type="button" id="history-btn" data-bs-toggle="dropdown" data-bs-auto-close="outside" aria-expanded="false">📂 历史</button>
        <ul class="dropdown-menu history-menu-scroll" id="history-menu" aria-labelledby="history-btn">
          <li><span class="dropdown-item-text text-muted">加载中...</span></li>
        </ul>
      </div>
      <button class="btn btn-sm mobile-nav-btn d-lg-none" type="button" data-bs-toggle="offcanvas" data-bs-target="#sectionNavCanvas" aria-controls="sectionNavCanvas">☰ 板块导航</button>
    </div>
  </div>
</header>

<div class="offcanvas offcanvas-start" tabindex="-1" id="sectionNavCanvas" aria-labelledby="sectionNavCanvasLabel">
  <div class="offcanvas-header">
    <h5 class="offcanvas-title" id="sectionNavCanvasLabel">板块导航</h5>
    <button type="button" class="btn-close" data-bs-dismiss="offcanvas" aria-label="Close"></button>
  </div>
  <div class="offcanvas-body">
    <div class="list-group list-group-flush" id="mobile-nav"></div>
  </div>
</div>

<div class="container-xxl app-wrap">
  <div class="row g-3 g-lg-4">
    <aside class="col-lg-3 d-none d-lg-block">
      <div class="panel sidebar-panel p-3" id="desktop-sidebar">
        <div class="sidebar-title px-2 pb-2">Sections</div>
        <div class="list-group list-group-flush" id="desktop-nav"></div>
      </div>
    </aside>
    <main class="col-12 col-lg-9">
      <div id="main-content"></div>
    </main>
  </div>
</div>

<footer class="container-xxl pb-4 text-center text-secondary small">
  Generated by DailyPulse AI · {date}
</footer>

<button class="btn quick-nav-fab d-lg-none" type="button" data-bs-toggle="offcanvas" data-bs-target="#sectionNavCanvas" aria-controls="sectionNavCanvas" aria-label="打开板块导航">
  ☰ 目录
</button>

<div id="raw-content" style="display:none">{html_body}</div>

<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js" integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz" crossorigin="anonymous"></script>
<script>
(function () {{
  const historyMenu = document.getElementById('history-menu');
  fetch(ARCHIVE_BASE + '/index.json')
    .then((res) => res.json())
    .then((dates) => {{
      historyMenu.innerHTML = '';
      if (!Array.isArray(dates) || dates.length === 0) {{
        historyMenu.innerHTML = '<li><span class="dropdown-item-text text-muted">暂无历史</span></li>';
        return;
      }}
      dates.forEach((d) => {{
        const li = document.createElement('li');
        const a = document.createElement('a');
        a.className = 'dropdown-item';
        a.href = ARCHIVE_BASE + '/' + d + '.html';
        a.textContent = d;
        li.appendChild(a);
        historyMenu.appendChild(li);
      }});
    }})
    .catch(() => {{
      historyMenu.innerHTML = '<li><span class="dropdown-item-text text-danger">加载失败</span></li>';
    }});

  const raw = document.getElementById('raw-content');
  const nodes = Array.from(raw.children);
  const sections = [];
  let currentSection = null;

  for (const node of nodes) {{
    if (node.tagName === 'H2') {{
      currentSection = {{ title: node.innerHTML, leadNodes: [], articles: [] }};
      sections.push(currentSection);
      continue;
    }}

    if (!currentSection) {{
      continue;
    }}

    if (node.tagName === 'H3') {{
      currentSection.articles.push({{ titleNode: node, nodes: [] }});
      continue;
    }}

    if (currentSection.articles.length === 0) {{
      currentSection.leadNodes.push(node);
    }} else {{
      currentSection.articles[currentSection.articles.length - 1].nodes.push(node);
    }}
  }}

  const desktopNav = document.getElementById('desktop-nav');
  const mobileNav = document.getElementById('mobile-nav');
  const main = document.getElementById('main-content');
  const navCanvasEl = document.getElementById('sectionNavCanvas');
  const navCanvas = navCanvasEl ? bootstrap.Offcanvas.getOrCreateInstance(navCanvasEl) : null;

  const labelMap = {{
    '🏛': '政治外交',
    '💹': '经济金融',
    '⚔': '军事安全',
    '🌱': '社会人文',
    '🌏': '亚洲焦点',
    '📖': '深度分析',
    '🧪': '质量指标'
  }};

  function shortLabel(title) {{
    for (const [emoji, text] of Object.entries(labelMap)) {{
      if (title.includes(emoji)) return emoji + ' ' + text;
    }}
    return title.replace(/<[^>]+>/g, '').trim().slice(0, 12);
  }}

  function scrollToTarget(targetId) {{
    const section = document.getElementById(targetId);
    if (!section) return;
    section.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }}

  function createNavLink(targetId, title, mobile) {{
    const a = document.createElement('a');
    a.href = '#' + targetId;
    a.className = mobile ? 'list-group-item list-group-item-action nav-item-link' : 'list-group-item list-group-item-action nav-item-link';
    a.textContent = shortLabel(title);
    a.dataset.target = targetId;
    a.addEventListener('click', (e) => {{
      e.preventDefault();
      if (mobile && navCanvasEl && navCanvas && navCanvasEl.classList.contains('show')) {{
        const onHidden = () => {{
          setTimeout(() => scrollToTarget(targetId), 30);
        }};
        navCanvasEl.addEventListener('hidden.bs.offcanvas', onHidden, {{ once: true }});
        navCanvas.hide();
        return;
      }}
      scrollToTarget(targetId);
    }});
    return a;
  }}

  sections.forEach((sec, idx) => {{
    const sectionId = 'sec-' + idx;

    const section = document.createElement('section');
    section.className = 'section';
    section.id = sectionId;

    const heading = document.createElement('h2');
    heading.className = 'section-head';
    heading.innerHTML = sec.title;
    section.appendChild(heading);

    if (sec.leadNodes.length > 0) {{
      const summaryCard = document.createElement('div');
      summaryCard.className = 'summary-card panel p-3 mb-3';
      sec.leadNodes.forEach((node) => {{
        const p = document.createElement('div');
        p.className = 'mb-2';
        p.innerHTML = node.innerHTML;
        summaryCard.appendChild(p);
      }});
      section.appendChild(summaryCard);
    }}

    if (sec.articles.length === 0 && sec.leadNodes.length === 0) {{
      const empty = document.createElement('div');
      empty.className = 'panel p-3 text-secondary';
      empty.textContent = '暂无数据';
      section.appendChild(empty);
    }}

    sec.articles.forEach((art) => {{
      const card = document.createElement('article');
      card.className = 'article-card p-3 p-md-4';

      const titleRow = document.createElement('div');
      titleRow.className = 'd-flex align-items-start justify-content-between gap-2';

      const title = document.createElement('h3');
      title.className = 'h5 mb-2 article-title';
      title.innerHTML = art.titleNode.innerHTML;

      const shareBtn = document.createElement('button');
      shareBtn.className = 'btn btn-sm btn-outline-secondary';
      shareBtn.textContent = '分享';

      titleRow.appendChild(title);
      titleRow.appendChild(shareBtn);
      card.appendChild(titleRow);

      let metaAdded = false;
      let firstSummary = '';

      art.nodes.forEach((node) => {{
        const text = (node.textContent || '').trim();

        if (node.tagName === 'P' && text.startsWith('📰')) {{
          const parts = text.split('|').map(s => s.trim()).filter(Boolean);
          let source = '', date = '', count = '', trend = '';
          parts.forEach(p => {{
            if (p.startsWith('📰')) source = p.replace('📰', '').trim();
            else if (p.startsWith('📅')) date = p.replace('📅', '').trim();
            else if (p.startsWith('🔁')) count = p.replace('🔁', '').trim();
            else if (p.startsWith('🆕') || p.includes('新出现') || p.includes('持续') || p.includes('热度')) trend = p;
          }});

          const row1 = document.createElement('div');
          row1.className = 'meta-row';
          if (source) {{
            const s = document.createElement('span');
            s.className = 'meta-source';
            s.textContent = source;
            row1.appendChild(s);
          }}
          if (trend) {{
            const b = document.createElement('span');
            b.className = 'meta-badge';
            b.textContent = trend;
            row1.appendChild(b);
          }}

          const row2 = document.createElement('div');
          row2.className = 'meta-row';
          const secondary = [date, count].filter(Boolean).join(' · ');
          if (secondary) {{
            const s = document.createElement('span');
            s.className = 'meta-secondary';
            s.textContent = secondary;
            row2.appendChild(s);
          }}

          const wrap = document.createElement('div');
          wrap.className = 'mb-2';
          wrap.appendChild(row1);
          if (secondary) wrap.appendChild(row2);
          card.appendChild(wrap);
          metaAdded = true;
          return;
        }}

        if (node.tagName === 'BLOCKQUOTE') {{
          const q = document.createElement('div');
          q.className = 'article-quote';
          q.innerHTML = node.innerHTML;
          card.appendChild(q);
          if (!firstSummary) firstSummary = text;
          return;
        }}

        if (node.tagName === 'P') {{
          const p = document.createElement('p');
          p.className = 'article-summary mb-2';
          p.innerHTML = node.innerHTML;
          card.appendChild(p);
          if (!firstSummary) firstSummary = text;
          return;
        }}

        const generic = document.createElement('div');
        generic.className = 'article-summary mb-2';
        generic.innerHTML = node.outerHTML;
        card.appendChild(generic);
      }});

      if (!metaAdded) {{
        const fallbackMeta = document.createElement('div');
        fallbackMeta.className = 'meta-row mb-2';
        const s = document.createElement('span');
        s.className = 'meta-source';
        s.textContent = '📰 元信息缺失';
        fallbackMeta.appendChild(s);
        card.appendChild(fallbackMeta);
      }}

      shareBtn.addEventListener('click', async () => {{
        const titleText = title.textContent.trim();
        const articleLink = title.querySelector('a');
        const articleUrl = articleLink ? articleLink.href : '';
        const pageUrl = window.location.href.split('#')[0];
        const shareUrl = articleUrl || pageUrl;
        const shareText = [
          `【${{titleText}}】`,
          firstSummary || '',
          `链接：${{shareUrl}}`
        ].filter(Boolean).join('\\n');

        try {{
          if (navigator.share) {{
            await navigator.share({{ title: titleText, text: shareText, url: shareUrl }});
          }} else {{
            await navigator.clipboard.writeText(shareText);
          }}
          shareBtn.textContent = '已复制';
          setTimeout(() => {{ shareBtn.textContent = '分享'; }}, 1200);
        }} catch (_) {{}}
      }});

      section.appendChild(card);
    }});

    main.appendChild(section);
    desktopNav.appendChild(createNavLink(sectionId, sec.title, false));
    mobileNav.appendChild(createNavLink(sectionId, sec.title, true));
  }});

  const desktopLinks = Array.from(desktopNav.querySelectorAll('.nav-item-link'));
  const sectionEls = Array.from(document.querySelectorAll('.section'));

  if (sectionEls.length > 0 && desktopLinks.length > 0) {{
    desktopLinks[0].classList.add('active');
    const observer = new IntersectionObserver((entries) => {{
      entries.forEach((entry) => {{
        if (!entry.isIntersecting) return;
        desktopLinks.forEach((l) => l.classList.remove('active'));
        const target = desktopLinks.find((l) => l.dataset.target === entry.target.id);
        if (target) target.classList.add('active');
      }});
    }}, {{ rootMargin: '-20% 0px -70% 0px', threshold: 0.02 }});

    sectionEls.forEach((el) => observer.observe(el));
  }}
}})();
</script>
</body>
</html>"""

# --- 3. Write output files ---
os.makedirs("archive", exist_ok=True)

with open("index.html", "w", encoding="utf-8") as f:
    f.write(page)

archive_path = f"archive/{date}.html"
with open(archive_path, "w", encoding="utf-8") as f:
    f.write(page)

print(f"Generated index.html and {archive_path} for {date}")

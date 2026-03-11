#!/usr/bin/env python3
"""Convert daily report Markdown to a fancy HTML page with Tab-based mobile UX."""
import sys
import os
import datetime
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
is_archive = (date != today)

# Back-to-today link for archive pages
back_link_html = ''
if is_archive:
    back_link_html = '<a href="../index.html" class="back-link">← 返回今日</a>'

# archive_base: relative path prefix for archive links
archive_base = "archive" if not is_archive else ".."

# --- 2. Enhanced HTML Template ---
page = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<title>DailyPulse \xb7 {date_display}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@500;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<script>const ARCHIVE_BASE = "{archive_base}";</script>

<style>
  :root {{
    --bg-body: #F3F4F6;
    --bg-card: #FFFFFF;
    --text-primary: #1F2937;
    --text-summary: #4B5563;
    --text-meta: #6B7280;
    --accent: #2563EB;
    --border-color: #E5E7EB;
    --header-bg: #1e1b4b;
    --header-gradient: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
    --shadow-card: 0 1px 3px 0 rgba(0, 0, 0, 0.1);
    --shadow-hover: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    --font-serif: "Noto Serif SC", serif;
    --font-sans: "Inter", -apple-system, sans-serif;
  }}

  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg-body: #111827;
      --bg-card: #1F2937;
      --text-primary: #F9FAFB;
      --text-summary: #9CA3AF;
      --text-meta: #9CA3AF;
      --accent: #60A5FA;
      --border-color: #374151;
      --header-bg: #0f172a;
      --header-gradient: linear-gradient(to right, #0f172a, #1e293b);
      --shadow-card: none;
      --shadow-hover: 0 0 0 1px var(--accent);
    }}
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; -webkit-tap-highlight-color: transparent; }}

  body {{
    background: var(--bg-body);
    color: var(--text-primary);
    font-family: var(--font-sans);
    line-height: 1.6;
    font-size: 15px;
    padding-bottom: 40px;
  }}

  /* --- Header --- */
  .site-header {{
    background: var(--header-gradient);
    color: #fff;
    padding: 2.5rem 1rem 5rem;
    text-align: center;
    clip-path: ellipse(120% 100% at 50% 0%);
    margin-bottom: 0;
  }}
  .site-header .brand {{
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-bottom: 0.5rem;
  }}
  .site-header h1 {{
    font-family: var(--font-serif);
    font-size: 2.2rem;
    margin-bottom: 0.8rem;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
  }}
  .header-meta {{
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    flex-wrap: wrap;
  }}
  .date-badge {{
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(4px);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    display: inline-block;
  }}
  .back-link {{
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(4px);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    color: #fff;
    text-decoration: none;
    display: inline-block;
    transition: background 0.2s;
  }}
  .back-link:hover {{ background: rgba(255,255,255,0.25); }}

  /* --- History Dropdown --- */
  .history-dropdown {{
    position: relative;
    display: inline-block;
  }}
  .history-btn {{
    background: rgba(255,255,255,0.15);
    backdrop-filter: blur(4px);
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.85rem;
    color: #fff;
    border: none;
    cursor: pointer;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    transition: background 0.2s;
  }}
  .history-btn:hover {{ background: rgba(255,255,255,0.25); }}
  .history-menu {{
    display: none;
    position: absolute;
    top: calc(100% + 6px);
    left: 50%;
    transform: translateX(-50%);
    background: #fff;
    border-radius: 10px;
    box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    min-width: 160px;
    z-index: 200;
    overflow: hidden;
  }}
  .history-menu.open {{ display: block; }}
  .history-menu a {{
    display: block;
    padding: 10px 16px;
    color: #1F2937;
    text-decoration: none;
    font-size: 0.9rem;
    transition: background 0.15s;
  }}
  .history-menu a:hover {{ background: #F3F4F6; }}
  .history-menu .loading {{
    padding: 10px 16px;
    color: #6B7280;
    font-size: 0.85rem;
  }}
  @media (prefers-color-scheme: dark) {{
    .history-menu {{ background: #1F2937; box-shadow: 0 8px 24px rgba(0,0,0,0.4); }}
    .history-menu a {{ color: #F9FAFB; }}
    .history-menu a:hover {{ background: #374151; }}
  }}

  /* --- Layout Wrapper --- */
  .layout-container {{
    max-width: 1000px;
    margin: -50px auto 0;
    padding: 0 20px;
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 30px;
    position: relative;
    z-index: 10;
  }}

  /* --- Sidebar (Desktop) --- */
  .sidebar {{
    position: sticky;
    top: 20px;
    align-self: start;
    background: var(--bg-card);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    border: 1px solid var(--border-color);
  }}
  .sidebar-title {{
    font-size: 0.75rem;
    font-weight: 700;
    color: var(--text-meta);
    margin-bottom: 12px;
    padding-left: 8px;
    text-transform: uppercase;
  }}
  .nav-link {{
    display: flex;
    align-items: center;
    padding: 10px 12px;
    color: var(--text-summary);
    text-decoration: none;
    font-size: 0.95rem;
    border-radius: 8px;
    margin-bottom: 4px;
    transition: background 0.2s, color 0.2s;
    cursor: pointer;
  }}
  .nav-link:hover {{ background: var(--bg-body); color: var(--text-primary); }}
  .layout-container:not(.mobile-mode) .nav-link.active {{
    background: #eff6ff;
    color: var(--accent);
    font-weight: 600;
  }}
  @media (prefers-color-scheme: dark) {{
    .layout-container:not(.mobile-mode) .nav-link.active {{ background: #1e293b; }}
  }}

  /* --- Main Content Area --- */
  #main-content {{
    min-width: 0;
    padding-top: 60px;
  }}
  .section {{
    background: transparent;
    margin-bottom: 50px;
    scroll-margin-top: 20px;
  }}
  .section-header h2 {{
    font-family: var(--font-serif);
    font-size: 1.5rem;
    color: var(--text-primary);
    padding-bottom: 15px;
    margin-bottom: 20px;
    border-bottom: 2px solid var(--border-color);
    line-height: 1.3;
  }}

  /* --- Article Cards --- */
  .article-card {{
    background: var(--bg-card);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
    box-shadow: var(--shadow-card);
    border: 1px solid var(--border-color);
    transition: transform 0.2s;
  }}
  .article-card:hover {{
    transform: translateY(-2px);
    box-shadow: var(--shadow-hover);
    border-color: var(--accent);
  }}
  .article-title {{
    font-family: var(--font-serif);
    font-size: 1.2rem;
    font-weight: 700;
    margin-bottom: 10px;
    line-height: 1.4;
    color: var(--text-primary);
  }}
  .article-title a {{ text-decoration: none; color: inherit; }}
  .article-summary {{
    font-size: 0.95rem;
    color: var(--text-summary);
    margin-bottom: 12px;
    line-height: 1.5;
  }}
  .article-meta {{
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 16px;
    font-size: 0.75rem;
  }}
  .meta-pill {{
    background: var(--bg-body);
    color: var(--text-meta);
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid var(--border-color);
  }}
  .article-content {{
    border-left: 3px solid var(--accent);
    padding-left: 14px;
    margin-top: 12px;
    font-size: 1rem;
    color: var(--text-primary);
    line-height: 1.7;
  }}

  footer {{
    text-align: center;
    font-size: 0.8rem;
    color: var(--text-meta);
    margin-top: 40px;
  }}

  /* --- MOBILE OPTIMIZATION --- */
  @media (max-width: 768px) {{
    .layout-container {{
      display: block;
      margin-top: -30px;
      padding: 0;
    }}
    .site-header {{
        padding-bottom: 4rem;
        clip-path: none;
    }}
    .sidebar {{
        position: sticky;
        top: 0;
        z-index: 100;
        border-radius: 0;
        border: none;
        border-bottom: 1px solid var(--border-color);
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(10px);
        margin: 0;
        padding: 0;
        overflow-x: auto;
        white-space: nowrap;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        -ms-overflow-style: none;
        scrollbar-width: none;
    }}
    @media (prefers-color-scheme: dark) {{
        .sidebar {{ background: rgba(31, 41, 55, 0.98); }}
    }}
    .sidebar::-webkit-scrollbar {{ display: none; }}
    .sidebar-title {{ display: none; }}
    .sidebar nav {{
        display: flex;
        padding: 0 16px;
    }}
    .nav-link {{
        display: inline-block;
        padding: 14px 16px;
        margin: 0;
        font-size: 0.9rem;
        background: transparent !important;
        border-radius: 0;
        color: var(--text-summary);
        border-bottom: 2px solid transparent;
        flex-shrink: 0;
    }}
    .nav-link.active {{
        color: var(--accent) !important;
        border-bottom-color: var(--accent);
        font-weight: 600;
        background: transparent !important;
    }}
    #main-content {{
        padding: 20px 16px;
        background: var(--bg-body);
        min-height: 60vh;
    }}
    .section {{
        display: none;
        animation: fadeIn 0.3s ease;
    }}
    .section.active-tab {{
        display: block;
    }}
    .section-header h2 {{
        font-size: 1.3rem;
        margin-top: 0;
        padding-top: 0;
    }}
    .article-card {{
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }}
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(5px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
  }}
</style>
</head>
<body>

<header class="site-header">
  <div class="brand">DailyPulse</div>
  <h1>\U0001f30d 国际时事日报</h1>
  <div class="header-meta">
    <div class="date-badge">\U0001f4c5 {date_display}</div>
    {back_link_html}
    <div class="history-dropdown">
      <button class="history-btn" id="history-btn">\U0001f4c2 历史 \u25be</button>
      <div class="history-menu" id="history-menu">
        <div class="loading">加载中...</div>
      </div>
    </div>
  </div>
</header>

<div class="layout-container" id="layout-container">
  <aside class="sidebar">
    <div class="sidebar-title">板块导航</div>
    <nav id="sidebar-nav"></nav>
  </aside>

  <main id="main-content"></main>
</div>

<footer>
  Generated by DailyPulse AI \xb7 {date}
</footer>

<div id="raw-content" style="display:none">{html_body}</div>

<script>
(function() {{
  // --- History Dropdown ---
  const histBtn = document.getElementById('history-btn');
  const histMenu = document.getElementById('history-menu');
  let histLoaded = false;

  histBtn.addEventListener('click', function(e) {{
    e.stopPropagation();
    histMenu.classList.toggle('open');
    if (histMenu.classList.contains('open') && !histLoaded) {{
      histLoaded = true;
      fetch(ARCHIVE_BASE + '/index.json')
        .then(r => r.json())
        .then(dates => {{
          histMenu.innerHTML = '';
          if (!dates || dates.length === 0) {{
            histMenu.innerHTML = '<div class="loading">暂无历史</div>';
            return;
          }}
          dates.forEach(d => {{
            const a = document.createElement('a');
            a.href = ARCHIVE_BASE + '/' + d + '.html';
            a.textContent = d;
            histMenu.appendChild(a);
          }});
        }})
        .catch(() => {{
          histMenu.innerHTML = '<div class="loading">加载失败</div>';
        }});
    }}
  }});

  document.addEventListener('click', function() {{
    histMenu.classList.remove('open');
  }});

  // --- Main Content Rendering ---
  const raw = document.getElementById('raw-content');
  const main = document.getElementById('main-content');
  const nav = document.getElementById('sidebar-nav');
  const layout = document.getElementById('layout-container');

  const isMobile = window.innerWidth <= 768;
  if(isMobile) {{
      layout.classList.add('mobile-mode');
  }}

  const labelMap = {{
    '\U0001f3db': '政治外交', '\U0001f4b9': '经济金融', '\u2694': '军事安全',
    '\U0001f331': '社会人文', '\U0001f30f': '亚洲焦点', '\U0001f4d6': '深度分析'
  }};

  function getShortLabel(text) {{
    for (const [emoji, label] of Object.entries(labelMap)) {{
      if (text.includes(emoji)) return emoji + ' ' + label;
    }}
    return text.replace(/<[^>]+>/g, '').trim().slice(0, 8);
  }}

  const nodes = Array.from(raw.childNodes);
  let currentSection = null;
  const sections = [];

  nodes.forEach(node => {{
    if (node.nodeType !== 1) return;
    if (node.tagName === 'H2') {{
      currentSection = {{ title: node.innerHTML, articles: [] }};
      sections.push(currentSection);
    }} else if (node.tagName === 'H3' && currentSection) {{
      currentSection.articles.push({{ title: node, elements: [] }});
    }} else if (currentSection && currentSection.articles.length > 0) {{
      currentSection.articles[currentSection.articles.length - 1].elements.push(node);
    }}
  }});

  sections.forEach((sec, idx) => {{
    const secID = 'sec-' + idx;
    const sectionEl = document.createElement('div');
    sectionEl.className = 'section';
    sectionEl.id = secID;

    const headerEl = document.createElement('div');
    headerEl.className = 'section-header';
    headerEl.innerHTML = `<h2>${{sec.title}}</h2>`;
    sectionEl.appendChild(headerEl);

    sec.articles.forEach(art => {{
      const card = document.createElement('div');
      card.className = 'article-card';

      const titleDiv = document.createElement('div');
      titleDiv.className = 'article-title';
      titleDiv.innerHTML = art.title.innerHTML;
      card.appendChild(titleDiv);

      art.elements.forEach(el => {{
        const text = el.textContent.trim();
        if (el.tagName === 'BLOCKQUOTE') {{
          const contentDiv = document.createElement('div');
          contentDiv.className = 'article-content';
          contentDiv.innerHTML = el.innerHTML;
          card.appendChild(contentDiv);
        }} else if (text.includes('BBC') || text.includes('\U0001f4c5') || text.includes('\U0001f4f0')) {{
          const metaDiv = document.createElement('div');
          metaDiv.className = 'article-meta';
          const parts = text.split('|');
          parts.forEach(p => {{
            const pill = document.createElement('span');
            pill.className = 'meta-pill';
            pill.innerHTML = p.trim();
            metaDiv.appendChild(pill);
          }});
          card.appendChild(metaDiv);
        }} else if (text.length > 0) {{
          const summaryDiv = document.createElement('div');
          summaryDiv.className = 'article-summary';
          summaryDiv.innerHTML = el.innerHTML;
          card.appendChild(summaryDiv);
        }}
      }});
      sectionEl.appendChild(card);
    }});

    main.appendChild(sectionEl);

    const link = document.createElement('a');
    link.href = isMobile ? 'javascript:void(0)' : '#' + secID;
    link.className = 'nav-link';
    link.innerHTML = getShortLabel(sec.title);
    link.dataset.target = secID;

    link.onclick = (e) => {{
        if(isMobile) {{
            e.preventDefault();
            switchTab(secID);
        }} else {{
            e.preventDefault();
            document.getElementById(secID).scrollIntoView({{ behavior: 'smooth' }});
        }}
    }};
    nav.appendChild(link);
  }});

  const navLinks = Array.from(document.querySelectorAll('.nav-link'));
  const sectionEls = Array.from(document.querySelectorAll('.section'));

  function switchTab(targetId) {{
      navLinks.forEach(l => l.classList.remove('active'));
      const activeLink = navLinks.find(l => l.dataset.target === targetId);
      if(activeLink) {{
          activeLink.classList.add('active');
          activeLink.scrollIntoView({{ behavior: 'smooth', block: 'nearest', inline: 'center' }});
      }}
      sectionEls.forEach(el => {{
          if (el.id === targetId) {{
              el.classList.add('active-tab');
          }} else {{
              el.classList.remove('active-tab');
          }}
      }});
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
  }}

  if (isMobile) {{
      if(sectionEls.length > 0) {{
          switchTab(sectionEls[0].id);
      }}
  }} else {{
      const observer = new IntersectionObserver((entries) => {{
        entries.forEach(entry => {{
          if (entry.isIntersecting) {{
            navLinks.forEach(l => l.classList.remove('active'));
            const activeLink = navLinks.find(l => l.dataset.target === entry.target.id);
            if (activeLink) activeLink.classList.add('active');
          }}
        }});
      }}, {{ rootMargin: '-10% 0px -80% 0px' }});
      sectionEls.forEach(el => observer.observe(el));
      if(navLinks.length > 0) navLinks[0].classList.add('active');
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

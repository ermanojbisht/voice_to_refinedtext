"""Manual & Help Service — Single-Source-of-Truth Documentation Engine.

Parses docs/CONFIGURATION_GUIDE.md into structured chapters, generates styled
standalone HTML with Catppuccin dark theme, and provides programmatic access
for in-app CustomTkinter and browser viewing.
"""
import os
import re
import time
import webbrowser
from typing import Dict, List, Optional, Tuple
import markdown


# Chapter Icons matching the 9 sections of docs/CONFIGURATION_GUIDE.md
CHAPTER_ICONS = {
    1: "🚀",  # Quick-Start Presets
    2: "⚙️",  # Voice Refiner Reference
    3: "🌙",  # Evening Review Reference
    4: "💡",  # Audio to Ideas Reference
    5: "🏛",  # PWD Helper & CLI
    6: "🎨",  # Visuals & Tray Icons
    7: "🔧",  # How to Adjust Settings
    8: "🛠",  # Tuning & Optimization
    9: "⚡",  # Best Practice Matrix
}

DEFAULT_ICON = "📖"


class ManualService:
    """Manages parsing, caching, and HTML compilation of docs/CONFIGURATION_GUIDE.md."""

    def __init__(self, script_dir: Optional[str] = None):
        if script_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
        self.script_dir = script_dir
        self.doc_path = os.path.join(self.script_dir, "docs", "CONFIGURATION_GUIDE.md")
        self.output_dir = os.path.join(self.script_dir, "docs", "generated")
        self.html_path = os.path.join(self.output_dir, "manual.html")

        self._cached_mtime: float = 0.0
        self._cached_chapters: List[Dict] = []
        self._cached_raw_md: str = ""

    def get_source_mtime(self) -> float:
        """Returns the last modification time of CONFIGURATION_GUIDE.md."""
        if os.path.isfile(self.doc_path):
            return os.path.getmtime(self.doc_path)
        return 0.0

    def load_markdown(self, force: bool = False) -> str:
        """Loads raw markdown from CONFIGURATION_GUIDE.md, reloading if modified."""
        current_mtime = self.get_source_mtime()
        if not force and self._cached_raw_md and current_mtime == self._cached_mtime:
            return self._cached_raw_md

        if not os.path.isfile(self.doc_path):
            return "# Manual Not Found\n\nPlease ensure `docs/CONFIGURATION_GUIDE.md` exists."

        with open(self.doc_path, "r", encoding="utf-8") as f:
            self._cached_raw_md = f.read()
        self._cached_mtime = current_mtime
        self._cached_chapters = []  # Invalidate parsed cache
        return self._cached_raw_md

    def get_chapters(self, force: bool = False) -> List[Dict]:
        """Parses markdown into structured chapter dictionaries:
        [
            {
                "id": 1,
                "title": "Quick-Start Hardware Presets",
                "icon": "🚀",
                "markdown": "...",
                "sections": [{"title": "...", "markdown": "..."}]
            },
            ...
        ]
        """
        raw_md = self.load_markdown(force=force)
        if self._cached_chapters and not force:
            return self._cached_chapters

        # Split on top-level section headings: ## N. Title
        pattern = re.compile(r"^##\s+(\d+)\.\s+(.+)$", re.MULTILINE)
        matches = list(pattern.finditer(raw_md))

        chapters = []
        for i, match in enumerate(matches):
            chapter_num = int(match.group(1))
            chapter_title = match.group(2).strip()
            start_pos = match.start()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(raw_md)

            chapter_content = raw_md[start_pos:end_pos].strip()

            # Parse sub-sections (### N.M Subtitle)
            sub_pattern = re.compile(r"^###\s+(.+)$", re.MULTILINE)
            sub_matches = list(sub_pattern.finditer(chapter_content))
            subsections = []
            for j, sub in enumerate(sub_matches):
                sub_title = sub.group(1).strip()
                sub_start = sub.start()
                sub_end = sub_matches[j + 1].start() if j + 1 < len(sub_matches) else len(chapter_content)
                subsections.append({
                    "title": sub_title,
                    "markdown": chapter_content[sub_start:sub_end].strip()
                })

            chapters.append({
                "id": chapter_num,
                "title": chapter_title,
                "icon": CHAPTER_ICONS.get(chapter_num, DEFAULT_ICON),
                "markdown": chapter_content,
                "subsections": subsections
            })

        self._cached_chapters = chapters
        return chapters

    def search_manual(self, query: str) -> List[Dict]:
        """Performs case-insensitive keyword search across all chapters."""
        query = query.strip().lower()
        if not query:
            return self.get_chapters()

        results = []
        for ch in self.get_chapters():
            if query in ch["title"].lower() or query in ch["markdown"].lower():
                # Count occurrences for basic relevance
                score = ch["title"].lower().count(query) * 3 + ch["markdown"].lower().count(query)
                results.append({**ch, "score": score})

        results.sort(key=lambda x: x["score"], reverse=True)
        return results

    def convert_markdown_to_html(self, md_content: str) -> str:
        """Converts Markdown snippet to HTML with tables, code highlighting, and callouts."""
        # Convert GitHub callouts: > [!NOTE], > [!TIP], > [!IMPORTANT], > [!WARNING]
        callout_map = {
            "NOTE": ("info", "ℹ️ NOTE"),
            "TIP": ("success", "💡 TIP"),
            "IMPORTANT": ("primary", "⚡ IMPORTANT"),
            "WARNING": ("warning", "⚠️ WARNING"),
            "CAUTION": ("danger", "🛑 CAUTION"),
        }
        for tag, (css_class, label) in callout_map.items():
            pattern = re.compile(rf"^>\s*\[!{tag}\]\s*\n((?:>.*\n?)+)", re.MULTILINE)
            def _replace_callout(m):
                lines = [l.lstrip(">").strip() for l in m.group(1).splitlines()]
                body = " ".join(lines)
                return f'<div class="callout callout-{css_class}"><strong>{label}:</strong> {body}</div>\n'
            md_content = pattern.sub(_replace_callout, md_content)

        extensions = [
            "extra",
            "codehilite",
            "tables",
            "toc",
            "fenced_code",
            "sane_lists",
        ]
        html_out = markdown.markdown(md_content, extensions=extensions)
        # Wrap tables in a responsive horizontal-scroll container
        html_out = re.sub(r"(<table>[\s\S]*?</table>)", r'<div class="table-responsive">\n\1\n</div>', html_out)
        return html_out

    def generate_html_manual(self, force: bool = False) -> str:
        """Generates a complete, standalone, styled HTML manual and writes to docs/generated/manual.html."""
        current_mtime = self.get_source_mtime()
        if not force and os.path.isfile(self.html_path) and os.path.getmtime(self.html_path) >= current_mtime:
            return self.html_path

        raw_md = self.load_markdown(force=True)
        chapters = self.get_chapters(force=True)
        os.makedirs(self.output_dir, exist_ok=True)

        # Build Navigation Items
        nav_items_html = []
        content_sections_html = []

        for ch in chapters:
            cid = f"chapter-{ch['id']}"
            nav_items_html.append(
                f'<a href="#{cid}" class="nav-link">'
                f'<span class="nav-icon">{ch["icon"]}</span> '
                f'<span class="nav-text">{ch["id"]}. {ch["title"]}</span>'
                f'</a>'
            )

            ch_html = self.convert_markdown_to_html(ch["markdown"])
            content_sections_html.append(
                f'<section id="{cid}" class="chapter-card">\n'
                f'<div class="chapter-badge">{ch["icon"]} Chapter {ch["id"]}</div>\n'
                f'{ch_html}\n'
                f'</section>'
            )

        full_html = HTML_TEMPLATE.format(
            title="AI Voice Refiner — Comprehensive User Manual",
            nav_links="\n".join(nav_items_html),
            content="\n".join(content_sections_html),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        with open(self.html_path, "w", encoding="utf-8") as f:
            f.write(full_html)

        return self.html_path

    def open_in_browser(self) -> str:
        """Generates the HTML manual and opens it as a standalone application window."""
        path = self.generate_html_manual()
        launcher = os.path.join(self.script_dir, "manual_launcher.py")
        if os.path.isfile(launcher):
            try:
                import subprocess, sys
                subprocess.Popen([sys.executable, launcher], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return path
            except Exception:
                pass
        try:
            import settings_server
            port = settings_server.get_configured_port()
            webbrowser.open(f"http://127.0.0.1:{port}/manual")
        except Exception:
            webbrowser.open(f"file://{os.path.abspath(path)}")
        return path


# Modern Catppuccin Dark Theme HTML Template
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        :root {{
            --bg-base: #1e1e2e;
            --bg-surface: #24273a;
            --bg-card: #2a2e45;
            --bg-sidebar: #181926;
            --border: #363a4f;
            --text-main: #cad3f5;
            --text-subtle: #a5adcb;
            --accent-blue: #8aadf4;
            --accent-teal: #8bd5ca;
            --accent-green: #a6da95;
            --accent-yellow: #eed49f;
            --accent-peach: #f5a97f;
            --accent-red: #ed8796;
            --code-bg: #181926;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            display: flex;
            flex-direction: column;
            height: 100vh;
            overflow: hidden;
        }}
        .suite-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 24px;
            background: rgba(36, 39, 58, 0.95);
            backdrop-filter: blur(16px);
            border-bottom: 1px solid var(--border);
            z-index: 100;
            flex-shrink: 0;
        }}
        .brand {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        .brand-icon {{
            font-size: 24px;
        }}
        .brand-title {{
            font-size: 15px;
            font-weight: 700;
            color: var(--text-main);
        }}
        .brand-sub {{
            font-size: 11px;
            color: var(--text-subtle);
        }}
        .badge-bar {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .badge-btn {{
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            border: 1px solid var(--border);
            background: var(--bg-surface);
            color: var(--text-main);
            transition: all 0.15s ease;
        }}
        .badge-btn:hover {{
            background: var(--bg-card);
            border-color: var(--accent-blue);
            transform: translateY(-1px);
        }}
        .badge-btn.active {{
            background: var(--accent-blue);
            color: #181926;
            border-color: var(--accent-blue);
        }}
        .app-body {{
            display: flex;
            flex: 1;
            height: calc(100vh - 53px);
            overflow: hidden;
        }}
        .in-iframe .suite-header {{
            display: none !important;
        }}
        .in-iframe .app-body {{
            height: 100vh !important;
        }}
        /* Sidebar Navigation */
        #sidebar {{
            width: 320px;
            background-color: var(--bg-sidebar);
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }}
        .sidebar-header {{
            padding: 24px 20px;
            border-bottom: 1px solid var(--border);
        }}
        .sidebar-header h1 {{
            font-size: 1.15rem;
            color: var(--accent-blue);
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .sidebar-header p {{
            font-size: 0.8rem;
            color: var(--text-subtle);
            margin-top: 4px;
        }}
        .search-container {{
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
        }}
        .search-box {{
            width: 100%;
            background-color: var(--bg-surface);
            border: 1px solid var(--border);
            color: var(--text-main);
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 0.85rem;
            outline: none;
        }}
        .search-box:focus {{ border-color: var(--accent-blue); }}
        .nav-list {{
            flex: 1;
            overflow-y: auto;
            padding: 12px 8px;
        }}
        .nav-link {{
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 10px 12px;
            color: var(--text-subtle);
            text-decoration: none;
            border-radius: 8px;
            font-size: 0.88rem;
            margin-bottom: 4px;
            transition: all 0.15s ease;
        }}
        .nav-link:hover {{
            background-color: var(--bg-surface);
            color: var(--text-main);
        }}
        .nav-icon {{ font-size: 1.1rem; }}
        /* Main Content Container */
        #content-wrapper {{
            flex: 1;
            overflow-y: auto;
            padding: 40px 60px;
            scroll-behavior: smooth;
        }}
        .content-container {{
            max-width: 1120px;
            margin: 0 auto;
        }}
        /* Chapter Card Container */
        .chapter-card {{
            background-color: var(--bg-surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 32px 36px;
            margin-bottom: 40px;
            box-shadow: 0 4px 16px rgba(0,0,0,0.2);
        }}
        .chapter-badge {{
            display: inline-block;
            background-color: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--accent-teal);
            font-size: 0.8rem;
            font-weight: 600;
            padding: 4px 10px;
            border-radius: 20px;
            margin-bottom: 16px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        h2 {{
            color: var(--accent-blue);
            font-size: 1.6rem;
            margin-bottom: 16px;
            padding-bottom: 8px;
            border-bottom: 2px solid var(--border);
        }}
        h3 {{
            color: var(--accent-teal);
            font-size: 1.25rem;
            margin: 24px 0 12px 0;
        }}
        h4 {{
            color: var(--accent-peach);
            font-size: 1.05rem;
            margin: 18px 0 8px 0;
        }}
        p, li {{
            color: var(--text-main);
            font-size: 0.95rem;
            line-height: 1.65;
            margin-bottom: 12px;
        }}
        ul, ol {{ margin-left: 24px; margin-bottom: 16px; }}
        /* Tables */
        .table-responsive {{
            overflow-x: auto;
            width: 100%;
            margin: 20px 0;
            border-radius: 8px;
            border: 1px solid var(--border);
            background-color: var(--bg-card);
            box-shadow: 0 2px 8px rgba(0,0,0,0.15);
        }}
        table {{
            min-width: 850px;
            width: 100%;
            border-collapse: collapse;
            margin: 0;
            font-size: 0.9rem;
        }}
        th {{
            background-color: var(--bg-sidebar);
            color: var(--accent-blue);
            padding: 12px 14px;
            text-align: left;
            font-weight: 600;
            border-bottom: 1px solid var(--border);
        }}
        td {{
            padding: 10px 14px;
            border-bottom: 1px solid var(--border);
            color: var(--text-main);
            vertical-align: top;
        }}
        tr:last-child td {{ border-bottom: none; }}
        tr:hover td {{ background-color: rgba(255, 255, 255, 0.02); }}
        /* Code Blocks */
        pre {{
            background-color: var(--code-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 16px;
            overflow-x: auto;
            margin: 16px 0;
            font-family: "JetBrains Mono", Consolas, Monaco, monospace;
            font-size: 0.88rem;
            color: var(--text-main);
        }}
        code {{
            background-color: rgba(255, 255, 255, 0.08);
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 0.88rem;
            color: var(--accent-yellow);
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
            color: inherit;
        }}
        /* Callouts */
        .callout {{
            border-left: 4px solid var(--accent-blue);
            background-color: rgba(138, 173, 244, 0.08);
            padding: 14px 18px;
            border-radius: 0 8px 8px 0;
            margin: 18px 0;
            font-size: 0.92rem;
        }}
        .callout-info {{ border-color: var(--accent-blue); background-color: rgba(138, 173, 244, 0.08); }}
        .callout-success {{ border-color: var(--accent-green); background-color: rgba(166, 218, 149, 0.08); }}
        .callout-warning {{ border-color: var(--accent-peach); background-color: rgba(245, 169, 127, 0.08); }}
        .callout-danger {{ border-color: var(--accent-red); background-color: rgba(237, 135, 150, 0.08); }}
        .footer-note {{
            text-align: center;
            font-size: 0.8rem;
            color: var(--text-subtle);
            padding: 24px 0 40px 0;
        }}
    </style>
</head>
<body>
    <header class="suite-header">
        <div class="brand">
            <span class="brand-icon">📖</span>
            <div>
                <div class="brand-title">AI Voice Refiner</div>
                <div class="brand-sub">Comprehensive Configuration & Operations Manual</div>
            </div>
        </div>
        <div class="badge-bar">
            <button class="badge-btn" onclick="window.location.href='/dashboard'">🎙️ Refiner</button>
            <button class="badge-btn" onclick="window.location.href='/review'">🌙 Evening Review</button>
            <button class="badge-btn" onclick="window.location.href='/pwd-lookup'">🏛️ PWD Terms</button>
            <button class="badge-btn" onclick="window.location.href='/audio-to-idea'">📁 Audio to Ideas</button>
            <button class="badge-btn" onclick="window.location.href='/'">⚙️ Settings</button>
            <button class="badge-btn active" onclick="window.location.href='/manual'">📖 Manual</button>
        </div>
    </header>
    <div class="app-body">
        <div id="sidebar">
            <div class="sidebar-header">
                <h1>📖 User Manual & Guide</h1>
                <p>Voice Refiner & Review Hub</p>
            </div>
            <div class="search-container">
                <input type="text" id="manualSearch" class="search-box" placeholder="🔍 Search manual..." onkeyup="filterManual()">
            </div>
            <nav class="nav-list" id="navList">
                {nav_links}
            </nav>
        </div>
        <div id="content-wrapper">
            <div class="content-container">
                {content}
                <div class="footer-note">
                    Auto-generated from <code>docs/CONFIGURATION_GUIDE.md</code> &bull; Last updated {timestamp}
                </div>
            </div>
        </div>
    </div>
    <script>
        if (window.self !== window.top) {{
            document.body.classList.add('in-iframe');
        }}
        function filterManual() {{
            const input = document.getElementById('manualSearch');
            const filter = input.value.toLowerCase();
            const cards = document.getElementsByClassName('chapter-card');
            const links = document.getElementsByClassName('nav-link');

            for (let i = 0; i < cards.length; i++) {{
                const text = cards[i].innerText.toLowerCase();
                if (text.includes(filter)) {{
                    cards[i].style.display = "";
                    if (links[i]) links[i].style.display = "flex";
                }} else {{
                    cards[i].style.display = "none";
                    if (links[i]) links[i].style.display = "none";
                }}
            }}
        }}
    </script>
</body>
</html>
"""


# Global singleton instance
manual_service = ManualService()


def get_chapters():
    return manual_service.get_chapters()


def get_chapter_summary():
    chs = manual_service.get_chapters()
    return f"Loaded {len(chs)} chapters from CONFIGURATION_GUIDE.md ({[c['title'] for c in chs]})"


def generate_html_manual():
    return manual_service.generate_html_manual()


def open_in_browser():
    return manual_service.open_in_browser()

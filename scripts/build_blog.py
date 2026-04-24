#!/usr/bin/env python3
"""Build static blog posts from Markdown.

Source: docs/blog/*.md
Outputs:
- frontend/posts/<slug>.html
- Blog listing between BLOG_POSTS_START/END in frontend/index.html

No third-party dependencies are required.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BLOG_SOURCE_DIR = ROOT / "docs" / "blog"
POST_OUTPUT_DIR = ROOT / "frontend" / "posts"
INDEX_FILE = ROOT / "frontend" / "index.html"

START_MARKER = "<!-- BLOG_POSTS_START -->"
END_MARKER = "<!-- BLOG_POSTS_END -->"


@dataclass(frozen=True)
class Post:
    title: str
    description: str
    date: str
    read_time: str
    tags: list[str]
    slug: str
    source_path: Path
    body_html: str

    @property
    def output_path(self) -> Path:
        return POST_OUTPUT_DIR / f"{self.slug}.html"

    @property
    def href_from_index(self) -> str:
        return f"posts/{self.slug}.html"

    @property
    def display_date(self) -> str:
        try:
            return datetime.strptime(self.date, "%Y-%m-%d").strftime("%b %Y").upper()
        except ValueError:
            return self.date.upper()

    @property
    def sort_date(self) -> datetime:
        try:
            return datetime.strptime(self.date, "%Y-%m-%d")
        except ValueError:
            return datetime.min


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "post"


def parse_front_matter(markdown: str) -> tuple[dict[str, object], str]:
    markdown = markdown.replace("\r\n", "\n")
    if not markdown.startswith("---\n"):
        return {}, markdown

    try:
        _, raw_meta, body = markdown.split("---\n", 2)
    except ValueError:
        return {}, markdown

    meta: dict[str, object] = {}
    current_list_key: str | None = None

    for line in raw_meta.splitlines():
        if not line.strip():
            continue

        list_match = re.match(r"^\s+-\s+(.+)$", line)
        if list_match and current_list_key:
            meta.setdefault(current_list_key, [])
            assert isinstance(meta[current_list_key], list)
            meta[current_list_key].append(clean_meta_value(list_match.group(1)))
            continue

        key_match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if not key_match:
            continue

        key, value = key_match.groups()
        current_list_key = None
        if value == "":
            meta[key] = []
            current_list_key = key
        else:
            meta[key] = clean_meta_value(value)

    return meta, body.strip()


def clean_meta_value(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def inline_markdown(value: str) -> str:
    escaped = html.escape(value)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', escaped)
    return escaped


def markdown_to_html(markdown: str) -> str:
    lines = markdown.splitlines()
    html_lines: list[str] = []
    paragraph: list[str] = []
    list_type: str | None = None
    in_code = False
    code_lang = ""
    code_lines: list[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph
        if paragraph:
            html_lines.append(f"<p>{inline_markdown(' '.join(paragraph))}</p>")
            paragraph = []

    def close_list() -> None:
        nonlocal list_type
        if list_type:
            html_lines.append(f"</{list_type}>")
            list_type = None

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("```"):
            if in_code:
                class_attr = f' class="language-{html.escape(code_lang)}"' if code_lang else ""
                html_lines.append(f"<pre><code{class_attr}>{html.escape(chr(10).join(code_lines))}</code></pre>")
                in_code = False
                code_lang = ""
                code_lines = []
            else:
                flush_paragraph()
                close_list()
                in_code = True
                code_lang = stripped.removeprefix("```").strip()
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            continue

        heading = re.match(r"^(#{2,4})\s+(.+)$", stripped)
        if heading:
            flush_paragraph()
            close_list()
            level = len(heading.group(1))
            html_lines.append(f"<h{level}>{inline_markdown(heading.group(2))}</h{level}>")
            continue

        quote = re.match(r"^>\s?(.+)$", stripped)
        if quote:
            flush_paragraph()
            close_list()
            html_lines.append(f"<blockquote><p>{inline_markdown(quote.group(1))}</p></blockquote>")
            continue

        unordered = re.match(r"^-\s+(.+)$", stripped)
        if unordered:
            flush_paragraph()
            if list_type != "ul":
                close_list()
                html_lines.append("<ul>")
                list_type = "ul"
            html_lines.append(f"<li>{inline_markdown(unordered.group(1))}</li>")
            continue

        ordered = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ordered:
            flush_paragraph()
            if list_type != "ol":
                close_list()
                html_lines.append("<ol>")
                list_type = "ol"
            html_lines.append(f"<li>{inline_markdown(ordered.group(1))}</li>")
            continue

        close_list()
        paragraph.append(stripped)

    flush_paragraph()
    close_list()
    return "\n".join(html_lines)


def estimate_read_time(markdown: str) -> str:
    words = re.findall(r"\b\w+\b", re.sub(r"```.*?```", "", markdown, flags=re.DOTALL))
    minutes = max(1, round(len(words) / 220))
    return f"{minutes} min"


def load_posts() -> list[Post]:
    posts: list[Post] = []
    for source_path in sorted(BLOG_SOURCE_DIR.glob("*.md")):
        if source_path.name.lower() == "readme.md":
            continue

        raw = source_path.read_text(encoding="utf-8")
        meta, body = parse_front_matter(raw)
        if not meta:
            continue
        title = str(meta.get("title") or source_path.stem.replace("-", " ").title())
        description = str(meta.get("description") or "")
        date = str(meta.get("date") or "1970-01-01")
        read_time = str(meta.get("readTime") or meta.get("read_time") or estimate_read_time(body))
        tags_value = meta.get("tags") or []
        tags = [str(tag) for tag in tags_value] if isinstance(tags_value, list) else []
        slug = slugify(str(meta.get("slug") or source_path.stem))
        posts.append(
            Post(
                title=title,
                description=description,
                date=date,
                read_time=read_time,
                tags=tags,
                slug=slug,
                source_path=source_path,
                body_html=markdown_to_html(body),
            )
        )
    return sorted(posts, key=lambda post: post.sort_date, reverse=True)


def roman(index: int) -> str:
    numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    return numerals[index] if index < len(numerals) else str(index + 1)


def render_post(post: Post, index: int) -> str:
    tags = "\n".join(f"            <span>{html.escape(tag)}</span>" for tag in post.tags)
    title = html.escape(post.title)
    description = html.escape(post.description)
    date = html.escape(post.display_date)
    read_time = html.escape(post.read_time)
    numeral = roman(index)

    return f'''<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{title} — Liam Goodchild</title>
    <meta name="description" content="{description}" />
    <link rel="icon" type="image/png" href="../assets/img/favicon.png" />
    <link
      href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400&family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap"
      rel="stylesheet"
    />
    <link rel="stylesheet" href="../css/styles.css" />
    <script>
      (function () {{
        var accent = localStorage.getItem("accentTheme") || "red";
        document.documentElement.setAttribute("data-accent", accent);
      }})();
    </script>
  </head>
  <body>
    <nav class="nav" id="navbar">
      <div class="nav-left"></div>
      <div class="nav-links">
        <div class="accent-picker" aria-label="Choose accent colour">
          <button class="accent-option accent-option-red" type="button" data-accent="red" aria-label="Use red accent" title="Red"></button>
          <button class="accent-option accent-option-gold" type="button" data-accent="gold" aria-label="Use gold accent" title="Gold"></button>
          <button class="accent-option accent-option-obsidian" type="button" data-accent="obsidian" aria-label="Use purple accent" title="Purple"></button>
        </div>
        <a href="../index.html#work" class="nav-link">Experience</a>
        <a href="../index.html#projects" class="nav-link">Projects</a>
        <a href="../index.html#writing" class="nav-link">Blog</a>
        <a href="../index.html#contact" class="nav-link">Contact</a>
      </div>
    </nav>

    <main class="post-page">
      <article class="post-article reveal revealed">
        <a href="../index.html#writing" class="project-link">&larr; Back to posts</a>

        <header class="post-header">
          <div class="section-label"><span class="section-numeral">{numeral}</span> / {date} / {read_time}</div>
          <h1 class="section-heading">{title}.</h1>
          <p class="hero-tagline post-description">{description}</p>
          <div class="post-tags" aria-label="Tags">
{tags}
          </div>
        </header>

        <div class="post-content">
{post.body_html}
        </div>
      </article>
    </main>

    <script>
      (function () {{
        var options = document.querySelectorAll(".accent-option");
        var activeAccent = document.documentElement.getAttribute("data-accent") || "red";

        function setAccent(accent) {{
          document.documentElement.setAttribute("data-accent", accent);
          localStorage.setItem("accentTheme", accent);
          options.forEach(function (option) {{
            option.classList.toggle("accent-option-active", option.getAttribute("data-accent") === accent);
          }});
        }}

        options.forEach(function (option) {{
          option.addEventListener("click", function () {{
            setAccent(option.getAttribute("data-accent"));
          }});
        }});

        setAccent(activeAccent);
      }})();
    </script>
  </body>
</html>
'''


def render_index_rows(posts: list[Post]) -> str:
    if not posts:
        return '''      <div class="writing-placeholder reveal" data-delay="40">
        <p>Posts coming soon.</p>
      </div>'''

    rows: list[str] = []
    last_index = len(posts) - 1
    for index, post in enumerate(posts):
        classes = "writing-row reveal"
        if index == last_index:
            classes += " writing-row-last"
        rows.append(
            f'''      <a href="{post.href_from_index}" class="{classes}" data-delay="{40 + (index * 60)}">
        <span class="writing-num">{roman(index)}</span>
        <span class="writing-date">{html.escape(post.display_date)}</span>
        <span class="writing-title">{html.escape(post.title)}</span>
        <span class="writing-time">{html.escape(post.read_time)}</span>
        <span class="writing-arrow">&rarr;</span>
      </a>'''
        )
    return "\n".join(rows)


def update_index(posts: list[Post]) -> None:
    index_html = INDEX_FILE.read_text(encoding="utf-8")
    rendered = render_index_rows(posts)

    if START_MARKER not in index_html or END_MARKER not in index_html:
        index_html = re.sub(
            r"      (?:<div class=\"writing-placeholder[\s\S]*?</div>|<a href=\"posts/[\s\S]*?</a>)",
            f"      {START_MARKER}\n{rendered}\n      {END_MARKER}",
            index_html,
            count=1,
        )
    else:
        index_html = re.sub(
            rf"(?m)^\s*{re.escape(START_MARKER)}[\s\S]*?^\s*{re.escape(END_MARKER)}",
            f"      {START_MARKER}\n{rendered}\n      {END_MARKER}",
            index_html,
            count=1,
        )

    INDEX_FILE.write_text(index_html, encoding="utf-8")


def main() -> None:
    BLOG_SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    POST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    posts = load_posts()
    for index, post in enumerate(posts):
        post.output_path.write_text(render_post(post, index), encoding="utf-8")

    update_index(posts)
    print(f"Built {len(posts)} blog post(s).")


if __name__ == "__main__":
    main()

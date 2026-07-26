#!/usr/bin/env python3
#
# Copyright (c) 2024-2026, Ryan Galloway (ryan@rsgalloway.com)
#

"""Build a simple Jekyll-friendly docs site from repository markdown files."""

import argparse
import re
import shutil
from pathlib import Path
from typing import Iterable

LINK_PATTERNS = (
    (r"\(README\.md\)", "(index.html)"),
    (r"\(docs/README\.md\)", "(docs/index.html)"),
    (r"\(docs/([^)]+)\.md\)", r"(docs/\1.html)"),
    (r"\(([^:)#]+)\.md\)", r"(\1.html)"),
)


def rewrite_links(content: str) -> str:
    """Rewrite local markdown links for generated HTML output."""
    updated = content
    for pattern, replacement in LINK_PATTERNS:
        updated = re.sub(pattern, replacement, updated)
    return updated


def extract_title(content: str, fallback: str) -> str:
    """Extract the first markdown H1 title or use a fallback."""
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return fallback


def wrap_markdown(content: str, title: str) -> str:
    """Add minimal Jekyll front matter to markdown content."""
    return f"---\nlayout: default\ntitle: {title}\n---\n\n{content}"


def write_markdown_page(src: Path, dst: Path, fallback_title: str) -> None:
    """Copy a markdown file into the site tree with front matter and fixed links."""
    content = src.read_text(encoding="utf-8")
    title = extract_title(content, fallback_title)
    content = rewrite_links(content)
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(wrap_markdown(content, title), encoding="utf-8")


def write_site_config(output_dir: Path) -> None:
    """Write a minimal Jekyll config file."""
    config = """title: pathbase
description: Lightweight bidirectional filesystem path templates for Python
markdown: kramdown
permalink: pretty
"""
    (output_dir / "_config.yml").write_text(config, encoding="utf-8")


def write_layout(output_dir: Path) -> None:
    """Write the shared Jekyll layout used by the generated docs site."""
    layout_dir = output_dir / "_layouts"
    layout_dir.mkdir(parents=True, exist_ok=True)
    template = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% if page.title %}{{ page.title }} | {% endif %}{{ site.title }}</title>
    <meta name="description" content="{{ site.description }}">
    <link rel="stylesheet" href="{{ '/assets/site.css' | relative_url }}">
  </head>
  <body>
    <div class="site-shell">
      <header class="site-header">
        <a class="site-brand" href="{{ '/' | relative_url }}">{{ site.title }}</a>
        <nav class="site-nav">
          <a href="{{ '/' | relative_url }}">Home</a>
          <a href="{{ '/docs/examples/' | relative_url }}">Examples</a>
          <a href="{{ '/docs/overrides/' | relative_url }}">Overrides</a>
          <a href="https://github.com/rsgalloway/pathbase">GitHub</a>
          <a href="https://pypi.org/project/pathbase/">PyPI</a>
        </nav>
      </header>
      <main class="site-main">
        {{ content }}
      </main>
    </div>
  </body>
</html>
"""
    (layout_dir / "default.html").write_text(template, encoding="utf-8")


def write_stylesheet(output_dir: Path) -> None:
    """Write a minimal light stylesheet for the generated docs site."""
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    css = """:root {
  --bg: #ffffff;
  --panel: #ffffff;
  --border: #d9e2ec;
  --text: #102033;
  --muted: #516172;
  --accent: #006f5f;
  --accent-dark: #004e43;
  --code: #f4f8fb;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  line-height: 1.7;
}

a {
  color: var(--accent-dark);
  text-decoration: none;
}

a:hover {
  color: var(--accent);
}

.site-shell {
  max-width: 1040px;
  margin: 0 auto;
  padding: 24px 24px 72px;
}

.site-header {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 36px;
}

.site-brand {
  color: var(--text);
  font-size: 0.98rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.site-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.site-nav a {
  color: var(--muted);
  font-size: 0.95rem;
}

.site-nav a:hover {
  color: var(--text);
}

.site-main {
  background: transparent;
}

.site-main h1:first-child,
.site-main p:first-child img {
  margin-top: 0;
}

h1, h2, h3 {
  color: var(--text);
  line-height: 1.15;
}

h1 {
  font-size: 2.7rem;
  margin: 0 0 1rem;
}

h2 {
  font-size: 1.5rem;
  margin-top: 2.5rem;
}

h3 {
  font-size: 1.08rem;
  margin-top: 1.5rem;
}

p, li {
  font-size: 1.02rem;
}

code, pre {
  font-family: "SFMono-Regular", Consolas, "Liberation Mono", monospace;
}

code {
  background: var(--code);
  border: 1px solid #e4ebf2;
  border-radius: 8px;
  padding: 0.12rem 0.4rem;
}

pre {
  background: var(--code);
  border: 1px solid var(--border);
  border-radius: 16px;
  overflow-x: auto;
  padding: 18px 20px;
}

pre code {
  background: transparent;
  border: 0;
  padding: 0;
}

blockquote {
  border-left: 4px solid #b8c6d6;
  color: var(--muted);
  margin: 1.5rem 0;
  padding-left: 1rem;
}

table {
  border-collapse: collapse;
  width: 100%;
}

th, td {
  border: 1px solid var(--border);
  padding: 0.7rem 0.8rem;
  text-align: left;
}

th {
  background: #f2f6fa;
}

@media (max-width: 720px) {
  .site-shell {
    padding: 18px 16px 56px;
  }

  h1 {
    font-size: 2.15rem;
  }
}
"""
    (assets_dir / "site.css").write_text(css, encoding="utf-8")


def copy_markdown_tree(root: Path, output_dir: Path, docs_files: Iterable[Path]) -> None:
    """Copy repository markdown files into the generated site tree."""
    write_markdown_page(root / "README.md", output_dir / "index.md", "pathbase")
    write_markdown_page(root / "docs" / "README.md", output_dir / "docs" / "index.md", "Docs")

    for src in docs_files:
        if src.name == "README.md":
            continue
        dst = output_dir / "docs" / src.name
        fallback = src.stem.replace("-", " ").title()
        write_markdown_page(src, dst, fallback)


def build_site(output_dir: Path) -> None:
    """Build the markdown source tree used by GitHub Pages."""
    root = Path(__file__).resolve().parents[1]
    docs_dir = root / "docs"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    docs_files = sorted(docs_dir.glob("*.md"))
    copy_markdown_tree(root, output_dir, docs_files)
    write_site_config(output_dir)
    write_layout(output_dir)
    write_stylesheet(output_dir)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="_site_src", help="Output directory")
    return parser.parse_args()


def main() -> None:
    """Build the GitHub Pages source tree."""
    args = parse_args()
    build_site(Path(args.output))


if __name__ == "__main__":
    main()

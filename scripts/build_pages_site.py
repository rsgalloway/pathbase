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

README_LINK_RE = re.compile(r"\(([^)#]*?)README\.md(#.*?)?\)")
MARKDOWN_LINK_RE = re.compile(r"\(([^:)#][^)]*?)\.md(#.*?)?\)")


def rewrite_links(content: str) -> str:
    """Rewrite local markdown links for generated HTML output."""
    updated = README_LINK_RE.sub(r"(\1index.html\2)", content)
    updated = MARKDOWN_LINK_RE.sub(r"(\1.html\2)", updated)
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
          <a href="{{ '/examples/' | relative_url }}">Examples</a>
          <a href="{{ '/docs/overrides/' | relative_url }}">Overrides</a>
          <a href="https://github.com/rsgalloway/pathbase">GitHub</a>
          <a href="https://pypi.org/project/pathbase/">PyPI</a>
        </nav>
      </header>
      <main class="site-main">
        {{ content }}
      </main>
    </div>
    <script>
      document.addEventListener("DOMContentLoaded", function () {
        var blocks = document.querySelectorAll("pre");

        function setButtonState(button, label) {
          button.textContent = label;
          window.setTimeout(function () {
            button.textContent = "Copy";
          }, 1200);
        }

        blocks.forEach(function (block) {
          var code = block.querySelector("code");
          if (!code) {
            return;
          }

          var button = document.createElement("button");
          button.className = "copy-button";
          button.type = "button";
          button.textContent = "Copy";

          button.addEventListener("click", function () {
            var text = code.innerText;

            if (navigator.clipboard && navigator.clipboard.writeText) {
              navigator.clipboard.writeText(text).then(function () {
                setButtonState(button, "Copied");
              });
              return;
            }

            var selection = window.getSelection();
            var range = document.createRange();
            range.selectNodeContents(code);
            selection.removeAllRanges();
            selection.addRange(range);

            try {
              document.execCommand("copy");
              setButtonState(button, "Copied");
            } finally {
              selection.removeAllRanges();
            }
          });

          block.classList.add("code-block");
          block.appendChild(button);
        });
      });
    </script>
  </body>
</html>
"""
    (layout_dir / "default.html").write_text(template, encoding="utf-8")


def write_stylesheet(output_dir: Path) -> None:
    """Write a minimal light stylesheet for the generated docs site."""
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    css = """:root {
  --bg: #f5f8fc;
  --panel: #ffffff;
  --panel-strong: #e8eef6;
  --border: #c9d4e2;
  --text: #122033;
  --muted: #4f5f73;
  --accent: #0b6bcb;
  --accent-dark: #084f98;
  --code-bg: #0f172a;
  --code-border: #1e293b;
  --code-text: #e2e8f0;
  --code-muted: #93a4ba;
}

* { box-sizing: border-box; }

html, body {
  margin: 0;
  padding: 0;
  background: var(--bg);
  color: var(--text);
  font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
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
  max-width: 1100px;
  margin: 0 auto;
  padding: 24px 24px 72px;
}

.site-header {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 24px;
  align-items: center;
  justify-content: space-between;
  margin: 12px 0 36px;
  padding: 18px 22px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
  backdrop-filter: blur(8px);
}

.site-brand {
  color: var(--text);
  font-size: 1rem;
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
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 28px;
  box-shadow: 0 24px 56px rgba(15, 23, 42, 0.08);
  padding: 42px 48px 56px;
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
  font-size: 2.8rem;
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
  background: #eef4fb;
  border: 1px solid #d8e3ef;
  border-radius: 8px;
  padding: 0.12rem 0.4rem;
}

pre {
  background: linear-gradient(180deg, #111b31 0%, #0f172a 100%);
  border: 1px solid var(--code-border);
  border-radius: 18px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  color: var(--code-text);
  overflow-x: auto;
  padding: 22px 22px 20px;
  position: relative;
}

pre code {
  background: transparent;
  border: 0;
  color: var(--code-text);
  padding: 0;
}

.copy-button {
  appearance: none;
  background: rgba(148, 163, 184, 0.12);
  border: 1px solid rgba(148, 163, 184, 0.28);
  border-radius: 999px;
  color: var(--code-text);
  cursor: pointer;
  font: inherit;
  font-size: 0.82rem;
  padding: 0.28rem 0.7rem;
  position: absolute;
  right: 14px;
  top: 12px;
}

.copy-button:hover {
  background: rgba(148, 163, 184, 0.18);
  border-color: rgba(148, 163, 184, 0.42);
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
  background: #f1f6fb;
}

hr {
  border: 0;
  border-top: 1px solid var(--border);
  margin: 2rem 0;
}

@media (max-width: 720px) {
  .site-shell {
    padding: 18px 16px 56px;
  }

  .site-header {
    padding: 14px 16px;
  }

  .site-main {
    border-radius: 22px;
    padding: 28px 20px 38px;
  }

  h1 {
    font-size: 2.15rem;
  }
}
"""
    (assets_dir / "site.css").write_text(css, encoding="utf-8")


def copy_markdown_tree(
    root: Path, output_dir: Path, docs_files: Iterable[Path], examples_dir: Path
) -> None:
    """Copy repository markdown files into the generated site tree."""
    write_markdown_page(root / "README.md", output_dir / "index.md", "pathbase")
    write_markdown_page(root / "docs" / "README.md", output_dir / "docs" / "index.md", "Docs")
    write_markdown_page(
        examples_dir / "README.md", output_dir / "examples" / "index.md", "Examples"
    )

    for src in docs_files:
        if src.name == "README.md":
            continue
        dst = output_dir / "docs" / src.name
        fallback = src.stem.replace("-", " ").title()
        write_markdown_page(src, dst, fallback)

    for src in sorted(examples_dir.rglob("README.md")):
        if src == examples_dir / "README.md":
            continue
        relative_parent = src.relative_to(examples_dir).parent
        dst = output_dir / "examples" / relative_parent / "index.md"
        fallback = relative_parent.name.replace("-", " ").title()
        write_markdown_page(src, dst, fallback)


def build_site(output_dir: Path) -> None:
    """Build the markdown source tree used by GitHub Pages."""
    root = Path(__file__).resolve().parents[1]
    docs_dir = root / "docs"
    examples_dir = root / "examples"

    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    docs_files = sorted(docs_dir.glob("*.md"))
    copy_markdown_tree(root, output_dir, docs_files, examples_dir)
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

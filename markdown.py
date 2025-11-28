"""Minimal Markdown to HTML converter used by the blog generator.

This is intentionally small to avoid external dependencies in CI, while still
supporting the basics used in GitHub Issues: headings, bullet lists, fenced code
blocks, paragraphs, and inline links.
"""
from __future__ import annotations

import html
import re
from typing import List


LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def _render_inline(text: str) -> str:
    segments: List[str] = []
    last = 0
    for match in LINK_PATTERN.finditer(text):
        start, end = match.span()
        if start > last:
            segments.append(html.escape(text[last:start]))
        label, url = match.groups()
        segments.append(f"<a href=\"{html.escape(url)}\" target=\"_blank\">{html.escape(label)}</a>")
        last = end
    if last < len(text):
        segments.append(html.escape(text[last:]))
    return "".join(segments)


def markdown(text: str, extensions=None) -> str:  # noqa: D401
    """Convert a small subset of Markdown into HTML."""
    lines = text.splitlines()
    html_parts: List[str] = []
    in_code = False
    in_list = False
    paragraph: List[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            html_parts.append(f"<p>{'<br/>'.join(paragraph)}</p>")
            paragraph.clear()

    def close_list() -> None:
        nonlocal in_list
        if in_list:
            html_parts.append("</ul>")
            in_list = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            flush_paragraph()
            close_list()
            if in_code:
                html_parts.append("</code></pre>")
                in_code = False
            else:
                html_parts.append("<pre><code>")
                in_code = True
            continue

        if in_code:
            html_parts.append(html.escape(line))
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            continue

        if stripped.startswith("#"):
            flush_paragraph()
            close_list()
            level = len(stripped) - len(stripped.lstrip("#"))
            content = stripped[level:].strip()
            html_parts.append(f"<h{level}>{_render_inline(content)}</h{level}>")
            continue

        if stripped[0] in "-*" and (len(stripped) == 1 or stripped[1] == " "):
            flush_paragraph()
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{_render_inline(stripped[1:].strip())}</li>")
            continue

        paragraph.append(_render_inline(stripped))

    flush_paragraph()
    close_list()
    if in_code:
        html_parts.append("</code></pre>")

    return "\n".join(html_parts)

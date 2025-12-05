"""Minimal Markdown to HTML converter used by the blog generator.

This is intentionally small to avoid external dependencies in CI, while still
supporting the basics used in GitHub Issues: headings, bullet lists, fenced code
blocks, paragraphs, and inline links.
"""
from __future__ import annotations

import html
import re
from typing import List, Optional


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


def _parse_table_row(line: str) -> Optional[List[str]]:
    if "|" not in line:
        return None
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    if not any(cells):
        return None
    return cells


def _is_table_separator(line: str) -> bool:
    if "|" not in line:
        return False
    parts = line.strip().strip("|").split("|")
    return all(re.fullmatch(r"\s*:?-{3,}:?\s*", part) for part in parts)


def _render_table(headers: List[str], rows: List[List[str]]) -> str:
    header_html = "".join(f"<th>{_render_inline(cell)}</th>" for cell in headers)
    body_html = "".join(
        f"<tr>{''.join(f'<td>{_render_inline(cell)}</td>' for cell in row)}</tr>"
        for row in rows
    )
    return f"<table><thead><tr>{header_html}</tr></thead><tbody>{body_html}</tbody></table>"


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

    i = 0
    while i < len(lines):
        line = lines[i]
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
            i += 1
            continue

        if in_code:
            html_parts.append(html.escape(line))
            i += 1
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            i += 1
            continue

        if i + 1 < len(lines):
            header_cells = _parse_table_row(stripped)
            if header_cells and _is_table_separator(lines[i + 1].strip()):
                flush_paragraph()
                close_list()
                rows: List[List[str]] = []
                i += 2
                while i < len(lines):
                    row = _parse_table_row(lines[i].strip())
                    if not row:
                        break
                    rows.append(row)
                    i += 1
                html_parts.append(_render_table(header_cells, rows))
                continue

        if stripped.startswith("#"):
            flush_paragraph()
            close_list()
            level = len(stripped) - len(stripped.lstrip("#"))
            content = stripped[level:].strip()
            html_parts.append(f"<h{level}>{_render_inline(content)}</h{level}>")
            i += 1
            continue

        if stripped[0] in "-*" and (len(stripped) == 1 or stripped[1] == " "):
            flush_paragraph()
            if not in_list:
                html_parts.append("<ul>")
                in_list = True
            html_parts.append(f"<li>{_render_inline(stripped[1:].strip())}</li>")
            i += 1
            continue

        paragraph.append(_render_inline(stripped))

        i += 1

    flush_paragraph()
    close_list()
    if in_code:
        html_parts.append("</code></pre>")

    return "\n".join(html_parts)

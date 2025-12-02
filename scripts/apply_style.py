from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config" / "author.json"
STYLES_DIR = ROOT / "styles"
TARGET_STYLE = ROOT / "style.css"


def load_style_name() -> str:
    """Return requested page style from config with fallback."""
    default_style = "default"
    if not CONFIG_PATH.exists():
        return default_style

    try:
        with CONFIG_PATH.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError:
        return default_style

    style = data.get("page_style")
    if not isinstance(style, str) or not style.strip():
        return default_style
    return style.strip()


def compute_style_version(css_content: str) -> str:
    """Generate a short hash used to bust caches for style.css."""

    return hashlib.sha256(css_content.encode("utf-8")).hexdigest()[:12]


def resolve_style_file(style_name: str) -> Path:
    """Find the stylesheet file, falling back to default when missing."""
    candidate = STYLES_DIR / f"{style_name}.css"
    if candidate.exists():
        return candidate
    return STYLES_DIR / "default.css"


def update_stylesheet_links(version: str) -> list[Path]:
    """Inject a cache-busting query string into all HTML stylesheet links."""

    html_files = [ROOT / "index.html", ROOT / "list.html"]
    posts_dir = ROOT / "_posts"
    if posts_dir.exists():
        html_files.extend(sorted(posts_dir.glob("*.html")))

    pattern = re.compile(r'href="(?P<prefix>\.\./)?style\.css(?:\?v=[^"]*)?"')
    replacement = r'href="\g<prefix>style.css?v=' + version + '"'

    updated: list[Path] = []
    for html_file in html_files:
        if not html_file.exists():
            continue
        original = html_file.read_text(encoding="utf-8")
        rewritten = pattern.sub(replacement, original)
        if rewritten != original:
            html_file.write_text(rewritten, encoding="utf-8")
            updated.append(html_file)

    return updated


def apply_style() -> None:
    style_name = load_style_name()
    source = resolve_style_file(style_name)
    css_content = source.read_text(encoding="utf-8")
    TARGET_STYLE.write_text(css_content, encoding="utf-8")

    version = compute_style_version(css_content)
    updated_files = update_stylesheet_links(version)

    print(f"Applied style: {source.name} -> {TARGET_STYLE.name} (version {version})")
    if updated_files:
        updated_paths = ", ".join(str(path.relative_to(ROOT)) for path in updated_files)
        print(f"Updated stylesheet references in: {updated_paths}")
    else:
        print("No HTML references required updating.")


if __name__ == "__main__":
    apply_style()

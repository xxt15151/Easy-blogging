from __future__ import annotations

import json
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


def resolve_style_file(style_name: str) -> Path:
    """Find the stylesheet file, falling back to default when missing."""
    candidate = STYLES_DIR / f"{style_name}.css"
    if candidate.exists():
        return candidate
    return STYLES_DIR / "default.css"


def apply_style() -> None:
    style_name = load_style_name()
    source = resolve_style_file(style_name)
    TARGET_STYLE.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    print(f"Applied style: {source.name} -> {TARGET_STYLE.name}")


if __name__ == "__main__":
    apply_style()

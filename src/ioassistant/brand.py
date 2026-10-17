"""Sectigo brand 2026 (V01.26) styling shared by the HTML reports.

Logos and fonts are bundled in ./brand (copied from the approved sectigo-brand-2026
skill) and inlined as base64 so each report is a single self-contained file.
"""
from __future__ import annotations

import base64
from functools import lru_cache
from html import escape
from pathlib import Path

BRAND_DIR = Path(__file__).resolve().parent / "brand"

FOREST, SPEARMINT = "#015258", "#06DFC7"
OFF_WHITE, OFF_BLACK = "#F3F2EA", "#333132"
CORAL, SCOUT = "#FF9479", "#7FA9B4"


@lru_cache(maxsize=None)
def _data_uri(name: str, mime: str) -> str:
    path = BRAND_DIR / name
    if not path.is_file():
        return ""
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _font_face(family: str, file: str) -> str:
    uri = _data_uri(file, "font/ttf")
    if not uri:
        return ""
    return (
        f"@font-face{{font-family:'{family}';src:url('{uri}') format('truetype');"
        "font-weight:100 900;font-style:normal;font-display:swap}"
    )


CSS_BASE = f"""
:root{{--forest:{FOREST};--spearmint:{SPEARMINT};--off-white:{OFF_WHITE};--off-black:{OFF_BLACK};
--coral:{CORAL};--scout:{SCOUT}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--off-white);color:var(--off-black);
font:15px/1.5 'DM Sans',Arial,sans-serif}}
h1,h2,h3{{font-family:'Urbanist',Arial,sans-serif;font-weight:700;color:var(--forest);margin:0;line-height:1.15}}
h4{{font-weight:600;font-size:13px;color:var(--forest);margin:1rem 0 .25rem}}
a{{color:var(--forest);text-decoration-color:var(--spearmint);text-underline-offset:2px}}
a:hover{{background:var(--spearmint)}}
header.top{{background:var(--forest);color:var(--off-white);padding:32px 0 36px}}
header.top img{{display:block;width:160px;height:auto;margin-bottom:28px}}
header.top h1{{color:var(--off-white);font-size:38px}}
header.top p{{margin:.5rem 0 0;color:var(--spearmint)}}
header.top p.range{{color:var(--off-white);font-weight:600;font-size:17px}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px}}
main.wrap{{padding-top:32px;padding-bottom:48px}}
h2{{font-size:26px;margin:2.5rem 0 1rem}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th{{text-align:left;font-weight:600;color:var(--forest);border-bottom:2px solid var(--forest);padding:6px 10px}}
td{{padding:6px 10px;border-bottom:1px solid rgba(51,49,50,.18);vertical-align:top}}
footer{{border-top:1px solid rgba(51,49,50,.18);margin-top:3rem;padding-top:1rem;font-size:12px}}
"""


def head(title: str, extra_css: str = "", fonts: bool = True) -> str:
    """fonts=False skips the ~450 KB of embedded fonts; CSS then falls back to Arial."""
    font_css = (
        _font_face("Urbanist", "Urbanist-VariableFont_wght.ttf")
        + _font_face("DM Sans", "DMSans-VariableFont_opsz,wght.ttf")
        if fonts else ""
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{escape(title)}</title><style>{font_css}{CSS_BASE}{extra_css}</style></head>"
    )


def banner(title: str, subtitle: str, range_line: str = "") -> str:
    logo = _data_uri("sectigo-logo-light.png", "image/png")  # wordmark for the Forest band
    img = f"<img src='{logo}' alt='Sectigo'>" if logo else ""
    return (
        f"<header class='top'><div class='wrap'>{img}<h1>{escape(title)}</h1>"
        f"<p>{escape(subtitle)}</p>"
        + (f"<p class='range'>{escape(range_line)}</p>" if range_line else "")
        + "</div></header>"
    )

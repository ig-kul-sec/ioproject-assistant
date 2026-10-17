"""Render the per-run spending report from usage.json."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from . import brand

PRICING_PATH = Path(__file__).resolve().parents[2] / "config" / "pricing.json"


def load_pricing(path: Path = PRICING_PATH) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def cost(row: dict, pricing: dict):
    """USD cost for one usage row, or None when the model has no price."""
    price = pricing.get(row.get("model"), {})
    if price.get("input") is None or price.get("output") is None:
        return None
    return (row["input_tokens"] * price["input"] + row["output_tokens"] * price["output"]) / 1_000_000


def render(rows: list[dict], pricing: dict, title: str, fonts: bool = True) -> str:
    body, total, unpriced = "", 0.0, False
    for r in rows:
        c = cost(r, pricing)
        unpriced |= c is None
        total += c or 0.0
        body += (
            f"<tr><td>{escape(r['agent'])}</td><td>{escape(r['model'])}</td>"
            f"<td>{r['input_tokens'] + r['output_tokens']:,}</td><td>{r['seconds']:.1f}</td>"
            f"<td>{'n/a' if c is None else f'${c:.4f}'}</td></tr>"
        )
    priced = any(cost(r, pricing) is not None for r in rows)
    if not priced:
        total_txt = "n/a (no model prices configured)"
    else:
        total_txt = f"${total:.4f}" + (" (partial: some models have no price)" if unpriced else "")
    return (
        brand.head(f"{title} spending", fonts=fonts)
        + "<body>"
        + brand.banner("I&O assistant run spending", title)
        + "<main class='wrap'><h2>Usage by agent</h2>"
        "<table><tr><th>Agent</th><th>Model</th><th>Tokens</th><th>Seconds</th><th>Est. cost (USD)</th></tr>"
        f"{body}</table><p><b>Total:</b> {total_txt}</p>"
        "<footer>sectigo.com &nbsp;|&nbsp; Sectigo&copy; 2026. All rights reserved.</footer></main></body></html>"
    )


def build(usage_path: Path, fonts: bool = True) -> Path:
    rows = json.loads(usage_path.read_text(encoding="utf-8"))
    run_id = usage_path.parent.name
    out = usage_path.parent / f"{run_id}_spending.html"
    out.write_text(render(rows, load_pricing(), run_id, fonts), encoding="utf-8")
    return out

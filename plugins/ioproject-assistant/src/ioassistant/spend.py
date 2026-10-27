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
    inp, out = row["input_tokens"], row["output_tokens"]
    share = pricing.get("_output_share")
    if out == 0 and share:  # only a total is known: split it by the assumed output share
        out = inp * share
        inp = inp - out
    return (inp * price["input"] + out * price["output"]) / 1_000_000


def render(rows: list[dict], pricing: dict, title: str, compact: bool = False) -> str:
    body, total, unpriced = "", 0.0, False
    tokens = seconds = 0
    for r in rows:
        c = cost(r, pricing)
        unpriced |= c is None
        total += c or 0.0
        tokens += r["input_tokens"] + r["output_tokens"]
        seconds += r["seconds"]
        body += (
            f"<tr><td>{escape(r['agent'])}</td><td>{escape(r['model'])}</td>"
            f"<td>{r['input_tokens'] + r['output_tokens']:,}</td><td>{r['seconds']:.1f}</td>"
            f"<td>{'n/a' if c is None else f'{c:.2f}$'}</td></tr>"
        )
    priced = any(cost(r, pricing) is not None for r in rows)
    total_cell = f"{total:.2f}$" if priced else "n/a"
    price_note = (
        "<p class='lbl'>No model prices are configured, so the cost total is n/a.</p>" if not priced
        else "<p class='lbl'>Some models have no price, so the cost total is partial.</p>" if unpriced else ""
    )
    return (
        brand.head(f"{title} spending", fonts=not compact)
        + "<body>"
        + brand.banner("I&O assistant run spending", title, compact=compact,
                       note_html=brand.sharepoint_note(f"{title}_spending.html"), dev=brand.is_dev(title))
        + "<main class='wrap'><h2>Usage by agent</h2>"
        "<table><tr><th>Agent</th><th>Model</th><th>Tokens</th><th>Seconds</th><th>Est. cost (USD)</th></tr>"
        f"{body}<tfoot><tr class='total'><td><b>Total</b></td><td></td><td><b>{tokens:,}</b></td>"
        f"<td><b>{seconds:.1f}</b></td><td><b>{total_cell}</b></td></tr></tfoot></table>{price_note}"
        f"<p class='lbl'>Rough estimate: token totals are split {round(100 * (1 - (pricing.get('_output_share') or 0)))}% input / "
        f"{round(100 * (pricing.get('_output_share') or 0))}% output at list prices; caching discounts are ignored.</p>"
        + brand.footer() + "</main>" + brand.foot()
    )


def set_orchestrator(usage_path: Path, tokens: int, seconds: float | None = None) -> None:
    """Put the orchestrator's own usage (from its Agent result) into usage.json, replacing the placeholder row."""
    rows = json.loads(usage_path.read_text(encoding="utf-8"))
    row = next((r for r in rows if r["agent"] == "orchestrator"), None)
    if row is None:
        row = {"agent": "orchestrator", "model": "claude-opus-5-5", "input_tokens": 0, "output_tokens": 0, "seconds": 0.0}
        rows.append(row)
    row.update(input_tokens=int(tokens), output_tokens=0)  # only a total is known: cost() splits it by _output_share
    if seconds is not None:
        row["seconds"] = float(seconds)
    row.pop("note", None)
    usage_path.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")


def _out_path(run_dir: Path, name: str, compact: bool) -> Path:
    """Compact builds (no embedded fonts, small logo) go to <run>/upload/ for the connector upload."""
    folder = run_dir / "upload" if compact else run_dir
    folder.mkdir(exist_ok=True)
    return folder / name


def build(usage_path: Path, compact: bool = False) -> Path:
    rows = json.loads(usage_path.read_text(encoding="utf-8"))
    run_id = usage_path.parent.name
    out = _out_path(usage_path.parent, f"{run_id}_spending.html", compact)
    out.write_bytes(render(rows, load_pricing(), run_id, compact).encode("utf-8"))  # LF endings
    return out

"""Command-line entry point.

Example:
    invoice-gen --client "WLSN" --client-note "YouTube channel" \
        --item "Full Edit – Premium Package:300" --number INV-0043
"""

from __future__ import annotations

import argparse
import datetime as dt
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .core import Invoice, LineItem, load_config, render_html
from .render import export


def parse_item(raw: str) -> LineItem:
    """Parse 'description:rate[:qty[:note]]' into a LineItem."""
    parts = raw.split(":")
    if len(parts) < 2:
        raise argparse.ArgumentTypeError(f"item must be 'description:rate[:qty[:note]]', got {raw!r}")
    desc, rate = parts[0].strip(), parts[1].strip()
    try:
        rate_d = Decimal(rate)
    except InvalidOperation:
        raise argparse.ArgumentTypeError(f"bad rate {rate!r} in item {raw!r}")
    qty = int(parts[2]) if len(parts) > 2 and parts[2].strip() else 1
    note = parts[3].strip() if len(parts) > 3 else ""
    return LineItem(description=desc, rate=rate_d, qty=qty, note=note)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="invoice-gen", description="Generate a clean invoice as PNG or PDF.")
    p.add_argument("--client", required=True, help="client name")
    p.add_argument("--client-note", default="", help="second line under the client name")
    p.add_argument("--item", action="append", type=parse_item, required=True,
                   help="line item 'description:rate[:qty[:note]]' (repeatable)")
    p.add_argument("--number", required=True, help="invoice number, e.g. INV-0043")
    p.add_argument("--date", type=dt.date.fromisoformat, default=dt.date.today(), help="YYYY-MM-DD (default: today)")
    p.add_argument("--due-days", type=int, default=None, help="payment terms in days (omit for no due date)")
    p.add_argument("--vat", type=Decimal, default=Decimal("0"), help="VAT rate, e.g. 0.2")
    p.add_argument("--config", type=Path, default=Path("config.toml"), help="sender + bank details")
    p.add_argument("--format", choices=["png", "pdf"], default="png")
    p.add_argument("--out", type=Path, default=None, help="output path (default: out/Invoice_<number>)")
    p.add_argument("--html", action="store_true", help="also save the rendered HTML")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    config = load_config(args.config)
    invoice = Invoice(
        number=args.number,
        client_name=args.client,
        client_note=args.client_note,
        items=args.item,
        date=args.date,
        due_days=args.due_days,
        vat_rate=args.vat,
    )
    html = render_html(invoice, config)
    out = args.out or Path("out") / f"Invoice_{args.number}"
    if args.html:
        out.with_suffix(".html").parent.mkdir(parents=True, exist_ok=True)
        out.with_suffix(".html").write_text(html, encoding="utf-8")
    written = export(html, out, args.format)
    print(f"wrote {written}  (total {invoice.total})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

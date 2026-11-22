"""Core invoice model: load config, compute totals, render HTML."""

from __future__ import annotations

import datetime as dt
import tomllib
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATE_DIR = Path(__file__).parent / "templates"
PENNY = Decimal("0.01")


def money(value: Decimal, symbol: str = "£") -> str:
    """Format a Decimal as currency, e.g. 1234.5 -> '£1,234.50'."""
    q = Decimal(value).quantize(PENNY, rounding=ROUND_HALF_UP)
    return f"{symbol}{q:,.2f}"


@dataclass
class LineItem:
    description: str
    rate: Decimal
    qty: int = 1
    note: str = ""

    @property
    def amount(self) -> Decimal:
        return (self.rate * self.qty).quantize(PENNY, rounding=ROUND_HALF_UP)


@dataclass
class Invoice:
    number: str
    client_name: str
    items: list[LineItem]
    client_note: str = ""
    date: dt.date = field(default_factory=dt.date.today)
    due_days: int | None = None
    vat_rate: Decimal = Decimal("0")
    footer_note: str = "Thank you for your business."

    @property
    def subtotal(self) -> Decimal:
        return sum((i.amount for i in self.items), Decimal("0"))

    @property
    def vat(self) -> Decimal:
        return (self.subtotal * self.vat_rate).quantize(PENNY, rounding=ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.vat

    @property
    def due_date(self) -> dt.date | None:
        if self.due_days is None:
            return None
        return self.date + dt.timedelta(days=self.due_days)


def load_config(path: Path) -> dict:
    """Read sender + bank details from a TOML file."""
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    for section in ("sender", "bank"):
        cfg.setdefault(section, {})
    return cfg


def _display_date(d: dt.date | None) -> str:
    return f"{d.day} {d.strftime('%B %Y')}" if d else ""


def render_html(invoice: Invoice, config: dict) -> str:
    """Render the invoice to a standalone HTML string."""
    env = Environment(
        loader=FileSystemLoader(TEMPLATE_DIR),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("base.html")
    symbol = config.get("currency_symbol", "£")
    return template.render(
        sender=config["sender"],
        bank=config["bank"],
        client={"name": invoice.client_name, "note": invoice.client_note},
        invoice={
            "number": invoice.number,
            "date_display": _display_date(invoice.date),
            "due_display": _display_date(invoice.due_date),
            "footer_note": invoice.footer_note,
        },
        items=[
            {"description": i.description, "note": i.note, "qty": i.qty,
             "rate": i.rate, "amount": i.amount}
            for i in invoice.items
        ],
        totals={"subtotal": invoice.subtotal, "vat": invoice.vat,
                "vat_rate": invoice.vat_rate, "total": invoice.total},
        money=lambda v: money(v, symbol),
    )

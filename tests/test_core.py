import datetime as dt
from decimal import Decimal

import pytest

from invoice_gen.cli import parse_item
from invoice_gen.core import Invoice, LineItem, money, render_html

CONFIG = {
    "sender": {"brand": "Test Co", "tagline": "Video Editing", "email": "a@b.c", "website": "example.com"},
    "bank": {"name": "Bank", "account_name": "A Person"},
}


def test_money_formats_and_rounds():
    assert money(Decimal("1234.5")) == "£1,234.50"
    assert money(Decimal("0.005")) == "£0.01"
    assert money(Decimal("10"), "$") == "$10.00"


def test_totals_with_qty_and_vat():
    inv = Invoice(
        number="T1",
        client_name="Client",
        items=[LineItem("Edit", Decimal("300"), qty=2), LineItem("Thumbnail", Decimal("25"))],
        vat_rate=Decimal("0.2"),
    )
    assert inv.subtotal == Decimal("625.00")
    assert inv.vat == Decimal("125.00")
    assert inv.total == Decimal("750.00")


def test_due_date_optional():
    inv = Invoice(number="T2", client_name="C", items=[], date=dt.date(2026, 11, 22))
    assert inv.due_date is None
    inv.due_days = 14
    assert inv.due_date == dt.date(2026, 12, 6)


def test_parse_item_variants():
    a = parse_item("Full Edit:300")
    assert (a.description, a.rate, a.qty) == ("Full Edit", Decimal("300"), 1)
    b = parse_item("Shorts:40:5:vertical cut-downs")
    assert (b.qty, b.note, b.amount) == (5, "vertical cut-downs", Decimal("200.00"))
    with pytest.raises(Exception):
        parse_item("no-rate")


def test_render_html_contains_key_fields():
    inv = Invoice(number="INV-999", client_name="Client Ltd", items=[LineItem("Full Edit", Decimal("300"))])
    html = render_html(inv, CONFIG)
    assert "INV-999" in html and "Client Ltd" in html and "£300.00" in html
    assert "class=\"blank\"" in html  # bank numbers left blank when not configured


def test_render_escapes_client_input():
    inv = Invoice(number="X", client_name="<script>", items=[LineItem("a", Decimal("1"))])
    assert "<script>" not in render_html(inv, CONFIG).split("<body>")[1]

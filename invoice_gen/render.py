"""Turn rendered HTML into PNG / PDF with headless Chromium (Playwright)."""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

PAGE_W, PAGE_H = 1240, 1754  # A4 at ~150 dpi


def export(html: str, out: Path, fmt: str = "png") -> Path:
    """Write the invoice to `out` as PNG or PDF. Returns the path written."""
    out = out.with_suffix(f".{fmt}")
    out.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": PAGE_W, "height": PAGE_H})
        page.set_content(html, wait_until="load")
        if fmt == "png":
            page.locator(".page").screenshot(path=str(out))
        elif fmt == "pdf":
            page.pdf(path=str(out), width=f"{PAGE_W}px", height=f"{PAGE_H}px",
                     print_background=True, page_ranges="1")
        else:
            raise ValueError(f"unsupported format: {fmt}")
        browser.close()
    return out

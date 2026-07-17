"""pdf_export — Chrome discovery + graceful degradation (no real Chrome needed)."""
from __future__ import annotations

from pathlib import Path

from orchestrator import pdf_export


def test_find_chrome_returns_str_or_none():
    r = pdf_export.find_chrome()
    assert r is None or isinstance(r, str)


def test_render_pdf_false_when_no_browser(tmp_path, monkeypatch):
    html = tmp_path / "r.html"
    html.write_text("<html><body>hi</body></html>")
    out = tmp_path / "r.pdf"
    # Simulate a machine with no Chromium-family browser installed
    monkeypatch.setattr(pdf_export, "find_chrome", lambda: None)
    assert pdf_export.render_pdf(html, out, chrome=None) is False
    assert not out.exists()


def test_render_pdf_false_when_html_missing(tmp_path):
    assert pdf_export.render_pdf(
        tmp_path / "nope.html", tmp_path / "x.pdf",
        chrome="/bin/false",
    ) is False


def test_render_pdf_false_on_bad_browser(tmp_path):
    html = tmp_path / "r.html"
    html.write_text("<html><body>hi</body></html>")
    # Non-Chrome executable → subprocess fails → graceful False
    assert pdf_export.render_pdf(html, tmp_path / "r.pdf",
                                 chrome="/bin/false") is False

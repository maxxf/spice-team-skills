from __future__ import annotations

"""HTML → PDF via headless Chrome/Chromium.

Isolated so the orchestrator stays renderer-pure and so Chrome discovery is
unit-testable. Used by scripts/run_diagnostic.py --pdf. Degrades gracefully:
if no Chromium-family browser is found, render_pdf returns False and the caller
prints actionable fallback instructions (the self-contained report.html still
exists and prints from any browser).
"""

import shutil
import subprocess
from pathlib import Path

# macOS app bundles + PATH names, in preference order.
_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
)
_PATH_NAMES = ("google-chrome", "chromium", "chromium-browser", "chrome", "msedge")


def find_chrome() -> str | None:
    """Return a usable Chromium-family executable path, or None."""
    for p in _CANDIDATES:
        if Path(p).exists():
            return p
    for name in _PATH_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def render_pdf(html_path: Path, pdf_path: Path, *, chrome: str | None = None) -> bool:
    """Print `html_path` to `pdf_path`. Return True on success, False if no
    browser is available or the render fails (caller handles fallback)."""
    chrome = chrome or find_chrome()
    if not chrome:
        return False
    html_path = Path(html_path)
    pdf_path = Path(pdf_path)
    if not html_path.exists():
        return False
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        subprocess.run(
            [
                chrome, "--headless", "--disable-gpu",
                "--no-pdf-header-footer",
                "--virtual-time-budget=15000",
                f"--print-to-pdf={pdf_path}",
                html_path.resolve().as_uri(),
            ],
            check=True,
            capture_output=True,
            timeout=120,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    return pdf_path.exists() and pdf_path.stat().st_size > 0

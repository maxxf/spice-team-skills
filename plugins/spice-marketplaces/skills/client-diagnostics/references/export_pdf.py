"""
PDF export helper for the client-diagnostics skill.

Takes a self-contained HTML report (charts base64-inlined) and produces a
single-file PDF via Chrome headless. The PDF is what gets emailed to the
client; the HTML is the analyst's working source.

Usage:
    python export_pdf.py report.html report.pdf

Notes:
    - Requires Google Chrome installed at the standard macOS path. The skill
      assumes a Mac runtime (Spice team uses Macs).
    - The HTML must be self-contained (no external image URLs) so the PDF
      doesn't need network access at render time.
    - PDF page size defaults to Chrome's "Letter" preset.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

CHROME_PATHS = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
]


def find_chrome() -> str:
    for p in CHROME_PATHS:
        if Path(p).exists():
            return p
    found = shutil.which("google-chrome") or shutil.which("chromium")
    if found:
        return found
    raise FileNotFoundError(
        "Chrome/Chromium not found. Install Chrome or update CHROME_PATHS."
    )


def html_to_pdf(html_path: Path, pdf_path: Path) -> Path:
    """Render `html_path` to a PDF at `pdf_path` via Chrome headless."""
    chrome = find_chrome()
    html_abs = html_path.resolve()
    pdf_abs = pdf_path.resolve()

    cmd = [
        chrome,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        "--no-margins",
        "--virtual-time-budget=5000",
        f"--print-to-pdf={pdf_abs}",
        f"file://{html_abs}",
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)

    if not pdf_abs.exists():
        raise RuntimeError(f"PDF was not written to {pdf_abs}")
    return pdf_abs


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print("usage: export_pdf.py <report.html> <report.pdf>", file=sys.stderr)
        return 2
    html_path = Path(argv[1])
    pdf_path = Path(argv[2])
    if not html_path.exists():
        print(f"HTML not found: {html_path}", file=sys.stderr)
        return 1
    out = html_to_pdf(html_path, pdf_path)
    print(f"PDF written: {out} ({out.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

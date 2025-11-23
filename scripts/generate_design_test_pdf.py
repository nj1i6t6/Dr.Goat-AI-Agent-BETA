#!/usr/bin/env python3
"""Generate a PDF version of the Goat Nutrition design & test document.

This script reads the Markdown source file and produces a PDF using the
ReportLab toolkit with a built-in Unicode CID font so that Traditional
Chinese characters render correctly without bundling extra font files.

Usage (from repository root):
    python scripts/generate_design_test_pdf.py [input_md] [output_pdf]

If paths are omitted, the script defaults to:
    input_md = docs/領頭羊博士設計測試文件.md
    output_pdf = docs/領頭羊博士設計測試文件.pdf
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

try:
    from reportlab.pdfbase import pdfmetrics  # type: ignore[import-not-found]
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont  # type: ignore[import-not-found]
    from reportlab.pdfgen import canvas  # type: ignore[import-not-found]
    from reportlab.lib.pagesizes import A4  # type: ignore[import-not-found]
except ImportError as exc:  # pragma: no cover - user environment dependency
    raise SystemExit(
        "ReportLab is required. Install it with `python -m pip install reportlab`"
    ) from exc


DEFAULT_INPUT = Path("docs/領頭羊博士設計測試文件.md")
DEFAULT_OUTPUT = Path("docs/領頭羊博士設計測試文件.pdf")
FONT_NAME = "HeiseiMin-W3"  # Built-in CID font shipped with ReportLab
FONT_SIZE = 12
LINE_HEIGHT = 16
LEFT_MARGIN = 40
TOP_MARGIN = 800
BOTTOM_MARGIN = 60
WRAP_WIDTH = 38  # Max characters per line before wrapping (full-width friendly)


def normalise_paths(argv: list[str]) -> tuple[Path, Path]:
    """Resolve input and output paths from argv."""
    if len(argv) > 2:
        input_path = Path(argv[1])
        output_path = Path(argv[2])
    elif len(argv) == 2:
        input_path = Path(argv[1])
        output_path = DEFAULT_OUTPUT
    else:
        input_path = DEFAULT_INPUT
        output_path = DEFAULT_OUTPUT
    if not input_path.is_absolute():
        input_path = (Path.cwd() / input_path).resolve()
    if not output_path.is_absolute():
        output_path = (Path.cwd() / output_path).resolve()
    return input_path, output_path


def load_markdown_lines(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    lines: list[str] = []
    for raw_line in text.splitlines():
        if not raw_line.strip():
            lines.append("")
            continue
        indent = len(raw_line) - len(raw_line.lstrip())
        wrapper = textwrap.TextWrapper(
            width=WRAP_WIDTH,
            break_long_words=False,
            break_on_hyphens=False,
            replace_whitespace=False,
            subsequent_indent=" " * indent,
        )
        wrapped = wrapper.wrap(raw_line)
        if wrapped:
            lines.extend(wrapped)
        else:
            lines.append("")
    return lines


def ensure_font_registered() -> None:
    """Register the Unicode CID font if it hasn't been registered."""
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))


def write_pdf(lines: list[str], output_path: Path) -> None:
    ensure_font_registered()
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setFont(FONT_NAME, FONT_SIZE)
    y = TOP_MARGIN
    for line in lines:
        if y < BOTTOM_MARGIN:
            c.showPage()
            c.setFont(FONT_NAME, FONT_SIZE)
            y = TOP_MARGIN
        c.drawString(LEFT_MARGIN, y, line)
        y -= LINE_HEIGHT
    c.save()


def main(argv: list[str]) -> None:
    input_path, output_path = normalise_paths(argv)
    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")
    lines = load_markdown_lines(input_path)
    write_pdf(lines, output_path)
    print(f"PDF generated at {output_path}")


if __name__ == "__main__":
    main(sys.argv)

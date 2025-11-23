"""Utility to aggregate code metrics into docs/code_metrics.md."""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

CODE_METRICS_JSON = DOCS / "code_metrics.json"
RADON_CC = DOCS / "radon_cc.txt"
RADON_MI = DOCS / "radon_mi.txt"
OUTPUT = DOCS / "code_metrics.md"


def _read_json(path: Path):
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return json.loads(raw.decode(encoding))
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", raw, 0, 0, "Unable to decode metrics JSON")


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    for encoding in ("utf-8", "utf-16", "utf-16-le", "utf-16-be"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise UnicodeDecodeError("utf-8", raw, 0, 0, "Unable to decode text file")


def load_code_metrics():
    data = _read_json(CODE_METRICS_JSON)
    summary = data["summary"]
    languages = data["languages"]

    name_map = {
        "IPython": "Python",
        "CSS+Lasso": "CSS",
        "JavaScript+Genshi Text": "JavaScript (templated)",
        "JavaScript+Django/Jinja": "JavaScript (templated)",
        "JavaScript+Lasso": "JavaScript (templated)",
    }

    lang_totals: dict[str, dict[str, int]] = {}
    for entry in languages:
        if entry.get("isPseudoLanguage"):
            continue
        lang = name_map.get(entry["language"], entry["language"])
        stats = lang_totals.setdefault(lang, {"files": 0, "source": 0, "comments": 0, "empty": 0})
        stats["files"] += entry["fileCount"]
        stats["source"] += entry["sourceCount"]
        stats["comments"] += entry["documentationCount"]
        stats["empty"] += entry["emptyCount"]

    ordered = sorted(lang_totals.items(), key=lambda kv: kv[1]["source"], reverse=True)
    return summary, ordered, data["runtime"]["finishedAt"]


def load_radon_cc():
    text = _read_text(RADON_CC)
    grades = re.findall(r"- ([A-F]) ", text)
    counts = Counter(grades)
    avg_line = next((line for line in text.splitlines() if line.startswith("Average complexity")), "")

    worst_blocks = []
    current_file = None
    for line in text.splitlines():
        if not line.startswith(" ") and line:
            current_file = line.strip()
            continue
        match = re.search(r"- ([BCDEF]) \((\d+)\)", line)
        if match and current_file:
            grade = match.group(1)
            score = int(match.group(2))
            block = line.strip().split(" - ", 1)[0]
            worst_blocks.append((grade, score, current_file, block))

    worst_blocks.sort(key=lambda item: (-ord(item[0]), -item[1]))  # prioritize poorer grades
    return counts, avg_line, worst_blocks[:10]


def load_radon_mi():
    grades = Counter()
    for line in _read_text(RADON_MI).splitlines():
        if " - " not in line:
            continue
        _, grade = line.rsplit(" - ", 1)
        grades[grade] += 1
    return grades


def estimate_tokens(total_source: int, avg_chars_per_line: int = 60, chars_per_token: int = 4) -> int:
    return round(total_source * avg_chars_per_line / chars_per_token)


def build_markdown():
    summary, languages, finished_at = load_code_metrics()
    radon_cc_counts, avg_line, worst_blocks = load_radon_cc()
    radon_mi_counts = load_radon_mi()

    total_source = summary["totalSourceCount"]
    total_comments = summary["totalDocumentationCount"]
    total_empty = summary["totalEmptyCount"]
    total_files = summary["totalFileCount"]
    est_tokens = estimate_tokens(total_source)

    lines = []
    lines.append("# Codebase Metrics Summary\n")
    lines.append(f"Generated: {finished_at} UTC  ")
    lines.append("Directories scanned: `backend`, `frontend/src`, `scripts`, `iot_simulator`  ")
    lines.append("Extensions counted: `py`, `js`, `ts`, `tsx`, `vue`, `css`, `scss`, `html`\n")

    lines.append("## Size Snapshot")
    lines.append(f"- Source lines: {total_source:,}")
    lines.append(f"- Comment lines: {total_comments:,}")
    lines.append(f"- Empty lines: {total_empty:,}")
    lines.append(f"- Files counted: {total_files:,}")
    lines.append(f"- Estimated tokens (~60 chars/line, ~4 chars/token): ~{est_tokens:,}\n")

    lines.append("## Language Breakdown")
    lines.append("| Language | Files | Source LOC | Comment LOC | Empty LOC | Source Share |")
    lines.append("| --- | ---: | ---: | ---: | ---: | ---: |")
    for name, stats in languages:
        share = stats["source"] / total_source if total_source else 0
        lines.append(
            f"| {name} | {stats['files']:,} | {stats['source']:,} | {stats['comments']:,} | {stats['empty']:,} | {share:.1%} |"
        )

    lines.append("\n> Notes\n> - pygount labels `.py` files as \"IPython\"; values are consolidated under **Python**.\n> - \"JavaScript (templated)\" aggregates pygount categories that contain embedded template syntax (Genshi, Django/Jinja, Lasso).\n> - Duplicate fixture files were skipped automatically by pygount.\n")

    lines.append("## Python Complexity (radon cc)")
    lines.append(f"- Average complexity: {avg_line.split(':', 1)[-1].strip() if avg_line else 'n/a'}")
    grade_order = ["A", "B", "C", "D", "E", "F"]
    grade_line = ", ".join(
        f"{grade}: {radon_cc_counts.get(grade, 0)}" for grade in grade_order if radon_cc_counts.get(grade, 0)
    )
    lines.append(f"- Blocks per grade: {grade_line if grade_line else 'n/a'}")
    if worst_blocks:
        lines.append("- Hot spots (top 10 by grade/score):")
        for grade, score, file_path, block in worst_blocks:
            lines.append(f"  - {grade} ({score}): `{file_path}` → `{block}`")
    lines.append("")

    lines.append("## Python Maintainability (radon mi)")
    mi_grade_line = ", ".join(
        f"{grade}: {radon_mi_counts.get(grade, 0)}" for grade in grade_order if radon_mi_counts.get(grade, 0)
    )
    lines.append(f"- Files per grade: {mi_grade_line if mi_grade_line else 'n/a'}\n")

    lines.append("## Raw Reports")
    lines.append("- pygount JSON: `docs/code_metrics.json`")
    lines.append("- radon cyclomatic complexity: `docs/radon_cc.txt`")
    lines.append("- radon maintainability index: `docs/radon_mi.txt`\n")

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    build_markdown()


if __name__ == "__main__":
    main()

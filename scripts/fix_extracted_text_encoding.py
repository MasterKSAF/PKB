# -*- coding: utf-8 -*-
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from ftfy import fix_text

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGETS = [ROOT / "data" / "extracted_text"]
HIGH_LATIN_RE = re.compile(r"[\u0080-\u00ff]+")


def count_cyrillic(text: str) -> int:
    return sum("\u0400" <= ch <= "\u04ff" for ch in text)


def count_high_latin(text: str) -> int:
    return sum("\u0080" <= ch <= "\u00ff" for ch in text)


def candidate_score(text: str) -> tuple[int, int, int]:
    """Higher is better: Cyrillic is useful, high Latin/control mojibake is not."""
    cyrillic = count_cyrillic(text)
    useful_symbols = sum(ch in "№«»—–" for ch in text)
    high_latin = count_high_latin(text)
    replacement = text.count("\ufffd")
    return (cyrillic + useful_symbols * 2, -high_latin, -replacement)


def fix_high_latin_chunk(match: re.Match[str]) -> str:
    chunk = match.group(0)
    candidates = [chunk]

    for encoding in ("utf-8", "cp1251"):
        try:
            candidates.append(chunk.encode("latin1").decode(encoding))
        except UnicodeDecodeError:
            continue

    best = max(candidates, key=candidate_score)
    if candidate_score(best) > candidate_score(chunk):
        return best
    return chunk


def fix_text_encoding(text: str) -> str:
    # First fix fragments that are stored as Latin-1 characters but represent
    # either UTF-8 or cp1251 bytes. Then let ftfy clean classic mojibake.
    text = HIGH_LATIN_RE.sub(fix_high_latin_chunk, text)
    return fix_text(text)


def iter_text_files(targets: list[Path]) -> list[Path]:
    files: list[Path] = []
    for target in targets:
        if target.is_file() and target.suffix.lower() == ".txt":
            files.append(target)
        elif target.is_dir():
            files.extend(path for path in target.rglob("*.txt") if path.is_file())
    return sorted(files)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="rewrite changed files")
    parser.add_argument("targets", nargs="*", type=Path)
    args = parser.parse_args()

    targets = [path if path.is_absolute() else ROOT / path for path in args.targets]
    if not targets:
        targets = DEFAULT_TARGETS

    changed: list[tuple[Path, int, int, int, int]] = []
    for path in iter_text_files(targets):
        try:
            before = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            before = path.read_text(encoding="cp1251")

        after = fix_text_encoding(before)
        if after == before:
            continue

        cyr_before = count_cyrillic(before)
        cyr_after = count_cyrillic(after)
        high_before = count_high_latin(before)
        high_after = count_high_latin(after)
        if cyr_after <= cyr_before and high_after >= high_before:
            continue

        changed.append(
            (
                path,
                cyr_before,
                cyr_after,
                high_before,
                high_after,
            )
        )
        if args.apply:
            path.write_text(after, encoding="utf-8", newline="")

    print(f"targets={len(iter_text_files(targets))}")
    print(f"changed={len(changed)}")
    print(f"mode={'apply' if args.apply else 'dry-run'}")
    for path, cyr_before, cyr_after, high_before, high_after in changed[:80]:
        rel = str(path.relative_to(ROOT))
        line = (
            f"{rel}\t"
            f"cyrillic={cyr_before}->{cyr_after}\t"
            f"high_latin={high_before}->{high_after}"
        )
        print(line.encode("ascii", errors="backslashreplace").decode("ascii"))


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        sys.exit(0)

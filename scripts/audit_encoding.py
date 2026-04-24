# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT_CSV = ROOT / "docs" / "encoding_audit.csv"
OUT_MD = ROOT / "docs" / "encoding_audit.md"
IGNORED_FILES = {
    Path("scripts/audit_encoding.py"),
    Path("scripts/read_knowledge_base.py"),
}

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".py",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".xml",
    ".html",
    ".htm",
    ".log",
}


def mojibake_tokens() -> set[str]:
    """Build mojibake signatures without storing Cyrillic literals."""
    codepoints = list(range(0x0410, 0x0450)) + [0x0401, 0x0451]
    codepoints += [0x2014, 0x2013, 0x00AB, 0x00BB, 0x2116, 0x2026]

    tokens: set[str] = set()
    for cp in codepoints:
        ch = chr(cp)
        for wrong_encoding in ("cp1251", "latin1"):
            try:
                bad = ch.encode("utf-8").decode(wrong_encoding)
            except UnicodeDecodeError:
                continue
            if bad != ch and len(bad) >= 2:
                tokens.add(bad)

    tokens.update(
        {
            chr(0xFFFD),
            chr(0x00D0),
            chr(0x00D1),
            chr(0x00C3),
            chr(0x00C2),
            chr(0x00E2) + chr(0x20AC) + chr(0x2122),
            chr(0x00E2) + chr(0x20AC) + chr(0x0153),
            chr(0x00E2) + chr(0x20AC),
            chr(0x00C2) + chr(0x00AB),
            chr(0x00C2) + chr(0x00BB),
        }
    )
    tokens.discard("?")
    tokens.discard("??")
    tokens.discard("???")
    return tokens


def read_text(path: Path) -> tuple[str, str]:
    data = path.read_bytes()
    try:
        return data.decode("utf-8"), "utf-8"
    except UnicodeDecodeError:
        pass

    try:
        return data.decode("cp1251"), "cp1251"
    except UnicodeDecodeError:
        pass

    return data.decode("utf-8", errors="replace"), "unknown"


def snippet(text: str, token: str) -> str:
    idx = text.find(token)
    if idx < 0:
        return ""
    start = max(0, idx - 90)
    end = min(len(text), idx + 190)
    return text[start:end].replace("\r", " ").replace("\n", " ")


def count_token_hits(text: str, token: str) -> int:
    count = 0
    start = 0
    close_guillemet = chr(0x00BB)
    open_guillemet = chr(0x00AB)
    ellipsis = chr(0x2026)

    while True:
        idx = text.find(token, start)
        if idx < 0:
            return count

        # A token ending with a closing guillemet can be real mojibake, but in
        # this knowledge base it often appears correctly inside quoted labels.
        is_quoted_fragment = (
            len(token) == 2
            and token[1] == close_guillemet
            and "\u0400" <= token[0] <= "\u04ff"
            and open_guillemet in text[max(0, idx - 500) : idx]
        )
        is_toc_ellipsis = (
            token == (chr(0x0421) + ellipsis)
            and text[idx + len(token) : idx + len(token) + 2] == ellipsis * 2
        )
        if not is_quoted_fragment and not is_toc_ellipsis:
            count += 1
        start = idx + len(token)


def main() -> None:
    tokens = mojibake_tokens()
    rows = []
    scanned = 0

    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.relative_to(ROOT) in IGNORED_FILES:
            continue
        if path == OUT_CSV or path == OUT_MD:
            continue

        scanned += 1
        try:
            text, encoding = read_text(path)
        except OSError as exc:
            rows.append(
                {
                    "file": str(path.relative_to(ROOT)),
                    "encoding": "read_error",
                    "score": 0,
                    "top_tokens": "",
                    "sample": str(exc),
                }
            )
            continue

        hits = {
            token: count
            for token in tokens
            if (count := count_token_hits(text, token))
        }
        if not hits:
            continue

        top = sorted(hits.items(), key=lambda item: item[1], reverse=True)[:8]
        rows.append(
            {
                "file": str(path.relative_to(ROOT)),
                "encoding": encoding,
                "score": sum(hits.values()),
                "top_tokens": "; ".join(f"{token!r}:{count}" for token, count in top),
                "sample": snippet(text, top[0][0]) if top else "",
            }
        )

    rows.sort(key=lambda row: int(row["score"]), reverse=True)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["file", "encoding", "score", "top_tokens", "sample"]
        )
        writer.writeheader()
        writer.writerows(rows)

    lines = [
        "# Encoding audit",
        "",
        f"- Text files scanned: {scanned}",
        f"- Files with mojibake signatures: {len(rows)}",
        "",
    ]
    if rows:
        lines.extend(["| file | score | tokens | sample |", "| --- | ---: | --- | --- |"])
        for row in rows:
            sample = row["sample"].replace("|", "\\|")
            tokens_summary = row["top_tokens"].replace("|", "\\|")
            lines.append(
                f"| `{row['file']}` | {row['score']} | `{tokens_summary}` | {sample[:240]} |"
            )
    else:
        lines.append("No mojibake signatures were found.")

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"scanned={scanned}")
    print(f"suspicious={len(rows)}")
    print(f"csv={OUT_CSV}")
    print(f"md={OUT_MD}")
    for row in rows[:20]:
        line = f"{row['score']}\t{row['file']}\t{row['top_tokens']}"
        print(line.encode("ascii", errors="backslashreplace").decode("ascii"))


if __name__ == "__main__":
    main()

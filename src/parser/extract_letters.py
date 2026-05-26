#!/usr/bin/env python3
"""M1 — Core Parser: Letter Extraction

Parses the Tanzil Uthmani XML and extracts every letter instance with
positional indices (surah, verse, word, position within word, global).

Output: data/processed/letters.csv
  327,793 rows (one per letter instance), columns:
    mushaf_pos, surah, verse, word_idx, char_idx, letter, codepoint
"""

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from src.parser.verify_source import DEFAULT_SOURCE, LETTER_SET


def extract_letters(source_path: str = None) -> list[dict]:
    """Extract every letter instance from the Tanzil XML.

    Returns list of dicts with keys:
        mushaf_pos, surah, verse, word_idx, char_idx, letter, codepoint
    """
    if source_path is None:
        source_path = DEFAULT_SOURCE

    tree = ET.parse(source_path)
    root = tree.getroot()

    rows = []
    mushaf_pos = 0

    for sura in root.findall("sura"):
        surah_num = int(sura.get("index"))
        for aya in sura.findall("aya"):
            verse_num = int(aya.get("index"))
            for attr_name in ("bismillah", "text"):
                text = aya.get(attr_name)
                if text is None:
                    continue
                words = text.split(" ")
                for word_idx, word in enumerate(words):
                    char_idx = 0
                    for ch in word:
                        cp = ord(ch)
                        if cp in LETTER_SET:
                            rows.append({
                                "mushaf_pos": mushaf_pos,
                                "surah": surah_num,
                                "verse": verse_num,
                                "word_idx": word_idx,
                                "char_idx": char_idx,
                                "letter": ch,
                                "codepoint": f"U+{cp:04X}",
                            })
                            mushaf_pos += 1
                            char_idx += 1

    return rows


FIELDNAMES = ["mushaf_pos", "surah", "verse", "word_idx", "char_idx", "letter", "codepoint"]


def write_csv(rows: list[dict], output_path: str) -> int:
    """Write letter rows to CSV. Returns row count."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="M1: Extract letters from Tanzil XML")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output", default=str(
        Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "letters.csv"
    ))
    args = parser.parse_args()

    rows = extract_letters(args.source)
    count = write_csv(rows, args.output)
    print(f"Extracted {count:,} letter instances → {args.output}")


if __name__ == "__main__":
    main()

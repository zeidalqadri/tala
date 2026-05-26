#!/usr/bin/env python3
"""M2 — Diacritical Stream Extraction

Enriches letter rows with diacritic information. For each letter, captures:
- primary diacritic (the main vowel/sukoon/shadda immediately following)
- all diacritics attached to this letter (ordered as they appear)
- has_shadda flag
- has_tanween flag
- tanween_type (fathatan/kasratan/dammatan or empty)

Output: data/processed/letters_with_diacritics.csv
"""

import csv
import xml.etree.ElementTree as ET
from pathlib import Path

from src.parser.verify_source import (
    DEFAULT_SOURCE, LETTER_SET, DIACRITIC_SET,
    EXPECTED_DIACRITIC_COUNTS,
)

# Primary vowel diacritics (harakat)
HARAKAT = {
    0x064E,  # FATHA
    0x064F,  # DAMMA
    0x0650,  # KASRA
    0x0652,  # SUKUN
}

# Tanween marks
TANWEEN = {
    0x064B: "fathatan",
    0x064C: "dammatan",
    0x064D: "kasratan",
}

SHADDA = 0x0651

FIELDNAMES = [
    "mushaf_pos", "surah", "verse", "word_idx", "char_idx",
    "letter", "codepoint",
    "primary_diacritic", "primary_diacritic_cp",
    "all_diacritics", "all_diacritics_cps",
    "has_shadda", "has_tanween", "tanween_type",
]


def extract_letters_with_diacritics(source_path: str = None) -> list[dict]:
    """Extract letters with their attached diacritics from the Tanzil XML.

    Diacritics are attached to the preceding letter. We walk through the text
    character by character: when we see a letter, we start a new entry; when we
    see diacritics, they attach to the current letter.
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
                    current_letter = None
                    char_idx = 0

                    for ch in word:
                        cp = ord(ch)
                        if cp in LETTER_SET:
                            # Flush previous letter if exists
                            if current_letter is not None:
                                rows.append(current_letter)
                            # Start new letter entry
                            current_letter = {
                                "mushaf_pos": mushaf_pos,
                                "surah": surah_num,
                                "verse": verse_num,
                                "word_idx": word_idx,
                                "char_idx": char_idx,
                                "letter": ch,
                                "codepoint": f"U+{cp:04X}",
                                "primary_diacritic": "",
                                "primary_diacritic_cp": "",
                                "all_diacritics": "",
                                "all_diacritics_cps": "",
                                "has_shadda": False,
                                "has_tanween": False,
                                "tanween_type": "",
                            }
                            mushaf_pos += 1
                            char_idx += 1
                        elif cp in DIACRITIC_SET and current_letter is not None:
                            # Attach diacritic to current letter
                            diacritics = current_letter["all_diacritics"]
                            diacritics_cps = current_letter["all_diacritics_cps"]
                            current_letter["all_diacritics"] += ch
                            current_letter["all_diacritics_cps"] += (
                                ("+" if diacritics_cps else "") + f"U+{cp:04X}"
                            )

                            # Classify
                            if cp == SHADDA:
                                current_letter["has_shadda"] = True
                            if cp in TANWEEN:
                                current_letter["has_tanween"] = True
                                current_letter["tanween_type"] = TANWEEN[cp]
                            if cp in HARAKAT and not current_letter["primary_diacritic"]:
                                current_letter["primary_diacritic"] = ch
                                current_letter["primary_diacritic_cp"] = f"U+{cp:04X}"
                            # If no primary yet and this is shadda/tanween, primary stays empty
                            # until a haraka is found (shadda + fatha → primary = fatha)

                    # Flush last letter of word
                    if current_letter is not None:
                        rows.append(current_letter)
                        current_letter = None

    return rows


def write_csv(rows: list[dict], output_path: str) -> int:
    """Write enriched letter rows to CSV."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main():
    import argparse
    parser = argparse.ArgumentParser(description="M2: Extract letters with diacritics")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output", default=str(
        Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "letters_with_diacritics.csv"
    ))
    args = parser.parse_args()

    rows = extract_letters_with_diacritics(args.source)
    count = write_csv(rows, args.output)

    # Summary stats
    shadda_count = sum(1 for r in rows if r["has_shadda"])
    tanween_count = sum(1 for r in rows if r["has_tanween"])
    print(f"Extracted {count:,} letter instances with diacritics → {args.output}")
    print(f"  has_shadda: {shadda_count:,}")
    print(f"  has_tanween: {tanween_count:,}")


if __name__ == "__main__":
    main()

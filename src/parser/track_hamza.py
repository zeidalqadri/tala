#!/usr/bin/env python3
"""M4 — Hamza Seat Tracking

Identifies the hamza seat for every letter instance.
Hamza is one sound (glottal stop) with five visual seats:

    alif_above   : أ  (U+0623) — alif with hamza above
    alif_below   : إ  (U+0625) — alif with hamza below
    waw          : ؤ  (U+0624) — waw with hamza above
    ya           : ئ  (U+0626) — ya with hamza above (no dots on ya body)
    standalone   : ء  (U+0621) — free-standing hamza
    none         : all other letters

Additional flags:
    has_maddah         : True when a letter carries U+0653 (maddah above).
                         Appears on 22 different letter types (5,376 total).
                         Most frequent on bare alif (U+0627, 2,945×) and
                         alif maqsura (U+0649, 839×). Recorded as observed —
                         no external interpretation imposed.
    has_combining_hamza: True when a letter carries U+0654
                         (combining hamza above as a separate diacritic mark,
                          496 instances in the corpus).

Output: data/processed/letters_with_hamza.csv
"""

import csv
from pathlib import Path

from src.parser.decompose_shadda import classify_shadda, FIELDNAMES as M3_FIELDNAMES
from src.parser.extract_diacritics import extract_letters_with_diacritics
from src.parser.verify_source import DEFAULT_SOURCE

# Hamza seat codepoints
HAMZA_SEATS = {
    0x0621: "standalone",   # ARABIC LETTER HAMZA
    0x0623: "alif_above",   # ARABIC LETTER ALEF WITH HAMZA ABOVE
    0x0624: "waw",          # ARABIC LETTER WAW WITH HAMZA ABOVE
    0x0625: "alif_below",   # ARABIC LETTER ALEF WITH HAMZA BELOW
    0x0626: "ya",           # ARABIC LETTER YEH WITH HAMZA ABOVE
}

MADDAH_ABOVE = 0x0653       # signals آ in this decomposed encoding
COMBINING_HAMZA_ABOVE = 0x0654


def _has_diacritic(row: dict, cp: int) -> bool:
    """Return True if the diacritic codepoint appears in the row's diacritic list.

    all_diacritics_cps is formatted as 'U+XXXX' or 'U+XXXX+U+YYYY+...'.
    All Arabic diacritic codepoints use exactly 4 hex digits, so a direct
    substring search for 'U+XXXX' is unambiguous.
    """
    cps_field = row.get("all_diacritics_cps", "")
    if not cps_field:
        return False
    return f"U+{cp:04X}" in cps_field


def assign_hamza_seats(rows: list[dict]) -> list[dict]:
    """Add hamza seat columns to each letter row.

    New columns:
        hamza_seat          : seat label or 'none'
        is_alif_madda       : True/False
        has_combining_hamza : True/False
    """
    result = []
    for row in rows:
        new_row = dict(row)
        cp = int(row["codepoint"][2:], 16)

        new_row["hamza_seat"] = HAMZA_SEATS.get(cp, "none")
        new_row["has_maddah"] = _has_diacritic(row, MADDAH_ABOVE)
        new_row["has_combining_hamza"] = _has_diacritic(row, COMBINING_HAMZA_ABOVE)

        result.append(new_row)
    return result


FIELDNAMES = M3_FIELDNAMES + [
    "hamza_seat", "has_maddah", "has_combining_hamza",
]


def write_csv(rows: list[dict], output_path: str) -> int:
    """Write enriched rows to CSV. Returns row count."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main():
    import argparse
    from collections import Counter
    parser = argparse.ArgumentParser(description="M4: Hamza seat tracking")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output", default=str(
        Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "letters_with_hamza.csv"
    ))
    args = parser.parse_args()

    raw = extract_letters_with_diacritics(args.source)
    rows = classify_shadda(raw)
    rows = assign_hamza_seats(rows)
    count = write_csv(rows, args.output)

    seat_counts = Counter(r["hamza_seat"] for r in rows)
    madda_count = sum(1 for r in rows if r["has_maddah"])
    combining_count = sum(1 for r in rows if r["has_combining_hamza"])

    print(f"Wrote {count:,} rows → {args.output}")
    print("Hamza seats:")
    for seat, n in sorted(seat_counts.items(), key=lambda x: -x[1]):
        if seat != "none":
            print(f"  {seat}: {n:,}")
    print(f"  none (non-hamza): {seat_counts['none']:,}")
    print(f"has_maddah=True: {madda_count:,}")
    print(f"has_combining_hamza=True: {combining_count:,}")


if __name__ == "__main__":
    main()

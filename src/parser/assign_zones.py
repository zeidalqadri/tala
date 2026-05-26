#!/usr/bin/env python3
"""M5 — Articulatory Zone Assignment

Assigns each letter instance to one of 6 primary articulatory zones based
on its anatomical place of production. Zone 7 (الخيشوم, nasal passage) is
a secondary articulation — not a primary zone — encoded as the boolean
`has_ghunna`.

The 6 primary zones (anatomical geography, admissible as physical fact):

    Zone 1  جوف         Empty Space   — ا و(madd) ي(madd) ى ٱ
    Zone 2  أقصى الحلق  Deepest Throat — ء أ إ ؤ ئ هـ
    Zone 3  وسط الحلق   Middle Throat  — ع ح
    Zone 4  أدنى الحلق  Upper Throat   — غ خ
    Zone 5  اللسان      Tongue         — ق ك ج ش ض ل ن ر ط د ت ص ز س ظ ذ ث ة ي(cons.)
    Zone 6  الشفتان     Lips           — ب ف م و(cons.)

Secondary nasal articulation (has_ghunna=True):
    - ن (all instances) — inherent nasality
    - م (all instances) — inherent nasality
    - any letter with has_tanween=True — tanween encodes a shadow ن

و (U+0648) and ي (U+064A) are context-dependent:
    - Carries short vowel (fatha/kasra/damma on the letter itself) → consonantal
    - Sukoon or no harakat → madd (vowel prolongation) → zone 1

ة (ta marbuta, U+0629): anatomically same locus as ت. Assigned zone 5.
Distributional comparison with ت and هـ is a finding, not an assumption.

Output: data/processed/letters_with_zones.csv
"""

import csv
from pathlib import Path

from src.parser.track_hamza import assign_hamza_seats, FIELDNAMES as M4_FIELDNAMES
from src.parser.decompose_shadda import classify_shadda
from src.parser.extract_diacritics import extract_letters_with_diacritics
from src.parser.verify_source import DEFAULT_SOURCE

# Short vowel codepoints (fatha, damma, kasra)
# Presence of any of these on و or ي indicates consonantal articulation.
SHORT_VOWELS = frozenset({0x064E, 0x064F, 0x0650})

# Static zone map: letter codepoint → zone (1-6)
# و (0x0648) and ي (0x064A) are resolved contextually — not listed here.
ZONE_BY_CP = {
    # Zone 1 — Empty Space (الجوف)
    0x0627: 1,   # ALEF (bare — vowel carrier)
    0x0649: 1,   # ALEF MAQSURA (word-final long vowel)
    0x0671: 1,   # ALEF WASLA

    # Zone 2 — Deepest Throat (أقصى الحلق)
    0x0621: 2,   # ARABIC LETTER HAMZA (standalone)
    0x0623: 2,   # ALEF WITH HAMZA ABOVE
    0x0624: 2,   # WAW WITH HAMZA ABOVE
    0x0625: 2,   # ALEF WITH HAMZA BELOW
    0x0626: 2,   # YEH WITH HAMZA ABOVE
    0x0647: 2,   # HEH

    # Zone 3 — Middle Throat (وسط الحلق)
    0x0639: 3,   # AIN
    0x062D: 3,   # HAH

    # Zone 4 — Upper Throat (أدنى الحلق)
    0x063A: 4,   # GHAIN
    0x062E: 4,   # KHAH

    # Zone 5 — Tongue (اللسان)
    0x0642: 5,   # QAF
    0x0643: 5,   # KAF
    0x062C: 5,   # JEEM
    0x0634: 5,   # SHEEN
    0x0636: 5,   # DAD
    0x0644: 5,   # LAM
    0x0646: 5,   # NOON
    0x0631: 5,   # REH
    0x0637: 5,   # TAH (emphatic)
    0x062F: 5,   # DAL
    0x062A: 5,   # TEH
    0x0635: 5,   # SAD (emphatic)
    0x0632: 5,   # ZAIN
    0x0633: 5,   # SEEN
    0x0638: 5,   # ZAH (emphatic)
    0x0630: 5,   # THAL
    0x062B: 5,   # THEH
    0x0629: 5,   # TEH MARBUTA (anatomically: same locus as ت)

    # Zone 6 — Lips (الشفتان)
    0x0628: 6,   # BA
    0x0641: 6,   # FEH
    0x0645: 6,   # MEEM
    # WAW (0x0648): consonantal → zone 6 (resolved contextually)
}

ZONE_NAMES = {
    1: "jawf",
    2: "aqsa_halq",
    3: "wasat_halq",
    4: "adna_halq",
    5: "lisan",
    6: "shafatan",
}

# Letters with inherent nasal secondary articulation
NASAL_CPS = frozenset({0x0646, 0x0645})  # noon, meem


def _primary_diacritic_cp_int(row: dict) -> int:
    """Return the primary diacritic codepoint as int, or 0 if absent."""
    pdcp = row.get("primary_diacritic_cp", "")
    if pdcp and pdcp.startswith("U+"):
        return int(pdcp[2:], 16)
    return 0


def _is_consonantal_waw_or_ya(row: dict) -> bool:
    """Return True if و or ي carries a short vowel (consonantal articulation).

    A short vowel on the letter itself marks it as a consonant.
    Sukoon or absence of harakat marks it as a madd (vowel prolongation) letter.
    """
    return _primary_diacritic_cp_int(row) in SHORT_VOWELS


def assign_zones(rows: list[dict]) -> list[dict]:
    """Add zone columns to each letter row.

    New columns:
        zone      : int 1-6 (primary articulatory zone)
        zone_name : str label (e.g. 'jawf', 'lisan')
        has_ghunna: bool — True for ن, م, and tanween-carrying letters
    """
    result = []
    for row in rows:
        new_row = dict(row)
        cp = int(row["codepoint"][2:], 16)

        # و and ي: context-dependent
        if cp == 0x0648:   # WAW
            zone = 6 if _is_consonantal_waw_or_ya(row) else 1
        elif cp == 0x064A:  # YEH
            zone = 5 if _is_consonantal_waw_or_ya(row) else 1
        else:
            zone = ZONE_BY_CP.get(cp, 0)

        new_row["zone"] = zone
        new_row["zone_name"] = ZONE_NAMES.get(zone, "unknown")
        new_row["has_ghunna"] = (cp in NASAL_CPS) or bool(row.get("has_tanween"))

        result.append(new_row)
    return result


FIELDNAMES = M4_FIELDNAMES + ["zone", "zone_name", "has_ghunna"]


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
    parser = argparse.ArgumentParser(description="M5: Articulatory zone assignment")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output", default=str(
        Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "letters_with_zones.csv"
    ))
    args = parser.parse_args()

    raw = extract_letters_with_diacritics(args.source)
    rows = classify_shadda(raw)
    rows = assign_hamza_seats(rows)
    rows = assign_zones(rows)
    count = write_csv(rows, args.output)

    zone_counts = Counter(r["zone"] for r in rows)
    ghunna_count = sum(1 for r in rows if r["has_ghunna"])

    print(f"Wrote {count:,} rows → {args.output}")
    print("Zone distribution:")
    for z in sorted(zone_counts):
        print(f"  Zone {z} ({ZONE_NAMES[z]}): {zone_counts[z]:,}")
    print(f"has_ghunna=True: {ghunna_count:,}")


if __name__ == "__main__":
    main()

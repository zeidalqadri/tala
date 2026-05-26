#!/usr/bin/env python3
"""M6 — Geometric Family Assignment

Assigns each letter instance its geometric family and dot configuration.
Letters are transformations of alif. Families group letters by shared base
geometry (the skeleton visible when dots are removed).

10 Families:
    cup       : ب ت ث ن ي (U-shaped trough)
    bowl      : ج ح خ (deep rounded open vessel)
    knee      : د ذ (right-angle bend)
    curve     : ر ز (smooth descending curve)
    teeth     : س ش (saw-tooth pattern)
    loop      : ص ض (closed loop with tail)
    cross     : ط ظ (vertical stroke crossing horizontal)
    hook      : ع غ (descending hook shape)
    circle    : ف ق (circular head on stem)
    singleton : ا ك ل م هـ و ة ء ٱ ى أ إ ؤ ئ (unique geometry, no family partner)

Two tiers:
    - base geometry (geometric_family): the skeleton shape
    - dot configuration (dot_count, dot_position): distinguishing marks

Non-connecting letters (cannot join to following letter in connected script):
    ا أ إ آ ٱ د ذ ر ز و ؤ ء

Output: data/processed/letters_with_geometry.csv
"""

import csv
from pathlib import Path

from src.parser.assign_zones import assign_zones, FIELDNAMES as M5_FIELDNAMES
from src.parser.track_hamza import assign_hamza_seats
from src.parser.decompose_shadda import classify_shadda
from src.parser.extract_diacritics import extract_letters_with_diacritics
from src.parser.verify_source import DEFAULT_SOURCE

# Geometric family assignment by codepoint
GEOMETRIC_FAMILY = {
    # cup family — U-shaped trough, distinguished by dots
    0x0628: "cup",   # BA (1 dot below)
    0x062A: "cup",   # TEH (2 dots above)
    0x062B: "cup",   # THEH (3 dots above)
    0x0646: "cup",   # NOON (1 dot above)
    0x064A: "cup",   # YEH (2 dots below)

    # bowl family — deep rounded vessel
    0x062C: "bowl",  # JEEM (1 dot below)
    0x062D: "bowl",  # HAH (no dots)
    0x062E: "bowl",  # KHAH (1 dot above)

    # knee family — right-angle bend
    0x062F: "knee",  # DAL (no dots)
    0x0630: "knee",  # THAL (1 dot above)

    # curve family — smooth descending curve
    0x0631: "curve", # REH (no dots)
    0x0632: "curve", # ZAIN (1 dot above)

    # teeth family — saw-tooth pattern
    0x0633: "teeth", # SEEN (no dots)
    0x0634: "teeth", # SHEEN (3 dots above)

    # loop family — closed loop with tail
    0x0635: "loop",  # SAD (no dots)
    0x0636: "loop",  # DAD (1 dot above)

    # cross family — vertical stroke crossing horizontal
    0x0637: "cross", # TAH (no dots)
    0x0638: "cross", # ZAH (1 dot above)

    # hook family — descending hook shape
    0x0639: "hook",  # AIN (no dots)
    0x063A: "hook",  # GHAIN (1 dot above)

    # circle family — circular head on stem
    0x0641: "circle",  # FA (1 dot above)
    0x0642: "circle",  # QAF (2 dots above)

    # singletons — unique geometry
    0x0627: "singleton",  # ALEF
    0x0623: "singleton",  # ALEF WITH HAMZA ABOVE
    0x0625: "singleton",  # ALEF WITH HAMZA BELOW
    0x0671: "singleton",  # ALEF WASLA
    0x0649: "singleton",  # ALEF MAQSURA
    0x0643: "singleton",  # KAF
    0x0644: "singleton",  # LAM
    0x0645: "singleton",  # MEEM
    0x0647: "singleton",  # HEH
    0x0648: "singleton",  # WAW
    0x0624: "singleton",  # WAW WITH HAMZA
    0x0629: "singleton",  # TEH MARBUTA
    0x0621: "singleton",  # HAMZA (standalone)
    0x0626: "singleton",  # YEH WITH HAMZA
}

# Dot configuration: (count, position)
# position: "above", "below", "none"
DOT_CONFIG = {
    # cup family
    0x0628: (1, "below"),   # BA
    0x062A: (2, "above"),   # TEH
    0x062B: (3, "above"),   # THEH
    0x0646: (1, "above"),   # NOON
    0x064A: (2, "below"),   # YEH

    # bowl family
    0x062C: (1, "below"),   # JEEM
    0x062D: (0, "none"),    # HAH
    0x062E: (1, "above"),   # KHAH

    # knee family
    0x062F: (0, "none"),    # DAL
    0x0630: (1, "above"),   # THAL

    # curve family
    0x0631: (0, "none"),    # REH
    0x0632: (1, "above"),   # ZAIN

    # teeth family
    0x0633: (0, "none"),    # SEEN
    0x0634: (3, "above"),   # SHEEN

    # loop family
    0x0635: (0, "none"),    # SAD
    0x0636: (1, "above"),   # DAD

    # cross family
    0x0637: (0, "none"),    # TAH
    0x0638: (1, "above"),   # ZAH

    # hook family
    0x0639: (0, "none"),    # AIN
    0x063A: (1, "above"),   # GHAIN

    # circle family
    0x0641: (1, "above"),   # FA
    0x0642: (2, "above"),   # QAF

    # singletons
    0x0627: (0, "none"),    # ALEF
    0x0623: (0, "none"),    # ALEF WITH HAMZA ABOVE (hamza is seat, not dot)
    0x0625: (0, "none"),    # ALEF WITH HAMZA BELOW
    0x0671: (0, "none"),    # ALEF WASLA
    0x0649: (0, "none"),    # ALEF MAQSURA
    0x0643: (0, "none"),    # KAF
    0x0644: (0, "none"),    # LAM
    0x0645: (0, "none"),    # MEEM
    0x0647: (0, "none"),    # HEH
    0x0648: (0, "none"),    # WAW
    0x0624: (0, "none"),    # WAW WITH HAMZA
    0x0629: (2, "above"),   # TEH MARBUTA (two dots above, heh body)
    0x0621: (0, "none"),    # HAMZA (standalone)
    0x0626: (0, "none"),    # YEH WITH HAMZA (dots disappear under hamza seat)
}

# Non-connecting letters (cannot join to following letter)
NON_CONNECTORS = frozenset({
    0x0627,  # ALEF
    0x0623,  # ALEF WITH HAMZA ABOVE
    0x0625,  # ALEF WITH HAMZA BELOW
    0x0671,  # ALEF WASLA
    0x0649,  # ALEF MAQSURA (in Uthmani, non-connecting)
    0x062F,  # DAL
    0x0630,  # THAL
    0x0631,  # REH
    0x0632,  # ZAIN
    0x0648,  # WAW
    0x0624,  # WAW WITH HAMZA
    0x0621,  # HAMZA (standalone)
})

# Letters sharing a base with others in their family
# Maps codepoint → frozenset of family partners (excluding self)
def _build_shares_base():
    """Build shares_base_with lookup from family definitions."""
    families = {}
    for cp, family in GEOMETRIC_FAMILY.items():
        if family != "singleton":
            families.setdefault(family, set()).add(cp)
    result = {}
    for cp, family in GEOMETRIC_FAMILY.items():
        if family != "singleton":
            result[cp] = frozenset(families[family] - {cp})
        else:
            result[cp] = frozenset()
    return result

SHARES_BASE_WITH = _build_shares_base()


def assign_geometry(rows: list[dict]) -> list[dict]:
    """Add geometric family and dot configuration columns to each letter row.

    New columns:
        geometric_family : family name (cup/bowl/knee/curve/teeth/loop/cross/hook/circle/singleton)
        dot_count        : number of distinguishing dots (0-3)
        dot_position     : "above", "below", or "none"
        is_non_connector : True if letter cannot join to following letter
    """
    result = []
    for row in rows:
        new_row = dict(row)
        cp = int(row["codepoint"][2:], 16)

        new_row["geometric_family"] = GEOMETRIC_FAMILY.get(cp, "singleton")
        dot_count, dot_pos = DOT_CONFIG.get(cp, (0, "none"))
        new_row["dot_count"] = dot_count
        new_row["dot_position"] = dot_pos
        new_row["is_non_connector"] = cp in NON_CONNECTORS

        result.append(new_row)
    return result


FIELDNAMES = M5_FIELDNAMES + [
    "geometric_family", "dot_count", "dot_position", "is_non_connector",
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
    parser = argparse.ArgumentParser(description="M6: Geometric family assignment")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output", default=str(
        Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "letters_with_geometry.csv"
    ))
    args = parser.parse_args()

    raw = extract_letters_with_diacritics(args.source)
    rows = classify_shadda(raw)
    rows = assign_hamza_seats(rows)
    rows = assign_zones(rows)
    rows = assign_geometry(rows)
    count = write_csv(rows, args.output)

    family_counts = Counter(r["geometric_family"] for r in rows)
    print(f"Wrote {count:,} rows → {args.output}")
    print("Geometric families:")
    for fam, n in sorted(family_counts.items(), key=lambda x: -x[1]):
        print(f"  {fam}: {n:,}")

    dot_counts = Counter(r["dot_count"] for r in rows)
    print("Dot counts:")
    for d in sorted(dot_counts.keys()):
        print(f"  {d} dots: {dot_counts[d]:,}")

    nc = sum(1 for r in rows if r["is_non_connector"])
    print(f"Non-connectors: {nc:,}")


if __name__ == "__main__":
    main()

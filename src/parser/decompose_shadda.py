#!/usr/bin/env python3
"""M3 — Shadda Decomposition

Classifies each of the 23,016 shadda instances by context:
  - true_doubling: root-internal or morphological doubling
  - al_assimilation: لام of definite article assimilated into sun letter
  - noon_assimilation: نون assimilated into the following letter (cross-word only)

Classification is purely context-based (preceding letters in the word).
No external grammar rules imported — only textual patterns observed.

Analytical choices:
  - noon_assimilation is cross-word only. Same-word noon+shadda is classified as
    true_doubling because within-word assimilation is structurally indistinguishable
    from morphological gemination (e.g. Form II تفعيل) without external morphological
    knowledge.
  - Tanween is treated as a shadow noon per the project's tanween framework (§2.7).
    Cross-word tanween→shadda is therefore classified as noon assimilation: tanween
    at the end of word A followed by a shadda'd letter at the start of word B is
    structurally identical to noon-at-end-of-A → shadda-at-start-of-B.

Output: data/processed/letters_with_shadda.csv
"""

import csv
from pathlib import Path

from src.parser.extract_diacritics import (
    extract_letters_with_diacritics, FIELDNAMES as M2_FIELDNAMES,
)
from src.parser.verify_source import DEFAULT_SOURCE

# Alif variants that can begin the definite article
ALIF_VARIANTS = frozenset({
    0x0627,  # ALEF
    0x0671,  # ALEF WASLA
    0x0623,  # ALEF WITH HAMZA ABOVE
    0x0625,  # ALEF WITH HAMZA BELOW
})

LAM = 0x0644  # ARABIC LETTER LAM
NOON = 0x0646  # ARABIC LETTER NOON

# Sun letters: those where the ل of ال assimilates
# Identified by observing which letters carry shadda after ال in the text
SUN_LETTERS = frozenset({
    0x062A,  # TEH
    0x062B,  # THEH
    0x062F,  # DAL
    0x0630,  # THAL
    0x0631,  # REH
    0x0632,  # ZAIN
    0x0633,  # SEEN
    0x0634,  # SHEEN
    0x0635,  # SAD
    0x0636,  # DAD
    0x0637,  # TAH
    0x0638,  # ZAH
    0x0644,  # LAM (ال + ل → اللّ)
    0x0646,  # NOON
})


def classify_shadda(rows: list[dict]) -> list[dict]:
    """Add shadda classification columns to letter rows.

    New columns:
        shadda_type: 'true_doubling' | 'al_assimilation' | 'noon_assimilation' | ''
        shadda_sonic_count: 2 if has_shadda else 1
        shadda_visual_count: 1 (always — shadda is one visible mark)
    """
    # Build a word-indexed structure for context lookups
    word_groups = {}
    for i, row in enumerate(rows):
        key = (row["surah"], row["verse"], row["word_idx"])
        if key not in word_groups:
            word_groups[key] = []
        word_groups[key].append(i)

    result = []
    for i, row in enumerate(rows):
        new_row = dict(row)
        new_row["shadda_type"] = ""
        new_row["shadda_sonic_count"] = 1
        new_row["shadda_visual_count"] = 1

        if row["has_shadda"]:
            new_row["shadda_sonic_count"] = 2
            letter_cp = int(row["codepoint"][2:], 16)

            key = (row["surah"], row["verse"], row["word_idx"])
            word_indices = word_groups[key]
            pos_in_word = row["char_idx"]

            # --- 1. ال-assimilation ---
            # Pattern: [alif][lam][sun_letter_with_shadda] in same word
            # The shaddaed letter must be a sun letter at char_idx >= 2
            if pos_in_word >= 2 and letter_cp in SUN_LETTERS:
                prev_letters = sorted(
                    [rows[idx] for idx in word_indices if rows[idx]["char_idx"] < pos_in_word],
                    key=lambda r: r["char_idx"]
                )
                if len(prev_letters) >= 2:
                    lam_cp = int(prev_letters[-1]["codepoint"][2:], 16)
                    alif_cp = int(prev_letters[-2]["codepoint"][2:], 16)
                    if lam_cp == LAM and alif_cp in ALIF_VARIANTS:
                        new_row["shadda_type"] = "al_assimilation"

            # Special case: lam with shadda at char_idx=1, preceded by alif
            # This is اللّ pattern (ال + word starting with ل)
            if (not new_row["shadda_type"] and pos_in_word == 1
                    and letter_cp == LAM):
                prev_letters = [rows[idx] for idx in word_indices
                                if rows[idx]["char_idx"] == 0]
                if prev_letters:
                    alif_cp = int(prev_letters[0]["codepoint"][2:], 16)
                    if alif_cp in ALIF_VARIANTS:
                        new_row["shadda_type"] = "al_assimilation"

            # --- 2. noon-assimilation (cross-word only) ---
            # Word-initial shadda, previous word ends with noon or tanween
            if not new_row["shadda_type"] and pos_in_word == 0 and i > 0:
                prev_row = rows[i - 1]
                if (prev_row["surah"] == row["surah"]
                        and prev_row["verse"] == row["verse"]
                        and prev_row["word_idx"] == row["word_idx"] - 1):
                    prev_cp = int(prev_row["codepoint"][2:], 16)
                    if prev_cp == NOON or prev_row["has_tanween"]:
                        new_row["shadda_type"] = "noon_assimilation"

            # --- 3. Default: true doubling ---
            if not new_row["shadda_type"]:
                new_row["shadda_type"] = "true_doubling"

        result.append(new_row)

    return result


FIELDNAMES = M2_FIELDNAMES + [
    "shadda_type", "shadda_sonic_count", "shadda_visual_count",
]


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
    from collections import Counter
    parser = argparse.ArgumentParser(description="M3: Shadda decomposition")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output", default=str(
        Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "letters_with_shadda.csv"
    ))
    args = parser.parse_args()

    rows = extract_letters_with_diacritics(args.source)
    rows = classify_shadda(rows)
    count = write_csv(rows, args.output)

    # Summary
    type_counts = Counter(r["shadda_type"] for r in rows if r["has_shadda"])
    print(f"Wrote {count:,} rows → {args.output}")
    print(f"Shadda instances: {sum(type_counts.values()):,}")
    for t, c in type_counts.most_common():
        print(f"  {t}: {c:,}")


if __name__ == "__main__":
    main()

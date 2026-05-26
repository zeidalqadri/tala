#!/usr/bin/env python3
"""M7 — Unified Multi-Layer Dataset

Merges all parsed data from M1-M6 into a single canonical CSV. The pipeline
already chains columns through each milestone. This module validates the
complete dataset across all four layers and writes the canonical output.

Columns by layer:

    Positional (M1):
        mushaf_pos, surah, verse, word_idx, char_idx, letter, codepoint

    Diacritics (M2):
        primary_diacritic, primary_diacritic_cp, all_diacritics,
        all_diacritics_cps, has_shadda, has_tanween, tanween_type

    Shadda decomposition (M3):
        shadda_type, shadda_sonic_count, shadda_visual_count

    Hamza seats (M4):
        hamza_seat, has_maddah, has_combining_hamza

    Sonic — articulatory zones (M5):
        zone, zone_name, has_ghunna

    Geometric — visual families (M6):
        geometric_family, dot_count, dot_position, is_non_connector

Output: data/processed/tala_unified.csv
"""

import csv
from collections import Counter
from pathlib import Path

from src.parser.assign_geometry import (
    assign_geometry, FIELDNAMES, GEOMETRIC_FAMILY,
)
from src.parser.assign_zones import assign_zones
from src.parser.track_hamza import assign_hamza_seats
from src.parser.decompose_shadda import classify_shadda
from src.parser.extract_diacritics import extract_letters_with_diacritics
from src.parser.verify_source import DEFAULT_SOURCE, EXPECTED_TOTAL_LETTERS

# Layer column groups for documentation and validation
LAYER_COLUMNS = {
    "positional": [
        "mushaf_pos", "surah", "verse", "word_idx", "char_idx",
        "letter", "codepoint",
    ],
    "diacritics": [
        "primary_diacritic", "primary_diacritic_cp", "all_diacritics",
        "all_diacritics_cps", "has_shadda", "has_tanween", "tanween_type",
    ],
    "shadda": [
        "shadda_type", "shadda_sonic_count", "shadda_visual_count",
    ],
    "hamza": [
        "hamza_seat", "has_maddah", "has_combining_hamza",
    ],
    "sonic": [
        "zone", "zone_name", "has_ghunna",
    ],
    "geometric": [
        "geometric_family", "dot_count", "dot_position", "is_non_connector",
    ],
}

ALL_COLUMNS = []
for cols in LAYER_COLUMNS.values():
    ALL_COLUMNS.extend(cols)


def build_unified(source: str = DEFAULT_SOURCE) -> list[dict]:
    """Run the full M1-M6 pipeline and return the unified dataset."""
    raw = extract_letters_with_diacritics(source)
    rows = classify_shadda(raw)
    rows = assign_hamza_seats(rows)
    rows = assign_zones(rows)
    rows = assign_geometry(rows)
    return rows


def validate(rows: list[dict]) -> list[str]:
    """Validate the unified dataset. Returns a list of error messages (empty = valid)."""
    errors = []

    # Row count
    if len(rows) != EXPECTED_TOTAL_LETTERS:
        errors.append(f"Row count {len(rows)} != expected {EXPECTED_TOTAL_LETTERS}")

    if not rows:
        errors.append("Empty dataset")
        return errors

    # All columns present
    sample = rows[0]
    for col in ALL_COLUMNS:
        if col not in sample:
            errors.append(f"Missing column: {col}")

    # Positional integrity: mushaf_pos must be sequential 0..N-1
    first_pos = rows[0].get("mushaf_pos")
    last_pos = rows[-1].get("mushaf_pos")
    if first_pos != 0:
        errors.append(f"First mushaf_pos is {first_pos}, expected 0")
    if last_pos != len(rows) - 1:
        errors.append(f"Last mushaf_pos is {last_pos}, expected {len(rows) - 1}")

    # Every row has a geometric_family from the known set
    valid_families = set(GEOMETRIC_FAMILY.values())
    bad_families = [r["geometric_family"] for r in rows
                    if r.get("geometric_family") not in valid_families]
    if bad_families:
        errors.append(f"{len(bad_families)} rows with invalid geometric_family")

    # Zone values must be 1-6
    valid_zones = {1, 2, 3, 4, 5, 6}
    bad_zones = [r["zone"] for r in rows if r.get("zone") not in valid_zones]
    if bad_zones:
        errors.append(f"{len(bad_zones)} rows with invalid zone")

    # Shadda consistency: has_shadda=True rows must have a shadda_type
    valid_shadda_types = {"true_doubling", "al_assimilation", "noon_assimilation"}
    for r in rows:
        if r.get("has_shadda") and r.get("shadda_type") not in valid_shadda_types:
            errors.append(
                f"mushaf_pos={r['mushaf_pos']}: has_shadda=True but "
                f"shadda_type={r.get('shadda_type')!r}"
            )
            break  # one example is enough

    # Non-shadda rows must have sonic_count=1, visual_count=1
    for r in rows:
        if not r.get("has_shadda"):
            if r.get("shadda_sonic_count") != 1 or r.get("shadda_visual_count") != 1:
                errors.append(
                    f"mushaf_pos={r['mushaf_pos']}: no shadda but "
                    f"sonic={r.get('shadda_sonic_count')}, visual={r.get('shadda_visual_count')}"
                )
                break

    return errors


def summary(rows: list[dict]) -> dict:
    """Compute summary statistics for the unified dataset."""
    stats = {
        "total_rows": len(rows),
        "columns": len(ALL_COLUMNS),
        "layers": list(LAYER_COLUMNS.keys()),
    }

    # Per-layer stats
    stats["unique_letters"] = len({r["codepoint"] for r in rows})
    stats["surahs"] = len({r["surah"] for r in rows})
    stats["shadda_count"] = sum(1 for r in rows if r["has_shadda"])
    stats["tanween_count"] = sum(1 for r in rows if r["has_tanween"])

    shadda_types = Counter(r["shadda_type"] for r in rows if r["has_shadda"])
    stats["shadda_types"] = dict(shadda_types.most_common())

    hamza_seats = Counter(r["hamza_seat"] for r in rows if r["hamza_seat"] != "none")
    stats["hamza_seats"] = dict(hamza_seats.most_common())

    zone_dist = Counter(r["zone_name"] for r in rows)
    stats["zone_distribution"] = dict(zone_dist.most_common())

    family_dist = Counter(r["geometric_family"] for r in rows)
    stats["family_distribution"] = dict(family_dist.most_common())

    dot_dist = Counter(r["dot_count"] for r in rows)
    stats["dot_distribution"] = {str(k): v for k, v in sorted(dot_dist.items())}

    stats["non_connectors"] = sum(1 for r in rows if r["is_non_connector"])
    stats["ghunna_count"] = sum(1 for r in rows if r["has_ghunna"])

    return stats


def write_csv(rows: list[dict], output_path: str) -> int:
    """Write unified dataset to CSV. Returns row count."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def main():
    import argparse
    import json

    parser = argparse.ArgumentParser(description="M7: Unified multi-layer dataset")
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output", default=str(
        Path(__file__).resolve().parent.parent.parent / "data" / "processed" / "tala_unified.csv"
    ))
    args = parser.parse_args()

    print("Building unified dataset (M1-M6 pipeline)...")
    rows = build_unified(args.source)

    print("Validating...")
    errors = validate(rows)
    if errors:
        print(f"VALIDATION FAILED ({len(errors)} errors):")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("Validation passed.")
    count = write_csv(rows, args.output)
    print(f"Wrote {count:,} rows x {len(FIELDNAMES)} columns → {args.output}")

    stats = summary(rows)
    print(f"\n--- Summary ---")
    print(f"Letters: {stats['total_rows']:,}")
    print(f"Unique codepoints: {stats['unique_letters']}")
    print(f"Surahs: {stats['surahs']}")
    print(f"Columns: {stats['columns']} across {len(stats['layers'])} layers")
    print(f"  Layers: {', '.join(stats['layers'])}")
    print(f"\nShadda: {stats['shadda_count']:,}")
    for st, n in stats["shadda_types"].items():
        print(f"  {st}: {n:,}")
    print(f"Tanween: {stats['tanween_count']:,}")
    print(f"Ghunna: {stats['ghunna_count']:,}")
    print(f"\nZones:")
    for z, n in stats["zone_distribution"].items():
        print(f"  {z}: {n:,}")
    print(f"\nGeometric families:")
    for f, n in stats["family_distribution"].items():
        print(f"  {f}: {n:,}")
    print(f"Non-connectors: {stats['non_connectors']:,}")
    print(f"Dot distribution: {stats['dot_distribution']}")

    # Write stats JSON alongside CSV
    stats_path = str(Path(args.output).with_suffix(".json"))
    with open(stats_path, "w") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"\nStats → {stats_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

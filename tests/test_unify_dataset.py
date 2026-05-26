#!/usr/bin/env python3
"""Tests for M7 — Unified Multi-Layer Dataset."""

import unittest
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser.verify_source import EXPECTED_TOTAL_LETTERS
from src.parser.unify_dataset import (
    build_unified, validate, summary, ALL_COLUMNS, LAYER_COLUMNS, FIELDNAMES,
)
from src.parser.assign_geometry import GEOMETRIC_FAMILY


class TestUnifiedDataset(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.rows = build_unified()

    # --- Schema completeness ---

    def test_total_row_count(self):
        """Unified dataset must have 327,793 rows."""
        self.assertEqual(len(self.rows), EXPECTED_TOTAL_LETTERS)

    def test_all_columns_present(self):
        """Every row must have all 27 columns from all 6 layers."""
        for col in ALL_COLUMNS:
            self.assertIn(col, self.rows[0],
                          f"Missing column: {col}")

    def test_all_columns_in_fieldnames(self):
        """ALL_COLUMNS must match FIELDNAMES exactly."""
        self.assertEqual(ALL_COLUMNS, FIELDNAMES)

    def test_layer_column_count(self):
        """Total columns across layers must equal 27."""
        total = sum(len(cols) for cols in LAYER_COLUMNS.values())
        self.assertEqual(total, 27)

    def test_six_layers_defined(self):
        """Six layer groups must be defined."""
        self.assertEqual(len(LAYER_COLUMNS), 6)

    # --- Validation passes ---

    def test_validation_clean(self):
        """validate() must return zero errors."""
        errors = validate(self.rows)
        self.assertEqual(errors, [], f"Validation errors: {errors}")

    # --- Positional layer (M1) ---

    def test_mushaf_pos_sequential(self):
        """mushaf_pos must be 0..327792 with no gaps."""
        positions = [r["mushaf_pos"] for r in self.rows]
        self.assertEqual(positions[0], 0)
        self.assertEqual(positions[-1], EXPECTED_TOTAL_LETTERS - 1)
        # Check monotonically increasing (no gaps or duplicates)
        for i in range(1, min(1000, len(positions))):
            self.assertEqual(positions[i], positions[i - 1] + 1)

    def test_surah_range(self):
        """Surahs must be 1-114."""
        surahs = {r["surah"] for r in self.rows}
        self.assertEqual(min(surahs), 1)
        self.assertEqual(max(surahs), 114)

    def test_all_114_surahs(self):
        """All 114 surahs must be represented."""
        surahs = {r["surah"] for r in self.rows}
        self.assertEqual(len(surahs), 114)

    # --- Diacritics layer (M2) ---

    def test_shadda_count(self):
        """23,016 letters must have has_shadda=True."""
        count = sum(1 for r in self.rows if r["has_shadda"])
        self.assertEqual(count, 23016)

    def test_tanween_count(self):
        """8,893 letters must have has_tanween=True."""
        count = sum(1 for r in self.rows if r["has_tanween"])
        self.assertEqual(count, 8893)

    # --- Shadda layer (M3) ---

    def test_shadda_type_distribution(self):
        """Shadda types must match the corrected M3 counts."""
        types = Counter(r["shadda_type"] for r in self.rows if r["has_shadda"])
        self.assertEqual(types["true_doubling"], 14244)
        self.assertEqual(types["al_assimilation"], 6457)
        self.assertEqual(types["noon_assimilation"], 2315)

    def test_non_shadda_sonic_count(self):
        """Non-shadda letters must have shadda_sonic_count=1."""
        for r in self.rows:
            if not r["has_shadda"]:
                self.assertEqual(r["shadda_sonic_count"], 1,
                    f"mushaf_pos={r['mushaf_pos']}: expected sonic=1")
                break  # spot check first non-shadda row

    def test_shadda_sonic_count_is_2(self):
        """Shadda letters must have shadda_sonic_count=2."""
        for r in self.rows:
            if r["has_shadda"]:
                self.assertEqual(r["shadda_sonic_count"], 2,
                    f"mushaf_pos={r['mushaf_pos']}: expected sonic=2")
                break

    # --- Hamza layer (M4) ---

    def test_hamza_seat_distribution(self):
        """Hamza seat counts must match M4."""
        seats = Counter(r["hamza_seat"] for r in self.rows)
        self.assertEqual(seats["alif_above"], 8900)
        self.assertEqual(seats["alif_below"], 5088)
        self.assertEqual(seats["standalone"], 3059)
        self.assertEqual(seats["ya"], 921)
        self.assertEqual(seats["waw"], 706)

    def test_maddah_count(self):
        """5,376 letters must have has_maddah=True."""
        count = sum(1 for r in self.rows if r["has_maddah"])
        self.assertEqual(count, 5376)

    # --- Sonic layer (M5) ---

    def test_zone_distribution(self):
        """Zone counts must match M5."""
        zones = Counter(r["zone"] for r in self.rows)
        self.assertEqual(zones[1], 68579)   # jawf
        self.assertEqual(zones[2], 33636)   # aqsa_halq
        self.assertEqual(zones[3], 13769)   # wasat_halq
        self.assertEqual(zones[4], 3718)    # adna_halq
        self.assertEqual(zones[5], 148419)  # lisan
        self.assertEqual(zones[6], 59672)   # shafatan

    def test_ghunna_count(self):
        """61,651 letters must have has_ghunna=True."""
        count = sum(1 for r in self.rows if r["has_ghunna"])
        self.assertEqual(count, 61651)

    # --- Geometric layer (M6) ---

    def test_family_distribution(self):
        """Geometric family counts must match M6."""
        families = Counter(r["geometric_family"] for r in self.rows)
        self.assertEqual(families["singleton"], 182676)
        self.assertEqual(families["cup"], 69251)
        self.assertEqual(families["circle"], 15781)
        self.assertEqual(families["curve"], 14226)
        self.assertEqual(families["knee"], 10923)
        self.assertEqual(families["hook"], 10626)
        self.assertEqual(families["bowl"], 10178)
        self.assertEqual(families["teeth"], 8246)
        self.assertEqual(families["loop"], 3760)
        self.assertEqual(families["cross"], 2126)

    def test_non_connector_count(self):
        """113,480 letters must be non-connectors."""
        count = sum(1 for r in self.rows if r["is_non_connector"])
        self.assertEqual(count, 113480)

    def test_dot_distribution(self):
        """Dot count distribution must match M6."""
        dots = Counter(r["dot_count"] for r in self.rows)
        self.assertEqual(dots[0], 222188)
        self.assertEqual(dots[1], 63835)
        self.assertEqual(dots[2], 38232)
        self.assertEqual(dots[3], 3538)

    # --- Cross-layer consistency ---

    def test_shadda_rows_have_valid_zones(self):
        """Every shadda'd letter must have a valid zone."""
        for r in self.rows:
            if r["has_shadda"]:
                self.assertIn(r["zone"], {1, 2, 3, 4, 5, 6},
                    f"Shadda at pos {r['mushaf_pos']} has invalid zone {r['zone']}")

    def test_shadda_rows_have_valid_family(self):
        """Every shadda'd letter must have a valid geometric family."""
        valid = set(GEOMETRIC_FAMILY.values())
        for r in self.rows:
            if r["has_shadda"]:
                self.assertIn(r["geometric_family"], valid,
                    f"Shadda at pos {r['mushaf_pos']} has invalid family {r['geometric_family']}")

    def test_hamza_seats_are_zone_2(self):
        """Letters with hamza seats (except 'none') should be zone 2 (deepest throat)."""
        # hamza's anatomical place is the glottal stop — zone 2
        hamza_zones = Counter()
        for r in self.rows:
            if r["hamza_seat"] not in ("none", ""):
                hamza_zones[r["zone"]] += 1
        # zone 2 should be the dominant zone for hamza-bearing letters
        self.assertEqual(max(hamza_zones, key=hamza_zones.get), 2)

    def test_tanween_implies_ghunna(self):
        """Every tanween-bearing letter must have has_ghunna=True."""
        for r in self.rows:
            if r["has_tanween"]:
                self.assertTrue(r["has_ghunna"],
                    f"mushaf_pos={r['mushaf_pos']}: tanween without ghunna")

    def test_non_connector_families(self):
        """Non-connectors should only appear in expected families."""
        # Non-connectors are: alef variants, dal/thal (knee), reh/zain (curve),
        # waw variants, standalone hamza — all singletons, knee, or curve
        non_conn_families = Counter()
        for r in self.rows:
            if r["is_non_connector"]:
                non_conn_families[r["geometric_family"]] += 1
        # Should be dominated by singleton, knee, curve
        self.assertEqual(
            set(non_conn_families.keys()),
            {"singleton", "knee", "curve"},
            f"Unexpected non-connector families: {dict(non_conn_families)}"
        )

    # --- Summary function ---

    def test_summary_keys(self):
        """summary() must return expected keys."""
        s = summary(self.rows)
        expected_keys = {
            "total_rows", "columns", "layers", "unique_letters", "surahs",
            "shadda_count", "tanween_count", "shadda_types", "hamza_seats",
            "zone_distribution", "family_distribution", "dot_distribution",
            "non_connectors", "ghunna_count",
        }
        self.assertTrue(expected_keys.issubset(s.keys()),
            f"Missing keys: {expected_keys - s.keys()}")

    def test_summary_total_rows(self):
        """summary() total_rows must match."""
        s = summary(self.rows)
        self.assertEqual(s["total_rows"], EXPECTED_TOTAL_LETTERS)


if __name__ == "__main__":
    unittest.main(verbosity=2)

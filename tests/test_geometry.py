#!/usr/bin/env python3
"""Tests for M6 — Geometric Family Assignment."""

import unittest
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser.verify_source import EXPECTED_TOTAL_LETTERS, EXPECTED_LETTER_COUNTS
from src.parser.decompose_shadda import classify_shadda
from src.parser.extract_diacritics import extract_letters_with_diacritics
from src.parser.track_hamza import assign_hamza_seats
from src.parser.assign_zones import assign_zones
from src.parser.assign_geometry import (
    assign_geometry, FIELDNAMES, GEOMETRIC_FAMILY, DOT_CONFIG,
    NON_CONNECTORS, SHARES_BASE_WITH,
)

VALID_FAMILIES = {
    "cup", "bowl", "knee", "curve", "teeth",
    "loop", "cross", "hook", "circle", "singleton",
}

VALID_DOT_POSITIONS = {"above", "below", "none"}


class TestGeometricFamilyAssignment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        raw = extract_letters_with_diacritics()
        m3 = classify_shadda(raw)
        m4 = assign_hamza_seats(m3)
        m5 = assign_zones(m4)
        cls.rows = assign_geometry(m5)

    # --- Row count and schema ---

    def test_total_row_count(self):
        """Row count must not change: 327,793."""
        self.assertEqual(len(self.rows), EXPECTED_TOTAL_LETTERS)

    def test_new_fields_present(self):
        """Every row must have the four new M6 fields."""
        for row in self.rows[:100]:
            self.assertIn("geometric_family", row)
            self.assertIn("dot_count", row)
            self.assertIn("dot_position", row)
            self.assertIn("is_non_connector", row)

    def test_fieldnames_complete(self):
        """FIELDNAMES must contain all four new fields."""
        for field in ("geometric_family", "dot_count", "dot_position", "is_non_connector"):
            self.assertIn(field, FIELDNAMES)

    # --- geometric_family values ---

    def test_family_values_valid(self):
        """All geometric_family values must be one of the 10 valid families."""
        for row in self.rows:
            self.assertIn(row["geometric_family"], VALID_FAMILIES,
                          f"Invalid family {row['geometric_family']!r} at pos {row['mushaf_pos']}")

    def test_all_families_present(self):
        """All 10 families must appear in the corpus."""
        families = {r["geometric_family"] for r in self.rows}
        self.assertEqual(families, VALID_FAMILIES)

    def test_cup_family_letters(self):
        """Cup family must only contain ب ت ث ن ي."""
        cup_letters = {"ب", "ت", "ث", "ن", "ي"}
        for r in self.rows:
            if r["geometric_family"] == "cup":
                self.assertIn(r["letter"], cup_letters,
                              f"Unexpected {r['letter']} in cup family")

    def test_bowl_family_letters(self):
        """Bowl family must only contain ج ح خ."""
        bowl_letters = {"ج", "ح", "خ"}
        for r in self.rows:
            if r["geometric_family"] == "bowl":
                self.assertIn(r["letter"], bowl_letters)

    def test_knee_family_letters(self):
        """Knee family must only contain د ذ."""
        knee_letters = {"د", "ذ"}
        for r in self.rows:
            if r["geometric_family"] == "knee":
                self.assertIn(r["letter"], knee_letters)

    def test_curve_family_letters(self):
        """Curve family must only contain ر ز."""
        curve_letters = {"ر", "ز"}
        for r in self.rows:
            if r["geometric_family"] == "curve":
                self.assertIn(r["letter"], curve_letters)

    def test_teeth_family_letters(self):
        """Teeth family must only contain س ش."""
        teeth_letters = {"س", "ش"}
        for r in self.rows:
            if r["geometric_family"] == "teeth":
                self.assertIn(r["letter"], teeth_letters)

    def test_loop_family_letters(self):
        """Loop family must only contain ص ض."""
        loop_letters = {"ص", "ض"}
        for r in self.rows:
            if r["geometric_family"] == "loop":
                self.assertIn(r["letter"], loop_letters)

    def test_cross_family_letters(self):
        """Cross family must only contain ط ظ."""
        cross_letters = {"ط", "ظ"}
        for r in self.rows:
            if r["geometric_family"] == "cross":
                self.assertIn(r["letter"], cross_letters)

    def test_hook_family_letters(self):
        """Hook family must only contain ع غ."""
        hook_letters = {"ع", "غ"}
        for r in self.rows:
            if r["geometric_family"] == "hook":
                self.assertIn(r["letter"], hook_letters)

    def test_circle_family_letters(self):
        """Circle family must only contain ف ق."""
        circle_letters = {"ف", "ق"}
        for r in self.rows:
            if r["geometric_family"] == "circle":
                self.assertIn(r["letter"], circle_letters)

    # --- dot_count and dot_position ---

    def test_dot_count_values(self):
        """dot_count must be 0, 1, 2, or 3."""
        for r in self.rows:
            self.assertIn(r["dot_count"], {0, 1, 2, 3},
                          f"Invalid dot_count {r['dot_count']} at pos {r['mushaf_pos']}")

    def test_dot_position_values(self):
        """dot_position must be 'above', 'below', or 'none'."""
        for r in self.rows:
            self.assertIn(r["dot_position"], VALID_DOT_POSITIONS,
                          f"Invalid dot_position {r['dot_position']!r} at pos {r['mushaf_pos']}")

    def test_zero_dots_means_none_position(self):
        """If dot_count is 0, dot_position must be 'none'."""
        for r in self.rows:
            if r["dot_count"] == 0:
                self.assertEqual(r["dot_position"], "none",
                    f"dot_count=0 but position={r['dot_position']!r} at pos {r['mushaf_pos']}")

    def test_nonzero_dots_means_direction(self):
        """If dot_count > 0, dot_position must be 'above' or 'below'."""
        for r in self.rows:
            if r["dot_count"] > 0:
                self.assertIn(r["dot_position"], {"above", "below"},
                    f"dot_count={r['dot_count']} but position={r['dot_position']!r}")

    def test_ba_has_one_dot_below(self):
        """ب (ba) must have 1 dot below."""
        for r in self.rows:
            if r["codepoint"] == "U+0628":
                self.assertEqual(r["dot_count"], 1)
                self.assertEqual(r["dot_position"], "below")
                break

    def test_sheen_has_three_dots_above(self):
        """ش (sheen) must have 3 dots above."""
        for r in self.rows:
            if r["codepoint"] == "U+0634":
                self.assertEqual(r["dot_count"], 3)
                self.assertEqual(r["dot_position"], "above")
                break

    def test_teh_marbuta_has_two_dots_above(self):
        """ة (teh marbuta) has 2 dots above (heh body + dots of teh)."""
        for r in self.rows:
            if r["codepoint"] == "U+0629":
                self.assertEqual(r["dot_count"], 2)
                self.assertEqual(r["dot_position"], "above")
                break

    # --- is_non_connector ---

    def test_non_connector_type(self):
        """is_non_connector must be boolean."""
        for r in self.rows[:1000]:
            self.assertIsInstance(r["is_non_connector"], bool)

    def test_alef_is_non_connector(self):
        """Bare alef (U+0627) is a non-connector."""
        for r in self.rows:
            if r["codepoint"] == "U+0627":
                self.assertTrue(r["is_non_connector"])
                break

    def test_ba_is_connector(self):
        """ب (ba) is a connector."""
        for r in self.rows:
            if r["codepoint"] == "U+0628":
                self.assertFalse(r["is_non_connector"])
                break

    def test_dal_is_non_connector(self):
        """د (dal) is a non-connector."""
        for r in self.rows:
            if r["codepoint"] == "U+062F":
                self.assertTrue(r["is_non_connector"])
                break

    def test_non_connector_count(self):
        """Non-connectors should only be from the known set."""
        for r in self.rows:
            cp = int(r["codepoint"][2:], 16)
            if r["is_non_connector"]:
                self.assertIn(cp, NON_CONNECTORS,
                    f"Unexpected non-connector: {r['letter']} ({r['codepoint']})")

    # --- Family consistency with dot differentiation ---

    def test_family_members_differ_by_dots(self):
        """Within each non-singleton family, members must have different dot configs."""
        from collections import defaultdict
        family_dots = defaultdict(set)
        for cp, family in GEOMETRIC_FAMILY.items():
            if family != "singleton":
                dot_count, dot_pos = DOT_CONFIG[cp]
                family_dots[family].add((dot_count, dot_pos))
        # Each family member must have a unique dot config
        for family, configs in family_dots.items():
            members = [cp for cp, f in GEOMETRIC_FAMILY.items() if f == family]
            self.assertEqual(len(configs), len(members),
                f"Family {family} has non-unique dot configs")

    # --- Coverage ---

    def test_all_corpus_codepoints_mapped(self):
        """Every codepoint in the corpus must have a geometric family assignment."""
        unmapped = set()
        for r in self.rows:
            if r["geometric_family"] == "singleton":
                cp = int(r["codepoint"][2:], 16)
                if cp not in GEOMETRIC_FAMILY:
                    unmapped.add(r["codepoint"])
        self.assertEqual(unmapped, set(),
            f"Codepoints without explicit mapping: {unmapped}")

    # --- Prior milestone data preserved ---

    def test_zone_data_preserved(self):
        """M5 zone fields must survive the M6 pass."""
        zones = {r["zone"] for r in self.rows}
        self.assertTrue(zones.issuperset({1, 2, 3, 4, 5, 6}))

    def test_shadda_data_preserved(self):
        """M3 shadda fields must survive."""
        shadda_rows = [r for r in self.rows if r["has_shadda"]]
        self.assertEqual(len(shadda_rows), 23016)

    def test_hamza_data_preserved(self):
        """M4 hamza_seat must survive."""
        seats = {r["hamza_seat"] for r in self.rows}
        self.assertIn("alif_above", seats)
        self.assertIn("standalone", seats)

    # --- shares_base_with lookup ---

    def test_shares_base_symmetric(self):
        """If A shares base with B, then B shares base with A."""
        for cp, partners in SHARES_BASE_WITH.items():
            for partner in partners:
                self.assertIn(cp, SHARES_BASE_WITH[partner],
                    f"Asymmetric: {cp:#06x} → {partner:#06x} but not reverse")

    def test_singletons_share_with_none(self):
        """Singleton letters have empty shares_base_with."""
        for cp, family in GEOMETRIC_FAMILY.items():
            if family == "singleton":
                self.assertEqual(SHARES_BASE_WITH[cp], frozenset(),
                    f"Singleton {cp:#06x} has non-empty shares_base_with")


if __name__ == "__main__":
    unittest.main(verbosity=2)

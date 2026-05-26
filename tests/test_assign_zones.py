#!/usr/bin/env python3
"""Tests for M5 — Articulatory Zone Assignment."""

import unittest
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser.verify_source import EXPECTED_TOTAL_LETTERS, EXPECTED_LETTER_COUNTS
from src.parser.decompose_shadda import classify_shadda
from src.parser.extract_diacritics import extract_letters_with_diacritics
from src.parser.track_hamza import assign_hamza_seats
from src.parser.assign_zones import (
    assign_zones, FIELDNAMES, ZONE_BY_CP, ZONE_NAMES,
    NASAL_CPS, SHORT_VOWELS,
)


class TestZoneAssignment(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        raw = extract_letters_with_diacritics()
        m3 = classify_shadda(raw)
        m4 = assign_hamza_seats(m3)
        cls.rows = assign_zones(m4)

        # Group by codepoint for efficient lookup tests
        cls.by_cp = {}
        for row in cls.rows:
            cls.by_cp.setdefault(row["codepoint"], []).append(row)

    # --- Row count and schema ---

    def test_total_row_count(self):
        """Row count must not change: 327,793."""
        self.assertEqual(len(self.rows), EXPECTED_TOTAL_LETTERS)

    def test_new_fields_present(self):
        """Every row must have the three new M5 fields."""
        for row in self.rows[:100]:
            self.assertIn("zone", row)
            self.assertIn("zone_name", row)
            self.assertIn("has_ghunna", row)

    def test_fieldnames_complete(self):
        """FIELDNAMES must contain all three new fields."""
        for field in ("zone", "zone_name", "has_ghunna"):
            self.assertIn(field, FIELDNAMES)

    # --- Zone value validity ---

    def test_zone_values_in_range(self):
        """zone must be an integer 1-6 for all rows."""
        for row in self.rows:
            self.assertIn(row["zone"], {1, 2, 3, 4, 5, 6},
                          f"Invalid zone {row['zone']} at {row['mushaf_pos']}")

    def test_zone_name_matches_zone(self):
        """zone_name must be the canonical name for the zone number."""
        for row in self.rows[:1000]:
            self.assertEqual(row["zone_name"], ZONE_NAMES[row["zone"]],
                             f"Name mismatch at {row['mushaf_pos']}: "
                             f"zone={row['zone']} name={row['zone_name']!r}")

    def test_all_zones_represented(self):
        """Zones 1-6 must each have at least one letter instance."""
        zones_present = {row["zone"] for row in self.rows}
        for z in range(1, 7):
            self.assertIn(z, zones_present, f"Zone {z} has no letter instances")

    # --- Static zone mapping correctness ---

    def test_alif_bare_is_zone_1(self):
        """ا (U+0627) must be zone 1 (جوف)."""
        for row in self.by_cp.get("U+0627", []):
            self.assertEqual(row["zone"], 1)

    def test_alif_maqsura_is_zone_1(self):
        """ى (U+0649) must be zone 1."""
        for row in self.by_cp.get("U+0649", []):
            self.assertEqual(row["zone"], 1)

    def test_alif_wasla_is_zone_1(self):
        """ٱ (U+0671) must be zone 1."""
        for row in self.by_cp.get("U+0671", []):
            self.assertEqual(row["zone"], 1)

    def test_hamza_seats_are_zone_2(self):
        """All five hamza-seat letters must be zone 2."""
        for cp_hex in ("U+0621", "U+0623", "U+0624", "U+0625", "U+0626"):
            for row in self.by_cp.get(cp_hex, []):
                self.assertEqual(row["zone"], 2,
                    f"Expected zone 2 for {cp_hex} at {row['mushaf_pos']}")

    def test_heh_is_zone_2(self):
        """ه (U+0647) must be zone 2."""
        for row in self.by_cp.get("U+0647", []):
            self.assertEqual(row["zone"], 2)

    def test_ain_is_zone_3(self):
        """ع (U+0639) must be zone 3."""
        for row in self.by_cp.get("U+0639", []):
            self.assertEqual(row["zone"], 3)

    def test_hah_is_zone_3(self):
        """ح (U+062D) must be zone 3."""
        for row in self.by_cp.get("U+062D", []):
            self.assertEqual(row["zone"], 3)

    def test_ghain_is_zone_4(self):
        """غ (U+063A) must be zone 4."""
        for row in self.by_cp.get("U+063A", []):
            self.assertEqual(row["zone"], 4)

    def test_khah_is_zone_4(self):
        """خ (U+062E) must be zone 4."""
        for row in self.by_cp.get("U+062E", []):
            self.assertEqual(row["zone"], 4)

    def test_ba_is_zone_6(self):
        """ب (U+0628) must be zone 6."""
        for row in self.by_cp.get("U+0628", []):
            self.assertEqual(row["zone"], 6)

    def test_meem_is_zone_6(self):
        """م (U+0645) must be zone 6."""
        for row in self.by_cp.get("U+0645", []):
            self.assertEqual(row["zone"], 6)

    def test_feh_is_zone_6(self):
        """ف (U+0641) must be zone 6."""
        for row in self.by_cp.get("U+0641", []):
            self.assertEqual(row["zone"], 6)

    def test_noon_is_zone_5(self):
        """ن (U+0646) must be zone 5."""
        for row in self.by_cp.get("U+0646", []):
            self.assertEqual(row["zone"], 5)

    def test_lam_is_zone_5(self):
        """ل (U+0644) must be zone 5."""
        for row in self.by_cp.get("U+0644", []):
            self.assertEqual(row["zone"], 5)

    def test_ta_marbuta_is_zone_5(self):
        """ة (U+0629) must be zone 5 (same anatomical locus as ت)."""
        for row in self.by_cp.get("U+0629", []):
            self.assertEqual(row["zone"], 5)

    # --- Context-dependent: و ---

    def test_waw_consonantal_is_zone_6(self):
        """و (U+0648) with a short vowel must be zone 6 (consonantal lips)."""
        short_vowel_cps = {f"U+{cp:04X}" for cp in SHORT_VOWELS}
        consonantal = [
            r for r in self.by_cp.get("U+0648", [])
            if r.get("primary_diacritic_cp") in short_vowel_cps
        ]
        self.assertGreater(len(consonantal), 0, "No consonantal waw found")
        for row in consonantal:
            self.assertEqual(row["zone"], 6,
                f"Consonantal waw should be zone 6 at {row['mushaf_pos']}")

    def test_waw_madd_is_zone_1(self):
        """و (U+0648) without a short vowel must be zone 1 (madd)."""
        short_vowel_cps = {f"U+{cp:04X}" for cp in SHORT_VOWELS}
        madd = [
            r for r in self.by_cp.get("U+0648", [])
            if r.get("primary_diacritic_cp") not in short_vowel_cps
        ]
        self.assertGreater(len(madd), 0, "No madd waw found")
        for row in madd:
            self.assertEqual(row["zone"], 1,
                f"Madd waw should be zone 1 at {row['mushaf_pos']}")

    # --- Context-dependent: ي ---

    def test_ya_consonantal_is_zone_5(self):
        """ي (U+064A) with a short vowel must be zone 5 (consonantal tongue)."""
        short_vowel_cps = {f"U+{cp:04X}" for cp in SHORT_VOWELS}
        consonantal = [
            r for r in self.by_cp.get("U+064A", [])
            if r.get("primary_diacritic_cp") in short_vowel_cps
        ]
        self.assertGreater(len(consonantal), 0, "No consonantal ya found")
        for row in consonantal:
            self.assertEqual(row["zone"], 5,
                f"Consonantal ya should be zone 5 at {row['mushaf_pos']}")

    def test_ya_madd_is_zone_1(self):
        """ي (U+064A) without a short vowel must be zone 1 (madd)."""
        short_vowel_cps = {f"U+{cp:04X}" for cp in SHORT_VOWELS}
        madd = [
            r for r in self.by_cp.get("U+064A", [])
            if r.get("primary_diacritic_cp") not in short_vowel_cps
        ]
        self.assertGreater(len(madd), 0, "No madd ya found")
        for row in madd:
            self.assertEqual(row["zone"], 1,
                f"Madd ya should be zone 1 at {row['mushaf_pos']}")

    # --- has_ghunna ---

    def test_noon_has_ghunna(self):
        """All ن instances must have has_ghunna=True."""
        for row in self.by_cp.get("U+0646", []):
            self.assertTrue(row["has_ghunna"],
                f"ن at {row['mushaf_pos']} missing ghunna")

    def test_meem_has_ghunna(self):
        """All م instances must have has_ghunna=True."""
        for row in self.by_cp.get("U+0645", []):
            self.assertTrue(row["has_ghunna"],
                f"م at {row['mushaf_pos']} missing ghunna")

    def test_tanween_letters_have_ghunna(self):
        """All letters with has_tanween=True must have has_ghunna=True."""
        tanween_rows = [r for r in self.rows if r["has_tanween"]]
        self.assertGreater(len(tanween_rows), 0)
        for row in tanween_rows:
            self.assertTrue(row["has_ghunna"],
                f"Tanween letter at {row['mushaf_pos']} missing ghunna")

    def test_non_nasal_non_tanween_no_ghunna(self):
        """Letters that are not ن/م and have no tanween must have has_ghunna=False."""
        # Sample non-nasal letters: ب, ك, ع, خ
        for cp_hex in ("U+0628", "U+0643", "U+0639", "U+062E"):
            for row in self.by_cp.get(cp_hex, []):
                if not row["has_tanween"]:
                    self.assertFalse(row["has_ghunna"],
                        f"{cp_hex} without tanween should have has_ghunna=False at {row['mushaf_pos']}")

    # --- Prior milestone data preserved ---

    def test_hamza_data_preserved(self):
        """M4 hamza_seat field must survive M5 pass."""
        hamza_rows = [r for r in self.rows if r["hamza_seat"] != "none"]
        self.assertEqual(len(hamza_rows), 18674)

    def test_shadda_data_preserved(self):
        """M3 shadda_type field must survive M5 pass."""
        shadda_rows = [r for r in self.rows if r["has_shadda"]]
        self.assertEqual(len(shadda_rows), 23016)


if __name__ == "__main__":
    unittest.main(verbosity=2)

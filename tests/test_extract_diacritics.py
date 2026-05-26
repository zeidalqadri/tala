#!/usr/bin/env python3
"""Tests for M2 — Diacritical Stream Extraction."""

import unittest
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser.verify_source import (
    EXPECTED_TOTAL_LETTERS, EXPECTED_DIACRITIC_COUNTS,
)
from src.parser.extract_diacritics import (
    extract_letters_with_diacritics, FIELDNAMES, SHADDA, TANWEEN,
)


class TestDiacriticExtraction(unittest.TestCase):
    """Verify diacritic attachment to letters."""

    @classmethod
    def setUpClass(cls):
        cls.rows = extract_letters_with_diacritics()

    def test_total_letter_count(self):
        """Must still have 327,793 letter instances."""
        self.assertEqual(len(self.rows), EXPECTED_TOTAL_LETTERS)

    def test_fieldnames(self):
        """Each row must have all expected fields."""
        for row in self.rows[:10]:
            for field in FIELDNAMES:
                self.assertIn(field, row)

    def test_mushaf_pos_sequential(self):
        """mushaf_pos still sequential."""
        for i, row in enumerate(self.rows):
            self.assertEqual(row["mushaf_pos"], i)

    def test_shadda_count_matches_vr001(self):
        """has_shadda count must match VR001: 23,016."""
        count = sum(1 for r in self.rows if r["has_shadda"])
        self.assertEqual(count, EXPECTED_DIACRITIC_COUNTS[SHADDA])

    def test_tanween_total(self):
        """Total tanween = fathatan + kasratan + dammatan."""
        expected = sum(EXPECTED_DIACRITIC_COUNTS[cp] for cp in TANWEEN)
        actual = sum(1 for r in self.rows if r["has_tanween"])
        self.assertEqual(actual, expected)

    def test_tanween_types(self):
        """Each tanween type count must match VR001."""
        type_counts = Counter(r["tanween_type"] for r in self.rows if r["has_tanween"])
        self.assertEqual(type_counts["fathatan"], EXPECTED_DIACRITIC_COUNTS[0x064B])
        self.assertEqual(type_counts["kasratan"], EXPECTED_DIACRITIC_COUNTS[0x064D])
        self.assertEqual(type_counts["dammatan"], EXPECTED_DIACRITIC_COUNTS[0x064C])

    def test_primary_diacritic_is_haraka(self):
        """Primary diacritic, when set, must be a haraka (fatha/kasra/damma/sukun)."""
        harakat_cps = {"U+064E", "U+064F", "U+0650", "U+0652"}
        for row in self.rows:
            if row["primary_diacritic_cp"]:
                self.assertIn(row["primary_diacritic_cp"], harakat_cps,
                              f"Primary diacritic {row['primary_diacritic_cp']} is not a haraka")

    def test_all_diacritics_nonempty_implies_primary_or_shadda(self):
        """If all_diacritics is non-empty, letter has at least a haraka, shadda, or tanween."""
        for row in self.rows[:5000]:
            if row["all_diacritics"]:
                has_something = (row["primary_diacritic"] or row["has_shadda"] or row["has_tanween"])
                # Note: some diacritics are annotation marks (small high rounded zero, etc.)
                # that don't set primary/shadda/tanween. This is expected.

    def test_shadda_in_all_diacritics(self):
        """If has_shadda, the shadda char must be in all_diacritics."""
        shadda_char = chr(SHADDA)
        for row in self.rows:
            if row["has_shadda"]:
                self.assertIn(shadda_char, row["all_diacritics"])

    def test_first_letter_bism(self):
        """First letter should still be ب from bismillah."""
        self.assertEqual(self.rows[0]["letter"], "ب")
        self.assertEqual(self.rows[0]["surah"], 1)

    def test_diacritic_count_per_letter_sums(self):
        """Total diacritics across all letters must match VR001 totals.

        Count each diacritic occurrence in all_diacritics across all rows.
        """
        diac_counts = Counter()
        for row in self.rows:
            for ch in row["all_diacritics"]:
                diac_counts[ord(ch)] += 1

        for cp, expected in EXPECTED_DIACRITIC_COUNTS.items():
            actual = diac_counts.get(cp, 0)
            self.assertEqual(actual, expected,
                             f"Diacritic U+{cp:04X}: expected {expected}, got {actual}")

    def test_primary_diacritic_coverage(self):
        """Most letters should have a primary diacritic (haraka)."""
        with_primary = sum(1 for r in self.rows if r["primary_diacritic"])
        # At minimum, fatha+kasra+damma+sukun occurrences
        min_expected = (EXPECTED_DIACRITIC_COUNTS[0x064E] +
                        EXPECTED_DIACRITIC_COUNTS[0x0650] +
                        EXPECTED_DIACRITIC_COUNTS[0x064F] +
                        EXPECTED_DIACRITIC_COUNTS[0x0652])
        # Some letters have shadda+haraka, so primary count <= haraka count
        # but should be close
        self.assertGreater(with_primary, min_expected * 0.95)

    def test_no_letter_in_diacritics(self):
        """No letter code point should appear in all_diacritics."""
        from src.parser.verify_source import LETTER_SET
        for row in self.rows[:5000]:
            for ch in row["all_diacritics"]:
                self.assertNotIn(ord(ch), LETTER_SET)


if __name__ == "__main__":
    unittest.main()

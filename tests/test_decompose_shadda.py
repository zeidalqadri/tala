#!/usr/bin/env python3
"""Tests for M3 — Shadda Decomposition."""

import unittest
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser.verify_source import EXPECTED_TOTAL_LETTERS, EXPECTED_DIACRITIC_COUNTS
from src.parser.decompose_shadda import classify_shadda, FIELDNAMES
from src.parser.extract_diacritics import extract_letters_with_diacritics

SHADDA_CP = 0x0651
EXPECTED_SHADDA = EXPECTED_DIACRITIC_COUNTS[SHADDA_CP]  # 23,016


class TestShaddaDecomposition(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        raw = extract_letters_with_diacritics()
        cls.rows = classify_shadda(raw)

    def test_total_letter_count(self):
        """Row count must not change: still 327,793."""
        self.assertEqual(len(self.rows), EXPECTED_TOTAL_LETTERS)

    def test_fieldnames_present(self):
        """Each row must carry the three new M3 fields."""
        for row in self.rows[:20]:
            self.assertIn("shadda_type", row)
            self.assertIn("shadda_sonic_count", row)
            self.assertIn("shadda_visual_count", row)

    def test_shadda_total_unchanged(self):
        """has_shadda count must still be 23,016."""
        count = sum(1 for r in self.rows if r["has_shadda"])
        self.assertEqual(count, EXPECTED_SHADDA)

    def test_shadda_types_partition(self):
        """Every shaddaed letter has exactly one of the three types."""
        valid = {"true_doubling", "al_assimilation", "noon_assimilation"}
        for r in self.rows:
            if r["has_shadda"]:
                self.assertIn(r["shadda_type"], valid,
                              f"Unexpected type {r['shadda_type']!r}")
            else:
                self.assertEqual(r["shadda_type"], "",
                                 "Non-shaddaed row should have empty shadda_type")

    def test_shadda_type_sum_equals_shadda_count(self):
        """Sum of all three type counts = total shadda count."""
        typed = sum(1 for r in self.rows if r["shadda_type"])
        self.assertEqual(typed, EXPECTED_SHADDA)

    def test_sonic_count(self):
        """shadda_sonic_count = 2 iff has_shadda, else 1."""
        for r in self.rows[:10000]:
            expected = 2 if r["has_shadda"] else 1
            self.assertEqual(r["shadda_sonic_count"], expected)

    def test_visual_count_always_one(self):
        """shadda_visual_count is always 1."""
        for r in self.rows[:10000]:
            self.assertEqual(r["shadda_visual_count"], 1)

    def test_three_types_all_present(self):
        """All three shadda types appear in the corpus."""
        types = {r["shadda_type"] for r in self.rows if r["has_shadda"]}
        self.assertIn("true_doubling", types)
        self.assertIn("al_assimilation", types)
        self.assertIn("noon_assimilation", types)

    def test_first_surah_verse1_no_shadda_on_ba(self):
        """First letter ب in بِسْمِ has no shadda."""
        first = self.rows[0]
        self.assertEqual(first["letter"], "ب")
        self.assertFalse(first["has_shadda"])
        self.assertEqual(first["shadda_type"], "")

    def test_al_assimilation_only_sun_letters_or_lam(self):
        """al_assimilation must only classify letters that can assimilate ال.

        Sun letters + ل (for اللّه pattern).
        """
        # The set of letters that legitimately get al_assimilation shadda
        al_only = {
            "ت", "ث", "د", "ذ", "ر", "ز", "س", "ش",
            "ص", "ض", "ط", "ظ", "ل", "ن",
        }
        for r in self.rows:
            if r["shadda_type"] == "al_assimilation":
                self.assertIn(r["letter"], al_only,
                              f"Unexpected letter {r['letter']!r} in al_assimilation")

    def test_shadda_type_counts_stable(self):
        """Shadda type breakdown must be internally consistent (non-zero, sums to total)."""
        counts = Counter(r["shadda_type"] for r in self.rows if r["has_shadda"])
        total = sum(counts.values())
        self.assertEqual(total, EXPECTED_SHADDA)
        self.assertGreater(counts["true_doubling"], 0)
        self.assertGreater(counts["al_assimilation"], 0)
        self.assertGreater(counts["noon_assimilation"], 0)

    def test_mushaf_pos_preserved(self):
        """mushaf_pos sequential index is unchanged after classification."""
        for i, row in enumerate(self.rows):
            self.assertEqual(row["mushaf_pos"], i)

    def test_no_cross_verse_noon_assimilation(self):
        """Cross-word noon_assimilation should not cross verse boundaries."""
        for i, r in enumerate(self.rows):
            if r["shadda_type"] == "noon_assimilation" and r["char_idx"] == 0 and i > 0:
                prev = self.rows[i - 1]
                # Must be same surah and verse
                same_context = (prev["surah"] == r["surah"] and prev["verse"] == r["verse"])
                if not same_context:
                    self.fail(
                        f"Cross-verse noon_assimilation at surah {r['surah']} "
                        f"verse {r['verse']} word {r['word_idx']}"
                    )


if __name__ == "__main__":
    unittest.main()

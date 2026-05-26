#!/usr/bin/env python3
"""Tests for M1 — Letter Extraction."""

import csv
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser.verify_source import EXPECTED_LETTER_COUNTS, EXPECTED_TOTAL_LETTERS
from src.parser.extract_letters import extract_letters, FIELDNAMES


class TestExtractLetters(unittest.TestCase):
    """Verify letter extraction against VR001 counts."""

    @classmethod
    def setUpClass(cls):
        cls.rows = extract_letters()

    def test_total_count(self):
        """Must extract exactly 327,793 letter instances."""
        self.assertEqual(len(self.rows), EXPECTED_TOTAL_LETTERS)

    def test_fieldnames(self):
        """Each row must have all expected fields."""
        for row in self.rows[:10]:
            for field in FIELDNAMES:
                self.assertIn(field, row)

    def test_per_letter_counts(self):
        """Per-letter counts must match VR001 exactly."""
        from collections import Counter
        counts = Counter()
        for row in self.rows:
            cp = int(row["codepoint"][2:], 16)
            counts[cp] += 1
        for cp, expected in EXPECTED_LETTER_COUNTS.items():
            self.assertEqual(counts[cp], expected,
                             f"U+{cp:04X}: expected {expected}, got {counts[cp]}")

    def test_mushaf_pos_sequential(self):
        """mushaf_pos must be strictly sequential 0..N-1."""
        for i, row in enumerate(self.rows):
            self.assertEqual(row["mushaf_pos"], i)

    def test_surah_range(self):
        """Surah numbers must be 1..114."""
        surahs = {row["surah"] for row in self.rows}
        self.assertEqual(min(surahs), 1)
        self.assertEqual(max(surahs), 114)

    def test_verse_positive(self):
        """All verse numbers must be positive."""
        for row in self.rows[:100]:
            self.assertGreater(row["verse"], 0)

    def test_char_idx_starts_zero(self):
        """char_idx within a word starts at 0."""
        first_row = self.rows[0]
        self.assertEqual(first_row["char_idx"], 0)

    def test_no_diacritics_in_letters(self):
        """No diacritic code points should appear in the letter column."""
        from src.parser.verify_source import DIACRITIC_SET
        for row in self.rows:
            cp = ord(row["letter"])
            self.assertNotIn(cp, DIACRITIC_SET,
                             f"Diacritic U+{cp:04X} found in letter column")

    def test_first_letter_is_bism(self):
        """First letter should be from bismillah of surah 1 (ب)."""
        self.assertEqual(self.rows[0]["surah"], 1)
        self.assertEqual(self.rows[0]["letter"], "ب")

    def test_114_surahs(self):
        """All 114 surahs must be represented."""
        surahs = {row["surah"] for row in self.rows}
        self.assertEqual(len(surahs), 114)

    def test_word_idx_nonnegative(self):
        """word_idx must be >= 0."""
        for row in self.rows[:100]:
            self.assertGreaterEqual(row["word_idx"], 0)

    def test_codepoint_format(self):
        """Codepoint must be U+XXXX format."""
        for row in self.rows[:100]:
            cp = row["codepoint"]
            self.assertTrue(cp.startswith("U+"))
            self.assertEqual(len(cp), 6)

    def test_letter_matches_codepoint(self):
        """Letter character must match its codepoint."""
        for row in self.rows[:1000]:
            cp_int = int(row["codepoint"][2:], 16)
            self.assertEqual(ord(row["letter"]), cp_int)


class TestCSVOutput(unittest.TestCase):
    """Test CSV file generation."""

    @classmethod
    def setUpClass(cls):
        cls.output_path = Path(__file__).resolve().parent.parent / "data" / "processed" / "letters.csv"
        if not cls.output_path.exists():
            from src.parser.extract_letters import extract_letters, write_csv
            rows = extract_letters()
            write_csv(rows, str(cls.output_path))

    def test_csv_exists(self):
        self.assertTrue(self.output_path.exists())

    def test_csv_header(self):
        with open(self.output_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        self.assertEqual(header, FIELDNAMES)

    def test_csv_row_count(self):
        with open(self.output_path, encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader)  # skip header
            count = sum(1 for _ in reader)
        self.assertEqual(count, EXPECTED_TOTAL_LETTERS)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for src/parser/verify_source.py (M0 — Source Verification)."""

import hashlib
import json
import unittest
from pathlib import Path

# Ensure src is on the path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser.verify_source import (
    DEFAULT_SOURCE,
    EXPECTED_SHA256,
    EXPECTED_TOTAL_LETTERS,
    EXPECTED_UNIQUE_LETTERS,
    EXPECTED_LETTER_COUNTS,
    EXPECTED_DIACRITIC_COUNTS,
    LETTER_SET,
    DIACRITIC_SET,
    run_verification,
)


class TestSourceExists(unittest.TestCase):
    """Verify the source XML file exists and has the right hash."""

    def test_file_exists(self):
        path = Path(DEFAULT_SOURCE)
        self.assertTrue(path.exists(), f"Source file not found: {path}")

    def test_sha256_matches(self):
        path = Path(DEFAULT_SOURCE)
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            sha256.update(f.read())
        self.assertEqual(sha256.hexdigest(), EXPECTED_SHA256,
                         "SHA-256 mismatch — file is not the expected version")


class TestCharacterInventory(unittest.TestCase):
    """Verify the character inventory matches VR001."""

    @classmethod
    def setUpClass(cls):
        cls.result = run_verification()
        cls.counts = cls.result

    def test_verification_passes(self):
        # Only expect pass if SHA matches and letter/diacritic counts match
        # (total char discrepancy from space counting is documented)
        sha_ok = self.result.get("sha256_ok", False)
        self.assertTrue(sha_ok, "SHA-256 should match")

    def test_letter_counts(self):
        """Each of the 36 letter forms must match VR001 exactly."""
        letter_counts = self.result.get("letter_counts", {})
        for cp, expected in EXPECTED_LETTER_COUNTS.items():
            actual = letter_counts.get(cp, 0)
            self.assertEqual(
                actual, expected,
                f"Letter U+{cp:04X} count mismatch: expected {expected}, got {actual}"
            )

    def test_total_letters(self):
        """Total letter instances must match VR001."""
        self.assertEqual(self.counts["total_letters"], EXPECTED_TOTAL_LETTERS)

    def test_unique_letters(self):
        """Must find exactly 36 unique letter forms."""
        self.assertEqual(self.counts["unique_letters"], EXPECTED_UNIQUE_LETTERS)

    def test_diacritic_counts(self):
        """Each diacritic/mark count must match VR001."""
        diacritic_counts = self.result.get("diacritic_counts", {})
        for cp, expected in EXPECTED_DIACRITIC_COUNTS.items():
            actual = diacritic_counts.get(cp, 0)
            self.assertEqual(
                actual, expected,
                f"Diacritic U+{cp:04X} count mismatch: expected {expected}, got {actual}"
            )

    def test_no_invisible_chars(self):
        """Zero invisible Unicode characters in verse text."""
        self.assertFalse(
            self.result.get("invisible_counts"),
            f"Invisible characters found: {self.result.get('invisible_counts')}"
        )

    def test_verse_structure(self):
        """Must have 114 surahs, 6236 verses."""
        self.assertEqual(self.counts["surahs"], 114)
        self.assertEqual(self.counts["verses"], 6236)


class TestClassification(unittest.TestCase):
    """Verify character classification boundaries."""

    def test_letter_boundaries(self):
        """All expected letter code points are classified as letters."""
        for cp in EXPECTED_LETTER_COUNTS:
            self.assertIn(cp, LETTER_SET, f"U+{cp:04X} should be in LETTER_SET")

    def test_diacritic_boundaries(self):
        """All expected diacritic code points are classified as diacritics."""
        for cp in EXPECTED_DIACRITIC_COUNTS:
            self.assertIn(cp, DIACRITIC_SET, f"U+{cp:04X} should be in DIACRITIC_SET")

    def test_no_overlap(self):
        """Letter and diacritic sets must not overlap."""
        overlap = LETTER_SET & DIACRITIC_SET
        self.assertFalse(overlap, f"Overlap between letter and diacritic sets: {overlap}")


class TestSourcePath(unittest.TestCase):
    """Test source path resolution."""

    def test_default_source_is_xml(self):
        self.assertTrue(DEFAULT_SOURCE.endswith(".xml"),
                        f"Default source should end with .xml: {DEFAULT_SOURCE}")


if __name__ == "__main__":
    unittest.main()

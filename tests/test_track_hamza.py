#!/usr/bin/env python3
"""Tests for M4 — Hamza Seat Tracking."""

import unittest
from collections import Counter
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.parser.verify_source import (
    EXPECTED_TOTAL_LETTERS, EXPECTED_LETTER_COUNTS, EXPECTED_DIACRITIC_COUNTS,
)
from src.parser.decompose_shadda import classify_shadda
from src.parser.extract_diacritics import extract_letters_with_diacritics
from src.parser.track_hamza import assign_hamza_seats, FIELDNAMES, HAMZA_SEATS

# Expected counts from VR001
EXPECTED_SEAT_COUNTS = {
    "alif_above": EXPECTED_LETTER_COUNTS[0x0623],  # 8,900
    "alif_below": EXPECTED_LETTER_COUNTS[0x0625],  # 5,088
    "waw":        EXPECTED_LETTER_COUNTS[0x0624],  # 706
    "ya":         EXPECTED_LETTER_COUNTS[0x0626],  # 921
    "standalone": EXPECTED_LETTER_COUNTS[0x0621],  # 3,059
}
EXPECTED_TOTAL_HAMZA = sum(EXPECTED_SEAT_COUNTS.values())  # 18,674
EXPECTED_MADDAH = EXPECTED_DIACRITIC_COUNTS[0x0653]         # 5,376
EXPECTED_COMBINING_HAMZA = EXPECTED_DIACRITIC_COUNTS[0x0654]  # 496


class TestHamzaSeatTracking(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        raw = extract_letters_with_diacritics()
        m3 = classify_shadda(raw)
        cls.rows = assign_hamza_seats(m3)

    # --- Row count and schema ---

    def test_total_row_count(self):
        """Row count must not change: 327,793."""
        self.assertEqual(len(self.rows), EXPECTED_TOTAL_LETTERS)

    def test_new_fields_present(self):
        """Every row must have the three new M4 fields."""
        for row in self.rows[:100]:
            self.assertIn("hamza_seat", row)
            self.assertIn("has_maddah", row)
            self.assertIn("has_combining_hamza", row)

    def test_fieldnames_complete(self):
        """FIELDNAMES must contain all three new fields."""
        for field in ("hamza_seat", "has_maddah", "has_combining_hamza"):
            self.assertIn(field, FIELDNAMES)

    # --- hamza_seat values and counts ---

    def test_hamza_seat_values(self):
        """hamza_seat must be one of the six valid values."""
        valid = set(HAMZA_SEATS.values()) | {"none"}
        for row in self.rows:
            self.assertIn(row["hamza_seat"], valid,
                          f"Invalid seat {row['hamza_seat']!r} at mushaf_pos={row['mushaf_pos']}")

    def test_seat_count_alif_above(self):
        """alif_above count must match VR001 أ count (8,900)."""
        n = sum(1 for r in self.rows if r["hamza_seat"] == "alif_above")
        self.assertEqual(n, EXPECTED_SEAT_COUNTS["alif_above"])

    def test_seat_count_alif_below(self):
        """alif_below count must match VR001 إ count (5,088)."""
        n = sum(1 for r in self.rows if r["hamza_seat"] == "alif_below")
        self.assertEqual(n, EXPECTED_SEAT_COUNTS["alif_below"])

    def test_seat_count_waw(self):
        """waw count must match VR001 ؤ count (706)."""
        n = sum(1 for r in self.rows if r["hamza_seat"] == "waw")
        self.assertEqual(n, EXPECTED_SEAT_COUNTS["waw"])

    def test_seat_count_ya(self):
        """ya count must match VR001 ئ count (921)."""
        n = sum(1 for r in self.rows if r["hamza_seat"] == "ya")
        self.assertEqual(n, EXPECTED_SEAT_COUNTS["ya"])

    def test_seat_count_standalone(self):
        """standalone count must match VR001 ء count (3,059)."""
        n = sum(1 for r in self.rows if r["hamza_seat"] == "standalone")
        self.assertEqual(n, EXPECTED_SEAT_COUNTS["standalone"])

    def test_total_hamza_count(self):
        """Sum of all non-'none' seats must equal 18,674."""
        n = sum(1 for r in self.rows if r["hamza_seat"] != "none")
        self.assertEqual(n, EXPECTED_TOTAL_HAMZA)

    # --- hamza_seat consistency with codepoint ---

    def test_seat_matches_codepoint(self):
        """Each hamza seat row must have the corresponding codepoint."""
        cp_to_seat = {
            "U+0621": "standalone",
            "U+0623": "alif_above",
            "U+0624": "waw",
            "U+0625": "alif_below",
            "U+0626": "ya",
        }
        seat_cps = set(cp_to_seat.keys())
        for row in self.rows:
            if row["hamza_seat"] != "none":
                expected_seat = cp_to_seat.get(row["codepoint"])
                self.assertIsNotNone(expected_seat,
                    f"Seat 'none' expected for codepoint {row['codepoint']}")
                self.assertEqual(row["hamza_seat"], expected_seat,
                    f"Seat mismatch at {row['mushaf_pos']}: "
                    f"cp={row['codepoint']} seat={row['hamza_seat']}")
            else:
                self.assertNotIn(row["codepoint"], seat_cps,
                    f"Expected a seat for {row['codepoint']} at {row['mushaf_pos']}")

    # --- has_maddah ---

    def test_maddah_count(self):
        """has_maddah=True count must equal U+0653 diacritic count (5,376)."""
        n = sum(1 for r in self.rows if r["has_maddah"])
        self.assertEqual(n, EXPECTED_MADDAH)

    def test_maddah_requires_diacritic(self):
        """has_maddah=True rows must have U+0653 in all_diacritics_cps."""
        for row in self.rows:
            if row["has_maddah"]:
                self.assertIn("U+0653", row["all_diacritics_cps"],
                    f"Missing U+0653 at {row['mushaf_pos']}")

    def test_maddah_most_common_on_bare_alif(self):
        """Bare alif (U+0627) must be the most common carrier of U+0653."""
        from collections import Counter
        carriers = Counter(r["codepoint"] for r in self.rows if r["has_maddah"])
        self.assertEqual(carriers.most_common(1)[0][0], "U+0627")

    # --- has_combining_hamza ---

    def test_combining_hamza_count(self):
        """has_combining_hamza=True count must equal U+0654 diacritic count (496)."""
        n = sum(1 for r in self.rows if r["has_combining_hamza"])
        self.assertEqual(n, EXPECTED_COMBINING_HAMZA)

    def test_combining_hamza_requires_diacritic(self):
        """has_combining_hamza=True rows must have U+0654 in all_diacritics_cps."""
        for row in self.rows:
            if row["has_combining_hamza"]:
                self.assertIn("U+0654", row["all_diacritics_cps"],
                    f"Missing U+0654 at {row['mushaf_pos']}")

    # --- non-hamza letters unchanged ---

    def test_non_hamza_seat_is_none(self):
        """Letters that are not hamza seats must have hamza_seat='none'."""
        non_hamza_cps = {
            "U+0627",  # bare alif
            "U+0628",  # ba
            "U+0644",  # lam
            "U+0645",  # meem
        }
        for row in self.rows:
            if row["codepoint"] in non_hamza_cps:
                self.assertEqual(row["hamza_seat"], "none",
                    f"Unexpected seat for {row['codepoint']} at {row['mushaf_pos']}")

    # --- prior milestone data preserved ---

    def test_shadda_data_preserved(self):
        """M3 shadda fields must survive the M4 pass unchanged."""
        shadda_rows = [r for r in self.rows if r["has_shadda"]]
        self.assertEqual(len(shadda_rows), 23016)
        for r in shadda_rows[:100]:
            self.assertIn(r["shadda_type"],
                          {"true_doubling", "al_assimilation", "noon_assimilation"})

    def test_diacritic_data_preserved(self):
        """M2 has_tanween field must survive."""
        tanween_count = sum(1 for r in self.rows if r["has_tanween"])
        self.assertGreater(tanween_count, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)

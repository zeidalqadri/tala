"""
Tests for src/parser/extract_letters.py.

Verifies:
- Total letter count matches VR001 (327,793)
- Known verses produce correct letter sequences
- Positional metadata is consistent
- Orthographic variants are preserved
"""

import os
import sys

# Ensure src/ is on the path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, REPO_ROOT)

from src.parser.extract_letters import (
    extract_letters,
    is_arabic_letter,
    variant_identity,
    word_position,
)

# ---------------------------------------------------------------------------
# Expected values (from VR001)
# ---------------------------------------------------------------------------
EXPECTED_TOTAL = 327793
BASMALAH_TEXT = 'بسمٱللهٱلرحمٰنٱلرحيم'


def _letters_only(text):
    """Extract only Arabic letters from a text string."""
    return ''.join(c for c in text if is_arabic_letter(c))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
class TestExtractLetters:
    """Test suite for letter extraction from Tanzil XML."""

    def setup_method(self):
        """Run extraction once per test method."""
        xml_path = os.path.join(REPO_ROOT, 'data', 'source', 'quran-uthmani-tanzil.xml')
        self.instances = extract_letters(xml_path)

    def test_total_count(self):
        """Total letter instances must match VR001: 327,793."""
        assert len(self.instances) == EXPECTED_TOTAL, (
            f"Expected {EXPECTED_TOTAL}, got {len(self.instances)}"
        )

    def test_surah_1_verse_1_sequence(self):
        """Surah 1, Verse 1 (basmalah) must have correct letter sequence."""
        chars = ''.join(
            r['letter_char'] for r in self.instances
            if int(r['surah_index']) == 1 and int(r['verse_index']) == 1
        )
        expected = _letters_only(BASMALAH_TEXT)
        assert chars == expected, (
            f"Surah 1:1 letters: expected '{expected}', got '{chars}'"
        )

    def test_surah_1_verse_1_count(self):
        """Surah 1, Verse 1 must have exactly 19 letters."""
        count = sum(
            1 for r in self.instances
            if int(r['surah_index']) == 1 and int(r['verse_index']) == 1
        )
        assert count == 19, f"Surah 1:1 expected 19 letters, got {count}"

    def test_surah_112_basmalah(self):
        """Surah 112 must have a bismillah (verse_index=0) before verse 1."""
        bismillah = [
            r for r in self.instances
            if int(r['surah_index']) == 112 and int(r['verse_index']) == 0
        ]
        assert len(bismillah) == 19, (
            f"Surah 112 basmalah expected 19 letters, got {len(bismillah)}"
        )

    def test_surah_112_verse_1(self):
        """Surah 112, Verse 1 must have correct letter sequence."""
        chars = ''.join(
            r['letter_char'] for r in self.instances
            if int(r['surah_index']) == 112 and int(r['verse_index']) == 1
        )
        assert len(chars) == 11, f"Surah 112:1 expected 11 letters, got {len(chars)}: {chars}"
        assert chars == 'قلهوٱللهأحد', f"Surah 112:1 got '{chars}'"

    def test_surah_2_bismillah_boundary(self):
        """Last bismillah before Surah 2:1 must precede first verse letter."""
        bismillah = [
            r for r in self.instances
            if int(r['surah_index']) == 2 and int(r['verse_index']) == 0
        ]
        verse1 = [
            r for r in self.instances
            if int(r['surah_index']) == 2 and int(r['verse_index']) == 1
        ]
        assert len(bismillah) == 19, "Surah 2 basmalah should have 19 letters"
        assert len(verse1) == 3, "Surah 2:1 should have 3 letters (الم)"

        last_bism = bismillah[-1]
        first_v1 = verse1[0]
        assert last_bism['following_letter'] == first_v1['letter_char'], (
            f"Boundary broken: bismillah following='{last_bism['following_letter']}', "
            f"verse1 first='{first_v1['letter_char']}'"
        )

    def test_mushaf_position_continuous(self):
        """Mushaf position must be sequential 1..327793 with no gaps or duplicates."""
        positions = [int(r['mushaf_position']) for r in self.instances]
        assert positions[0] == 1, f"First mushaf_position should be 1, got {positions[0]}"
        assert positions[-1] == EXPECTED_TOTAL, (
            f"Last mushaf_position should be {EXPECTED_TOTAL}, got {positions[-1]}"
        )
        assert positions == list(range(1, EXPECTED_TOTAL + 1)), (
            "Mushaf positions are not continuous 1..327793"
        )

    def test_surah_position_continuous(self):
        """Surah position must be sequential within each surah."""
        current_surah = 0
        expected_pos = 0
        for r in self.instances:
            s = int(r['surah_index'])
            p = int(r['surah_position'])
            if s != current_surah:
                current_surah = s
                expected_pos = 1
            assert p == expected_pos, (
                f"Surah {s}: expected surah_position {expected_pos}, got {p}"
            )
            expected_pos += 1

    def test_verse_position_starts_at_1(self):
        """Verse position must start at 1 for each verse (and each bismillah)."""
        seen_verses = set()
        for r in self.instances:
            key = (int(r['surah_index']), int(r['verse_index']))
            if key not in seen_verses:
                seen_verses.add(key)
                assert int(r['verse_position']) == 1, (
                    f"Surah {r['surah_index']} verse {r['verse_index']} "
                    f"first letter: expected verse_position=1, "
                    f"got {r['verse_position']}"
                )

    def test_word_position_values(self):
        """Word position must be one of: isolated, initial, medial, final."""
        valid = {'isolated', 'initial', 'medial', 'final'}
        for r in self.instances:
            assert r['word_position'] in valid, (
                f"Invalid word_position '{r['word_position']}' at "
                f"mushaf_position {r['mushaf_position']}"
            )

    def test_orthographic_variants_preserved(self):
        """Key letter counts must match VR001 per-letter table."""
        counts = {}
        for r in self.instances:
            variant = r['variant_identity']
            counts[variant] = counts.get(variant, 0) + 1

        expected_counts = {
            'lam': 38550,
            'noon': 27380,
            'meem': 27071,
            'bare_alif': 25184,
            'waw': 24970,
        }
        for variant, expected in expected_counts.items():
            actual = counts.get(variant, 0)
            assert actual == expected, (
                f"Variant '{variant}': expected {expected}, got {actual}"
            )

    def test_adjacent_letters_boundaries(self):
        """preceding_letter empty only for first; following_letter only for last."""
        assert self.instances[0]['preceding_letter'] == '', (
            "First letter should have empty preceding_letter"
        )
        assert self.instances[-1]['following_letter'] == '', (
            "Last letter should have empty following_letter"
        )
        for r in self.instances[1:-1]:
            assert r['preceding_letter'] != '', (
                f"Internal letter at mushaf_position {r['mushaf_position']} "
                f"has empty preceding_letter"
            )
            assert r['following_letter'] != '', (
                f"Internal letter at mushaf_position {r['mushaf_position']} "
                f"has empty following_letter"
            )


class TestHelpers:
    """Unit tests for helper functions."""

    def test_is_arabic_letter_lam(self):
        assert is_arabic_letter('ل') is True

    def test_is_arabic_letter_space(self):
        assert is_arabic_letter(' ') is False

    def test_is_arabic_letter_fatha(self):
        assert is_arabic_letter('\u064E') is False

    def test_variant_identity_lam(self):
        assert variant_identity('ل') == 'lam'

    def test_variant_identity_alef_wasla(self):
        assert variant_identity('ٱ') == 'alef_wasla'

    def test_variant_identity_teh_marbuta(self):
        assert variant_identity('ة') == 'teh_marbuta'

    def test_word_position_isolated(self):
        assert word_position(['ب'], 0) == 'isolated'

    def test_word_position_initial(self):
        assert word_position(['ب', 'س', 'م'], 0) == 'initial'

    def test_word_position_medial(self):
        assert word_position(['ب', 'س', 'م'], 1) == 'medial'

    def test_word_position_final(self):
        assert word_position(['ب', 'س', 'م'], 2) == 'final'

"""
Extract structured letter instances from Tanzil Uthmani XML.

Parses quran-uthmani-tanzil.xml and produces a CSV where each row is
one Arabic letter instance with full positional metadata.

Output: data/processed/letter_instances.csv
Total letter instances expected: 327,793 (36 orthographic forms, VR001).

Premises upheld:
  - Text is read-only (never modified)
  - Orthographic variants preserved as distinct (Premise 9)
  - No external labels applied (Premise 2, 11)
  - Every letter counted, including bismillah attributes (Premise 4)
"""

import csv
import os
import sys
import xml.etree.ElementTree as ET

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
XML_PATH = os.path.join(REPO_ROOT, 'data', 'source', 'quran-uthmani-tanzil.xml')
OUTPUT_DIR = os.path.join(REPO_ROOT, 'data', 'processed')
OUTPUT_PATH = os.path.join(OUTPUT_DIR, 'letters.csv')

# ---------------------------------------------------------------------------
# Arabic letter inventory -- 36 orthographic forms (from VR001)
# ---------------------------------------------------------------------------
_ARABIC_LETTERS = {
    0x0621: 'hamza',
    0x0623: 'alif_hamza_above',
    0x0624: 'waw_hamza_above',
    0x0625: 'alif_hamza_below',
    0x0626: 'yeh_hamza_above',
    0x0627: 'bare_alif',
    0x0628: 'beh',
    0x0629: 'teh_marbuta',
    0x062A: 'teh',
    0x062B: 'theh',
    0x062C: 'jeem',
    0x062D: 'hah',
    0x062E: 'khah',
    0x062F: 'dal',
    0x0630: 'thal',
    0x0631: 'reh',
    0x0632: 'zain',
    0x0633: 'seen',
    0x0634: 'sheen',
    0x0635: 'sad',
    0x0636: 'dad',
    0x0637: 'tah',
    0x0638: 'zah',
    0x0639: 'ain',
    0x063A: 'ghain',
    0x0641: 'feh',
    0x0642: 'qaf',
    0x0643: 'kaf',
    0x0644: 'lam',
    0x0645: 'meem',
    0x0646: 'noon',
    0x0647: 'heh',
    0x0648: 'waw',
    0x0649: 'alif_maqsura',
    0x064A: 'yeh',
    0x0671: 'alef_wasla',
}


def is_arabic_letter(char):
    """Return True if char is one of the 36 Arabic letter forms."""
    return ord(char) in _ARABIC_LETTERS


def variant_identity(char):
    """Return the orthographic variant label for a letter character."""
    return _ARABIC_LETTERS.get(ord(char), 'unknown')


def word_position(word_letters, idx):
    """Return position of letter within word: isolated, initial, medial, final."""
    n = len(word_letters)
    if n == 1:
        return 'isolated'
    if idx == 0:
        return 'initial'
    if idx == n - 1:
        return 'final'
    return 'medial'


# ---------------------------------------------------------------------------
# Core extraction
# ---------------------------------------------------------------------------
def _collect_segments(root):
    """Yield dicts with 'text', 'surah_index', 'verse_index' in reading order.

    Bismillah attributes (present on verse 1 of suras 2-8, 10-114) are
    emitted before verse 1 with verse_index=0.
    """
    for sura in root.findall('.//sura'):
        sura_idx = int(sura.get('index'))
        for aya in sura.findall('aya'):
            verse_idx = int(aya.get('index'))
            bism = aya.get('bismillah')
            if bism:
                yield {'text': bism,
                       'surah_index': sura_idx,
                       'verse_index': 0}
            yield {'text': aya.get('text', ''),
                   'surah_index': sura_idx,
                   'verse_index': verse_idx}


def extract_letters(xml_path=None):
    """Parse XML and return list of letter-instance dicts."""
    if xml_path is None:
        xml_path = XML_PATH

    tree = ET.parse(xml_path)
    root = tree.getroot()

    # ---- Pass 1: collect text segments in reading order ----
    segments = list(_collect_segments(root))

    # ---- Pass 2: flat array of every letter char in sequence ----
    all_letters = []
    for seg in segments:
        for word in seg['text'].split(' '):
            for ch in word:
                if is_arabic_letter(ch):
                    all_letters.append(ch)

    # ---- Pass 3: build instances with positional metadata ----
    instances = []
    global_idx = 0  # index into all_letters (0-based)

    for seg in segments:
        words = seg['text'].split(' ')
        verse_letter_pos = 0

        for word_idx, word in enumerate(words):
            if not word:
                continue

            # Collect letter chars + their positions in the global array
            word_letters = []
            word_global_positions = []
            for ch in word:
                if is_arabic_letter(ch):
                    word_letters.append(ch)
                    word_global_positions.append(global_idx)
                    global_idx += 1

            for li, letter in enumerate(word_letters):
                gp = word_global_positions[li]
                verse_letter_pos += 1

                # preceding / following letter (global adjacency)
                preceding = all_letters[gp - 1] if gp > 0 else ''
                following = all_letters[gp + 1] if gp < len(all_letters) - 1 else ''

                instances.append({
                    'letter_char': letter,
                    'letter_code': f'U+{ord(letter):04X}',
                    'variant_identity': variant_identity(letter),
                    'surah_index': seg['surah_index'],
                    'verse_index': seg['verse_index'],
                    'word_index': word_idx + 1,
                    'mushaf_position': gp + 1,  # 1-based
                    'word_position': word_position(word_letters, li),
                    'verse_position': verse_letter_pos,
                    'surah_position': None,  # filled below
                    'preceding_letter': preceding,
                    'following_letter': following,
                })

    # ---- Pass 4: fill surah_position (sequential within surah) ----
    current_surah = 0
    surah_pos = 0
    for inst in instances:
        if inst['surah_index'] != current_surah:
            current_surah = inst['surah_index']
            surah_pos = 0
        surah_pos += 1
        inst['surah_position'] = surah_pos

    return instances


def write_csv(instances, path=None):
    """Write letter instances to CSV."""
    if path is None:
        path = OUTPUT_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)

    fieldnames = [
        'surah_index', 'verse_index', 'word_index',
        'mushaf_position', 'surah_position', 'verse_position',
        'word_position',
        'letter_char', 'letter_code', 'variant_identity',
        'preceding_letter', 'following_letter',
    ]

    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(instances)

    return len(instances)


def main():
    print(f"Parsing: {XML_PATH}")
    instances = extract_letters()
    total = len(instances)
    print(f"Extracted {total} letter instances")

    write_csv(instances)
    print(f"Written to: {OUTPUT_PATH}")

    expected = 327793
    if total == expected:
        print(f"Count match: {total:,} (expected {expected:,})")
        return 0
    else:
        print(f"Count MISMATCH: {total:,} vs expected {expected:,}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

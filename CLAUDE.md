# The Weight of Letters — Project Instructions

## What This Project Is

A computational investigation into whether each Arabic letter in the Quran carries intrinsic semantic significance — a discoverable "meaning direction" that is consistent across the text's vocabulary, grounded in four independent layers of evidence (sonic, geometric, structural, frequency), and verifiable by the text's own usage without any external reference.

The project opens with the الم that begins Al-Baqarah and closes by returning to it. The letters that open certain surahs are the held-out validation — reserved for last, after all 28 semantic directions are independently established from ordinary vocabulary.

## Core Documents

- **The_Weight_of_Letters_Whitepaper.md** — The theoretical framework, motivation, and aspiration. Start here.
- **Quranic_Letter_Significance_ML_Methodology.md** — The full technical pipeline.

Both must stay synchronized. Changes to one must be reflected in the other.

## The Eleven Premises (Non-Negotiable)

Every response, analysis, code, and design decision must comply with all eleven. If a premise would be violated, stop and flag it.

1. **Sole data source**: Only the Quran (Uthmani script, complete tashkeel). Admitted metadata: surah boundaries, verse boundaries, sequential position only.
2. **لسان not لغة**: The text calls itself لسان عربي (a tongue), not لغة عربية (a language). External Arabic linguistic resources — grammars, dictionaries, scholarly traditions — are لغة, the derivative. Never import the daughter to explain the mother.
3. **No imposed meaning**: No assumptions about what letters mean. Significance must emerge from data.
4. **Every beat counts**: Every letter and diacritic at every position carries full weight, including word-final. The written text is authoritative. No pausal conventions, no spoken-Arabic modifications.
5. **Letters are geometric objects**: Every letter is a transformation of alif. Shape is data.
6. **Frequency is a primary dimension**: Described by whatever distribution fits. No external law imposed as a standard.
7. **Astronomical metaphor**: Conjunctions, oppositions, transits, phases, occultations, sequential order — as precise statistical mappings, not decoration.
8. **Surah-opening letters reserved for last**: The letters that open certain surahs are the held-out test. Never use them to derive or train semantic directions. The individual letters (ا, ل, م, etc.) ARE analyzed in normal vocabulary — only the opening letter sequences themselves are reserved for the Final Stage.
9. **Orthographic variants are data**: Never collapse أ/إ/آ/ا/ٱ, never merge ة into ت or هـ, never conflate ى and ي. Also track small alif (الألف الخنجرية). Unification is a finding, not an assumption.
10. **No recitation conventions as data**: Tajweed rules, pausal practices, and oral tradition describe what people do with the text, not what the text says. Only textually-observable features count.
11. **No external names for textual features**: Describe what you observe in the text, never apply external scholarly labels or categories. The text contains letters at the openings of certain surahs — describe them as such, not with external terms from scholarly tradition.

## The Four Layers (Always This Order — Developmental Sequence)

1. **Sonic (الصوت)**: Articulatory geography (7 makhraj zones) + diacritical modulation (8 marks). Makhraj = fixed geography. Diacritic = variable weather. Admitted as anatomical fact.
2. **Geometric (الشكل)**: Transformations of alif. Visual families. Two tiers (base geometry + dots). لا ligature as composite entity. Transformation distance.
3. **Structural (الرسم)**: Identity, position, morphological role. Root vs. affix. Connecting vs. non-connecting.
4. **Frequency (التكرار)**: Luminosity — magnitude, distribution, regularity, rank, evolution.

## External Contamination Checklist

Before any analysis, code, or response, verify. If any item is being used as data, input, label, validation target, or naming convention — stop.

**Never use as data or apply to the text:**
- Tafsir (commentary)
- Hadith (prophetic traditions)
- External Arabic corpora
- Arabic dictionaries or lexicons
- Arabic grammar references (as training data)
- Recitation recordings or oral tradition
- Tajweed rule specifications (beyond what is marked in the text)
- Meccan/Medinan classification
- Juz divisions
- Subject matter categories
- External scholarly terms or labels for textual features
- Pre-trained Arabic language models
- Pausal reading conventions
- Any external naming convention applied to textual phenomena (describe, don't label)

**Admissible:**
- The Quranic text itself (Uthmani, complete tashkeel)
- Surah and verse boundaries
- Sequential position in the mushaf
- Articulatory geography (anatomical fact)
- Physical acoustic properties (measurable)
- Statistical tools and ML algorithms (instruments)
- Rendering of letters in standard Arabic typefaces (for geometric analysis)

**Gray areas requiring caution:**
- PyArabic: Use for Unicode character processing and text handling only. Do not use any analytical component trained on external data.
- Word boundaries: The text's own spacing defines words. Proclitics (بـ, لـ, وـ, فـ, كـ) are written attached — they are part of the written unit as the text presents it.
- Morphological terminology: "Root," "template," "pattern" describe computationally-discovered structures, not assumed categories. If the analysis discovers tri-consonantal clustering, calling it "roots" is descriptive shorthand.

## Special Cases

### ة (Ta Marbuta)
Always vocalized in the Quran (never sukoon). The text never silences it. Treat as its own entity — neither ت nor هـ. Its distributional proximity to either is a finding.

### Shadda
Three counts: visual (1), sonic (2), shadow (1). Distinguish true doubling (root-internal) from assimilation (letter consumed). The consumed letter's geometry disappears but its sonic ghost persists.

### Hamza
One sound (glottal stop, zone 2), multiple visual seats (أ إ ؤ ئ ء). Analyze each seat separately.

### لا Ligature
Two structural letters, one geometric form. Track as composite entity.

### Small Alif (الألف الخنجرية)
Superscript dagger alif in Uthmani script. Track as an alif variant alongside bare ا, أ, إ, آ, ٱ.

### Alif Maqsura (ى) vs. Ya (ي)
Functionally different despite visual similarity. Treated as separate entities.

## Pipeline

```
Stage 0: Calibration (17 tests, 0A-0Q)
    8 single-letter particles: بـ لـ كـ فـ وـ (prepositional) + يـ تـ نـ (actor)
    [GATE: All 17 pass]

Cycle 1: Exploratory — all five tracks + variants + cross-track

Cycle 2: Confirmatory — sequence modeling, causal analysis, probing, initial semantic estimation

Cycle 3: Validation + Semantic Extraction — pre-registered predictions, robustness, full semantic pipeline
    [GATE: All directions established and verified]

Final Stage: Surah-Opening Letters — compose directions, test against surahs, close the loop
```

## Semantic Direction Verification Standard

The text claims لَا رَيْبَ فِيهِ — no discrepancy. This sets the bar:

- A proposed direction must work across EVERY word containing that letter
- Cross-word consistency score must exceed chance (permutation test, p < 0.01)
- Root-decomposition must show composed directions predict root semantic domains
- If a direction fails for any subset, it is wrong or incomplete — refine, don't rationalize

## Formatting and Communication

- Use Arabic script for letter references wherever possible
- Layer order is always: sonic → geometric → structural → frequency
- The surah-opening letters are always "the final stage" or "the held-out test"
- Never apply external scholarly labels to textual phenomena — describe what you observe
- The closing line: "The text is لسان. We honor the tongue."
- Mark hypothetical letter-meaning illustrations clearly — never present as established fact until cross-word verification is complete

## What Not To Do

- Do not impose meaning before the data suggests it
- Do not use any surah-opening letter sequence to derive or constrain semantic directions
- Do not normalize orthographic variants without distributional evidence
- Do not apply pausal or recitation conventions to the written text
- Do not reference external Arabic linguistic resources as data
- Do not treat frequency as requiring conformance to any external distribution
- Do not present speculative interpretations as findings
- Do not drop or downweight word-final diacritics
- Do not use external analytical tools trained on non-Quranic data
- Do not label data-emergent clusters or textual features with external names
- Do not assume Arabic morphological categories — discover them
- Do not use the term "muqatta'at" or "disconnected letters" or "حروف مقطعة" — these are external scholarly labels, not the text's own description. Refer to them as "the letters that open certain surahs" or "surah-opening letters"

## When In Doubt

Ask: "Is this coming from the text, or from something built around the text?" If the latter, it is لغة. Exclude it.

Ask: "Am I describing what I observe, or applying a name from tradition?" If the latter, describe instead.

The text is لسان. We honor the tongue.

# Decision Document 001: Data Source Selection and Validation

## The Weight of Letters — Pre-Implementation Decision Record

---

## 0. Purpose

Before writing any code, we must select and validate the exact digital text that will serve as the sole data source for the entire project. Every subsequent analysis traces back to this file. An error here propagates everywhere. An undocumented choice here becomes an invisible assumption.

This document records the decision, the reasoning, the risks, and the validation steps.

---

## 1. What We Need

The data source must satisfy all of the following requirements, derived from the project's premises:

**R1 — Complete tashkeel**: Every letter must carry its full diacritical marking.

**R2 — Orthographic variants preserved**: The encoding must distinguish ا from أ from إ from آ from ٱ. It must distinguish ى from ي. It must encode ة as a distinct character. It must track hamza seats (أ إ ؤ ئ ء) as separate code points.

**R3 — No tajweed encoding**: The Unicode must not embed tajweed rules into the character stream (e.g., no different tanween forms for ikhfaa/idghaam, no substituted sukoon characters).

**R4 — Standard Unicode**: Standard Arabic Unicode code points (U+0600 block), not Private Use Area or font-specific encodings.

**R5 — Small alif (الألف الخنجرية) tracked**: Encoded and distinguishable.

**R6 — Surah and verse structure preserved**.

**R7 — No external annotations embedded**: Clean text only.

**R8 — Verified against a physical mushaf**.

**R9 — Ya (ي) and alif maqsura (ى) not collapsed**: Must remain distinct code points.

---

## 2. Available Sources

### 2.1 Tanzil.net Uthmani Text (v1.1, February 2021)

**What it is**: The most widely used digital Quranic text for applications and research. Produced by integrating multiple previous digital Quran projects, then verified through manual and automatic phases against the Medina Mushaf. UTF-8. Creative Commons Attribution 3.0.

**Strengths**:
- Manually verified against the Medina Mushaf (Uthman Taha calligraphy)
- Does not encode tajweed rules into the character stream
- Version-controlled with change logs
- The most independently cited and cross-checked digital Quran text

**Risks**:
- Sequential tanweens (visually distinct in the printed mushaf for idghaam/ikhfaa) encoded as standard tanweens — a Unicode limitation, not a Tanzil choice, but information from the printed page is lost
- Encoding has changed slightly over time — version pinning is essential
- Small alif handling needs verification
- ي/ى distinction needs verification
- Alif variant encoding needs verification

### 2.2 QPC Hafs Standard Unicode (via Tarteel QUL)

**What it is**: The standard Unicode Hafs text published by the King Fahd Glorious Quran Printing Complex (KFGQPC), made accessible through the Quranic Universal Library (QUL) maintained by Tarteel AI. Described as "standard unicode based hafs script."

**Strengths**:
- Official source — published by the institution that prints the Medina Mushaf
- Available through QUL in structured formats (SQLite, JSON)
- QUL provides a Unicode character inspection tool and a script comparison tool — directly useful for our validation
- Word-by-word and ayah-by-ayah breakdowns available

**Risks**:
- Must verify this is the standard Unicode variant, not a glyph-based variant (QPC V1, V2, V4 are glyph-based and font-dependent — unusable for character-level analysis)
- Must verify variant handling matches our requirements
- The QPC ecosystem includes multiple text variants for different fonts and printing traditions — must select the correct one
- Less independently verified by external researchers compared to Tanzil

### 2.3 Quran.com Text

**What it is**: Quran.com defaults to the Uthmani script (Medina Mushaf). Its backend data draws from the QPC/Tarteel ecosystem. A comparative analysis characterized Quran.com as a "Visual Liturgy" focused on faithful visual rendering, versus Tanzil as a "Purist Archive" focused on Unicode integrity.

**Assessment**: Quran.com's text is derivative of the QPC source, served through their API with rendering-oriented formatting. It does not appear to be an independent encoding. Its value is as a third cross-reference point, not as a primary source.

**Risks**:
- Text may include rendering-specific characters or formatting not present in the underlying QPC data
- API-served text may undergo transformations not documented for raw data consumers
- The "Visual Liturgy" orientation suggests choices may favor display fidelity over character-level analytical integrity

### 2.4 Nuqayah Text (Derived from Tanzil)

**Disqualified.** Collapses ي and ى into one character (U+06CC Farsi Yeh). Encodes tajweed rules into Unicode (open tanween for ikhfaa/idghaam). Substitutes non-standard sukoon and madda characters. Violates R2, R3, R4, R9.

### 2.5 aliftype/quran-data (GitHub)

**What it is**: UTF-8 encoded Quran text following Unicode best practices. Self-described as "not formally reviewed" and "may contain unintentional errors."

**Assessment**: Insufficient verification. Self-acknowledged error risk. Not suitable as primary source. May serve as an additional cross-reference.

---

## 3. Recommendation

### Primary candidate: Tanzil.net Uthmani text, v1.1

**Rationale**: Most verified, most widely used, does not encode tajweed rules, standard Unicode, independent of any specific font ecosystem. The "Purist Archive" orientation aligns with our analytical needs — we need character-level integrity, not visual rendering fidelity.

### Cross-validation source: QPC Hafs Standard Unicode (via QUL)

**Rationale**: Official source from the mushaf publisher. Independent encoding of the same printed text. Having two encodings of the same physical mushaf allows character-by-character cross-validation. Where they agree, confidence is high. Where they disagree, investigation against the physical mushaf resolves the discrepancy.

### Tertiary reference: Quran.com API (quran-uthmani edition)

**Rationale**: Third data point for triangulation on specific discrepancies. Not relied upon for primary or cross-validation.

### Validation tools: QUL Unicode character inspector and script comparison tool

**Rationale**: These tools, built by Tarteel for exactly this kind of character-level inspection, can accelerate validation steps without introducing analytical dependency on external لغة resources.

**This recommendation is preliminary.** It cannot be finalized until the validation protocol in §4 is completed.

---

## 4. Validation Protocol

### 4.1 Character Inventory

Download the Tanzil Uthmani v1.1 text. Produce a complete inventory of every unique Unicode code point:

- Unicode value (e.g., U+0628)
- Unicode name (e.g., ARABIC LETTER BEH)
- Our interpretation (e.g., ب — ba)
- Count of occurrences
- Category: letter / diacritic / structural marker / whitespace / other

This is the ground-truth inventory. Unexpected code points or missing expected ones must be investigated.

### 4.2 Variant Verification

For each orthographic variant, verify presence and distinctness:

| Variant | Expected Code Point | Present? | Count | Distinct from? |
|---------|-------------------|----------|-------|----------------|
| ا (bare alif) | U+0627 | ? | ? | أ إ آ ٱ |
| أ (alif + hamza above) | U+0623 | ? | ? | ا |
| إ (alif + hamza below) | U+0625 | ? | ? | ا |
| آ (alif + madda) | U+0622 | ? | ? | ا أ |
| ٱ (alif al-wasl) | U+0671 | ? | ? | ا |
| ٰ (small/dagger alif) | U+0670 | ? | ? | ا |
| ى (alif maqsura) | U+0649 | ? | ? | ي |
| ي (ya) | U+064A | ? | ? | ى |
| ة (ta marbuta) | U+0629 | ? | ? | ت هـ |
| ء (standalone hamza) | U+0621 | ? | ? | أ إ ؤ ئ |
| ؤ (hamza on waw) | U+0624 | ? | ? | و ء |
| ئ (hamza on ya-seat) | U+0626 | ? | ? | ي ء |

### 4.3 Diacritical Completeness Check

Flag any consonant letter not followed by a diacritical code point. Review flagged instances against a physical mushaf to determine if the omission is an encoding error or legitimate Uthmani orthography.

### 4.4 Ta Marbuta Diacritical Verification

Enumerate every ة (U+0629). Verify each carries a vowel diacritic and never sukoon.

### 4.5 Structural Integrity Check

Verify 114 surahs, correct verse counts, no missing or duplicated verses.

### 4.6 Invisible Character Audit

Search for: Zero-Width Joiner (U+200D), Zero-Width Non-Joiner (U+200C), Word Joiner (U+2060), Hair Space (U+200A), RTL/LTR marks (U+200F/U+200E), any Private Use Area characters. Document locations and purposes.

### 4.7 Three-Way Cross-Validation

For a representative sample of surahs (Al-Fatihah; Al-Baqarah verses 1-5; a mid-length surah; a short surah), compare character-by-character across three sources:

1. Tanzil Uthmani v1.1
2. QPC Hafs Standard Unicode (via QUL)
3. Quran.com API (quran-uthmani)

For each discrepancy:
- Document the exact code points that differ
- Identify which source uses which encoding
- Resolve against a physical Medina Mushaf where possible
- If unresolvable, document as a known encoding ambiguity

The QUL script comparison tool and Unicode character inspector can assist with this step directly.

### 4.8 Physical Mushaf Spot-Check

For at least 10 verses selected from different parts of the text, manually compare the primary digital text against a physical Medina Mushaf, character by character, diacritic by diacritic.

---

## 5. Embedded Decisions and Their Risks

### 5.1 The Tanween Problem

The printed Medina Mushaf visually distinguishes regular tanween from sequential tanween (in idghaam/ikhfaa contexts). Unicode has no separate code point for sequential tanween. All known digital sources encode them identically.

**Impact**: A visual distinction present in the physical mushaf is lost in every available digital encoding. This is information loss at the digitization boundary.

**Mitigation**: Document the loss. Flag any tanween-related findings as operating on an underdetermined representation.

**Open question**: Is the distinction a property of the text itself, or a visual rendering convention? This question may be unresolvable without introducing external tajweed knowledge (prohibited) or finding a way to derive the distinction from context.

### 5.2 Unicode Encoding of Compound Diacritics

Shadda + vowel (e.g., shadda + fatha) may be encoded as two separate code points in varying order. Parsing logic must handle both orders consistently.

### 5.3 Normalization Prohibition

Do NOT apply any Unicode normalization (NFC, NFD, NFKC, NFKD). Analyze raw code points exactly as they appear. Normalization could silently merge or split characters.

### 5.4 Font-Dependent Variants

QPC V1, V2, and V4 texts are glyph-based — entire words encoded as single glyphs rendered by specific fonts. These are not character-level text. They cannot be used for letter-level analysis. The distinction between "standard Unicode" QPC Hafs and "glyph-based" QPC variants is critical and must be verified before using any QPC data.

---

## 6. Acceptance Criteria

The source text is accepted when:

1. All validation steps in §4 are completed and documented
2. All nine requirements in §1 are confirmed met
3. All embedded decisions in §5 are documented
4. The character inventory is committed to version control as the definitive token reference
5. Any discrepancies from cross-validation are resolved or documented as known limitations

Until all five criteria are met, no analytical code is written against the text.

---

## 7. Post-Acceptance Protocol

1. The exact file committed with SHA-256 hash
2. All code references the file by hash
3. No modification to the source file — all transformations produce new files
4. The character inventory serves as the definitive code-point-to-entity mapping
5. The validation report is a permanent companion document

---

## 8. What Could Still Go Wrong

- **The source text may contain errors we don't catch.** Spot-checks are samples.
- **Unicode may be an imperfect container.** The tanween problem is one instance. Other features of the physical mushaf may have no Unicode representation.
- **We are analyzing Unicode's encoding of the text, not the text itself.** This gap is irreducible but nameable.
- **Our parsing choices are analytical choices.** Tokenization, code point handling, "letter instance" definition — these shape everything downstream.
- **The QPC "standard Unicode" variant may have undocumented encoding choices.** The QPC ecosystem serves multiple font families and each may require text modifications. We must verify that the "standard Unicode" variant is truly font-independent.

The antidote is documentation. Every choice recorded. Every assumption named. Every risk acknowledged.

---

*Decision Document 001 in the project's decision record. Next: download the Tanzil Uthmani v1.1 text and execute the validation protocol, using QUL tools and QPC Hafs data for cross-validation.*

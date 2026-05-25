# The Weight of Letters — Claude Code Agent Setup

## Project Structure

```
weight-of-letters/
├── CLAUDE.md                          # Already built — project instructions
├── docs/
│   ├── whitepaper.md                  # The Weight of Letters whitepaper
│   ├── methodology.md                 # Full technical methodology
│   ├── DD001_data_source.md           # Decision document: data source
│   └── VR001_validation_report.md     # Validation report
├── data/
│   ├── source/
│   │   └── quran-uthmani-tanzil.xml   # SHA-256 verified source (NEVER modified)
│   └── processed/                     # Parser outputs go here
├── src/
│   ├── parser/                        # Text ingestion and multi-layer extraction
│   ├── calibration/                   # Stage 0 tests
│   ├── analysis/                      # Cycle 1-3 analytical code
│   ├── semantic/                      # Phase 5 semantic direction extraction
│   └── final/                         # Surah-opening letter validation
├── tests/                             # Validation and unit tests
├── notebooks/                         # Exploration (human review)
├── outputs/                           # Generated atlases, matrices, reports
├── milestones/                        # Milestone completion markers
├── orchestrator.sh                    # Main loop runner
└── notify.sh                          # Notification script
```

## Step 1: Install and Authenticate Claude Code

```bash
# Install Claude Code (requires Node.js 18+)
npm install -g @anthropic-ai/claude-code

# Authenticate
claude login

# Verify
claude --version
```

## Step 2: Initialize the Project

```bash
mkdir -p weight-of-letters/{docs,data/{source,processed},src/{parser,calibration,analysis,semantic,final},tests,notebooks,outputs,milestones}
cd weight-of-letters
git init

# Copy in the documents we've built
# (copy CLAUDE.md, whitepaper, methodology, DD001, VR001 from Claude chat outputs)
# (copy the validated XML into data/source/)

# Verify source integrity
echo "bb2fe2b9e86b532228d7f74005080c1679c14aa2da6024fe30d29772f4f5b189  data/source/quran-uthmani-tanzil.xml" | sha256sum -c

git add .
git commit -m "Initial project setup with validated data source"
```

## Step 3: Create the Notification Script

```bash
cat > notify.sh << 'SCRIPT'
#!/bin/bash
# Notification dispatcher — customize for your setup
MILESTONE="$1"
MESSAGE="$2"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Log to file always
echo "[$TIMESTAMP] MILESTONE: $MILESTONE — $MESSAGE" >> milestones/log.txt

# macOS notification
if command -v osascript &> /dev/null; then
    osascript -e "display notification \"$MESSAGE\" with title \"Weight of Letters\" subtitle \"$MILESTONE\""
fi

# Terminal bell
echo -e "\a"

# Optional: Slack webhook (uncomment and set your webhook URL)
# SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
# curl -s -X POST -H 'Content-type: application/json' \
#   --data "{\"text\":\"🔔 *Weight of Letters* — $MILESTONE\n$MESSAGE\"}" \
#   "$SLACK_WEBHOOK"

# Optional: Email via sendmail (uncomment)
# echo "Subject: WoL Milestone: $MILESTONE
# $MESSAGE" | sendmail your@email.com
SCRIPT
chmod +x notify.sh
```

## Step 4: Create the Milestone Task File

This is what Claude Code reads. Each milestone is a self-contained task with clear entry criteria, exit criteria, and verification.

```bash
cat > MILESTONES.md << 'EOF'
# Weight of Letters — Milestone Definitions

## How This Works

The orchestrator runs Claude Code in headless mode for each milestone sequentially.
Each milestone produces:
1. Code in the appropriate src/ directory
2. Test files in tests/
3. A completion marker in milestones/ (a JSON file with results summary)
4. All tests passing

A milestone is COMPLETE when its marker file exists AND all its tests pass.
A milestone FAILS if tests fail after 3 retry attempts.

---

## M0: Source Verification Script
**Entry**: data/source/quran-uthmani-tanzil.xml exists
**Task**: Write src/parser/verify_source.py that reproduces the full character inventory from VR001. Run it. Output must match the validation report exactly.
**Exit**: tests/test_verify_source.py passes. milestones/M0.json written.
**Notify**: "Source verification complete. Character inventory confirmed."

## M1: Core Parser — Letter Extraction
**Entry**: M0 complete
**Task**: Write src/parser/extract_letters.py that parses the XML and produces a structured dataset where each row is one letter instance with:
- letter_char, letter_code (Unicode)
- variant_identity (which orthographic form)
- word_index, verse_index, surah_index, mushaf_position
- word_position (initial/medial/final), verse_position, surah_position
- preceding_letter, following_letter
**Exit**: tests/test_extract_letters.py passes (total count = 325,665; spot-checks on known verses). milestones/M1.json written.
**Notify**: "Letter extraction complete. 325,665 instances indexed."

## M2: Diacritical Stream Extraction
**Entry**: M1 complete
**Task**: Write src/parser/extract_diacritics.py that adds to each letter instance:
- diacritics (list of combining marks following this letter)
- primary_diacritic (fatha/kasra/damma/sukoon/shadda/tanween or bare)
- has_shadda (boolean)
- has_tanween (boolean)
- is_bare (boolean — no standard diacritic)
- diacritic_sequence (preceding and following diacritics for melody)
**Exit**: tests/test_extract_diacritics.py passes (ة never sukoon; counts match VR001). milestones/M2.json written.
**Notify**: "Diacritical extraction complete. Sonic layer raw data ready."

## M3: Shadda Decomposition
**Entry**: M2 complete
**Task**: Write src/parser/decompose_shadda.py that for every shadda instance:
- Creates visual_count (1) and sonic_count (2)
- Classifies as true_doubling or assimilation (contextual: after ال + sun letter = assimilation)
- Records shadow_source letter for assimilation cases
- Records shadow_diacritic_1 (sukoon) and shadow_diacritic_2 (the visible diacritic)
**Exit**: tests/test_shadda.py passes (total shadda = 23,016; assimilation classification spot-checked). milestones/M3.json written.
**Notify**: "Shadda decomposition complete. Shadow census ready."

## M4: Hamza Seat Tracking
**Entry**: M1 complete
**Task**: Write src/parser/track_hamza.py that for every hamza instance:
- Records seat (alif_above/alif_below/waw/ya_form/standalone)
- Records surrounding context
- Verifies counts against character inventory
**Exit**: tests/test_hamza.py passes. milestones/M4.json written.
**Notify**: "Hamza seat tracking complete."

## M5: Articulatory Zone Assignment
**Entry**: M1 complete
**Task**: Write src/parser/assign_makhraj.py that assigns each letter its makhraj zone (1-7) and subzone based on the 7-zone articulatory map from the methodology. This is a static lookup — each letter identity maps to a fixed zone. Handle variants: أ/إ → zone 2, bare ا → zone 1, etc.
**Exit**: tests/test_makhraj.py passes (zone assignments verified against methodology table). milestones/M5.json written.
**Notify**: "Articulatory zones assigned. Body geography mapped."

## M6: Geometric Family Assignment
**Entry**: M1 complete
**Task**: Write src/parser/assign_geometry.py that assigns each letter:
- geometric_family (cup/bowl/knee/curve/teeth/loop/cross/hook/circle/singleton)
- dot_count, dot_position
- is_non_connector
- shares_base_with (list)
Static lookup from methodology geometric family table.
**Exit**: tests/test_geometry.py passes. milestones/M6.json written.
**Notify**: "Geometric families assigned. Visual layer mapped."

## M7: Unified Multi-Layer Dataset
**Entry**: M1-M6 all complete
**Task**: Write src/parser/build_dataset.py that merges all parsed data into one unified dataset:
- Each row = one letter instance
- Columns span all four layers: sonic (makhraj + diacritics), geometric (family + dots), structural (position + variant), frequency (to be computed)
- Output as both CSV and Parquet
- Compute basic frequency features: per-letter global count, per-surah count, per-verse presence
**Exit**: tests/test_dataset.py passes (column completeness, row count, no nulls in required fields). milestones/M7.json written.
**Notify**: "🎯 MAJOR MILESTONE: Unified multi-layer dataset built. The text is computable."

## M8: Calibration — PMI and Embedding Infrastructure
**Entry**: M7 complete
**Task**: Write src/calibration/pmi.py (PMI computation) and src/calibration/embeddings.py (character-level transformer training on Quran text only — NO pre-training). These are the tools Stage 0 tests depend on.
**Exit**: tests/test_pmi.py and tests/test_embeddings.py pass. milestones/M8.json written.
**Notify**: "Calibration infrastructure built. Ready for Stage 0."

## M9: Stage 0 — Calibration Tests 0A-0Q
**Entry**: M8 complete
**Task**: Write src/calibration/stage0.py that runs all 17 calibration tests from the methodology. Each test produces a pass/fail with evidence. If any test fails, diagnose and fix the underlying issue (in the parser, embeddings, or PMI), then re-run.
**Exit**: All 17 tests pass. milestones/M9.json written with full results.
**Notify**: "🎯 MAJOR MILESTONE: Stage 0 calibration PASSED. All 17 tests green. Pipeline validated against known ground truth. Ready for Cycle 1."

EOF
```

## Step 5: Create the Orchestrator

```bash
cat > orchestrator.sh << 'SCRIPT'
#!/bin/bash
set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

MILESTONES=(M0 M1 M2 M3 M4 M5 M6 M7 M8 M9)
MAX_RETRIES=3

run_milestone() {
    local milestone=$1
    local attempt=1
    
    # Check if already complete
    if [ -f "milestones/${milestone}.json" ]; then
        echo "[$milestone] Already complete. Skipping."
        return 0
    fi
    
    while [ $attempt -le $MAX_RETRIES ]; do
        echo ""
        echo "=========================================="
        echo "[$milestone] Attempt $attempt of $MAX_RETRIES"
        echo "$(date '+%Y-%m-%d %H:%M:%S')"
        echo "=========================================="
        
        # Run Claude Code in headless mode
        claude --print \
            --prompt "Read MILESTONES.md. Execute milestone $milestone. Follow CLAUDE.md premises strictly. Write code, write tests, run tests. If tests pass, write milestones/${milestone}.json with results summary. If tests fail, diagnose and fix. Do not proceed to the next milestone." \
            --output-format json \
            --max-turns 50 \
            2>&1 | tee "milestones/${milestone}_attempt${attempt}.log"
        
        # Check if milestone marker was created
        if [ -f "milestones/${milestone}.json" ]; then
            # Run tests one final time to confirm
            if python3 -m pytest tests/ -k "test_${milestone,,}" --tb=short 2>&1; then
                echo "[$milestone] PASSED"
                
                # Extract notify message from MILESTONES.md
                NOTIFY_MSG=$(grep -A1 "## ${milestone}:" MILESTONES.md | grep "Notify:" | sed 's/.*Notify: "//' | sed 's/"$//')
                ./notify.sh "$milestone" "${NOTIFY_MSG:-Milestone $milestone complete}"
                
                git add .
                git commit -m "Complete $milestone" || true
                return 0
            else
                echo "[$milestone] Tests failed after agent claimed completion. Retrying."
                rm -f "milestones/${milestone}.json"
            fi
        fi
        
        attempt=$((attempt + 1))
    done
    
    echo "[$milestone] FAILED after $MAX_RETRIES attempts"
    ./notify.sh "$milestone" "FAILED after $MAX_RETRIES attempts. Human review needed."
    return 1
}

# Main loop
echo "Weight of Letters — Autonomous Pipeline"
echo "Started: $(date)"
echo ""

for milestone in "${MILESTONES[@]}"; do
    if ! run_milestone "$milestone"; then
        echo ""
        echo "Pipeline halted at $milestone. Review logs in milestones/"
        ./notify.sh "PIPELINE" "Halted at $milestone. Review needed."
        exit 1
    fi
done

echo ""
echo "=========================================="
echo "ALL MILESTONES COMPLETE"
echo "$(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
./notify.sh "COMPLETE" "All milestones through Stage 0 complete. Dataset built and calibrated. Ready for Cycle 1 exploration."
SCRIPT
chmod +x orchestrator.sh
```

## Step 6: Run

```bash
# First, do a dry run on M0 interactively to verify setup
claude --prompt "Read MILESTONES.md. Execute milestone M0 only."

# Once satisfied, run the full loop
nohup ./orchestrator.sh > pipeline.log 2>&1 &

# Monitor
tail -f pipeline.log

# Or check milestone status
ls -la milestones/*.json
cat milestones/log.txt
```

## Key Design Decisions

### Why sequential milestones, not parallel?
Each milestone's output is the next milestone's input. M2 (diacritics) needs M1 (letters). M7 (unified dataset) needs M1-M6. The dependency chain is linear through M7, then Stage 0 depends on M7+M8. No safe parallelism exists except M4/M5/M6 which can run after M1 independently — but the simplicity of sequential execution outweighs the speed gain.

### Why --max-turns 50?
Each milestone involves: read instructions, write code, write tests, run tests, possibly debug. 50 turns gives generous room without runaway sessions. If 50 turns isn't enough for a milestone, the task definition is probably too large and should be split.

### Why git commit per milestone?
State lives in the repo, not the context window. If a session crashes, the next attempt starts from the last committed state. Claude Code reads git history for context.

### Why re-run tests outside the agent?
Trust but verify. The agent may claim tests pass when they don't (hallucinated test results). The orchestrator runs pytest independently after the agent finishes. Only an external pass counts.

### Retry logic
Three attempts per milestone. If the agent fails three times, a human looks at it. This prevents infinite loops on genuinely hard problems while allowing self-correction on transient issues.

## Monitoring

```bash
# Live progress
watch -n 30 'echo "=== Milestones ==="; ls milestones/*.json 2>/dev/null; echo ""; echo "=== Latest Log ==="; tail -5 milestones/log.txt 2>/dev/null'

# Cost tracking (from Claude Code JSON output)
cat milestones/*_attempt*.log | grep '"cost"' | python3 -c "
import sys, json
total = 0
for line in sys.stdin:
    try:
        data = json.loads(line.strip())
        total += data.get('cost', 0)
    except: pass
print(f'Total cost so far: \${total:.2f}')
"
```

## What Happens After M9

Stage 0 is the gate. Once all 17 calibration tests pass, the pipeline has proven it can detect known signal. Everything after that — Cycles 1-3, semantic direction extraction, the final surah-opening letter validation — follows the same orchestrator pattern with new milestones added to MILESTONES.md.

But those milestones require human judgment at cycle boundaries (which tracks show strongest signal? what to pre-register?). The orchestrator pauses at those decision points and notifies you. Full autonomy stops where scientific judgment begins.

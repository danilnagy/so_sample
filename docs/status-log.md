# Research status log

The chronological record of the reverse-engineering work, moved here from the README
when the research phase closed on 2026-10-11. Newest entries are at the end. For the
consolidated results see the [format reference](format-reference.md) and the
[FX reference](fx-reference.md).

---

# PO-33 Desktop Editor / Backup Format Reverse Engineering

## Overview

This project explores the Teenage Engineering PO-33 K.O! backup/restore format with the long-term goal of building a desktop application capable of reading, editing, creating, and transferring complete PO-33 projects.

The PO-33 does not provide USB data transfer or an official desktop editor. Instead, complete device backups are transmitted through the 3.5 mm audio connection as an encoded stereo audio signal.

These backups contain substantially more than ordinary recorded audio. They preserve the state of the PO-33, including:

- Sample data
- Melodic sample slots
- Drum sample slots and slices
- Patterns
- Sequencer events
- Sound assignments
- Sample parameters
- Pattern parameters
- Potentially tempo, swing, effects, and other global state

The central idea of this project is to reverse engineer this encoded backup format and eventually provide a workflow like:

```text
PO-33
  ↓
record backup audio
  ↓
decode transfer
  ↓
desktop project
  ↓
edit samples / patterns / settings
  ↓
encode transfer
  ↓
audio output
  ↓
PO-33
```

The immediate goal is not to build the graphical editor.

The first goal is to understand the transfer and binary formats well enough that controlled modifications can be made to a PO-33 backup and successfully restored to the hardware.


# Project Goals

## Primary Goal

Create a bidirectional desktop representation of a PO-33 project.

Eventually:

```text
PO-33 backup WAV
        ↓
      Decode
        ↓
PO-33 project representation
        ↓
      Modify
        ↓
      Encode
        ↓
PO-33 restore WAV
```

The desktop project should ultimately expose information in a human-readable form rather than treating the backup as an opaque binary file.


## Long-Term Capabilities

The final application could provide:

### Sample Management

- Import WAV files
- Assign samples to sound slots 1-16
- Replace existing samples
- Export PO-33 samples
- Preview samples
- Trim samples
- Normalize samples
- Convert audio into the PO-33's internal format
- Configure melodic and drum sample behavior
- Edit drum slice boundaries
- Display total sample memory usage


### Pattern Editing

Provide a graphical 16-step sequencer representing PO-33 patterns.

For example:

```text
Pattern 1

        01 02 03 04 05 06 07 08 09 10 11 12 13 14 15 16

Kick    ●  ·  ·  ·  ●  ·  ·  ·  ●  ·  ·  ·  ●  ·  ·  ·
Snare   ·  ·  ·  ·  ●  ·  ·  ·  ·  ·  ·  ·  ●  ·  ·  ·
Hat     ●  ·  ●  ·  ●  ·  ●  ·  ●  ·  ●  ·  ●  ·  ●  ·
```

Potential pattern properties include:

- Trigger position
- Sound number
- Pitch
- Volume
- Filter settings
- Effects
- Parameter locks
- Automation
- Pattern chaining
- Pattern length
- Tempo
- Swing


### Project Management

Possible project format:

```text
project/
│
├── project.json
│
├── samples/
│   ├── 01.wav
│   ├── 02.wav
│   ├── 03.wav
│   └── ...
│
├── sounds.json
│
├── patterns/
│   ├── 01.json
│   ├── 02.json
│   └── ...
│
└── source/
    ├── backup.wav
    └── backup.bin
```

This format is only conceptual at this stage and should evolve as the PO-33 data structure becomes better understood.


# Current Understanding of the PO-33 Transfer

Existing reverse-engineering work suggests that the PO-33's backup system behaves somewhat like an audio modem.

The backup operation can conceptually be divided into two separate problems:

```text
PO-33 STATE
     ↓
binary representation
     ↓
audio modulation
     ↓
stereo audio file
```

Restore performs the reverse:

```text
stereo audio
     ↓
demodulation
     ↓
binary representation
     ↓
PO-33 STATE
```

This separation is important.

The project should treat these as two independent layers:

1. Transfer / modem layer
2. PO-33 data format layer


# Layer 1: Transfer / Modem Protocol

Existing reverse-engineering work has already made substantial progress on the physical/audio transfer layer.

The transfer appears to use:

- Stereo audio
- Phase-modulated digital data
- Approximately 7.8 kHz symbol rate
- Multiple phase states
- Both audio channels carrying data

Existing open-source experiments have demonstrated decoding PO-33 transfer WAV files into binary data and reconstructing compatible transfer audio from binary data.

The first milestone for this project is therefore NOT to redesign the modem protocol.

Instead, existing work should be studied, reproduced, tested, and incorporated into a clean implementation.


# Layer 2: PO-33 Binary Format

This is expected to be the main reverse-engineering challenge.

The decoded transfer contains information representing the PO-33's internal state.

The exact structure is not yet fully understood.

Likely information includes:

```text
HEADER

GLOBAL SETTINGS

SOUND METADATA
    sound 1
    sound 2
    ...
    sound 16

PATTERN DATA
    pattern 1
    pattern 2
    ...
    pattern 16

SAMPLE DATA

CHECKSUM / VALIDATION DATA
```

The real structure may differ significantly from this.

One important goal of the project is to avoid assuming a structure before experimental evidence supports it.


# Sample Representation

Previous reverse-engineering indicates that PO-33 sample audio is likely represented internally using approximately:

```text
23,437.5 Hz sample rate
8-bit µ-law encoded audio
```

This needs to be independently verified.

If correct, desktop WAV samples could eventually be converted using:

```text
source WAV
    ↓
mono conversion
    ↓
resample to PO-33 sample rate
    ↓
µ-law encoding
    ↓
PO-33 sample data
```

The reverse operation would allow samples extracted from a PO-33 backup to be converted back into conventional PCM WAV files.


# Reverse Engineering Strategy

The primary technique used by this project should be controlled differential analysis.

Instead of trying to understand an entire backup at once, create multiple PO-33 backups where exactly one known property changes.

Then compare the decoded binary payloads.


# Baseline Experiment

Create the simplest possible known PO-33 state.

For example:

```text
BASELINE A

Factory reset or controlled empty state
No patterns programmed
Known sample configuration
Known tempo
Known global settings
```

Create a backup:

```text
A.wav
```

Decode it:

```text
A.bin
```


# Single-Variable Experiments

Modify exactly one parameter. The first such experiment's plan is
[first pattern event](first-event-experiment.md).

Example:

```text
BASELINE

Pattern 1
Step 1 = empty
```

Change to:

```text
EXPERIMENT B

Pattern 1
Step 1 = Sound 9
```

Create:

```text
B.wav
B.bin
```

Compare:

```text
A.bin
vs
B.bin
```

Useful comparisons include:

```text
A XOR B
```

and byte-by-byte difference maps.


# Experimental Rules

For useful differential analysis:

1. Change only one parameter per experiment whenever possible.
2. Preserve every unrelated PO-33 setting.
3. Record the exact actions used to create each state.
4. Save both the original WAV and decoded binary payload.
5. Never overwrite experiments.
6. Keep experiments reproducible.
7. Give experiments machine-readable IDs.
8. Generate automated binary comparisons.


# Suggested Experiment Dataset

The first experiment series should focus on sequencing because step changes are easy to control.


## Pattern Position Experiments

Create backups containing one identical trigger at different positions.

```text
EXP-POS-01
Pattern 1
Step 1
Sound 9

EXP-POS-02
Pattern 1
Step 2
Sound 9

EXP-POS-03
Pattern 1
Step 3
Sound 9

...

EXP-POS-16
Pattern 1
Step 16
Sound 9
```

Look for repeating or shifting binary structures.


## Sound Number Experiments

Keep position constant and change sound.

```text
EXP-SOUND-01
Pattern 1
Step 1
Sound 1

EXP-SOUND-02
Pattern 1
Step 1
Sound 2

...

EXP-SOUND-16
Pattern 1
Step 1
Sound 16
```

This may reveal the bit field used for sound selection.


## Pattern Number Experiments

Keep the event identical while changing patterns.

```text
Pattern 1 → one trigger
Pattern 2 → one trigger
Pattern 3 → one trigger
...
```

This may reveal:

- Pattern boundaries
- Fixed pattern sizes
- Pattern indexes
- Address calculations


## Parameter Experiments

Once basic trigger encoding is identified, investigate:

```text
Pitch
Volume
Filter
FX
Swing
Tempo
Step parameter locks
Pattern length
```

Only one variable should change per experiment.


# Sample Experiments

Samples should be investigated separately from pattern data.

Use highly controlled synthetic audio rather than music.

Useful signals include:

### Silence

```text
0 0 0 0 0 0 0 0 ...
```


### Impulse

```text
0 0 0 MAX 0 0 0 ...
```


### Constant Value

```text
X X X X X X X X ...
```


### Ramp

```text
0 1 2 3 4 5 6 7 ...
```


### Alternating Values

```text
MIN MAX MIN MAX MIN MAX ...
```

These signals should make sample encoding significantly easier to identify than arbitrary audio.


# Potential Encoding Complications

Decoded PO-33 backups may not contain immediately recognizable structures.

Possible reasons include:

- XOR scrambling
- Stateful scrambling
- Interleaving
- Differential encoding
- Compression
- Checksums
- Error correction
- Channel interleaving
- Memory paging
- Byte transformations
- Data whitening

High entropy does not necessarily mean encryption.

A simple scrambling or whitening stage can make structured data appear random.

Before assuming compression or encryption, test simple reversible transformations.


# Differential Analysis Tools

The project should eventually provide command-line tools such as:

```text
po33 decode backup.wav backup.bin

po33 encode backup.bin backup.wav

po33 compare A.bin B.bin

po33 diff A.bin B.bin

po33 inspect backup.bin
```

Possible future commands:

```text
po33 extract-samples backup.bin ./samples/

po33 extract-patterns backup.bin patterns.json

po33 replace-sample backup.bin 9 kick.wav

po33 export project.po33 backup.wav
```


# Suggested Repository Structure

Initial repository:

```text
po33-re/
│
├── README.md
│
├── docs/
│   ├── transfer-format.md
│   ├── binary-format.md
│   ├── sample-format.md
│   ├── pattern-format.md
│   └── experiments.md
│
├── src/
│   ├── decoder/
│   ├── encoder/
│   ├── analysis/
│   ├── formats/
│   └── cli/
│
├── experiments/
│   ├── baseline/
│   ├── patterns/
│   ├── sounds/
│   ├── parameters/
│   └── samples/
│
├── scripts/
│
├── tests/
│
└── tools/
```

Raw PO-33 backups may become large, so experiment audio files may eventually need to be excluded from Git and stored separately.


# Recommended Technology Stack

The initial reverse-engineering tools should prioritize speed of experimentation over application architecture.

A practical starting point is:

```text
Python
NumPy
SciPy
wave / soundfile
matplotlib
```

Python is useful for:

- Signal analysis
- Binary analysis
- WAV processing
- Visualization
- Statistical analysis
- Rapid experimentation

Once the format is understood, the desktop application can use a different stack.


## Possible Desktop Application

A later GUI could use:

```text
React
TypeScript
Vite
Electron
```

or:

```text
React
TypeScript
Tauri
```

The low-level decoder could either remain Python or eventually be ported to TypeScript, Rust, C++, or another implementation language.

Do not prioritize this decision during the reverse-engineering phase.


# Visual Studio / VS Code Development

The repository should initially be usable primarily through scripts and command-line commands.

Recommended workflow:

```text
repository
   ↓
Python virtual environment
   ↓
scripts / CLI
   ↓
experimental files
   ↓
automated reports
```

The project should make it very easy to run a new experiment and compare it against a baseline.


# Experiment Metadata

Every experiment should have metadata describing exactly how it was produced.

Example:

```json
{
  "id": "pattern-01-step-01-sound-09",
  "description": "Single Sound 9 trigger on step 1 of pattern 1",
  "baseline": "baseline-001",
  "changes": {
    "pattern": 1,
    "step": 1,
    "sound": 9
  }
}
```

This will become extremely valuable once dozens or hundreds of backups exist.


# Binary Difference Reports

The analysis tool should generate reports such as:

```text
Baseline:
baseline-001.bin

Experiment:
pattern-01-step-01-sound-09.bin

Total bytes:
XXXXXX

Different bytes:
XXX

Changed ranges:

0x00001230 - 0x00001234
0x00008210 - 0x0000821F
0x0003A422 - 0x0003A423
```

The tool should additionally support:

```text
XOR output
bit-level changes
changed-range grouping
entropy analysis
repeated sequence search
correlation between experiments
```

Eventually it may be useful to visualize the entire binary file as a heat map.


# Critical First Milestone

Before attempting to understand samples or patterns, establish a completely reliable round trip:

```text
PO-33
  ↓
backup WAV
  ↓
decoder
  ↓
binary
  ↓
encoder
  ↓
generated WAV
  ↓
PO-33
```

The reconstructed backup should load successfully into the PO-33.

The resulting device should behave identically to the original state.

Until this works reliably, higher-level format analysis should remain secondary.


# Milestone 1: Reproduce Existing Decoder

Tasks:

- Study existing PO-33 reverse-engineering implementations
- Collect several genuine PO-33 backup recordings
- Decode them
- Verify deterministic decoding
- Document synchronization and framing
- Document stereo-channel behavior
- Document symbol encoding
- Add automated decoder tests


# Milestone 2: Reproduce Existing Encoder

Tasks:

- Convert decoded binary back into transfer audio
- Restore generated transfers to the PO-33
- Compare restored state against original
- Determine acceptable audio levels
- Determine required sample rate
- Determine synchronization requirements
- Document transfer reliability


# Milestone 3: Build Binary Analysis Framework

Implement:

```text
compare
xor
bitdiff
entropy
changed ranges
hex dump
pattern search
statistics
```

Do this before attempting manual binary interpretation.


# Milestone 4: Establish Controlled Baseline

Create a documented baseline PO-33 state.

Produce:

```text
baseline.wav
baseline.bin
baseline.json
```

Repeat the same backup several times without intentionally changing anything.

This is extremely important.

If two backups of an apparently identical state produce different binary payloads, determine why before interpreting individual bytes.

Possible causes include:

- Counters
- Randomized whitening
- State-dependent encoding
- Timing differences
- Hidden device state
- Checksums
- Uninitialized memory


# Milestone 5: Map Pattern Storage

Start with:

```text
one trigger
one sound
one pattern
```

Determine:

- Pattern boundaries
- Step boundaries
- Sound identifiers
- Trigger representation
- Empty step representation

Then incrementally investigate additional sequencer properties.


# Milestone 6: Locate Sample Storage

Use known synthetic sample data.

Determine:

- Location of sample payload
- Audio encoding
- Sample length representation
- Slot boundaries
- Sample allocation method
- Trim metadata
- Drum slicing metadata


# Milestone 7: Modify a Backup

This is the first major proof of true format understanding.

Start with the smallest possible modification.

For example:

```text
Existing valid backup

Pattern 1:
Step 1 = empty

        ↓

Modify decoded data

        ↓

Pattern 1:
Step 1 = Sound 9
```

Re-encode the transfer and restore it to the PO-33.

If the new step appears correctly, the project has demonstrated arbitrary state modification rather than simple backup round-tripping.


# Milestone 8: Replace One Sample

Take an existing backup and replace one sample while preserving everything else.

Target workflow:

```text
kick.wav
   ↓
resample
   ↓
PO-33 encoding
   ↓
insert into backup
   ↓
recalculate metadata/checksums
   ↓
encode transfer
   ↓
PO-33
```

This is likely the most important milestone toward a usable desktop sample manager.


# Milestone 9: Define Internal Project Model

Once enough of the PO-33 format is understood, define a clean internal representation independent of the binary format.

For example:

```text
Project
 ├── globals
 ├── sounds[16]
 │    ├── sample
 │    ├── type
 │    ├── trim
 │    ├── pitch
 │    └── slices
 │
 └── patterns[16]
      └── steps[16]
           └── events[]
```

The desktop application should operate on this model.

Import/export code should translate between:

```text
PO-33 binary format
      ↕
internal project model
      ↕
desktop UI
```

This prevents undocumented hardware details from leaking throughout the application.


# Milestone 10: Desktop Editor

Only after the project model is stable should development move toward the graphical editor.

Possible initial UI:

```text
┌──────────────────────────────────────────────┐
│ PO-33 Project                                │
├──────────────────────────────────────────────┤
│                                              │
│ SOUNDS                                       │
│                                              │
│ 01 Piano       05 ----        09 Kick        │
│ 02 Rhodes      06 ----        10 Snare       │
│ 03 Strings     07 ----        11 Hat         │
│ 04 Bass        08 ----        12 Cymbal      │
│                                              │
├──────────────────────────────────────────────┤
│ Pattern 01                                   │
│                                              │
│      01 02 03 04 05 06 07 08 ... 16         │
│ 09   ●  ·  ·  ·  ●  ·  ·  ·      ·          │
│ 10   ·  ·  ·  ·  ●  ·  ·  ·      ·          │
│ 11   ●  ·  ●  ·  ●  ·  ●  ·      ·          │
│                                              │
├──────────────────────────────────────────────┤
│ [Import PO-33 Backup]    [Export to PO-33]   │
└──────────────────────────────────────────────┘
```


# Important Development Principle

Do not try to reverse engineer everything simultaneously.

The preferred progression is:

```text
TRANSFER
    ↓
BINARY
    ↓
DIFF TOOLS
    ↓
PATTERN TRIGGER
    ↓
PATTERN PARAMETERS
    ↓
SAMPLE DATA
    ↓
SAMPLE PARAMETERS
    ↓
PROJECT MODEL
    ↓
EDITOR
```

Every newly understood field should be backed by repeatable experiments.


# Documentation Rules

For every suspected field in the backup format, record:

```text
Offset / region
Length
Observed values
Experiment that identified it
Current interpretation
Confidence level
Open questions
```

Example:

```text
Offset:
0x012340

Length:
4 bits

Hypothesis:
Sound number for Pattern 1 / Step 1 / Voice 1

Evidence:
Changing Sound 1 → Sound 2 modifies these bits.

Confidence:
Medium

TODO:
Test sounds 1-16.
Test empty step.
Test same sound on other steps.
```


# Confidence Levels

Use explicit confidence labels:

```text
CONFIRMED
HIGH
MEDIUM
LOW
SPECULATIVE
```

This is important because reverse-engineering notes can easily turn guesses into apparent facts over time.


# Safety

PO-33 restore operations overwrite the device's existing samples and patterns.

Before running experimental transfers:

1. Create a known-good backup.
2. Verify that the backup can be restored.
3. Keep the backup unchanged.
4. Do not rely on an experimental encoder as the only copy of important PO-33 projects.

Malformed transfer files may fail to load.

Any experiments involving modified binary data should therefore be treated as destructive until proven otherwise.


# Immediate Next Steps

The first development session should focus only on establishing the toolchain.

## Step 1

Create the repository structure.

## Step 2

Set up a Python virtual environment and basic dependencies.

## Step 3

Collect and study existing PO-33 decoder/encoder implementations.

## Step 4

Record one known-good PO-33 backup as:

```text
experiments/baseline/baseline-001.wav
```

## Step 5

Decode it into:

```text
experiments/baseline/baseline-001.bin
```

## Step 6

Re-encode the binary data without modifying it:

```text
experiments/baseline/baseline-001-roundtrip.wav
```

## Step 7

Restore that generated WAV to the PO-33.

If successful, document the exact process.

## Step 8

Back up the unchanged device several more times.

Compare:

```text
baseline-001.bin
baseline-002.bin
baseline-003.bin
baseline-004.bin
```

Determine whether identical PO-33 states produce identical decoded binary data.

## Step 9

Implement the first binary comparison utility.

It should report:

```text
file size
number of different bytes
percentage changed
changed ranges
XOR result
```

## Step 10

Create the first controlled pattern experiment:

```text
Pattern 1
Step 1
Sound 9
```

Compare it against the baseline.

That comparison marks the beginning of the actual PO-33 format reverse engineering.


# First Success Criteria

The initial phase of the project will be considered successful when all of the following are possible:

```text
✓ Record PO-33 backup

✓ Decode WAV → binary

✓ Encode binary → WAV

✓ Restore reconstructed WAV to PO-33

✓ Compare two decoded backups automatically

✓ Produce controlled experimental backups

✓ Identify at least one binary structure corresponding
  to a known PO-33 state change
```

After that point, development can transition from investigating the transport protocol to systematically mapping the PO-33's internal project format.


# Ultimate Goal

The final goal is a workflow where the PO-33 behaves almost as if it had a USB project editor:

```text
                    PO-33 DESKTOP EDITOR

                  ┌──────────────────┐
 WAV samples ────►│                  │
                  │ Samples          │
 patterns ───────►│ Patterns         │
                  │ Parameters       │
 backup.wav ─────►│                  │
                  └────────┬─────────┘
                           │
                           ▼
                    encoded backup
                           │
                           ▼
                     audio cable
                           │
                           ▼
                         PO-33
```

And in the opposite direction:

```text
PO-33
  ↓
backup audio
  ↓
desktop application
  ↓
editable samples + patterns + settings
```

The PO-33's audio backup mechanism therefore becomes a bidirectional data interface rather than merely a backup system.


# Project Status

Current phase:

```text
Native state research / controlled editing
```

Immediate objective:

```text
Extend verified trim and fixed-size sample edits to controlled pattern editing.
```

Do not begin designing the full editor until this round trip is repeatable and tested.

## Implemented Session 1 tools

The Python 3.12 package now provides stereo PCM WAV inspection and strict binary comparison.
See [Session 1 usage](session-1.md) for commands and capture placement, and
[the upstream audit](upstream-audit.md) for pinned commits and limitations.
DEVELOPMENT.md is the implementation contract where conceptual examples above differ.
Session 2 adds experimental phase-symbol decoding and reversible channel exports; see
[transport notes](transport.md). Session 3 now adds experimental waveform encoding and
strict software roundtrip; see [reconstruction and manual test](reconstruction.md).

Session 1 validation initially passed 29 unit tests. A genuine recording is now registered
for inspection and decoder regression; current results are in the transport notes. No generated hardware restore
has been performed.


## Hardware milestone

The user reports that the corrected staggered-quadrature 44.1 kHz reconstruction
restores successfully to their PO-33. The first whole-phase blend candidate was rejected.
Specific artifact hashes and manual evidence are in [reconstruction notes](reconstruction.md).
Detailed musical checks and a post-restore backup comparison remain pending.

## Controlled hardware roundtrip validated

The user restored corrected candidate 002 and immediately backed up without intervening
state changes. The lower-level re-capture matches all 1,970,367 labels per channel and
their exact counts against baseline 002/003, with zero alignment or discarded labels.
See [controlled re-capture validation](../experiments/reconstructed-002/validation.md).
This is evidence for this local device/state/playback path; it does not verify arbitrary
state editing or every encoder input. The current recording level is suitable when using
the explicit 0.0063 threshold profile.

## Coding analysis tools

Experimental `analyze-coding` reports bounded recurrence, structural and clock probes.
It does not decode state data. See [coding investigation](coding-investigation.md)
for reproducible commands, the current limits and the focused populated-state repeat control.

## Native packet milestone

The toolkit now decodes CRC-whitened packets and re-encodes their bodies exactly across
24 registered-source captures. A controlled Sound3 trim field reproduces the recorded
minimum trim exactly. The user restored the generated short-tone edit successfully;
its post-test backup matches the complete target packet body, with all511 checksums
valid and unchanged sample bytes. See [packet decoding](packet-decoding.md)
and [the completed restore test](native-trim-restore-test.md).

A fixed-size sample replacement has also passed its separate hardware test:
[750Hz sample restore](native-sample-restore-test.md). The recapture matches the
generated body and every shared backing code exactly, with unchanged headers and511
valid checksums. Sample allocation, resizing and the full editor remain future work.

`inspect-patterns` exposes raw pattern regions. Existing controlled kick recordings now
verify step spacing and two exact native-body reconstructions, while one auxiliary-byte
difference remains unresolved. See [pattern results](native-pattern-results.md).
The [melodic note control](melodic-step1-control.md) is complete.
The latest full-suite run passed **416 tests**; Ruff lint and formatting checks also pass.

The melodic note capture now passes every registered check. Three primary bytes and one
auxiliary byte change at the Sound3 cell, with all samples preserved. `clone-step` copies
complete raw note rows to empty steps and reproduces the genuine joint kick backup exactly.
The user confirms the first [four-note pattern restore](native-pattern-restore-test.md)
and expected playback worked. Its after-playback recapture matches the complete target
native body, with all511 checksums valid and unchanged samples and other patterns.
Opaque step copying is now validated locally. The next control is
[one keyboard-key change at Step5](melodic-key2-control.md); note pitch/gate bitfields
and general pattern editing remain open.

The fixed-Step5 keyboard-key2 capture passes all preservation checks and both registered
field hypotheses: exactly one auxiliary byte changes F0→F1. A narrow `set-note-key`
writer now reproduces the genuine forward/inverse bodies, supporting only the calibrated
Sound3 keys1/2 and known source parameters. The next device test is the
[generated alternating-key pattern](native-note-key-restore-test.md), which changes
only Step13's key, now restored and recaptured exactly with user-confirmed alternating
pitches. The crossing decoder hit a timing slip in this recording; a separate
[measured-clock method](measured-clock-recovery.md) recovers the full frame and
matches all24 earlier corpus bodies, preserving the failed attempt. The next device
control [keyboard key16 at a fixed step](melodic-key16-control.md) now passes:
only the predicted auxiliary byte changes F1→FF. The next required capture is
[keyboard key7 at that same step](melodic-key7-control.md), an independent middle
value check, now passed with only the predicted FF→F6 byte change. The writer supports
the four directly calibrated Sound3 keys1/2/7/16, while rejecting other values. The next
device test, [the generated four-key phrase](native-four-keys-restore-test.md), is
now complete: the user confirms all four pitches matched, and the recapture equals
the entire generated frame with 511 valid checksums and unchanged unrelated state.
See [four-key results](native-four-keys-results.md). The next control adds
[Sound 2 alongside Sound 3 on Step 1](sound2-layer-control.md), testing another
sound cell and preservation of an existing note. Other keys, gate meanings and
broader note parameter edits remain open.

The Sound 2 addition now passes every preservation and cell-location check. Its
primary parameters differ from Sound 3's, rejecting the registered equality hypothesis;
its key 1 auxiliary value matches F0. See [Sound 2 results](sound2-layer-results.md).
The experimental `clone-sound-cell` writer copies this observed note intact into an
empty Sound 2 cell while preserving a calibrated Sound 3 neighbour. The
[next restore test](native-sound-cell-restore-test.md) adds Sound 2 at Step 9
without changing the four-note Sound 3 phrase. Software checks pass; this new
cell-copy operation is now hardware verified: the user confirms the light and playback
checks, and the recapture matches the entire generated frame with all 511 checksums valid.
See [cell-copy results](native-sound-cell-results.md).

The experimental `remove-sound-cell` command clears only observed Sound 2 cells while
preserving calibrated neighbours. It reproduces genuine inverse baseline bodies exactly.
The [next removal restore test](native-sound-cell-removal-test.md) removes Sound 2
at Step 1 while preserving Sound 3 there and Sound 2 at Step 9. Full software checks pass;
this generated removal is now hardware verified, with an exact whole-frame recapture and
user-confirmed light/playback checks. See [removal results](native-sound-cell-removal-results.md).

`export-project` now writes a [read-only project folder](project-export.md), retaining
the original capture, artifact and every native packet, with 16 pattern views and four
sample previews. The current export is `experiments/exported-project-001/project.json`.
Unknown data remains intact; JSON import and the graphical editor are future work.
The next [sample-start control](sound3-start-control.md) moves only Sound 3's TRIM
knob A to investigate nonzero-start metadata and the second trim field's semantics.

That start control passes all preservation checks. The first Sound 3 reference field
moves from 0 to 31393 and the second from 8000 to 65535, rejecting both registered
second-field predictions; the user still hears the tone. See [start results](sound3-start-results.md).
Nonzero-start interpretation remains disabled, and the new read-only export retains
that record raw with Sound 3 preview marked unsupported. The next
[minimum-length control](sound3-start-min-control.md) keeps the start fixed and
tests stored-length versus endpoint alternatives with only knob B changed.

That minimum control preserves the start and all unrelated data, but produces second31504,
rejecting both exact predictions79/31472. The user then confirms a very short click/burst,
supporting a local endpoint interpretation. See [minimum results](sound3-start-min-results.md).
`set-sound-end` now experimentally supports only Sound 3 at fixed start31393 within the
observed endpoint interval, reproducing both genuine endpoint bodies and inverses exactly.
A separate preview uses an explicit half-open selection policy. Other starts and general
minimum/inclusivity rules remain unsupported. The [next restore test](native-nonzero-trim-restore-test.md)
expands the window to 8000 codes with all samples and patterns preserved; hardware acceptance
of this generated edit remains pending.

That fixed-start edit now passes hardware verification: both tone checks are user confirmed,
and the recapture equals the entire generated target with all511 checksums valid. See
[window hardware results](native-nonzero-trim-results.md). Project export can explicitly
include the calibrated cropped preview with `--calibrated-windows`.

`apply-edits` now compiles [hash-bound JSON plans](edit-plans.md) through existing bounded
writers. Its replay generates a WAV byte-identical to the accepted window restore, with
source/plan snapshots, per-operation body traces and strict software checks. Unknown fields
stay preserved; arbitrary JSON import and the GUI remain future work. The next
[quarter-position start control](sound3-start-quarter-control.md) checks a second
start value before expanding the current fixed-start trim scope.

That second-start control now passes preservation, producing start11716/end11827.
The lower-start prediction passes; both endpoint predictions fail and remain retained.
See [second-start results](sound3-start-quarter-results.md). A separate experimental
candidate expands this window to8000 codes, with strict software roundtrips and an exact
whole-body inverse. The [next device test](native-quarter-window-restore-test.md)
must verify this second start; the public writer still retains its previous start31393 scope.

The user reports the second-start restore and both tone checks passed. Its first recapture
has widespread waveform errors and cannot validate a native frame with either decoder.
The failed recording and analyses remain preserved; a fresh backup recording is requested
in the [current test instructions](native-quarter-window-restore-test.md). Exact
native verification remains pending, and the public writer scope is unchanged.

The clean retry now verifies the second-start window exactly: all511 checksums pass,
and the complete state equals the target. See
[second-start hardware results](native-quarter-window-results.md). Bounded window
editing and opt-in previews support the two discrete measured starts with separate
local endpoint intervals. The window-position replay reproduces the accepted WAV byte
for byte. The current project export is `experiments/exported-two-start-window-001/project.json`.
The next [drum copy control](drum9-copy-control.md) copies Sound1 to empty Sound9
to investigate its slice records while preserving the existing samples and patterns.

That drum copy passes preservation with527 valid checksums, adding sixteen9-byte owner0
references and preserving all existing sample codes and patterns. The first-group-only
prediction fails. See [drum-copy results](drum9-copy-results.md). The corrected project
view groups all16 records under Sound9; the current export is
`experiments/exported-drum9-copy-001/project.json`. Individual keyboard order, drum previews
and drum writers remain unverified. The next [key1 minimum-trim control](drum9-key1-trim-min-control.md)
changes one slice to identify its selector and compare its minimum with the melodic controls.

That slice control now passes preservation: key1 changes selector8 alone, retaining
start0 and producing second127. The exact melodic-minimum79 prediction fails. See
[drum key1 results](drum9-key1-trim-min-results.md). An experimental endpoint writer
and edit-plan operation support only this slice within its observed context and local
127..4044 interval. The [first generated drum restore test](native-drum9-slice-end-restore-test.md)
sets endpoint2000 and passes all software checks; hardware acceptance is pending.
The current read-only export is `experiments/exported-drum9-key1-min-001/project.json`.

The first generated drum edit now passes its device test: the entire recapture matches
the target with527 valid checksums and user-confirmed short Sound9/key1 and unchanged
Sound8 tones. See [hardware results](native-drum9-slice-end-results.md).
`export-project --calibrated-drum-slices` explicitly adds only its calibrated raw-sample
preview. The current export is `experiments/exported-verified-drum9-slice-001/project.json`.
Other drum keys/slots and nonzero starts remain unverified. The next
[key2 minimum control](drum9-key2-trim-min-control.md) tests the adjacent reference,
preserving the accepted key1 window, and compares length/endpoint hypotheses.

That key2 control passes preservation and the exact endpoint4172 prediction at start4045;
the literal length127 alternative fails, and the user reports a click. See
[key2 results](drum9-key2-trim-min-results.md). The bounded writer supports the two
directly controlled slices at separate fixed starts and endpoint intervals, preserving
the remaining14 references. The [first key2 restore test](native-drum9-key2-end-restore-test.md)
sets endpoint6045, selecting2000 codes and preserving key1. Software checks pass; this
nonzero-start drum edit awaits hardware verification. The current export is
`experiments/exported-drum9-key2-min-001/project.json`, with only accepted key1 previewed.

The user reports the generated key2 restore and both Sound9 tone checks passed. The first
recapture has distributed waveform errors and fails both established decoders and higher
threshold attempts. Its WAV, artifact and diagnostics are archived; a fresh backup is
requested in the [current key2 test instructions](native-drum9-key2-end-restore-test.md).
Exact native verification and project key2 preview remain pending; no second restore is needed.

The clean updated recording now verifies the entire key2 target with527 valid checksums,
preserving key1 and all unrelated state. See
[key2 hardware results](native-drum9-key2-end-results.md). Explicit drum-preview
opt-in now includes both controlled Sound9 slices; the current export is
`experiments/exported-verified-drum9-slices-001/project.json`. The failed first recording
and analyses remain archived. The next [Sound10 copy control](drum10-copy-control.md)
tests a second inferred drum selector block while retaining both accepted Sound9 edits.

The first Sound10-copy recording has a late waveform discontinuity and cannot produce
a valid native frame with either established decoder. Waveform-only clock-window and
repeat-frame diagnostics also fail; all originals and attempts are preserved. The
[current Sound10 instructions](drum10-copy-control.md) request a fresh full backup
without repeating the copy. No Sound10 mapping or editor scope is promoted before validation.

The clean retry now verifies the Sound10 copy with543 valid checksums and all saved
predictions passing. Selector24..39 contains sixteen owner0 references matching the
original Sound9 autocopy, with both current Sound9 edits and all existing state intact.
See [Sound10 results](drum10-copy-results.md). The current read-only export is
`experiments/exported-drum10-copy-002/project.json`; Sound10's raw block is observed,
while its keys/writer/preview remain unverified. Identical preview audio now reuses
encoded bytes within an export to avoid timestamp differences between aliases. The next
[single-slice copy](cross-drum-slice-copy-control.md) targets Sound10/key1 from
the calibrated Sound9/key1 source.

The single-slice capture now verifies that Sound10/key1 maps to selector24 and receives
the exact Sound9/key1 reference. All543 packet checksums and all saved hypotheses pass;
every other plain packet remains identical. The reduced recording levels remain suitable.
See [cross-drum results](cross-drum-slice-copy-results.md). The current read-only
export is `experiments/exported-cross-drum-copy-002/project.json`, with Sound10/key1
mapped raw and the existing Sound9 previews retained.

A guarded `copy_drum_slice` plan operation now copies only existing Sound9/keys1 or2
into Sound10/key1, retaining the calibrated owner/buffer and literal neighboring records.
It reproduces both whole genuine control bodies and passes strict WAV roundtrips.
The new `experiments/generated-drum-slice-copy-001/restore.wav` copies the accepted
nonzero-start key2 reference, preserving all other state. Its
[restore and recapture test](native-cross-drum-slice-copy-restore-test.md) is the
next required device action; this candidate's hardware acceptance remains pending.

The generated nonzero-start copy now has an exact whole-target recapture with543 valid
checksums and user-confirmed restore/tone checks. All source slices and unrelated state
remain intact. See [hardware results](native-cross-drum-slice-copy-results.md).
Explicit drum-preview export now includes Sound10/key1 only at its two accepted copied
windows; its current nonzero preview equals the source Sound9/key2 preview byte for byte.
The current export is `experiments/exported-verified-cross-drum-copy-001/project.json`.
Software reports remain separate from hardware acceptance. The
[next drum-note control](drum10-note-control.md) adds Sound10/key1 at Pattern1/Step1
alongside the existing Sound3 note, preserving every sample/reference and other event.

The physical drum note now localizes Sound10 to the expected Pattern1 cell10 with543
valid checksums and all unrelated state preserved. Its observed pair is **0df883/10**:
primary matches Sound3, but the predicted melodic auxiliaryF0 fails. See
[drum-note results](drum10-note-results.md). The current read-only export is
`experiments/exported-drum10-note-001/project.json`, projecting slice1 only for the exact
observed pair and retaining all raw/source data and existing previews.

Guarded `clone_drum_cell`/`remove_drum_cell` plans now copy/clear only that opaque Sound10
note in Pattern1, with its accepted copied sample window and calibrated Sound2/Sound3
neighbors. Whole genuine bodies and inverses are reproduced in software. The first
`experiments/generated-drum-cell-copy-001/restore.wav` adds its Step1 note at Step9
alongside the two existing melodic notes. The
[restore and recapture test](native-drum-cell-copy-restore-test.md) is the next
required device action; generated drum-pattern hardware acceptance remains pending.

The generated drum-cell copy now has an exact full-target recapture with543 valid
checksums and user-confirmed grids/playback. Sound10/key1 is present at Steps1/9,
while all melodic notes, samples/references and unrelated state remain intact. See
[hardware results](native-drum-cell-copy-results.md). The current read-only export
is `experiments/exported-verified-drum-cell-copy-001/project.json`. Original software
reports and target registration remain unchanged; hardware acceptance is separate.
The [next key2 control](drum10-step9-key2-control.md) replaces only the Step9 drum
note, testing auxiliary11 againstF1 while retaining Step1/key1 and the full melodic
context. Other keys, general bitfields and Sound10/key2 sample-reference mapping remain
unverified; no key2 writer/projection is promoted before that control.

The physical key2 control now passes preservation with543 valid checksums. Only
Pattern1 auxiliary905 changes10 to11; primary0df883 and every other event/sample remain
unchanged. The exact drum-key prediction passes and melodicF1 fails. See
[key2 results](drum10-step9-key2-results.md). The current read-only export is
`experiments/exported-drum10-key2-note-001/project.json`, projecting only the two exact
observed recorded-key pairs. Sound10/key2 sample-reference mapping/preview and generated
key2 editing remain unsupported.

We now prioritize sample allocation over further small key calibrations. The
[next independent-sample control](sound4-allocation-control.md) records a distinct
half-second1000Hz tone into verified empty Sound4, retaining all existing data/patterns.
Its source file and capture folder are prepared. The checker measures actual record
size/ownership and reports any old-buffer/global bookkeeping changes independently;
no exact allocation size or resizing rule is assumed in advance.

The independent Sound4 recording now passes all registered hypotheses with679 valid
checksums. It adds a32768-code self-owned buffer under selector3, header0/28608/owner3;
the original65536-code owner0 buffer and every previous sound/pattern remain intact.
The extracted sample independently fits1000.033Hz. Capacity exceeds the endpoint and
its nonzero code tail remains preserved; no general allocation rule is inferred. See
[allocation results](sound4-allocation-results.md). The current read-only export is
`experiments/exported-second-owner-001/project.json`, including the new Sound4 preview.
The [next Sound4-to5 copy](sound4-to5-copy-control.md) creates a retained reference
before observing how re-recording Sound4 at a different length affects ownership and
the copied sound.

The Sound4-to5 physical copy now confirms sharing of owner3: Sound5 adds only the exact
nine-byte reference0/28608/owner3, with680 valid checksums and both sample buffers/all
prior state unchanged. Three fixed threshold profiles recover the same complete body;
the original failed acquisition and uploaded `po_33_61.wav` remain preserved. See
[copy results](sound4-to5-copy-results.md). The current read-only export is
`experiments/exported-second-owner-copy-001/project.json`, with identical Sound4/5 previews.
The [next shared-owner overwrite control](shared-sound4-rerecord-control.md) records
a longer distinct tone into Sound4 while retaining Sound5, exposing preservation versus
shared replacement and actual allocation changes. No allocator/resizing writer is
promoted before that evidence.

The shared-owner re-recording now passes with985 valid checksums. Sound4 gets a new
73728-code/end72128 buffer; the complete old32768-code sample transfers to Sound5/owner4
with every code and its used window preserved. Only selectors3/4 change; all previous
patterns and unrelated sounds stay intact. The decoded new/retained tones independently
fit1250.043/1000.033Hz. See [results](shared-sound4-rerecord-results.md). The current
read-only export is `experiments/exported-shared-owner-growth-001/project.json`.

This records shared-overwrite ownership transfer, not a general allocator implementation.
The73728 capacity also disproves a universal power-of-two capacity assumption. Ordered
data packets follow4096-code page splits in all current buffers; allocation rounding
is still unresolved. The [next unshared shrink control](unshared-sound4-shrink-control.md)
re-records Sound4 with a quarter-second tone to distinguish actual capacity reduction
from simply reducing the endpoint, while preserving independently owned Sound5.

The shorter unshared recording now passes with815 valid checksums. Sound4's capacity
shrinks73728 to32768 and endpoint72128 to30912; only selector3 changes. Sound5's full
buffer, all other sound records and all patterns remain identical. The extracted tone
fits1500.059Hz. See [shrink results](unshared-sound4-shrink-results.md). The current
read-only project is `experiments/exported-unshared-shrink-001/project.json`.

The [first generated growth test](sound4-generated-growth-control.md) is ready in
`experiments/edited-sound4-growth-001/restore.wav`. An isolated research script reuses
the previously observed73728-code Sound4 layout and inserts a new1750Hz tone lasting
about3.08seconds. Full software waveform/native checks pass; Sound5 and all unrelated
state remain preserved. Manual restore, audition and recapture are pending. General
allocation and public edit-plan resizing remain unsupported.

The generated growth is now accepted on hardware: all985 checksums pass and the entire
recaptured native body/packets match the synthesized target exactly. Sound4's73728-code
buffer, including every generated tone/tail code, survives restoration; Sound5 and
every other sound/pattern remain intact. The user confirms the audible checks. See
[growth results](sound4-generated-growth-results.md). The current read-only export
is `experiments/exported-generated-sound4-growth-001/project.json`.

The [generated shrink test](sound4-generated-shrink-control.md) is ready at
`experiments/edited-sound4-shrink-001/restore.wav`: it returns Sound4 to the observed
32768-code layout with a new2250Hz tone lasting about1.32seconds. The bounded research
helper and checker support both known directions;28 targeted tests and software
waveform checks pass. Manual shrink restore/recapture is pending. No general allocator
or public allocation edit is introduced.

The generated shrink is now hardware-accepted: all815 native checksums pass and the
entire recapture matches the synthesized target, including every2250Hz sample/tail
code. Sound5 and all other sounds/patterns remain unchanged, with audible checks
user-confirmed. Both known unshared Sound4 resize directions now have exact hardware
evidence. See [shrink results](sound4-generated-shrink-results.md). The current
read-only export is `experiments/exported-generated-sound4-shrink-001/project.json`.

The [empty Sound6 creation test](sound6-generated-creation-control.md) is ready in
`experiments/edited-sound6-create-001/restore.wav`. It inserts a32768-code self-owned
500Hz tone lasting about1.32seconds while preserving every existing sound/pattern.
The helper independently reconstructs the earlier physical empty-Sound4 recording;
software waveform checks and35 targeted tests pass. This new-slot test awaits hardware
restore/recapture. General allocation, deletion and shared-owner resizing remain unsupported.

Generated Sound6 creation is now hardware-accepted: all951 checksums pass and the entire
recapture matches the synthesized target, including every500Hz sample/tail code. Every
existing sound/pattern and opaque global packet remains intact; audible checks are
user-confirmed. See [creation results](sound6-generated-creation-results.md). The
current read-only export is `experiments/exported-generated-sound6-create-001/project.json`,
with seven melodic/three calibrated drum previews and32 verified content files.

The [generated Sound6-to7 copy test](sound6-to7-generated-copy-control.md) is ready
in `experiments/edited-sound6-to7-copy-001/restore.wav`. It adds only one9-byte owner5
reference under Sound7, keeping the full Sound6 buffer and all existing state exact.
Decoded previews match, and software waveform checks/30 targeted tests pass. The
helper independently reconstructs the earlier real Sound4-to5 copy. Hardware copy
acceptance is pending; this prepares a shared owner for later deletion investigation.

The generated Sound6-to7 copy is now hardware-accepted: all952 checksums pass and the
entire recapture matches the target. Sound7's exact nine-byte owner5 reference shares
the unchanged full Sound6 buffer; every other record/pattern is intact. Audible checks
are user-confirmed. See [copy results](sound6-to7-generated-copy-results.md). The
current read-only export is `experiments/exported-generated-sound6-to7-copy-001/project.json`,
with eight melodic/three drum previews, identical Sound6/7 WAVs and33 verified content files.

The next [physical shared-owner deletion control](shared-sound6-deletion-control.md)
deletes only Sound6 while retaining Sound7. Its preregistration and checker separately
evaluate full transfer to owner6, retained storage under owner5, used-window preservation
and unrelated-state preservation; unknown/lost-copy layouts are reported without guesses.
The model and26 targeted tests pass, and the capture folder is prepared. No deletion
writer is enabled before the device observation.

Deleting shared Sound6 now matches the complete transfer model with951 valid checksums:
Sound6 becomes empty, and Sound7 receives all32768 original codes under self-owner6,
including the identical used window and tail. Every other sound/pattern/plain packet
remains intact. See [deletion results](shared-sound6-deletion-results.md). The
current read-only export is `experiments/exported-shared-sound6-deletion-001/project.json`.
The user reported completion; specific audible checks were not separately confirmed.

The verified Sound6-to7 copy is now a bounded `copy_melodic_reference` edit-plan
operation. Its replay plan/compiler reproduces the previously accepted restore WAV
byte-for-byte, retaining existing guards and software-report provenance. See
[edit plans](edit-plans.md). The next [unshared Sound7 deletion](unshared-sound7-deletion-control.md)
tests serialized buffer removal; its predicted body independently equals the earlier
hardware-observed pre-creation state. Generated deletion remains unsupported.

Unshared Sound7 deletion now removes its whole32768-code record, leaving Sound6/7
empty and every unrelated sound/pattern intact. All815 checksums pass, and the entire
body exactly returns to the earlier pre-creation state. See
[deletion results](unshared-sound7-deletion-results.md). The current read-only export
is `experiments/exported-unshared-sound7-deletion-001/project.json`. Specific audible
checks were not separately confirmed by the user's completion report.

The two observed deletion contexts are now bounded `delete_melodic_sound` edit-plan
operations. A composed copy/transfer/removal plan matches every genuine intermediate
body and reproduces a previously accepted restore WAV byte-for-byte. Existing hashes,
event/layout/referrer guards and software-only compiler reports remain intact. See
[edit plans](edit-plans.md).

The next [nine-page Sound6 capacity test](sound6-nine-page-control.md) is ready at
`experiments/edited-sound6-nine-pages-001/restore.wav`. It appends one unused4096-code
page to the tested sample, keeping the logical tone/window unchanged. Exact36864,
rounded40960 and truncated32768 capacities are separate outcomes; physical allocation
units and general rounding remain unresolved. Public operation scopes are unchanged.

The nine-page Sound6 restore is now hardware-accepted: all968 native checksums pass,
capacity stays36864 and the complete recapture matches the target exactly. The original
sample/window and extra zero page survive; all other sounds/patterns remain intact,
with user-confirmed audible checks. See [results](sound6-nine-page-results.md).
The current read-only export is `experiments/exported-sound6-nine-pages-001/project.json`.
This establishes an odd-page serialized capacity, not physical allocation units or a
universal rounding rule. Public operation guards remain unchanged.

The [one-page ordinary-WAV import test](sound6-one-page-import-control.md) is ready
at `experiments/edited-sound6-one-page-import-001/restore.wav`. It reads a saved100ms
48k PCM tone, resamples/encodes it without normalization, and replaces Sound6 with a
4096-code buffer/end2344. Software waveform/code checks and24 targeted tests pass.
Hardware acceptance, smaller-capacity support and the new endpoint are pending; the
research importer does not enable unrestricted sample editing.

The one-page ordinary-WAV import is now hardware-accepted: all832 checksums pass,
capacity stays4096, endpoint stays2344 and the entire recapture matches the supplied
codes/body exactly. Every other sound/pattern remains intact, with audible checks
confirmed. See [results](sound6-one-page-import-results.md). The current read-only
export is `experiments/exported-one-page-sound6-import-001/project.json`.

The public [import-sample command](sample-import.md) now imports integer PCM mono
or selected stereo44.1/48k WAVs into calibrated empty/unshared Sound6, preserving
all other packets and rejecting unsupported sharing/layout/length/capacity contexts.
It chooses only verified buffer sizes within a conservative calibration budget.
Its replay reproduces the accepted100ms restore WAV byte-for-byte. Public copy/deletion
guards and read-only project JSON remain unchanged.

The [mono44.1k import test](sound6-mono-WAV-import-control.md) is prepared at
`experiments/edited-sound6-mono-WAV-import-001/restore.wav`: it replaces Sound6 with a
roughly0.75second rising pitch sweep using the new command. Software checks pass,
but this rate/channel/duration combination still awaits its hardware capture.

The mono 44.1 kHz WAV import is now hardware verified: all 951 native checksums pass,
and the complete recapture preserves the imported chirp, its exact 17,579-code endpoint,
the zero tail and every unrelated sample/pattern. Audible checks are confirmed.
See [results](sound6-mono-WAV-import-results.md). The current read-only export is
`experiments/exported-mono-WAV-sound6-import-001/project.json`.

The next [copy probe](imported-sound6-to7-copy-control.md) is ready at
`experiments/edited-imported-sound6-to7-copy-001/restore.wav`. It copies the imported
sample to Sound7 using one header reference, preserving every backing code. Software
roundtrip and 50 affected tests pass; public copy/deletion guards retain their previous
scope pending evidence for this imported endpoint.

The imported Sound6-to7 reference copy is now hardware verified: all 952 native
checksums pass, the complete target body matches, and every backing code and unrelated
packet is preserved. Audible checks are confirmed. See
[results](imported-sound6-to7-copy-results.md). The current read-only export is
`experiments/exported-imported-sound6-to7-copy-001/project.json`.

The public copy operation now includes the verified imported endpoint 17,579 alongside
30,912, retaining the Sound6-to-empty-Sound7, unshared, zero-start and 32,768-code guards.
Its compiled plan replays the accepted WAV byte-for-byte. The next
[physical deletion control](imported-shared-sound6-deletion-control.md) requires
no restore: delete only Sound6, leaving Sound7 intact, then capture before auditioning.
This checks full ownership transfer at the imported endpoint; public deletion scope
remains unchanged until suitable evidence is available.

Physical shared Sound6 deletion at the imported endpoint is now hardware verified:
all 951 checksums pass, Sound6 becomes empty, and Sound7 owns all 32,768 original codes
with endpoint 17,579 preserved. Every unrelated packet and pattern remains exact,
with audible checks confirmed. See [results](imported-shared-sound6-deletion-results.md).
The current read-only export is
`experiments/exported-imported-shared-sound6-deletion-001/project.json`.

The bounded shared-deletion operation now supports this verified endpoint; its compiled
plan and a composed copy/deletion plan reproduce the genuine native body. The next
[last-owner control](imported-unshared-sound7-deletion-control.md) needs no restore:
delete only Sound7, then capture before audition. Its prediction equals the entire
independently verified earlier state with both slots empty. Public Sound7 deletion
retains its earlier endpoint guard until the new control is observed.

The imported sample lifecycle is complete: final Sound7 deletion passes all 815 native
checksums and recovers the complete independently genuine earlier state with Sound6/7
empty. Every other sample/pattern remains exact, with user-confirmed audible checks.
See [results](imported-unshared-sound7-deletion-results.md). The current read-only
export is `experiments/exported-imported-last-owner-deletion-001/project.json`.

Both bounded deletion contexts now support the imported endpoint 17,579 alongside
30,912. The composed copy/transfer/removal plan replays the independently accepted
Sound4 shrink WAV byte-for-byte. Unsupported slots, capacities, referrers and pattern
contexts remain rejected. The next [tempo control](tempo-preset-control.md) uses
one short BPM button press and asks for the display values before and after. Tempo
storage and the preregistered direct-byte candidate remain unverified; no tempo writer
is enabled.

The first tempo control supports the preregistered byte: the user observed 120 to140,
and only offset129 in the second 7d5c payload changes120 to140. All 815 checksums pass;
every sample, pattern and unrelated byte remains exact. See
[results](tempo-120-to140-results.md). The current read-only export is
`experiments/exported-tempo-140-001/project.json`.

The next [two-capture series](tempo-preset-series-control.md) collects80 BPM and a
return to120. Both predictions are registered before collection; the return must equal
the whole independently genuine original120 body. Actual display readings remain
independent observations, and no tempo writer is enabled. All 21 tempo tests pass;
the preceding full regression suite had669 passes before these research-only additions.

The three-preset tempo series passes: the user confirmed 140 to80 and80 to120; each
capture changes only second7d5c payload byte129, preserving all samples/patterns.
Both pass815 checksums, and the120 return exactly equals the complete independent
original backup. See [results](tempo-preset-series-results.md). The current
read-only export is `experiments/exported-tempo-return120-001/project.json`.

The next [generated tempo restore](generated-tempo80-control.md) is ready at
`experiments/edited-tempo80-001/restore.wav`. It changes120 to80 and reproduces the
independently genuine80 native body exactly. Full waveform/body software checks and
all28 tempo tests pass. Device acceptance and an independent display80 reading remain
pending; no public tempo writer or arbitrary BPM range is enabled.

The generated tempo edit is hardware verified: the user confirmed the restored 80 BPM
display and checks, and all 815 checksums/full native body match the independent genuine
80 state. Every sample and pattern remains exact. See
[results](generated-tempo80-results.md). The current read-only export is
`experiments/exported-generated-tempo80-001/project.json`.

Bounded [tempo preset editing](tempo-preset-edits.md) is available through hash-bound
plans for 80, 120 and 140 in the recognized opaque global context. Its compiler replays
the accepted WAV byte-for-byte, while retaining software-only reports. Unknown global
settings, fine tempos and arbitrary values remain rejected. The next
[fine-tempo 100 control](fine-tempo100-control.md) needs no restore: adjust knob B
only while holding BPM, then capture before playback and report the actual display.

The physical fine-tempo 80-to-100 control matches its prediction: all 815 checksums
pass, only second7d5c payload byte129 changes, and every other global/sound-parameter,
sample and pattern byte remains exact. The user independently reported100. See
[results](fine-tempo100-results.md). The current read-only export is
`experiments/exported-fine-tempo100-001/project.json`.

The next [endpoint/return series](fine-tempo-range-series-control.md) requests60,
240 and a return to100 in three captures. The return must equal the complete independent
original100 backup. All43 affected tests pass. Public tempo editing remains restricted
to the three tested presets; range and generated fine-tempo acceptance are pending.

The fine-tempo endpoint series passes: the user independently confirmed60,240,100, and
all three815-checksum captures change only the same tempo byte. The100 return equals
the complete independent original100 body; all samples, patterns and other settings
remain exact. See [results](fine-tempo-range-series-results.md). The current
read-only export is `experiments/exported-fine-tempo-return100-001/project.json`.

The next [generated137 restore](generated-fine-tempo137-control.md) is ready at
`experiments/edited-fine-tempo137-001/restore.wav`. It probes a previously unobserved
fine value, retaining every unrelated byte. Full waveform/body software checks and
all37 affected tests pass. Public tempo scope stays the three presets until appropriate
fine-restore evidence arrives.

The generated 137 BPM restore is hardware verified: all 815 checksums and the complete
new target match, with the user confirming the requested display and checks. Every
sample, pattern and other global byte remains exact. See
[results](generated-fine-tempo137-results.md). The current read-only export is
`experiments/exported-generated-fine137-001/project.json`.

Guarded [integer tempo editing](tempo-edits.md) now supports 60 to 240 BPM within
the recognized opaque context. Physical endpoints, representative values and generated
80/137 restores ground this policy; not every integer has been individually hardware
tested. The compiler replays the accepted WAV byte-for-byte, and all 740 regression
tests pass. The original preset-only API stays compatible. The next
[swing maximum control](swing-max-control.md) needs no restore and keeps 137 BPM.

The maximum swing control supports the adjacent-byte lead: the user reportedS18,
and only second7d5c byte130 changes0 to18. All815 checksums pass, serialized137 BPM and
every other global/sound/sample/pattern byte remain exact. See
[results](swing-max18-results.md). The current read-only export is
`experiments/exported-swing-max18-001/project.json`.

The next [swing range series](swing-range-series-control.md) collects the unknown
minimum, displayed9 and an exactS18 return. Unsigned and signed-byte models are registered
before minimum data; no percentage/timing units or minimum number are assumed. All26
affected tests pass. No swing writer is enabled, and tempo editing retains its opaque
context guard, rejecting this changed swing state instead of resetting it.

The physical swing series now verifies S00/S09/S18 as byte values 0/9/18 at second
`0x7d5c` payload offset 130. All three captures pass 815 checksums, preserve tempo 137
and every unrelated byte, and exactly recover both independent endpoint bodies.
See [results](swing-range-results.md). The current genuine read-only export is
`experiments/exported-swing-range-return18-001/project.json`.

The [next timing pair](swing-timing-pair-control.md) adds the same offbeat high note
to two research targets that differ only in swing 0 versus 6. Both waveform round trips
and all 40 affected tests pass. First verify the straight restore, backup and ordinary
playback recording; the swing-6 restore waits for that evidence. Numeric timing units
remain unresolved, and no public swing writer is enabled.

The straight offbeat restore is now hardware verified: its entire backup matches the
generated target, the user hears the added note, and ordinary playback provides 14
clear cycles at the expected straight timing. The repeated component is near 500 Hz,
correcting the earlier high-note description. See
[results](swing-straight-control-results.md). Current genuine export:
`experiments/exported-swing-timing0-001/project.json`.

A fixed onset method is registered using straight data before the swing-6 recordings.
All 47 affected tests pass. The [next action](swing-timing-pair-control.md) restores
the already prepared swing-6 pair member and records its backup plus separate ordinary
playback. Positive generated swing and numeric timing units remain unverified.

Generated swing 6 is now hardware verified: the entire backup matches the target,
the user hears more swing, and all six frozen stereo timing comparisons show an
approximately 27 ms offbeat delay with the whole loop preserved. See
[results](generated-swing6-results.md). The current genuine read-only export is
`experiments/exported-swing-timing6-001/project.json`.

Guarded [swing editing](swing-edits.md) supports integer values 0 to 18 within the
recognized global context. Only tempo/swing bytes are masked; other unknown settings
still fail. Public plans replay both accepted timing WAVs byte-for-byte, and tempo
editing preserves a supported swing setting. All **790** regression tests pass.
Percent/clock units and individual hardware tests of every integer are not claimed.

The next [joint 100 BPM / swing 9 restore](joint-tempo-swing-control.md) is ready.
Only the two calibrated global bytes change; samples and patterns stay exact. This
new combination needs a physical restore, independent BPM reading and complete backup.

The joint 100 BPM / swing 9 restore is now hardware verified: the user confirms the
requested checks, all 815 checksums pass and the entire target matches. Every sample,
pattern and unrelated byte stays exact. Public setters reproduce the genuine joint
body in either order, and the inverse recovers the preceding 137/6 body. See
[results](joint-tempo-swing-results.md). Current genuine read-only export:
`experiments/exported-joint-tempo100-swing9-001/project.json`.

The next [Sound 3 live volume probe](sound3-volume-probe-control.md) first captures
selection alone, then minimum TONE volume. No location, numeric scale or serialized
effect is assumed; an unchanged backup remains meaningful. All 27 affected tests pass,
including actual joint hardware replay and independent selection/volume alternatives.
The previous full suite passed 790 tests; no production writer changes occur this turn.

The stopped Sound 3 volume probe produces **no serialized change**: both the fresh
selection capture and minimum-volume capture exactly match the prior project. The user
hears a quieter, non-silent sample, but supplies no numeric display value. This scopes
the result to live adjustment under the tested conditions; no volume field is located.
See [results](sound3-live-volume-results.md). Current genuine export:
`experiments/exported-sound3-live-volume-minimum-001/project.json`; raw sample previews
retain their unchanged codes and do not reproduce the quieter live gain.

The next [recorded TONE probe](sound3-tone-lock-probe-control.md) compares plain
playback with WRITE-held B movement. All differences, changed auxiliary bytes and
previously empty cells remain visible; no volume-specific bitfield or uniform maximum
is assumed. All 13 affected tests pass. Public volume editing remains disabled.

Recorded TONE now produces a stored change: plain playback leaves the body exact,
while the WRITE-held B pass changes 32 primary bytes across all 16 Sound 3 cells in
Pattern 1. The user hears louder sound. All auxiliary values, other sounds, samples,
global bytes and other patterns remain exact. See
[results](sound3-tone-lock-up-results.md). Current genuine read-only export:
`experiments/exported-sound3-tone-lock-maximum-001/project.json`.

The observed transformation sets high `0xc0` bits in the first primary byte and low
`0xf` nibbles in the second. These remain TONE-associated observations; volume-specific
semantics are unconfirmed. The next [minimum and exact maximum return](sound3-volume-lock-range-control.md)
tests a fixed low-nibble-zero prediction, preserving every other bit. All 14 affected
tests pass. No public volume writer is enabled.

The minimum clears the low nibble **and two adjacent first-byte bits**, so the
four-bit-only prediction is falsified and retained as failed. The complete louder
return exactly matches the independent earlier maximum. All samples, auxiliary values,
other sounds/patterns and globals remain unchanged. See
[results](sound3-volume-lock-range-results.md). Current genuine export:
`experiments/exported-sound3-volume-range-return-maximum-001/project.json`.

The next [quarter/halfway/maximum series](sound3-volume-middle-series-control.md)
declares a broader six-bit candidate, two value orderings and an enable-bit alternative
before interior data. Mechanical position bands remain auxiliary evidence; neither
interior bodies nor UI numbers are guessed. All 13 affected tests pass, and public
volume editing remains disabled.

The three interior captures preserve every bit outside the candidate masks and return
to the exact maximum. Quarter is uniform21 under both orderings; middle retains a
37–47 ramp under the contiguous interpretation and fails the registered uniform-middle
condition. The simple enable-pair alternative is refuted. The user confirms ascending
loudness. See [results](sound3-volume-middle-series-results.md). Current genuine export:
`experiments/exported-sound3-volume-middle-return-maximum-001/project.json`.

A [generated gain-ordering pair](generated-sound3-volume18-control.md) now replays
the genuine uniform21 reference and probes fixed18, interpreted as36 by the alternate
ordering. The two models predict opposite gain directions. Both waveform checks and
all15 affected tests pass; native reception and ordinary audio remain pending. First
verify the reference backup and playback. Public volume editing remains disabled.

The uniform21 reference replay is now hardware verified: the entire815-packet body
matches, the user confirms the lower-level sound, and all six frozen ordinary-audio
measurements pass. Recording levels remain suitable. All31 export content hashes and
full native reconstruction pass for the current genuine export:
`experiments/exported-sound3-volume21-reference-001/project.json`.
The [next action](generated-sound3-volume18-control.md) restores generated18 and
records its complete backup plus separate playback with unchanged knobs/audio settings.
Candidate reception, the competing gain directions and public volume editing remain
unverified.

Generated18 is now physically accepted with an exact complete recapture. All six
frozen ordinary-audio comparisons measure about18.1% lower repeated-tone amplitude
than reference21, with stable pitch and loop, supporting contiguous ordering. The
user's uncertain louder guess is retained without claiming subjective confirmation.
See [results](generated-sound3-volume18-results.md). Current genuine export:
`experiments/exported-sound3-volume18-001/project.json`, with all31 hashes and full
native reconstruction checked.

The [next upper-interior control](generated-sound3-volume36-control.md) uses
**`experiments/edited-sound3-volume36-002/restore.wav`**: contiguous36 versus alternate9
predicts opposite gain directions relative to21. Folder001 is retired after a test
caught incorrect alternate-code metadata, with failed evidence preserved. The active
waveform and all23 focused tests pass. Candidate36 hardware/audio and a public volume
writer remain pending; production editing code is unchanged.

The complementary generated 36 control is now accepted: complete recapture matches,
the user confirms pattern playback, and all six frozen comparisons measure about
2.20 times the reference tone amplitude with stable pitch and loop. Together with
the generated 18 decrease, this supports contiguous volume ordering in Sound 3 /
Pattern 1. See [results](generated-sound3-volume36-results.md). Current genuine
export: `experiments/exported-sound3-volume36-001/project.json`; all 31 hashes and
complete native reconstruction pass.

Guarded [uniform Sound 3 volume editing](sound3-volume-edits.md) now supports raw
integers 0..63 in the tested sample/note context. Whole physical endpoint/interior
bodies and both accepted WAVs replay exactly. Unknown nonvolume fields fail, and
per-step/other-sound volume edits remain unavailable. No gain law or mute/UI scale is
claimed. The next [post-playback backup](sound3-volume-post-playback-control.md)
checks persistence before a TONE pitch knob action.

All **853 regression tests pass** (52 focused volume/plan checks). The
[public workflow validation](../experiments/sound3-volume-public-plan-workflow-validation-001.json)
binds the accepted physical evidence, both byte-exact public WAV replays and the
next persistence capture registration. Software tests exercise all raw volume codes
for preservation; individual hardware calibration of all integers is not claimed.

The post-playback capture exactly matches the accepted volume 36 body and all 815
packets. All 16 volume values persist; recording levels remain suitable. See
[results](sound3-volume-post-playback-results.md). Current genuine export:
`experiments/exported-sound3-volume36-post-playback-001/project.json`, with all 31
content hashes and full-body reconstruction checked.

The next [recorded TONE A down control](sound3-tone-pitch-probe-control.md) probes
first-primary low-six bits while preserving broader TONE/auxiliary alternatives.
Only A moves, and changes in recorded volume remain explicit. No raw pitch endpoint,
uniformity or semitone scale is assumed. All 40 affected tests pass; production volume
guards are unchanged and the previous full suite passed 853 tests. Pitch recording
and a pitch-field writer remain pending.

Recorded TONE A down changes only the registered Sound 3 / Pattern 1 pitch-candidate
bits. All 16 candidate values become raw 1; volume remains 36 and every unrelated
byte stays exact. The user hears lower pitch and reports "Ptc" plus decreasing
ticks, without a numeric display reading. See
[results](sound3-tone-pitch-minimum-results.md). Current genuine export:
`experiments/exported-sound3-tone-pitch-minimum-001/project.json`; all 31 content
hashes and native reconstruction pass. Public volume guards remain unchanged.

The next [recorded maximum and minimum return](sound3-tone-pitch-range-control.md)
registers an unknown upper endpoint and exact return to the independent low-end body.
First-low-six and narrower low-five masks remain separate alternatives. All 45
affected tests pass; the last full suite passed 853. Pitch scale, complete field
width and a pitch-field writer remain unverified.

The recorded upper endpoint is raw 25 in all 16 cells, and the return exactly matches
the independent raw-1 minimum body. Only first-primary low-five bits change; volume
36 and all other state remain exact. The user hears pitch go up/down. See
[results](sound3-tone-pitch-range-results.md). Current genuine export:
`experiments/exported-sound3-tone-pitch-return-minimum-001/project.json`; all 31 hashes
and full native reconstruction pass. Field width, UI units and pitch law remain unknown.

A [generated 13/14 pair](generated-sound3-pitch-pair-control.md) now tests interior
pitch edits and a frequency-interval hypothesis. Both WAVs recover exact targets,
and all 40 affected checks pass with independent synthetic tones. The frequency
method is frozen before both recordings and uses one common search for both legs.
First restore and verify generated 13 with complete backup plus ordinary playback.
Production code is unchanged; no public pitch setter is enabled.

Generated pitch13 is now physically accepted with an exact entire target recapture.
All six frozen ordinary-frequency measurements pass near500.626 Hz and a2.4-second
loop; the user confirms hearing the pattern. Recording levels remain suitable.
Current genuine export: `experiments/exported-sound3-pitch13-reference-001/project.json`,
with all31 content hashes and native reconstruction checked. See
[next candidate14 action](generated-sound3-pitch-pair-control.md).
Candidate reception and the frequency/one-semitone hypothesis remain unverified.

Generated14 is now accepted with an exact complete recapture. All six frozen audio
comparisons measure approximately99.53 cents above reference13, supporting the
one-semitone hypothesis for this interval with stable loop timing. Volume36 and all
other state remain exact, and the user confirms playback. See
[results](generated-sound3-pitch-interval-results.md). Current genuine export:
`experiments/exported-sound3-pitch14-001/project.json`; all31 content hashes and
complete native reconstruction pass.

Guarded [uniform raw pitch editing](sound3-pitch-edits.md) supports integer
codes1..25 in the tested Sound3/Pattern1 layout at volume36, preserving bit5 and
every unrelated bit. Whole physical endpoint/interior bodies and both accepted WAVs
replay exactly. All **917 regression tests pass**. Full field width and an exact
all-code semitone law remain unknown. The next
[FILTER selection backup](sound3-filter-probe-control.md) keeps both knobs
untouched before a separately gated recorded A probe. All37 added FILTER/pitch
checks pass; no public filter writer is enabled.

FILTER selectionA now matches the entire accepted pitch14 body and all815 packets.
Pitch14, volume36 and every other byte remain exact after existing playback and
confirmed selection with knobs untouched. Recording levels remain suitable. Current
genuine export: `experiments/exported-sound3-filter-selection-001/project.json`, with
all31 content hashes and native reconstruction checked. The next
[recorded FILTER A pass](sound3-filter-probe-control.md) uses actualA under the
unchanged preregistered masks and retains broader TONE/auxiliary alternatives.
No filter endpoint, scale or writer is inferred from selection alone.

Recorded FILTER A clockwise changes only the strict registered candidate masks.
All16 contiguous projections are62 (alternate grouping59); pitch14, volume36 and
every other state bit remain exact. The user hears high-pass filtering until the
sample is inaudible and describes bar segments decreasing toward the right, without
a numeric UI reading. See [results](sound3-filter-A-clockwise-results.md).
Current genuine export: `experiments/exported-sound3-filter-A-clockwise-001/project.json`,
with all31 content hashes and full native reconstruction checked.

The next [opposite endpoint and exact clockwise return](sound3-filter-A-range-control.md)
registers an unknown counterclockwise code and a complete-body return prediction.
Both bit groupings and broader snapshot alternatives remain explicit. All50 affected
FILTER/pitch checks pass; production code is unchanged and the last full suite passed917.
Filter order, width, frequency law, resonance and a public filter writer remain unknown.

The opposite endpoint now has uniform contiguous 1 / alternate 4, and the clockwise
return exactly matches the independent earlier body and all packets at 62 / 59.
Pitch 14, volume 36 and every unrelated bit remain exact. The user confirms both
low-pass and high-pass extremes are inaudible; capture levels remain suitable. See
[results](sound3-filter-A-range-results.md). Current genuine export:
`experiments/exported-sound3-filter-A-return-clockwise-001/project.json`, with all
31 content hashes and complete native reconstruction checked.

The next [center and ordinary-playback control](sound3-filter-A-center-control.md)
leaves the interior code unknown, tests both scalar orderings separately and compares
the repeated tone with the pinned prior playback under the unchanged frequency method.
All 53 affected checks pass; production code is unchanged and the last full suite
passed 917. No filter writer, broadband bypass or resonance model is enabled.

The audible FILTER center now stores uniform **63** under both projections. Strict
scope, pitch 14 and volume 36 checks pass, but both registered numerical
between-endpoint hypotheses **fail**. All six frozen playback comparisons pass
within 3% of the prior repeated-tone amplitude, with stable pitch and timing. The
user hears the whole sample as though neither filter is applied and corrects the
center display cue to a **single middle tick**. See
[results](sound3-filter-A-center-results.md). Current genuine export:
`experiments/exported-sound3-filter-A-center-001/project.json`, with all 31 hashes
and complete native reconstruction checked.

New [interior controls](sound3-filter-A-interior-control.md) test partial
low-pass/high-pass settings under two branch-order hypotheses, followed by an
exact entire center return. These hypotheses are explicitly revised after center
data and registered before interior data. All 69 affected checks pass; production
code is unchanged. Special neutral encoding, broadband bypass, resonance and a
public filter writer remain unconfirmed.

The recorded interior controls store contiguous **16** for audible low-pass and
**52** for audible high-pass, with alternate projections 1 and 19. Both contiguous
branch-order predictions pass; both alternate predictions fail. The final **63**
return exactly matches the entire independent center body and every packet. Pitch
14, volume 36 and all unrelated state remain exact. See
[results](sound3-filter-A-interior-results.md). Current genuine export:
`experiments/exported-sound3-filter-A-interior-center-return-001/project.json`,
with all 31 hashes and complete native reconstruction checked.

The [generated fixed-16/52 pair](generated-sound3-filter-pair-control.md)
reproduces both independently recorded target bodies and every packet through WAV
roundtrip. Hardware acceptance remains pending; first restore and verify low-pass
16 before the high-pass leg. All 88 affected checks pass. Production code remains
unchanged; full field width, all-code filter law, resonance and a public filter
writer remain unconfirmed.

Generated FILTER16 is now physically accepted: the complete recapture and every
packet match its registered target and independent recorded low-pass body. Pitch
14, volume 36 and all unrelated state remain exact, and the user confirms audible
low-pass filtering. See [results](generated-sound3-filter16-results.md).
Current genuine export: `experiments/exported-sound3-generated-filter16-001/project.json`,
with all 31 hashes and complete native reconstruction checked. Recording levels
remain suitable. The next [generated high-pass52 restore](generated-sound3-filter-pair-control.md)
is now gated by the verified first leg; its hardware acceptance remains pending.
Production code and the existing 88-test focused / 917-test full validations are unchanged.

Generated FILTER52 now also recaptures its complete registered target and every
packet, with pitch14/volume36 and all unrelated state exact. The user confirms
high-pass filtering. See [pair results](generated-sound3-filter-pair-results.md).
Current genuine export: `experiments/exported-sound3-generated-filter52-001/project.json`,
with all31 hashes and complete native reconstruction checked.

A guarded [uniform FILTER operation](sound3-filter-edits.md) now supports only
observed raw codes1/16/52/62/63 in the tested Sound3/Pattern1 pitch14/volume36 layout.
Public plans replay both accepted16/52 WAVs byte-for-byte. All **1,025 regression
tests pass**; eight subsequent center-checker tests also pass. The next
[public-plan center63 restore](generated-sound3-filter-center-control.md)
predicts the entire independent center body before its recapture. All-code laws,
cutoffHz, resonance and broadband bypass remain unknown.

The public-plan center63 restore now recaptures the entire independent center body
and every packet, preserving pitch14/volume36 and all unrelated state. The user
confirms unfiltered playback. See [results](generated-sound3-filter63-results.md).
Current genuine export: `experiments/exported-sound3-generated-filter63-001/project.json`,
with all31 hashes and full native reconstruction checked. Established recording
levels remain suitable.

The next [recorded FILTER B probe](sound3-filter-B-probe-control.md) keeps A
at center and registers third-primary masks0x7c/0xfc separately, retaining bit7,
no change, ramps and coupled FILTER snapshots. No resonance endpoint or audible
change is predicted. All67 affected checks pass; production code is unchanged
since the full1,025-test run. Public observed-code filter guards stay unchanged.

Recorded FILTER B minimum changes only third-primary bit7 in the five Sound3 note
cells, leaving pitch14/volume36/cutoff63 and every other state bit exact. Both raw
projections now read0 throughout. The0xfc candidate passes; the0x7c mask fails and
its report remains retained. The user hears no audible change. See
[results](sound3-filter-B-minimum-results.md). Current genuine export:
`experiments/exported-sound3-filter-B-minimum-001/project.json`, with all31 hashes
and full native reconstruction checked. Recording levels remain suitable.

The next [unknown B maximum and exact minimum return](sound3-filter-B-range-control.md)
freezes the whole return-body prediction before both captures without guessing the
maximum code. All82 affected checks pass; production code is unchanged since the
full1,025-test run. Public cutoff guards reject the new B context rather than
overwrite unknown bits. Full resonance width, law and a writer remain unconfirmed.

B maximum now stores six-bit63 / narrow31 throughout; the return stores0 and matches
the entire independent minimum body and every packet. Only0xfc candidate bits
change, preserving pitch14/volume36/cutoff63 and every unrelated state bit. The
user reports no sound change and a resonance display adjustment. See
[results](sound3-filter-B-range-results.md). Current genuine export:
`experiments/exported-sound3-filter-B-return-minimum-001/project.json`, with all31
hashes and full native reconstruction checked.

The next [low-pass16 B0/B63 generated pair](generated-sound3-resonance-pair-control.md)
tests the new combined contexts and a frozen repeated-tone amplitude hypothesis.
Both WAVs recover their targets exactly in software; first verify B0 reference
reception and ordinary playback before B63. All108 affected checks pass; production
code remains unchanged since the full1,025-test run. Public cutoff guards still
reject the B layout; no general resonance law or public resonance writer is enabled.

The generated LPF16/B0 reference now recaptures its entire target and every packet,
preserving pitch14/volume36 and every non-FILTER bit. The user confirms filtered
playback. All six frozen audio measurements are usable near530.28Hz with stable
2.4002-second loops; the10.96-second recording passes unchanged coverage despite
being shorter than requested. See [results](generated-sound3-resonance-reference-results.md).
Current genuine export: `experiments/exported-sound3-filter16-B0-reference-001/project.json`,
with all31 hashes and full native reconstruction checked. The next
[unchanged generated B63 candidate](generated-sound3-resonance-pair-control.md)
will test exact reception and the preregistered amplitude increase. Production
code and the prior108 affected /1,025 full regression validations are unchanged.

Generated LPF16/B63 now recaptures its entire target and every packet, with all
non-B state equal to the accepted B0 reference. All six frozen comparisons show
about7.15 times the repeated-tone component amplitude, with stable frequency and
loop timing. The user reports more resonance or filter effect. See
[pair results](generated-sound3-resonance-pair-results.md). Current genuine
export: `experiments/exported-sound3-filter16-B63-candidate-001/project.json`, with
all31 hashes and full native reconstruction checked.

The next [raw32 interior test](generated-sound3-resonance-middle-control.md)
changes only B bits at the same cutoff and registers a two-sided amplitude hypothesis
against the already observed endpoint audio. Its WAV recovers the exact new target
in software; hardware acceptance remains pending. All110 affected checks pass;
production code remains unchanged since the full1,025-test run. General resonance
law, bit7 semantics and a public resonance writer remain unconfirmed.

Generated B32 now recaptures its complete target at cutoff16, preserving every
non-B state bit. All six frozen comparisons put its tone component between B0 and
B63, with ratios about6.47 above B0 and1.105 below B63. The user confirms the pattern
remains audible. See [results](generated-sound3-resonance-middle-results.md).
Current genuine export: `experiments/exported-sound3-filter16-B32-middle-001/project.json`,
with all31 hashes and full native reconstruction checked.

Guarded [uniform resonance plans](sound3-resonance-edits.md) now support only
observed codes0/32/63 in the tested cutoff16/pitch14/volume36 layout. All three accepted
WAVs replay byte-for-byte. All **1,137 regression tests pass**, followed by42 affected
FX/resonance checks with no later production changes. The next
[saved Pattern1 FX7 probe](pattern1-FX-probe-control.md) registers the eight-byte
footer as a location hypothesis, retaining broader alternatives and both nibble
orders without guessing a raw code. No public FX writer or complete resonance law
is enabled.

Recorded FX7 stores uniform footer6 and one additional global change at second
0x7d5c payload byte131,0 to9. The original footer-only hypothesis **fails** and its
report remains immutable. A post-observation two-field model reproduces the whole
body; every other state byte remains exact. The user confirms hearing an octave
higher. See [results](pattern1-FX7-results.md). Current genuine export:
`experiments/exported-pattern1-FX7-recorded-001/project.json`, with all31 hashes and
full native reconstruction checked.

The next [octave-down and clear controls](pattern1-FX8-clear-control.md) register
new footer/global low-four and whole-byte alternatives, unknown global values and
a return to original no-FX state except that explicit byte. Both nibble orders and
failed predictions remain separate. All56 affected checks pass; production code
is unchanged since the full1,137-test run. No public FX writer or global-byte role
is enabled.

Octave-down now passes the predicted footer7 and footer/global low-four scope,
with global byte131=1 and every other state byte exact. The user reports lower
octave then normal, but the two supplied WAVs are byte-identical copies of the first
recording. Clear remains unverified; its software comparison cannot adjudicate
the clearing model from duplicate input. See [results](pattern1-FX8-results.md).
Export at that stage: `experiments/exported-pattern1-FX8-recorded-001/project.json`,
with all31 hashes and full native reconstruction checked.

The [corrected clear capture](pattern1-FX16-corrected-clear-control.md) uses a
fresh folder and the unchanged earlier prediction. Original WAVs/reports remain
retained; known duplicate input is rejected without mistaking equal device state
for duplicate raw recordings. All34 affected checks pass. Production code is
unchanged since the full1,137-test run; global role, nibble order and a public FX
writer remain unconfirmed.

The corrected clear capture now passes the original FF-footer prediction and
returns every byte of the original no-FX state except global131, now7. Entire
original-body equality is false. The distinct capture and separate hardware
observation resolve the duplicated-input problem without changing old evidence.
Current genuine export:
`experiments/exported-pattern1-FX16-corrected-clear-001/project.json`, with all31
hashes and full native reconstruction checked. See
[completed correction](pattern1-FX16-corrected-clear-control.md).

The next [stopped-repeat and ordinary-playback control](pattern1-playback-global-control.md)
tests whether the opaque global byte can vary without saving an effect. Its
predictions are registered before data, with no new effect code or public writer.
All45 affected checks pass; production code remains unchanged since the full1,137
test run.

The user replaced dead batteries before the stopped-repeat/plain-playback pair.
Both distinct captures preserve the entire prior clear body exactly; global131
stays7 and effects stay cleared. This does not establish the global byte's role.
See [results](pattern1-plain-playback-results.md). Current genuine read-only
export: `experiments/exported-pattern1-plain-playback-001/project.json`, with all31
hashes and full native reconstruction checked.

The [generated octave-up restore](generated-pattern1-FX-up-control.md) changes
only Pattern1 footer bytes to66 and preserves global131=7, rather than reproducing
the earlier co-occurring global9. Exact native and waveform roundtrips pass;
hardware reception and listening are pending. All58 affected tests pass, with no
production change since the full1,137-test run and no public FX writer enabled.

The generated footer6/global7 restore now matches every native packet and the
entire target body; the user confirms hearing the octave effect. This verifies
the fixed footer-only restore while preserving global131=7. See
[results](generated-pattern1-FX-up-results.md) for the precise listening scope.
Current genuine export:
`experiments/exported-pattern1-generated-FX6-global7-up-001/project.json`, with all31
hashes and full native reconstruction checked.

The [generated octave-down/clear pair](generated-pattern1-FX-return-control.md)
tests raw footer7 thenF with global131 fixed at7. Both waveforms pass exact native
roundtrips; clear returns the entire independent baseline in software. Hardware
and listening checks are pending. All74 affected checks pass, production code
is unchanged since the full1,137-test run, and no public FX writer is enabled.

Generated octave-down and clear now match every packet and their entire targets.
The user explicitly confirms down then normal. Clear exactly returns the complete
independent global7 no-effect baseline. Current genuine export:
`experiments/exported-pattern1-generated-FX15-global7-clear-001/project.json`, with
all31 hashes and full native reconstruction checked. See
[results](generated-pattern1-FX-return-results.md).

Guarded [uniform effect plans](pattern1-effect-edits.md) now support `none`,
`octave_up` and `octave_down` in the exact tested Pattern1/global7 project. Each
accepted restore WAV replays byte-for-byte. Unknown project contexts, mixed
effects and arbitrary per-step codes remain rejected. All **1,246 regression
tests pass**, followed by72 focused checks with no later production changes.

The next [mixed-effect restore](generated-pattern1-FX-mixed-control.md) changes
only footer bytes, predicting higher then lower sections within a loop. Hardware
and listening are pending; adjacent-step nibble order and global131's role remain
unconfirmed.

The mixed-effect capture now matches the complete target, preserves global131=7
and all nonfooter state, and has user-confirmed first high then low playback.
See [results](generated-pattern1-FX-mixed-results.md). Current genuine export:
`experiments/exported-pattern1-FX6-7-halves-global7-001/project.json`, with all31
hashes and full native reconstruction checked. Public effect plans remain
uniform-only; this result does not distinguish adjacent-step nibble order.

The [complementary first-pair control](pattern1-FX-first-pair-control.md)
registers F6/6F targets and separate playback recordings, with both local nibble
orders and a frozen first-tone frequency comparison. Native and waveform checks
pass; hardware/audio are pending. All100 affected checks pass with no production
change since the full1,246-test run.

## Faster hardware round trips

[Guided hardware sessions](hardware-sessions.md) now automate the computer side of
each round trip. `po33 hw run` plays the restore, arms the backup recording, stops it
after the transfer ends, decodes it within seconds and reports an exact target match,
a cell-level list of differences, or a failed decode with an immediate retry. Every
attempt, the ordinary playback recording and the person's answers go into one
`hardware-session-NNN.json` record, and the accepted backup is copied to the
standard `capture.wav` and `derived/analysis-001` names used by existing check scripts.
`po33 build-batch` compiles one research restore carrying many explicit raw edits,
so several independent candidates share a single round trip. Both tools keep
`hardware_verified: false`; sound checks and field claims still need their own evidence.
The pending [single-tone baseline](../experiments/edited-pattern1-single-tone-no-FX-001/instructions.md)
can be run with `python -m po33_re hw run experiments/edited-pattern1-single-tone-no-FX-001 --playback 14`.

## Single-tone baseline verified

Both first-pair effect restores were received exactly, but their frozen first-tone
comparison is inconclusive: restore B's first sound was too weak to fit. The registered
single-tone follow-up is now hardware verified through the guided session. Its complete
backup matches the target, all nine native checks pass, and the unchanged first-tone
method measures 1190.417 Hz in all six measurements, with one tone per 2.4-second loop.
Restore A's first tone lies within 0.02% of this unshifted reference, which suggests
high-nibble-first effect order. That is a lead for a new registered pair, not a result.
See [results](pattern1-single-tone-baseline-results.md). Current genuine export:
`experiments/exported-pattern1-single-tone-no-FX-001/project.json`.

## Single-tone effect-order pair registered

The [F6/6F pair on the single-tone pattern](pattern1-single-tone-FX-order-control.md)
changes only Pattern 1's first footer byte. With one note on step 1, only step 1's
effect is audible. Low nibble first predicts F6 an octave up and 6F unshifted; high
nibble first predicts the reverse. The frozen A/B ratio decides, and each leg must also
match the measured 1190.417 Hz reference or its octave. Both restores pass exact
software round trips; the two hardware sessions are pending.

## Single-tone effect order: registered inconclusive, exploratory high nibble first

Both F6/6F restores were received exactly. The registered steady-tone comparison is
inconclusive because the effect fades in over its step, so restore B's first tone is
not steady. An exploratory pitch track places the effect on step 1 for the footer's high
nibble and on step 2 for the low nibble in both restores, matching the earlier lead.
A registered time-resolved test on fresh recordings is needed before relying on it. See
[results](pattern1-single-tone-FX-order-results.md).

The [pitch-track confirmation](pattern1-FX-order-pitch-track-control.md) freezes
that method and registers fresh recordings of the same F6/6F restores. Step 1 rising at
least 10% above the reference counts as the effect; staying within 1% counts as none.
Its two hardware sessions are pending.

## Effect order confirmed for footer byte 0

The registered pitch-track test supports **high nibble first**: in Pattern 1's first
footer byte, the high nibble holds step 1's effect and the low nibble step 2's. Both
fresh restores were received exactly, and all five loops of each agree. Effect code 6
fades in over its step rather than jumping an octave. See
[results](pattern1-FX-order-pitch-track-results.md).

The next [position map](pattern1-FX-position-map-control.md) puts the same note on
steps 1, 5, 9 and 13 and the rising effect on footer bytes 2 and 6. The sequential
model predicts that only steps 5 and 13 rise. Its hardware session is pending.

## Effect position map confirmed

Footer byte k holds steps 2k+1 (high nibble) and 2k+2 (low nibble). With the rising
effect written to bytes 2 and 6, only the notes on steps 5 and 13 rose, in all five
loops, and the person heard the second and fourth notes bend. See
[results](pattern1-FX-position-map-results.md).

The next [effect code map](FX-code-map-control.md) records FX keys 1 to 15 into
patterns 2 to 16 on the device and reads every stored code from one backup. The
registered model is code = key - 1, with keys 7 and 8 as known controls.

## Effect code map confirmed

Recording FX keys 1 to 15 into patterns 2 to 16 stored code = key - 1 uniformly on all
16 steps, with F meaning no effect. The same backup suggests the second global record
holds the selected pattern in byte 0 and one byte per pattern in bytes 131 to 146. See
[results](FX-code-map-results.md).

The next [full step map](pattern1-FX-full-step-map-control.md) plays the note on all
16 steps at 60 BPM with the rising effect on steps 2, 3, 5, 6, 10, 11, 13 and 14,
observing every footer nibble position at once. Its hardware session is pending.

## Full step map: exact reception, inconclusive, octave effect explained

The 16-note restore was received exactly. Every effect and no-effect step agreed with
the sequential layout, but the second step of each effect pair read indeterminate: under
a fully engaged effect the note plays an exact octave at double speed and low level,
below the audibility gate. A per-note gate is registered for a fresh backup and playback.
See [results](pattern1-FX-full-step-map-results.md).

## Per-step effect writer

`set_step_effects` is now a public edit-plan operation: 16 entries per pattern, each
none or an FX key 1 to 15. The earlier confirmation without a restore failed its
registered precondition because byte 131 changes when playback stops; its exploratory
reading matched the layout on all 16 steps. A [writer hardware test](step-effects-writer-control.md),
compiled through the public plan path, is registered and pending.

## Per-step effect writer verified

The public `set_step_effects` plan, compiled through `apply-edits`, was received exactly,
and all 16 steps played as planned in all five loops. The full per-step effect encoding
is now hardware verified. See [results](step-effects-writer-results.md).

The next [keyboard scale map](pattern1-key-scale-map-control.md) plays Sound 3 keys
1 to 16 on steps 1 to 16 and measures each pitch, testing chromatic, major and natural
minor layouts. Its hardware session is pending.

The first keyboard scale run was received exactly but played back at 80 BPM after an
accidental tempo change. Read on that grid, the keys formed whole-semitone rows on the
4x4 grid, falling by row from key 1. A [rerun](pattern1-key-scale-map-control.md)
registers that row layout as a fourth model with a grid-only method.

## Melodic keyboard layout confirmed

On Sound 3, keys 1 to 16 play rows of the 4x4 grid: 0, +1, +3, +4 / -7, -5, -4, -2 /
-12, -11, -9, -8 / -19, -17, -16, -14 semitones from key 1, each within half a cent in
the registered rerun. See [results](pattern1-key-scale-map-results.md).

## Melodic notes writer

`set_melodic_notes` is now a public edit-plan operation: 16 steps per melodic sound and
pattern, each a key 1 to 16 or a rest. Its [hardware test](melodic-notes-writer-control.md),
a shuffled melody using every key once, is registered and pending.

## Melodic notes writer verified

A shuffled melody written by `set_melodic_notes` through the public plan path was
received exactly, and every step played within one cent of its predicted pitch. See
[results](melodic-notes-writer-results.md).

## Note parameters decoded

A note's three primary bytes hold pitch, an unknown bit, volume, filter and resonance,
matching every calibrated field module. `set_step_parameters` writes one of them per
step. The [pitch-law test](pitch-law-control.md), one semitone per code across 1 to
25, is registered and pending.

The first pitch-law run was received exactly; its early window caught a 25 to 35 ms
glide from the previous pitch, so it was inconclusive. Read after the glide, every code
held within about 2 cents of one semitone per code. A [confirmation](pitch-law-control.md)
with a new code order and a later window is registered.

## Pitch-code law confirmed

Per-step pitch codes 1 to 25 play -12 to +12 semitones around code 13, one semitone per
code, within 2.4 cents after a 25 to 35 ms glide. See [results](pitch-law-results.md).
The harness now also realigns one-label acquisition slips at the frame start, and
`hw reanalyze` re-decodes kept backups.

The next [volume law test](volume-law-control.md) gives every step its own volume
code from 0 to 63 at one pitch and measures the gain table. Two laws fitted to earlier
measurements are registered. Its hardware session is pending.

## Volume gain table measured

Per-step volume codes 3 to 63 span about -15.4 to +7.5 dB relative to code 36, about
0.4 dB per code in the middle and flattening at both ends; neither registered law fits.
Code 0 played at the preceding step's level rather than silence. A follow-up test is
registered. See [results](volume-law-results.md).

Volume code 0 is confirmed to mean "no volume set": in the registered follow-up, every 0
step played at its predecessor's level, and the gain table reproduced within 0.01 dB.

## Sample import beyond Sound 6

The importer's core is now slot-generic, and `set_melodic_notes_from` lets a sound with no
notes copy another sound's note parameters. A [registered test](sound7-import-control.md)
imports a 600 Hz tone into Sound 7 and alternates it with Sound 3 in a pattern, predicting
-386.3 cents. Public import stays Sound 6 until that passes.

## Sample import into Sound 7 verified

A tone imported into Sound 7 was received exactly and played exactly -386.3 cents from
Sound 3, as predicted; the absolute pitch matched "stored audio plays 7 semitones up at key
1, pitch 13" within 0.2 cents. `import-sample` now accepts Sound 6 and Sound 7. See
[results](sound7-import-results.md).

The next [drum recording observation](drum11-record-observation-control.md) samples
16 tone bursts into empty drum Sound 11 on the device and reads how the recording and its
16 slices are stored. Its hardware session is pending.

## Drum recording structure observed

Recording into a drum slot creates one buffer owned by its first slice and 16 references.
The device trims leading silence and places slice boundaries at detected onsets; slice k
holds the k-th hit and slice 16 runs to the end. See
[results](drum11-record-observation-results.md).

## Drum notes writer verified

`set_drum_notes` writes drum key k as auxiliary byte 0x10 + k - 1, and on the device key k
plays the k-th window of the kit at the stored rate. See
[results](drum-notes-writer-results.md). The first software drum-kit import is
[registered](drum-kit-import-control.md) and awaits its hardware session.

## Software drum-kit import verified

Sixteen WAV hits imported into Sound11 play back exactly: key k plays hit k at the stored
rate and stops at its window end. See [results](drum-kit-import-results.md). An import
into empty Sound12 with page-rounded capacities is [registered](drum-kit-pages-control.md).

## Page-rounded drum kits verified

Drum kits stored in any whole number of 4096-code pages play correctly, and an empty drum
slot accepts an imported kit. See [results](drum-kit-pages-results.md). A
[sample-memory step](drum-memory-control.md) to 675840 codes is registered.

## Sample memory holds at least 675840 codes

Four extra full drum kits restored and backed up exactly, for 28.8 s of sample audio in
total. See [results](drum-memory-results.md). A
[step to 815104 codes](sample-memory-step2-control.md) is registered.

## Sample memory holds at least 815104 codes

The device stores and returns 34.8 s of sample audio exactly. A battery loss between
restore and backup left the device empty. See [results](sample-memory-step2-results.md).
A [step to 917504 codes](sample-memory-step3-control.md) is registered.

## Sample memory holds at least 917504 codes

The device stores and returns 39.1 s of sample audio exactly, and a borrowed drum kit can
get its own buffer. See [results](sample-memory-step3-results.md). A
[step past the advertised 40 s](sample-memory-step4-control.md) is registered.

## Sample memory limit found near 241 pages

Offered 43.5 s of samples, the PO-33 showed ERR and kept an exact 241-page prefix,
987136 codes or 42.1 s. See [results](sample-memory-step4-results.md). A
[test at exactly 241 pages](sample-memory-limit-control.md) is registered.

## Sample memory limit confirmed: 241 pages

The PO-33 holds 241 pages of 4096 sample codes: 987136 codes, 42.1 s. See
[results](sample-memory-limit-results.md). A [4.0 s melodic import](long-melodic-control.md)
is registered.

## Long melodic samples verified

A 4.0 s melodic sample in a page-rounded buffer plays whole and in order. See
[results](long-melodic-results.md). Imports into
[all eight melodic slots](all-melodic-slots-control.md) are registered.

## All eight melodic slots verified

Every melodic slot accepts an imported sample, including slots that borrowed another
sound's buffer. See [results](all-melodic-slots-results.md). A
[selected-pattern test](selected-pattern-control.md) is registered.

## Patterns beyond Pattern 1 and the selected pattern verified

Pattern 5 written through the plan path plays when selected through global byte 0. See
[results](selected-pattern-results.md). A [pattern chain observation](pattern-chain-control.md)
is registered.

## Pattern chain storage observed

A chain is stored as entries in second global record bytes 0 to 127 and a length in byte
128. See [results](pattern-chain-results.md). A [chain writer test](chain-writer-control.md)
is registered.

## Chain writer verified

A chain written in software plays in entry order with repeats. See
[results](chain-writer-results.md). A [drum pitch test](drum-pitch-control.md) is
registered.

## Drum pitch codes verified

A drum note's pitch code transposes it one semitone per code from the stored rate. See
[results](drum-pitch-results.md). A [filter law test](filter-law-control.md)
covering every filter code is registered.

## Filter law measured

Every filter code was measured: 1 to 31 low-pass, 44 to 62 high-pass, 0 and 63 off, with
cutoff rising about one octave per 4 codes. See [results](filter-law-results.md). A
[resonance law test](resonance-law-control.md) is registered.

## Resonance law measured

Resonance has eight levels of eight codes each, peaking up to about 20 dB higher at the
top level; code 0 appears to mean no parameter lock. See
[results](resonance-law-results.md). A [no-lock test](no-lock-control.md) is registered.

## Code 0 is no parameter lock

A step with filter, resonance or volume code 0 keeps the last locked value. See
[results](no-lock-results.md). A [knob observation](sound-knobs-control.md) is registered.

## Knob settings are live state, not backup data

Turning a sound's knobs without WRITE changes no byte of a backup. See
[results](sound-knobs-results.md). A [parameter-only lock test](param-only-control.md)
is registered.

## Parameter-only locks verified

A lock on a step without a note holds for the unlocked notes after it. See
[results](param-only-results.md). A [polyphony test](polyphony-control.md) is registered.

## Four-voice polyphony

Stacks of more than four sounds on one step play exactly four voices. See
[results](polyphony-results.md). A [voice priority test](voice-priority-control.md)
is registered.

## Voice priority mapped

When more than four sounds share a step, the lowest-numbered sounds play, with one
recorded exception. See [results](voice-priority-results.md). A
[voice stealing test](voice-steal-control.md) is registered.

## Sounding notes are not stolen

A sounding note is never cut to make room; extra new notes are dropped unless a voice is
about to end. See [results](voice-steal-results.md). A
[voice release test](voice-release-control.md) is registered.

## Voice release rule measured

A new note gets a voice only if one is free or within about 100 ms of its end; nothing
sounding is cut. See [results](voice-release-results.md). A
[note bits test](note-bits-control.md) for pitch code 0 and bit 5 is registered.

## Pitch code 0 is no lock; bit 5 under test

Pitch code 0 holds the previous pitch, like the other parameters. Bit 5 is stored by the
device; its effect was confounded with the pitch glide. See
[results](note-bits-results.md). A [bit-5 glide test](bit5-glide-control.md) is registered.

## Bit 5 is inert

The last unexplained bit of a note cell is stored but changes nothing audible. See
[results](bit5-glide-results.md).

## Sample windows verified

A melodic sample plays from its header's start code to its end code, so samples can be
trimmed by rewriting two fields. See [results](sample-window-results.md).

## Swing law measured

Even steps are delayed by swing/24 of a step; 18 delays them by three quarters of a
step. See [results](swing-law-results.md). A [priority map test](priority-map-control.md)
is registered.

## Voice ranking mapped

When more than four sounds share a step the ranking is 1, 2, 3, 11, 4, 5 to 8, 12 to 16.
See [results](priority-map-results.md).

## A project built from a spec plays as built

`po33_re.project_build` turns a description of samples, patterns, chain, tempo and swing
into a restore the device accepts exactly and plays at the intended tempo and feel. See
[results](project-build-results.md).

## Every field accounted for

Unseen auxiliary nibbles and global bytes 131 to 146 are stored as written; only F and 1
matter for notes. See [results](stray-bits-results.md). An
[FX catalogue observation](fx-catalog-control.md) for previews is registered.

## FX catalogue on single notes

Nine effects change a single note measurably (extend, double, octave copy, sweeps, cut,
delay); six do nothing to an isolated note and must act at pattern level. See
[results](fx-catalog-results.md).

## FX over a run of notes

Loops, sweeps, copies, cuts and gates are described per effect. See
[results](fx-pattern-results.md). FX 1, 2 and 15 are not loops of any
length; FX 14 restarts the pattern from the hold. See [loop results](fx-loop-results.md).
FX 15 is reverse, 1 and 2 loop the sample's start, 12 retriggers and 11 scratches. See
[direction results](fx-direction-results.md). The loop effects divide the bar: FX 1 loops 1/16,
2 1/12, 3 1/32, 4 1/48, and FX 12 retriggers every 1/16. See [period results](fx-period-results.md).
FX 1, 2 and 3 follow the tempo; FX 4 is a fixed 80 ms. See [tempo-sync results](fx-period-120-results.md).
The [FX reference](fx-reference.md) and [format reference](format-reference.md)
collect everything an editor needs.

FX 9, 10, 12 and 13 scale with the step; see [120 BPM results](fx-onsets-120-results.md).
## Full project build verified

A device-filling project from one spec, sixteen imports and sixteen patterns, restores
exactly and plays at tempo in chain order. See [results](project-build-full-results.md).

## Last two effects resolved

FX 14 loops the steps before the hold; FX 13 is a triplet quantize. See
[results](fx-rules-results.md). The [FX reference](fx-reference.md) has no open points.

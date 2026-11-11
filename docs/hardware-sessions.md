# Guided hardware sessions and research batches

These tools shorten each hardware round trip. You still press the PO-33 buttons.
The computer plays the restore, records the backup, decodes it within seconds and
tells you at once whether it matched. Every attempt is kept, and one session record
holds the hashes, levels, checks and your answers.

## One-time setup

Two cables are used:

- computer output to the PO-33 line input, for restores
- PO-33 output to the computer stereo input, for backups and playback

### Swap cables around every restore

The PO-33 mixes its line input into its output. With both cables connected, part of
its output returns to its input and comes back about 4.5 ms later, inverted and mostly
in the left channel. On 2026-10-10 this broke backups and a restore. Turning the
interface's MIX pot fully to DAW reduced the copy but did not remove it, and no
software setting did either.

The reliable fix is to have only one cable connected at a time. The session prompts
for it (`input_cable` is `unplug` by default):

1. Before the restore: connect the computer output to the PO-33 input, and unplug the
   PO-33 output from the computer.
2. After the restore: unplug the computer output from the PO-33 input, and connect the
   PO-33 output to the computer input. Backup and playback recordings use this cable.

Short extension cables make the swaps quick and spare the device's jacks. Every backup
is still checked for a delayed copy of itself. If one is found, the session reports an
error at once, which usually means the computer output is still plugged in.

### Restore playback level

The harness pads every restore with 0.25 s of silence before and 1 s after, and waits
for the output latency before closing the stream. Without this, the MME output stopped
before its last buffer played, cutting the final transfer packet. The PO-33 then showed
ERR at the end of the transfer, although the same file restored from a media player.

Generated restores peak at 0.5, while genuine backups peak near 0.15. Both restore
through Audacity at the established level. If the PO-33 shows ERR part-way through a
transfer, try a lower software gain. A gain of 0.3 sends a generated restore at about
the level of a genuine backup.

```powershell
.\.venv\Scripts\python.exe -m po33_re hw play experiments/<folder>/restore.wav --gain 0.3
.\.venv\Scripts\python.exe -m po33_re hw config --playback-gain 0.3
```

`hw play` plays one WAV without recording anything. `--playback-gain` stores the gain
for every session restore. Each session record keeps the gain and the resulting peak.

### Optional playback-path check without the device

Patch the interface output straight into its input, then play a known restore:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw loopback experiments/edited-pattern1-single-tone-no-FX-001/restore.wav --expect experiments/edited-pattern1-single-tone-no-FX-001/edited.symbols.npz --out-dir C:/temp/loopback-001
```

Exit code 0 means the recorded playback decodes to the exact target. If it fails,
look for resampling, enhancements, clipping or a mono path before blaming the device.

## Running an experiment that has a restore

Any experiment folder with `restore.wav` and `edited.symbols.npz` works, including
earlier prepared folders, compiled edit plans and research batches.

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/edited-pattern1-single-tone-no-FX-001 --playback 14
```

The session then runs in order:

1. You press WRITE + SOUND + RECORD, then Enter. The restore plays.
2. Recording arms by itself. You press WRITE + SOUND + PLAY. The recording stops
   1.5 seconds after the transfer ends, so it keeps the lead-in and a quiet tail.
3. The backup is decoded with the established 0.0063 threshold. If that fails, the
   measured-clock decoder is tried. You see one of these verdicts:
   - **MATCHES TARGET EXACTLY**
   - **DIFFERS FROM TARGET**, with every differing pattern cell, footer, sound header
     or global byte listed. The backup is still real evidence and is kept.
   - **NOT DECODED**. You are asked to record the backup again straight away.
4. With `--playback`, you press Enter and then PLAY about one second later. The stated
   number of seconds is recorded after the first sound, keeping the silence before
   it. The recording is rejected at once, with an offer to record again, if the first
   sound comes after 4.5 s or before 0.3 s, or if the level changes by more than 1.5x.
   The registered audio methods need all three. Keep the PO-33 and computer volumes
   fixed while recording.
5. You answer the experiment's questions. Answers are stored verbatim.

Exit code 0 means the backup decoded and matched any expected target. Exit code 3
means it did not decode or differed from the target.

To record only playback again in a folder that already has its backup:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw playback experiments/<folder> --seconds 14
```

## Recording device-side changes

For a control where you change something on the device instead of restoring, give
a baseline artifact so the session can describe what changed:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/observe-notes-001 --new --no-restore --baseline experiments/<earlier>/derived/analysis-001/capture.symbols.npz
```

If the folder has an `instructions.md`, it is shown before recording. Several
changes in different patterns, steps or sounds can be made before one backup,
because each change is reported at its own cell.

## Files a session writes

| Path | Content |
| --- | --- |
| `attempts/backup-NN.wav` | Every backup recording, untrimmed integer PCM |
| `attempts/backup-NN-analysis/` | Its decode artifact, decode report and harness analysis |
| `capture.wav` | Byte copy of the accepted attempt, for existing check scripts |
| `derived/analysis-001/` | Copy of the accepted attempt's analysis |
| `playback.wav` | Ordinary playback recording, when requested |
| `hardware-session-NNN.json` | Devices, input hashes, every attempt, verdicts, answers |

The session never edits `experiment.json`, registrations or earlier evidence. It
refuses a folder that already has `capture.wav`. Session records keep
`hardware_verified: false`: exact reception is a software check on a real backup,
and confirming sound still needs a listening or playback measurement.

## Building one restore that tests many things

`build-batch` applies explicit raw edits to a hash-bound source artifact and writes
a ready experiment folder. Use it to test many independent values in one round
trip, for example one candidate per pattern.

```json
{
  "schema": "po33.research-batch",
  "schema_version": 1,
  "description": "Pitch codes 1..16 on Sound 3, one pattern each",
  "source_artifact": "experiments/<source>/derived/analysis-001/capture.symbols.npz",
  "source_artifact_sha256": "<sha256 of that file>",
  "operations": [
    {"op": "clear_pattern", "pattern": 1},
    {"op": "set_cell", "pattern": 1, "step": 1, "sound": 3, "primary": "0e0981", "auxiliary": "f0"},
    {"op": "copy_pattern", "source": 1, "destination": 2},
    {"op": "set_footer", "pattern": 2, "footer": "6fffffffffffffff"},
    {"op": "set_record_byte", "tag": "0x7d5c", "ordinal": 2, "offset": 129, "value": 100}
  ],
  "playback_seconds": 14,
  "observation_questions": ["Did every pattern play?"]
}
```

```powershell
.\.venv\Scripts\python.exe -m po33_re build-batch spec.json --out-dir experiments/batch-pitch-001
.\.venv\Scripts\python.exe -m po33_re hw run experiments/batch-pitch-001
```

| Operation | Arguments |
| --- | --- |
| `set_cell` | `pattern`, `step`, `sound` (1..16), `primary` (3 hex bytes), `auxiliary` (1 hex byte) |
| `clear_cell` | `pattern`, `step`, `sound` |
| `set_footer` | `pattern`, `footer` (8 hex bytes) |
| `clear_pattern` | `pattern`: zero cells and an all-F footer |
| `copy_pattern` | `source`, `destination` |
| `set_record_byte` | `tag`, 1-based `ordinal`, payload `offset`, `value` |

Every operation may also carry a `note`. Operations apply in order. The build
reports operations that changed nothing, which usually means a planning mistake.
The restore only gets its final name after the full waveform round trip recovers
the exact target. A failed build leaves `restore.FAILED.wav` and raises an error.

This is a research tool. It writes raw bytes that may never have been seen on the
device, unlike the guarded edit-plan writers. Keep a recovery backup that you
have restored successfully, and do not cite a batch result for a field until the
backup and sound checks support it.

## Making batches informative

- Give each candidate its own pattern, so both the backup and the playback can be
  read independently. Chain patterns when recording playback to hear several at once.
- Keep one unchanged reference pattern in every batch, so a sound measurement has
  a comparison inside the same recording.
- Remove samples you do not need from the source state. Smaller states transfer
  faster, and every restore and backup gets shorter.
- If the device rejects a batch, split it in half and try each half.

## Device actions after a restore

If an experiment folder has both a restore WAV and an `instructions.md`, the harness shows
the instructions after the restore and cable swap, and waits for Enter before arming the
backup. This lets an observation start from a known restored state. The session record is
written only after the end-of-session questions are answered.

## Keeping transfers short

Restore and backup time grow with the sample data on the device, about 0.27 s per 1000
codes each way. When a test does not need a sound's full content, shrink it first in the
same plan: `scripts/slim_drum_kits.py` re-imports drum kits with only key 1 kept and the
other keys as 20 ms of silence, 4 pages per kit. Melodic slots can be shrunk the same way
by re-importing shorter tones. The key-1 audio stays byte-identical, so tests that play it
are unaffected; the backup must still match the compiled target exactly.

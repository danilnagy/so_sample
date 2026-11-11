# Recorded Sound 3 TONE pitch down

The post-playback baseline is verified unchanged with raw volume 36 in all 16 Sound 3
cells. This probe intentionally records movement of TONE knob A, leaving B untouched.
The [official guide](https://teenage.engineering/guides/po-33/en), section 6, identifies
TONE pitch/volume controls and parameter locking by holding WRITE while turning knobs
during pattern playback. It does not specify backup bitfields or guarantee that moving
one knob records only that parameter.

1. Select Pattern 1 / Sound 3 / TONE, stopped with write off. Keep B and all recording
   and playback settings unchanged.
2. Start Pattern 1. Hold WRITE and slowly turn **only A fully counterclockwise** over
   approximately 5 seconds. Do not press keyboard keys or hold BPM/FX during the pass.
3. Continue holding WRITE for 3 more seconds with both knobs stationary. Release
   WRITE, stop playback and ensure write off.
4. Record a complete backup as
   `experiments/event-051-b-sound3-tone-pitch-lock-down/capture.wav`, using the established
   reduced recording level with one second trailing silence.
5. Report whether Sound 3 dropped in pitch and any display label/number actually seen.
   An uncertain audition or absent display value remains unknown. Leave A at minimum
   and B untouched. No restore or separate ordinary playback recording is needed.

## Registered alternatives

The first primary byte's low six bits are a new pitch-location hypothesis. Their
baseline values are 13 at the five note cells and 0 at parameter-only cells. That
observation does not define a pitch scale or predict a minimum endpoint code.

- No serialized change: the complete body remains equal to the actual baseline.
- Strict candidate: at least one first-low-six field changes and only mask 0x3f
  in Sound 3 / Pattern 1 first-primary bytes changes. Auxiliary data stays exact.
- Candidate plus volume: first-low-six data changes, with changes confined to first
  byte 0xff and second byte 0x0f. This separately exposes a volume snapshot.
- Broader Sound 3 primary changes, or primary and auxiliary changes: complete raw
  tuples and auxiliary values remain visible without interpreting extra bits.

Samples, global settings 100/9, other 15 patterns, other sounds, the pattern footer,
packet tags/lengths and native geometry have independent checks. A wider change
cannot be silently called pitch-only. The movement can retain a per-step ramp;
neither uniformity nor a complete target body is predicted. No endpoint value,
numeric UI reading, semitone law or pitch-field writer is assumed.

The public volume writer continues to require its existing nonvolume context and
rejects the synthetic changed-pitch layout. No production writer is extended.
All 40 focused pitch/volume tests pass; the last full regression suite passed 853.
Tests include no-change, mixed values, coupled volume, volume-only changes, other
primary/auxiliary changes and hidden neighbor, sample, global or pattern changes.

- [Preregistration](../experiments/sound3-tone-pitch-down-registration-001.json)
- [Verified post-playback baseline](sound3-volume-post-playback-results.md)
- [Checker](../scripts/check_sound3_tone_pitch_probe.py)

After independent capture decoding at threshold 0.0063:
`python -m scripts.check_sound3_tone_pitch_probe`.
Optional `--display-text` and `--audition-result lower|higher|unchanged|unknown` inputs
must reflect actual user reports. Software reports remain hardware-unverified.

Completed: only the strict first-low-six candidate bits change; all 16 values
become raw 1 while volume 36 and every unrelated byte remain exact. The user hears
lower pitch and reports Ptc/ticks without a numeric reading. See
[results](sound3-tone-pitch-minimum-results.md) and the next
[upper endpoint / exact minimum return](sound3-tone-pitch-range-control.md).

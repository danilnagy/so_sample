# First software drum-kit import verified

The [drum-kit import test](drum-kit-import-control.md) replaced the device-recorded kit in
Sound11 with 16 generated WAV hits, written by `src/po33_re/drum_import.py` in the device's
own layout. The backup equals the compiled target exactly, including every imported code
and all 16 windows. The person heard a falling run of 16 beeps that got longer.

Every registered prediction holds in all five playback loops:

- **Key k plays hit k.** Each step lands within 0.1 cents of -100 (k-1) cents;
  `old_kit_still_playing` fails.
- **Stored rate.** Step 1 sounds at 1499.9 Hz against the 1500 Hz hit, 0.1 cents off.
- **Stops at the window end.** Each step sounds for its window length, 74.7 to 234.7 ms,
  within 0.6 ms.

| Step | Window ms | Measured ms |
| --- | --- | --- |
| 1 | 74.7 | 74.6 |
| 8 | 149.3 | 149.5 |
| 16 | 234.7 | 234.3 |

So a drum kit is a contiguous buffer with 16 windows, and key k plays exactly window k at
the stored rate. Window boundaries can be anywhere: unequal lengths play as written.

- [Registration](../experiments/drum-kit-import-registration-001.json)
- [Decision](../experiments/drum-kit-import-decision-001.json)
- [Observation](../experiments/compiled-drum-kit-import-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-drum-kit-import-001/project.json`

The next [page-capacity test](drum-kit-pages-control.md) imports into empty Sound12 and
shrinks Sound11's buffer to whole pages.

# FX reference

What each of the 15 punch-in effects does, as measured on the device. Footer encoding:
pattern byte 1024 + k holds steps 2k+1 (high nibble) and 2k+2 (low nibble); the nibble is
the FX key minus 1, and F means no effect ([code map](FX-code-map-results.md)). An effect
applies to the whole mix on the steps where it is set.

| FX | Measured behaviour | Source |
| --- | --- | --- |
| 1 | loops 1/16 of a bar of the sample from where the effect starts, following the tempo; the loop runs on past the note's end while held | [period](fx-period-results.md), [tempo sync](fx-period-120-results.md) |
| 2 | loops 1/12 of a bar, following the tempo | same |
| 3 | loops 1/32 of a bar, following the tempo | same |
| 4 | loops a fixed 80 ms | same |
| 5 | doubles each note: a second onset about 93 ms after the first, up to +8 dB, slightly detuned | [single note](fx-catalog-results.md) |
| 6 | adds a copy one octave down, +6 dB where they overlap | same |
| 7 | bends the pitch upward through the note, reaching about an octave above by 200 ms | same, [run](fx-pattern-results.md) |
| 8 | bends the pitch downward, about an octave below, over about 300 ms | same |
| 9 | cuts every note short at about half a step, following the tempo | same, [120 BPM](fx-onsets-120-results.md) |
| 10 | gates the run: of each four steps the third starts late and quieter and the fourth is silent; step-relative | [run](fx-pattern-results.md), [120 BPM](fx-onsets-120-results.md) |
| 11 | scratch: the playback position jumps about the sample; over a run of steps it repeats the step on which it began | [direction](fx-direction-results.md), [loop](fx-loop-results.md) |
| 12 | retriggers the first held step's note once per step, following the tempo | [period](fx-period-results.md), [120 BPM](fx-onsets-120-results.md) |
| 13 | triplet quantize: the first three notes of each beat play at 0, 1/3 and 2/3 of the beat and the fourth is dropped | [rules](fx-rules-results.md) |
| 14 | loops the steps before the hold, from step 1, with a period of the hold's start step minus one | [rules](fx-rules-results.md) |
| 15 | reverse: the sample plays backwards | [direction](fx-direction-results.md) |

No open points remain. Everything was measured at 60 BPM, the timing effects also at 120,
on one melodic tone.

# Web template test: the TypeScript compile step's first restore

Registered 2026-10-11. The sosample core (`web/src/core`) compiles a project onto the
empty-device template and encodes the restore itself. This session asks the device to
accept that restore exactly and to play every sample layout the compiler produces.

## Build

`web/scripts/build-web-template-test.ts` compiles a project from generated samples (a
decaying 329.6 Hz tone, two noise bursts, a rising chirp) and writes `restore.wav`,
`packets.json` and `project.json` into `experiments/web-template-001`.
`scripts/prepare_web_template_test.py` rebuilds the same packets with the Python encoder
on the template's label prefix, requires the two restore WAVs to be byte-identical, and
registers the test. Source state: [empty-001-a](empty-baseline.md).

## Layouts under test

| Sound | Layout | Verified before? |
| --- | --- | --- |
| 1 | owns the tone (3 pages), window 0..11719 | yes (imports) |
| 2 | references Sound 1's buffer, window 0..5000 | yes (Sound 6 to 7 copy, factory) |
| 3 | references Sound 1's buffer, window 3000..9000 | factory Sound 3 only |
| 9 key 1 | owns the kit buffer: kick then snare (1 page) | yes (kit import) |
| 9 key 2 | window into the kit buffer | yes |
| 9 key 3 | a second window into the kick, start 400 | windows verified, reuse new |
| 9 key 4 | no record | **new** |
| 9 key 5 | references Sound 1's buffer, window 0..4000 | factory Sounds 9/10 to Sound 1 |
| 9 keys 6..16 | the same snare window, eleven references | new combination |
| 10 | one chirp sliced into sixteen 512-code windows; key 2 overlaps (256..2000) | drum windows verified, overlap new |

Patterns: Pattern 1 has a Sound 1 run with a filter lock on step 9 and a volume lock
without a note on step 2, Sound 2 and 3 notes, and kit hits on keys 1 to 6; Pattern 2
plays the sixteen chirp slices on Sound 10 with FX 1 on steps 9 to 12. Chain 1, 2;
tempo 100; swing 4.

## Predictions

1. The backup equals the compiled target exactly.
2. Sound 2 plays the tone cut at 5000 codes; Sound 3 starts part-way in.
3. Sound 9 key 4 is silent; key 5 plays the tone.
4. Sound 10 plays a chirp fragment on every step.

Prediction 1 is decided by the native check; 2 to 4 by the observation answers.

## Session

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/web-template-001 --playback 22
.\.venv\Scripts\python.exe -m scripts.check_web_template_test
.\.venv\Scripts\python.exe -m scripts.finalize_web_template_test
```

# Kit-sharing test: drum keys referencing another kit's buffer

Registered 2026-11-09. The compiler stores a sample used only by drum sounds inside each
drum sound's own kit buffer, so a kit loaded on two drum sounds is stored twice. The
format allows a key to reference any sound's buffer with its own window, and a melodic
buffer referenced by drum keys restored exactly in [web-template-001](web-template-results.md).
A drum key referencing another drum sound's kit buffer has not been restored. This
session asks the device to accept and play that layout; if it does, the compiler's
`SHARE_KIT_SAMPLES` default is turned on, and the bundled projects, which load one
standard kit on several drum sounds, need about half the drum pages.

## Build

`web/scripts/build-kit-sharing-test.ts` compiles a project from generated samples (a
falling-sine kick, two noise bursts for snare and hat, a square blip) with
`shareKitSamples: true`, checks the layout below, and writes `restore.wav`,
`packets.json` and `project.json` into `experiments/kit-sharing-001`.
`scripts/prepare_kit_sharing_test.py` decodes that restore with the Python decoder into the
expected artifact, requires the decoded packets and body to equal the compiler's, and
registers the test. The compile starts from the empty-device template,
[empty-001-a](empty-baseline.md), as every app export does.

## Layouts under test

| Sound | Layout | Verified before? |
| --- | --- | --- |
| 11 keys 1, 3, 7 | own kit buffer: kick, snare, hat (3 pages) | yes (kit import) |
| 12 keys 1, 3, 7 | every key references Sound 11's buffer at the same windows; Sound 12 stores nothing | **new** |
| 13 key 1 | own kit buffer, kick first then the blip (3 pages) | yes |
| 13 key 6 | window into Sound 13's own buffer | yes |
| 13 keys 3, 7 | reference Sound 11's buffer | **new** |
| 13 key 5 | references Sound 11's buffer from 1500 codes into the snare | **new** |

Six pages in all; the same project compiled without sharing takes ten.

Patterns: each plays one drum sound with the same beat (kick 1 and 9, snare 5 and 13,
hats 3, 7, 11, 15): Pattern 1 Sound 11, Pattern 2 Sound 12, Pattern 3 Sound 13 with the
blip on step 14 and the snare tail on step 16. Chain 1, 2, 3; tempo 100; swing 0.

## Predictions

1. The backup equals the compiled target exactly.
2. Pattern 2 sounds the same as Pattern 1.
3. Pattern 3 plays the beat, the blip on step 14 and a short snare tail on step 16.

## Running it

```
cd web && npx tsx scripts/build-kit-sharing-test.ts && cd ..
.venv/bin/python -m scripts.prepare_kit_sharing_test
.venv/bin/python -m po33_re hw run experiments/kit-sharing-001
.venv/bin/python -m scripts.check_kit_sharing_test
.venv/bin/python -m scripts.finalize_kit_sharing_test
```

`po33 hw run` plays the restore, prompts for the cable swap, records the backup and the
playback, and asks the observation questions. A failed prediction is kept with its
evidence; the default then stays off.

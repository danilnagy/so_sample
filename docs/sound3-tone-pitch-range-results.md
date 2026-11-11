# Pitch endpoints and exact low-end return

Both captures independently decode at threshold 0.0063 to 815 checksum-valid packets
and end byte 156758. The recorded high end is uniform raw 25 across all 16 Sound 3
cells; the return is uniform raw 1 and exactly equals the entire independent earlier
low-end body and all packets. The preregistered complete-return prediction passes.

| Capture | Body SHA-256 |
| --- | --- |
| Recorded maximum, raw 25 | `3924a9ad5734cb5603513ab3660eb3fcb176d53b269d049e9ff9f77740c2e5d1` |
| Minimum return, raw 1 | `227d4d25e644c83f2d8e89d2a4135125f8cb926082983a81b4842de21e654fc2` |

Only first-primary low-five bits change. Volume stays 36 throughout; all sample
records, auxiliary note keys, other primary bits, other sounds, other 15 patterns,
globals 100/9 and the footer remain exact. Both registered low-five and low-six masks
fit; the unchanged sixth bit does not prove full field width. The high code 25 was
unknown before its data and is retained as an observation, not a prior prediction.

The user explicitly reports hearing pitch go up and down. No numeric UI readings or
measured frequency ratio are supplied. Backup peaks remain near 0.153/0.148. All 31
content hashes and full native reconstruction pass for the latest genuine read-only
export: `experiments/exported-sound3-tone-pitch-return-minimum-001/project.json`.
Raw sample previews do not render the pattern pitch shift.

- [Immutable native range checks](../experiments/sound3-tone-pitch-range-results-001.json)
- [Maximum hardware observation](../experiments/event-052-c-sound3-tone-pitch-lock-up/hardware-observation-001.json)
- [Return hardware observation](../experiments/event-053-d-return-sound3-tone-pitch-lock-minimum/hardware-observation-001.json)
- [Upper literal model, explicitly post-observation](../experiments/sound3-tone-pitch-upper-post-observation-model-001.json)

The next [generated 13/14 pair](generated-sound3-pitch-pair-control.md) tests an interior
edit and a one-semitone interval hypothesis with ordinary audio. Neither a pitch law,
UI scale, full field width nor a public pitch setter is enabled by endpoint data alone.

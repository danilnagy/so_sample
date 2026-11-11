# Web template test: the TypeScript compile step restores exactly

Session 2026-10-11, one restore, one backup, 22 s of playback. Control:
[web template control](web-template-control.md).

## Results

| Prediction | Result |
| --- | --- |
| The backup equals the compiled target exactly | **held**: every packet and the whole body matched (`hardware-recapture-results-001.json`) |
| Sound 2 plays the tone cut at 5000 codes; Sound 3 starts part-way in | **held** (answer: yes) |
| Sound 9 key 4, stored as no record, is silent; key 5 plays the tone from Sound 1's buffer | **held** (answer: yes) |
| Sound 10 plays a chirp slice on every step, including the overlapping key 2 | **held** (answer: yes) |

The restore was built entirely by `web/src/core` (project model, compile onto the
empty-device template, canonical packet layout, label streams, waveform synthesis). The
Python encoder produced the byte-identical WAV from the same packets before the session,
and the device accepted it on the first attempt.

## What this establishes

- The empty backup `experiments/empty-001-a` works as the template every export starts
  from; the device accepts a state whose unknown bytes are the template's.
- Memory sharing by reference: a melodic sample stored once and referenced by two other
  melodic tracks with different windows (including a nonzero start), and by a drum slice,
  plays as expected. This closes both sharing sessions the proposal asked for.
- A drum kit may mix its own buffer with references into another sound's buffer, reuse one
  window several times, and leave a key with no record, which is silent.
- A drum track can be one sample sliced into sixteen arbitrary, even overlapping, windows.

The session is golden fixture `golden-web-template-001.json` for the TypeScript tests.

## Limits

One device, one session; the audible predictions rest on listening. The template's
unverified bytes (first global record, bytes 131 onwards of the second) are carried as
the device wrote them.

Observation: [`hardware-observation-001.json`](../experiments/web-template-001/hardware-observation-001.json).

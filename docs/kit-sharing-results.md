# Kit-sharing test: drum keys may reference another kit's buffer

Session 2026-11-09, one restore, one backup, 20 s of playback. Control:
[kit-sharing control](kit-sharing-control.md).

## Results

| Prediction | Result |
| --- | --- |
| The backup equals the compiled target exactly | **held**: every packet and the whole body matched (`hardware-recapture-results-001.json`) |
| Pattern 2 on Sound 12, every key a reference into Sound 11's kit buffer, sounds the same as Pattern 1 | **held** (answer: yes) |
| Pattern 3 on Sound 13 plays its own kick and blip, Sound 11's snare and hat, and a window from 1500 codes into Sound 11's snare | **held** (answer: yes) |

## What this establishes

- A drum key may reference another drum sound's kit buffer, with any window into it,
  including one starting part-way into a sample; a drum sound may store nothing and play
  entirely from another kit's buffer.
- A kit may mix its own buffer with references into another kit's buffer.
- The compiler's `SHARE_KIT_SAMPLES` is therefore on: a sample used by several drum
  sounds is stored once where it can be. A later drum sound plays it from the kit that
  stores the most of it so far, which is the verified layout (a reference to another drum
  sound's buffer with any window into it); a sound needing more than any kit stores keeps
  its own copy. The test project needed 6 pages instead of 10.

## Limits

One device, one session; the audible predictions rest on listening. The expected artifact
was the Python decode of the TypeScript restore, checked to carry the compiler's packets,
since the template capture is on the research machine.

Observation: [`hardware-observation-001.json`](../experiments/kit-sharing-001/hardware-observation-001.json).

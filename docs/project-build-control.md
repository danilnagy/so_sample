# Project build test

The first end-to-end use of the toolkit the way an editor would use it. A project spec
names samples, patterns, a chain, a tempo and a swing, and `po33_re.project_build` turns
it into a restore: it imports the samples, then compiles one edit plan with the verified
writers. Pattern notes are written with explicit parameters by the new `set_notes`
operation, so no template notes are needed.

The spec:

- **Sound 8** gets a new 0.3 s tone at C5, played by a melody on keys 1, 3, 5 and 8.
- **Sound 9** gets a new kit of sixteen 85 ms tones.
- **Pattern 1** has the melody on odd steps, Sound 13 on steps 1, 5, 9, 13, Sound 14 on 5
  and 13, and Sound 9 on steps 2, 6, 10, 14.
- **Pattern 2** transposes the melody by keys, gives its notes filter 24 and resonance 40,
  adds a filter lock on an empty step, keeps the drums, and puts FX 7 on step 16.
- Chain 1, 2, 2, 1. Tempo 100. Swing 4.

Registered before the session:

- **Reception.** The backup equals the built target exactly.
- **tempo_100.** Sound 13 onsets are 0.600 s apart within 5 ms.
- **swing_4.** Each Sound 9 onset follows the Sound 13 onset before it by 0.175 s within
  5 ms: one step plus 4/24 of a step.
- **melody_first_note.** The melody's first note, 784 Hz, sounds in step 1 and not in
  step 2, by at least 20 dB.

The restore lasts about 70 seconds.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/project-build-001/compiled
.\.venv\Scripts\python.exe -m scripts.check_project_build_test
```

- [Registration](../experiments/project-build-registration-001.json)
- [Build report](../experiments/project-build-001/build-report.json)

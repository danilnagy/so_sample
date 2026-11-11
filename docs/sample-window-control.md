# Sample window test

Every melodic import so far started at code 0 of its buffer. The factory state has
references with nonzero starts, but a nonzero start on a slot's own buffer is untested.
If it works, an editor can trim a sample by changing two header fields instead of
re-importing it.

A 1.0 s sample of four 0.25 s segments at 400, 500, 600 and 700 Hz goes into Sound 6 and
Sound 7. The new `set_sample_window` operation then sets Sound 6's header to segment 3
and Sound 7's to segment 2. Pattern 2 plays Sound 6 on steps 1, 5, 9 and 13 and Sound 7
on steps 3, 7, 11 and 15; at key 1 a segment lasts 166.8 ms.

Registered before the session:

- **Reception.** The backup equals the target exactly, or differs only in the two 8-byte
  windows, which is recorded as `window_rewritten_by_device`.
- **window_honoured.** Sound 6 sounds at 899 Hz and Sound 7 at 749 Hz, each 166.8 ms.
- **start_ignored.** Both play from code 0: 599 Hz in the window and notes that outlast
  the step.

You should hear two alternating short tones if the windows are honoured. The restore lasts
about a minute.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-sample-window-001
.\.venv\Scripts\python.exe -m scripts.check_sample_window_test
```

- [Registration](../experiments/sample-window-registration-001.json)

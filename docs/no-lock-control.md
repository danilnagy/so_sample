# No-lock test: does code 0 keep the last locked value?

The [resonance law test](resonance-law-results.md) suggested that code 0 means no
parameter lock: the step keeps the last nonzero value. This test checks that for filter
and resonance with designed sequences on the sawtooth kit, chaining Patterns 1 and 2:

- **Pattern 1** locks resonance to the lowest level and uses filter codes
  63, 10, 0, 0, 50, 0, 0, 63, 0, 20, 0, 56, 0, 0, 0, 63. Its 63 steps are the bypass
  references.
- **Pattern 2** locks filter 16 and uses resonance codes
  1, 56, 0, 0, 8, 0, 0, 40, 0, 24, 0, 63, 0, 0, 1, 0.

Registered before the session, over five chain cycles:

- **zero_holds_last_lock.** Every code-0 step is within 1 dB of the last nonzero step of
  its pattern.
- **zero_filter_is_off.** Every filter code-0 step is within 1 dB of the bypass.

You should hear two alternating patterns, with some steps repeating the sound before
them. The restore lasts about 3.4 minutes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-no-lock-001
.\.venv\Scripts\python.exe -m scripts.check_no_lock_test
```

- [Registration](../experiments/no-lock-registration-001.json)

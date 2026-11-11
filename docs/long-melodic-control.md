# Long melodic sample with page-rounded capacity

The melodic importer was verified only up to 1.32 s, in the device's own capacities. This
test imports a 4.0 s sample into Sound6 with a capacity of whole pages, 94208 codes. The
sample is four 1.0 s segments at 400, 500, 600 and 700 Hz, so its length and order are
audible. The total sample memory becomes 872448 codes, within the 241-page limit.

Pattern 1 gets a single Sound6 note on step 1. At 60 BPM the pattern loops every 4.0 s.
Melodic key 1 at pitch code 13 plays the stored audio 7 semitones up, so the note should
last 4.0 s / 2^(7/12) = 2669.7 ms.

Registered before the session, with a new frozen method in `scripts/long_note_method.py`:

- **Reception.** The backup must equal the compiled target exactly.
- **whole_sample_plays.** The note lasts 2669.7 ms within 10 ms.
- **quarters_in_order.** Its four quarters sound at 599, 749, 899 and 1049 Hz within
  20 cents.

The restore lasts about 3.9 minutes. You should hear one long note per loop that steps
up four times.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-long-melodic-001
.\.venv\Scripts\python.exe -m scripts.check_long_melodic_test
```

- [Registration](../experiments/long-melodic-registration-001.json)

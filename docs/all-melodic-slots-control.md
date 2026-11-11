# Imports into all eight melodic slots

So far, melodic imports have been verified in Sound6 and Sound7 only. In the source state
Sound1 owns a buffer that Sound2, Sound3 and Sound8, and drum kits Sound9 and Sound10,
borrow. This test gives every slot its own buffer:

1. Sound9 and Sound10 get small kits of their own, 16384 codes each.
2. Sound2, Sound3 and Sound8 get their own buffers. The melodic importer's new
   `replace_borrowed` option does this.
3. Sound1, now unreferenced, and Sound4 to Sound7 are replaced.

Slot s gets a 0.5 s tone at 400 * 2^(150 (s-1) / 1200) Hz in three pages. Pattern 1 plays
Sound s on step 2s-1, so the eight notes rise by 150 cents each.

Registered before the session:

- **Reception.** The backup must equal the compiled target exactly, with every melodic
  slot holding its own buffer.
- **slot_s_plays_its_tone.** Steps 2s-1 and 2s sound 150 (s-1) cents above step 1.
- **Absolute pitch.** Step 1 within 20 cents of 599.3 Hz.

The restore lasts about 3.4 minutes.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-all-melodic-slots-001
.\.venv\Scripts\python.exe -m scripts.check_all_melodic_slots_test
```

- [Registration](../experiments/all-melodic-slots-registration-001.json)

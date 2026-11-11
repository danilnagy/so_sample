# Sample import into Sound 7, played in a pattern

The public importer writes only into Sound 6, the slot its earlier hardware tests used. Its
core is now slot-generic: an empty melodic slot's sound id is slot - 1, and a self-owned
record stores that id as its owner byte, as observed for Sounds 4, 5 and 6. The public
scope stays Sound 6 until another slot has hardware evidence.

This test imports a 600 Hz, 0.3 s tone into empty Sound 7, a slot never imported before,
with a 32768-code capacity (total sample capacity 163840 codes, inside the 172032-code
calibration budget). Through the public plan path, Sound 3 plays key 1 on odd steps and
Sound 7 plays key 1 on even steps, copying Sound 3's note parameters with the new
`set_melodic_notes_from` operation.

Sound 3 plays a 750.0 Hz tone stored in Sound 1's buffer. That window plays at 1190.4 Hz
at pitch code 14, exactly 8 semitones above its stored rate, so pitch code 13 with key 1
plays stored audio 7 semitones up. Whatever that offset, the imported tone should sound
1200 log2(600 / 750) = -386.3 cents relative to Sound 3 at the same key and pitch. The
backup must equal the target exactly, including every imported code. See the
[registration](../experiments/sound7-import-registration-001.json).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-sound7-import-001
.\.venv\Scripts\python.exe -m scripts.check_sound7_import_test
```

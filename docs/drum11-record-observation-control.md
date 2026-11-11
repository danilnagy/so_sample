# How the PO-33 stores a drum recording

Drum sounds 9 to 16 play 16 slices. The existing Sound 9 slices split a 64704-code
recording into 16 consecutive windows of 4044 codes, all referencing Sound 1's buffer,
but that came from a device copy. No drum recording has been observed directly.

The person samples a 2.8-second file of 16 tone bursts at distinct pitches (400 Hz rising
by 1/8 octave per burst) into empty Sound 11, holding RECORD + key 11 while the harness
plays it into the line input. One backup is then compared cell by cell with the verified
Sound 7 import state. Registered hypotheses: one new self-owned buffer; 16 nine-byte
references from Sound 11's slice ids 40 to 55 to that buffer; 16 equal consecutive windows
starting at 0; and nothing else changed. The burst pitches let a later playback test
identify which slice holds which part of the recording. See the
[registration](../experiments/drum11-record-registration-001.json) and
[instructions](../experiments/observe-drum11-record-001/instructions.md).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw play experiments/observe-drum11-record-001/burst-source.wav
.\.venv\Scripts\python.exe -m po33_re hw run experiments/observe-drum11-record-001
.\.venv\Scripts\python.exe -m scripts.check_drum11_record_observation
```

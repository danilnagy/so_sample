# Record 16 tone bursts into drum Sound 11

Sound 11 is empty. These steps sample a 2.8-second file of 16 short tone bursts into it.

1. Connect only the computer output to the PO-33 input; unplug the PO-33 output.
2. In a terminal, run the play command below. When it asks for Enter, first hold RECORD
   and key 11 on the PO-33, then press Enter. Keep holding until playback finishes,
   then release.
3. Swap the cables (PO-33 output to the computer), then run the backup session below.
   Do not play any pattern or move knobs before the backup.

```powershell
.\.venv\Scripts\python.exe -m po33_re hw play experiments/observe-drum11-record-001/burst-source.wav
.\.venv\Scripts\python.exe -m po33_re hw run experiments/observe-drum11-record-001
```

The session prints these steps again and asks you to press Enter once the recording is done.

# Recorded Sound10 key2 changes one note byte

The physical replacement passes every preservation check with543 valid native checksums.
Normal sign-crossing decode at threshold0.0063 succeeds. Only packet7 changes:
Pattern1 auxiliary byte905 changes **10 to11** hex (16 to17 decimal). Primary0df883
remains identical. Step1/key1, every melodic note, all sample/reference records and
every other plain packet remain unchanged.

Primary retention, exact drum auxiliary11, one-byte change and packet7 predictions pass.
The alternative melodicF1 prediction fails and remains in the original report. These two
observed key values do not establish every drum key, upper-nibble meaning or general
note-parameter interpretation. The user reports "done" for the physical control;
pattern playback was not requested before capture.

- [Saved predictions](../experiments/drum10-step9-key2-predictions-001.json)
- [Measured results](../experiments/drum10-step9-key2-results-001.json)
- Capture SHA-256: `853d6d6249a98538ab4200b1067d216636b6e796044dc01bf1993c2b80061114`
- Artifact SHA-256: `d0f24bc36ccf232dd4c8e9fba5bc9afb8b46b9d997f5c81efd5c856d75cec9f9`
- Body SHA-256: `1ca3319167b14624b25a4bddf88abf4263040d2491269cb20ef188841d2955fb`

The read-only export is **experiments/exported-drum10-key2-note-001/project.json**.
Exact Sound10 primary0df883/auxiliary10 or11 pairs project recorded keys1 or2. Other
pairs remain raw. Sound10/key2 sample-reference mapping is still unverified: selecting
key2 for a note does not independently prove selector25. Its sample reference receives
no keyboard mapping or audio preview. Existing previews and all raw/source files remain
intact; report version is read-only-project-export-0.10.

The generated drum writers retain their prior key1-only scope. No key2 writer or
general key setter is introduced in this milestone. We now prioritize the larger
allocation question through [a second independent recording](sound4-allocation-control.md)
into the verified empty Sound4, retaining both recorded drum keys and every existing sample.

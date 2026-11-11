# Volume law: a measured gain table, and code 0 is not silence

The [volume law test](volume-law-control.md) was received exactly and its playback was
clean. Neither registered law holds, but the measured table is consistent in every loop
(within about 0.02 dB) and reproduces the earlier pair: 18 against 21 is -1.6 dB, and 36
against 21 is +7.0 dB.

| Volume code | 3 | 6 | 9 | 12 | 18 | 21 | 27 | 30 | 36 | 39 | 45 | 48 | 54 | 60 | 63 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dB vs code 36 | -15.4 | -14.6 | -13.3 | -11.8 | -8.6 | -7.0 | -4.0 | -2.6 | 0 | +1.2 | +3.4 | +4.4 | +6.2 | +7.2 | +7.5 |

The middle of the range runs at about 0.4 dB per code; both ends flatten. Measured at
pitch 13 on Sound 3, 50 to 90 ms into each note.

**Code 0 means "keep the previous volume".** It first played at exactly the preceding
step's level. The registered [follow-up](../experiments/volume-zero-decision-001.json)
alternated codes 63, 9, 36, 21, 54, 3, 45 and 27 with 0: every 0 step matched its
predecessor's level within 0.01 dB, across levels from -23 to 0 dB, so `hold_previous` is
supported and a fixed default is rejected. The same run reproduced the gain table within
about 0.01 dB of the first. Codes 1 to 63 set a level; 0 sets none.

See the [decision](../experiments/volume-law-decision-001.json) and
[observation](../experiments/compiled-volume-law-001/hardware-observation-001.json).
Current genuine export: `experiments/exported-volume-law-001/project.json`.

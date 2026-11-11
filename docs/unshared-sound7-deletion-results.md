# Deleting the final Sound7 owner removes its serialized buffer

The capture passes all core checks with815 native checksums using the normal0.0063
acquisition. Sound7's entire record is removed; Sound6 remains empty. No other sample
record, pattern or non-Sound7 plain packet changes.

The frame loses136 data packets and33457 encoded-body bytes, including the32768-code
buffer. It ends at156758 and its complete native body exactly equals the earlier
hardware state from before Sound6 creation. The alternative of keeping all codes
under owner6 with a changed endpoint fails. This verifies serialized record removal;
it does not measure physical RAM reclamation.

The user reported "done". Completion is recorded; specific audible checks were not
separately confirmed. Native state equality independently establishes empty Sound6/7
records and unchanged earlier sounds/patterns.

- [Preregistered models](../experiments/unshared-sound7-deletion-predictions-001.json)
- [Native comparison](../experiments/unshared-sound7-deletion-results-001.json)
- [Physical native evidence](../experiments/event-027-b-delete-unshared-sound7/native-evidence-001.json)
- [User observation](../experiments/event-027-b-delete-unshared-sound7/manual-observation.json)
- Current read-only export: `experiments/exported-unshared-sound7-deletion-001/project.json`
- Capture SHA-256: `29658f8c814a9babcfe859316a8e9313e4a6e1ef31f7d7ce2d4d4c2e56e55412`
- Artifact SHA-256: `e6c1e18bd04232af76bcf2fe4099fe4f03399a6945381d6c47d55c9a4e96d1fa`
- Native body SHA-256: `12acce04d44039abcda973f1e6590f47ac798610e40f4ef440f8322a7b3bebd0`

Six melodic/three calibrated drum previews and all31 export content hashes pass.
Both observed deletion contexts are now bounded edit-plan operations. A composed
copy, shared-owner deletion and final-owner deletion plan reproduces the prior
hardware-accepted empty-state restore WAV byte-for-byte; compiler reports remain
software-only. See [edit plans](edit-plans.md).

The next [nine-page capacity test](sound6-nine-page-control.md) adds one unused4096-code
page to the previously accepted Sound6 sample while preserving its logical window.

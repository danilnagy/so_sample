# Joint tempo 100 and swing 9 accepted

The user reported **“done and confirmed”** in response to the requested restore,
100 BPM display and same-note/slower-swung playback checks. This confirms the requested
display check; the number 100 was not separately typed. No independent swing display
or ordinary-audio timing measurement is claimed for this combination.

The capture independently decodes at threshold 0.0063 to 815 checksum-valid packets
ending at byte 156758. Its complete body and every plain packet match the public-plan
target:
`1dab085d95629db191991a089c9e4e67f56fc2a7dd571b1674fa8dbce144e551`.
Only second `0x7d5c` payload offsets 129 and 130 change, from tempo/swing 137/6 to 100/9.
All samples, patterns, sound parameters and other global bytes remain exact.

This verifies composition of the guarded tempo and swing writers on the device.
The accepted capture reproduces through the public setters in either edit order.
An inverse software edit to 137/6 exactly recovers the earlier genuine swing-6 body.
No percentage or timer-unit interpretation follows from this joint check.

The original WAV SHA-256 is
`41ecbebbaa09b5055b1cf5b2c3c6035f012da17bfde9460aa96385ac5718275a`.
Decoded artifact SHA-256 is
`506843efa4aeb08ac739e5a371e5e052ade1667b514f3831d8b79c7a9e3529a7`.
Capture channel peaks are approximately 0.1603 and 0.1555, with no clipping.
The established reduced levels remain suitable.

Immutable manual and hardware observations bind those sources, the native report and
the current read-only export. Compiler/research reports remain hardware-unverified.
`experiments/exported-joint-tempo100-swing9-001/project.json` has 31 verified content
hashes and reconstructs the entire native body exactly.

All 27 affected tests pass, including the new actual joint/inverse check and independent
selection-versus-volume probe logic. The preceding full suite passed 790 tests; this
turn adds research scripts/tests and documentation without changing production writers.

- [Hardware observation](../experiments/edited-joint-tempo100-swing9-001/hardware-observation-001.json)
- [Native results](../experiments/edited-joint-tempo100-swing9-001/hardware-recapture-results-001.json)
- [Next Sound 3 volume probe](sound3-volume-probe-control.md)

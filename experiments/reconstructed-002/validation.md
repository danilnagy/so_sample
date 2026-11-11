# Controlled hardware re-capture matches baseline

The user followed the immediate backup procedure after restoring candidate 002 and used
the same reduced recording settings as reconstructed-001. Recording SHA-256:
8f8107745ecd6473e1df17c7c5660b56352ca155de6631c98f70b4a623ba5c80.

44.1 kHz, 16-bit stereo; 11,189,933 frames; duration 253.739977 seconds. Left/right peaks
0.168457 / 0.160736 (approximately -15.5 / -15.9 dBFS), RMS 0.092293 / 0.088108.
No clipping. Peak idle noise in measured first/last 100 ms is at most 0.001221.
These levels are adequate for this path and decoder profile; no gain increase is required.
Keep capture settings consistent. This is not a general noise-tolerance specification.

At amplitude-adjusted threshold 0.0063, both channels have 1,970,367 labels and match the
baseline 002/003 labels and counts exactly. No alignment, remapping, tail trimming or
padding was used. The 0.02 threshold matches every overlapping label but misses one
terminal label per channel; threshold selection remains explicit in metadata.

This completes a local software synthesis -> manual device restore -> genuine backup
comparison for this controlled state. The user previously reported matching audible
behavior. The first post-restore comparison was confounded by possible pattern changes;
this controlled re-capture resolves transport preservation without explaining every
change in that earlier backup. No arbitrary state field, codec or sample insertion has
been verified. Repeated acceptance across other states remains future evidence.

The recording remains untouched. Derived symbols/diagnostics are in derived/validation-001/;
tracked exact comparison is comparison-summary.json. The specific generated artifact's
manual record has been updated with the controlled re-capture result.

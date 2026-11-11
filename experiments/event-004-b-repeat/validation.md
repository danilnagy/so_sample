# Populated-state repeatability validated

User supplied the requested repeat of Pattern 1, Step 1, Sound 9, slice key 1 kick state.
Recording SHA-256:
b36cd797d11e808b4481b32aef0808c978905d52466c8f2599018445a107490d.

The stereo 44.1 kHz/16-bit recording has suitable reduced levels and no detected clipping.
At explicit threshold 0.0063, both complete streams equal original event-001-b exactly:
1,970,367 labels per channel, zero differing labels, zero tails and zero alignment shifts.
No trimming or phase remapping was applied. The original WAV remains untouched.

The empty-state controls and this single populated state are reproducible despite acoustic
recording differences. Thus the widespread event-associated phase changes are repeatable
in this dataset, rather than explained by ordinary recording variation. This does not
prove any particular scrambling/encryption/compression algorithm or exclude randomness
under all other device conditions. No editable state field is identified.

Exact comparison: comparison-summary.json. Symbols and diagnostics: derived/analysis-001/.
Further work should investigate deterministic coding and framing using the fixed captures,
with this populated-state control preserved as a regression anchor.

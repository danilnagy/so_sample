# Unshared Sound4 releases backing capacity when re-recorded shorter

The untouched capture passes all control checks with 815 valid native checksums using
the normal 0.0063 acquisition. Only Sound4, selector3, changes. Its self-owned capacity
shrinks from 73728 to 32768 code bytes, and its endpoint falls from 72128 to 30912.
The new header is `00000000c078000003` (start0/end30912/owner3).

Sound5's entire independently owned header and32768-code buffer remain identical.
All other sound records, all16 patterns and every non-Sound4 plain packet also match.
There are170 fewer packets and41810 fewer encoded body bytes. The capacity-shrink
hypothesis passes; retaining the previous73728 capacity fails. The new capacity is
divisible by both4096 and8192, so this does not distinguish allocation quantum.

All three owned buffers retain the observed ordered4096-code page packet layout.
Sound4's decoded preview independently fits1500.059Hz, with a thresholded active
span around0.21seconds. Sound5 retains its exact old1000Hz window. Logical endpoint,
backing capacity and active sound duration remain distinct: manual recording timing
is not an exact counter oracle. Raw code tails remain preserved without interpretation.
The user reported "done"; specific audition results were not separately supplied.

The stereo capture peaks are0.16858/0.16144 with no clipped samples. These are consistent
with the previously successful reduced recording levels.

- [Registered predictions](../experiments/unshared-sound4-shrink-predictions-001.json)
- [Native comparison](../experiments/unshared-sound4-shrink-results-001.json)
- [Sample and packet-page analysis](../experiments/unshared-sound4-shrink-sample-analysis-001.json)
- [Workflow audit](../experiments/unshared-shrink-to-growth-workflow-validation-001.json)
- Current read-only project: `experiments/exported-unshared-shrink-001/project.json`
- Capture SHA-256: `859e6eaeee774088e16eff03c60fedb909284de0ee2231c6c025d2aedfd7bf84`
- Native body SHA-256: `160983f68b2ed012e92819643a69828ed84e4cd8fb2eab3c23c1fa2104252f04`

The next [generated growth test](sound4-generated-growth-control.md) reuses the larger
device layout while inserting a newly synthesized sample. It is confined to the
unshared Sound4 buffer; public CLI/edit-plan allocation operations remain unavailable.

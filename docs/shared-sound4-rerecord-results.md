# Shared-owner re-recording preserves the old copy by transferring ownership

The capture passes all control checks with985 valid native checksums using the normal
0.0063 crossing profile. Sound4 now owns a larger73728-code buffer, header
**00000000c019010003** (start0/end72128/owner3). Sound5 now owns the entire old32768-code
buffer, header **00000000c06f000004** (start0/end28608/owner4).

Every original sample code, including the nonzero code tail, is retained exactly in
Sound5. The used sample window is also byte-identical. Only selectors3/4 change; owner0,
all other sounds/references, every pattern and every non-Sound4/5 plain packet remain
unchanged. The full-transfer and old-window-preservation hypotheses pass; the alternative
that Sound5's unchanged reference follows the new recording fails.

Packet count grows680 to985 and native body75253 bytes, ending at198568. Sound4 has306
data packets and Sound5 has136. This demonstrates ownership transfer in the serialized
backup when this shared owner is re-recorded. It does not expose physical RAM addresses
or establish every overwrite, deletion or multi-copy policy.

- [Original predictions](../experiments/shared-sound4-rerecord-predictions-001.json)
- [Measured ownership result](../experiments/shared-sound4-rerecord-results-001.json)
- [Sample and ordered packet analysis](../experiments/shared-sound4-sample-analysis-002.json)
- [User observation](../experiments/event-024-b-rerecord-shared-sound4/manual-observation.json)
- Capture SHA-256: `5dca9a554b76bb538cf6a24deb5fdc707893730f6bea5519c76f5106342cb057`
- Artifact SHA-256: `b1f5f51d82f861c472f07763137c466c4da986ec244c986425d3af1279bd8f4d`
- Body SHA-256: `be92460f9d8014d92b54c1e6baf2a6fcdb29c8cad37a2f1d6f25cda3e69364b2`

The decoded Sound4 preview independently fits1250.043Hz with99.94% single-sine explained
variance and a thresholded active span around1.91seconds. Retained Sound5 fits1000.033Hz
and its prior sample window is exact. These are raw-code/nominal-rate preview measurements,
not a device playback recording. The user reports "done and confirmed"; a specific
Sound5 audition classification was not separately supplied.

The73728-code buffer is not a power of two. Its capacity is18 blocks of4096 codes.
All three current self-owned buffers match this ordered packet model: the first
header+4096-code page is sixteen255-byte payloads followed by25 bytes; subsequent
4096-code pages are sixteen255-byte payloads followed by16 bytes. This is a packetization
observation, not an allocation-rounding rule. The earlier analysis001 tried the remainder
packet at the start of each page and failed the ordering comparison; that report is
retained. Analysis002 records the corrected order observed in every complete sequence.

Buffer capacity, logical endpoint and audible duration remain distinct. Sound4 has1600
codes after its endpoint,1399 nonzero code bytes; Sound5 retains its full original tail.
These raw bytes are preserved without interpretation or zero normalization.

The current export is **experiments/exported-shared-owner-growth-001/project.json**,
with independent owners0/3/4, six melodic/three drum previews, every pattern and all
raw/source data. Sound4 exports147719FLOAT frames at48kHz; Sound5 exports58590.
Export/sample-analysis reports remain software-only and no allocator/resizing writer
is introduced.

Only Sound4 now refers to owner3. The next [shorter unshared re-recording](unshared-sound4-shrink-control.md)
tests whether capacity shrinks or stays allocated while the endpoint reduces, retaining
Sound5's independently owned old sample and all unrelated state.

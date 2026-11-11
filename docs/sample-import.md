# Import an ordinary PCM WAV into Sound6

`import-sample` creates a restore WAV from an existing decoded backup and an ordinary
audio file. It is a bounded prototype for empty or unshared, zero-start melodic Sound6.
Other slots, shared owners and unknown source layouts are rejected. Existing samples,
patterns and opaque slot/global parameters are preserved.

```powershell
.\.venv\Scripts\python.exe -m po33_re import-sample experiments/edited-sound6-one-page-import-001/derived/analysis-001/capture.symbols.npz experiments/calibration-mono-WAV-import-001/chirp-300-to-1800hz-0p75s-mono.wav --sound 6 --out-dir experiments/example-mono-import-001
```

The output directory must be fresh. The original artifact and input are never modified.
Output includes `restore.wav`, an unpitched 48 kHz `preview.wav`, the original source
artifact/input WAV copies, edited/redecoded phase artifacts and `import-report.json`.
Reports bind all input/target hashes and check every native checksum, strict phase
roundtrip, complete target-body equality and all unrelated sample/pattern preservation.
Every compilation remains `hardware_verified:false` until a separate manual test.

| Input/option | Behavior |
| --- | --- |
| Integer PCM WAV at 44,100 or 48,000 Hz | PCM_U8/16/24/32 accepted; compressed and floating WAV rejected |
| Mono | Imported directly; `--channel right` rejected |
| Identical stereo | Left imported automatically |
| Different stereo channels | Requires explicit `--channel left`, `right` or `mix`; mix is the channel mean |
| Native length | 2,344 to 30,912 samples, about 0.1 to 1.319 seconds at a nominal 23,437.5 Hz |
| Capacity omitted | Smallest verified 4,096/32,768/36,864-code size that fits; it does not round to untested intermediate capacities |
| `--capacity` | Explicit 4,096, 32,768 or 36,864, large enough for the input |
| Memory budget | Total serialized backing capacity must remain within the currently observed 172,032-code calibration budget |

This budget is not a device memory-limit claim: it is the most this importer had been
calibrated against. The device's own limit, measured later, is 241 pages of 4,096 codes
(987,136 codes; [format reference](format-reference.md)). The new header uses start 0, the exact
resampled frame count as endpoint and self-owner 5. Known 4,096-code page packetization
is retained; all remaining capacity is zero padded. Source Sound6 must be empty or
self-owned with a recognized capacity and a window inside the same calibrated range.
No other record may refer to owner 5. Existing full backing owners must have recognizable
zero-start/self-owned page layouts for the capacity accounting.

44.1k resampling uses 625/1176; 48 kHz uses 125/256. There is no gain normalization. Inputs
that produce resampling peaks outside [-1, 1] are rejected with a request to lower the
source level. Existing device pitch, filter and gain settings remain opaque and are
preserved; the preview uses the nominal codec rate without applying those settings.

The software replay at **experiments/compiled-one-page-WAV-import-001/restore.wav**
equals the hardware-accepted 100 ms stereo 48 kHz import WAV byte-for-byte, SHA-256
`f8736ed60f4206b9b08ee2d1c209e6797f2c8bb955c33247b876d951e37f20eb`.
Both empty-source creation and occupied-source replacement independently reproduce
the genuine target body in tests. See [hardware results](sound6-one-page-import-results.md).
Other duration/channel/rate combinations use the same bounded format policy but need
appropriate hardware evidence. The [mono 44.1 kHz chirp](sound6-mono-WAV-import-results.md)
now also matches its genuine hardware recapture exactly, including its longer
17,579-code endpoint. Copying this imported sample from Sound6 to empty Sound7 is
now also [hardware verified](imported-sound6-to7-copy-results.md) and supported through
bounded edit plans. Other endpoints and capacities remain outside the copy guard;
shared Sound6 deletion at this endpoint is also
[hardware verified](imported-shared-sound6-deletion-results.md). Sound7 last-owner
deletion at this endpoint is now also
[hardware verified](imported-unshared-sound7-deletion-results.md). The complete bounded
copy/transfer/removal cycle recovers the independently genuine earlier state.

This command does not make the read-only project JSON writable and does not provide
arbitrary allocation, shared-owner replacement, drum import or a graphical editor.

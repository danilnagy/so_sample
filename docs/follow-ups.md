# Follow-ups

The project is complete for its first release (2026-11-11): the format is decoded and
verified, the web app is live at [sosample.com](https://sosample.com), and the repository
is public. Nothing here blocks anything. These are the open questions, known rough edges
and ideas worth picking up later, each with where it stands and what would settle it.

Hardware items follow the usual rules ([hardware sessions](hardware-sessions.md)): a
registered session with predictions written down first, prepared by tracked
`scripts/prepare_*` scripts.

## Format questions

- **Note timing under swing at other tempos.** The preview's rule that a swung note's time
  ends on the unswung grid (a delayed melodic note loses the delay; a delayed drum step
  plays only the repeats before the next grid line) was fitted to one session at 120 BPM,
  swing 12, after all six registered rules failed ([aux nibble 3](aux-nibble-3-results.md)).
  A registered session at another tempo and swing value, predicting from that rule, would
  settle it.
- **Retriggers and voices beyond the tested case.** Repeats re-strike one voice
  ([aux nibble 2](aux-nibble-2-results.md)), tested with a 4-fold retrigger on one drum
  against melodic notes holding the other voices. Drum against drum, other counts, and the
  interplay with voice priority were not tested.
- **Timing with the punch-in effects.** Read only as exploratory: FX 13 stretched a 2-step
  melodic note to 0.67 s, FX 14 replayed retriggered bursts whole. The preview does not
  model timing under effects.
- **Global bytes 131 to 146.** Stored, with no audible effect on a single-pattern chain;
  their reading as per-pattern stop steps remains a hypothesis
  ([stray bits](stray-bits-results.md)). A multi-pattern chain session would test it.
- **The device's cut.** The preview fades a cut note or repeat over 4 ms; how the device
  ends one was not measured.

## The app

- **Undo, second round.** The first version keeps one in-memory history for the open
  project. Deferred: naming each step ("Undid: Paint filter"), a history per project kept
  across switches, and undo for deleting samples, kits and projects (a short-lived "Undo"
  in the toast).
- **Single-sound transfers.** Send one sample to the device without replacing the whole
  project, as [libpo](https://github.com/ericlewis/libpo) has shown a restore holding one
  sound does ([prior art](prior-art.md)). It would need its own registered session before
  the app offers it.
- **Updated presets for existing users.** A library keeps its copy of a bundled project
  once it has one (judged by identity, not content), so improvements such as Late Shift's
  retriggered hat roll reach new libraries only. Offering an update would be a deliberate,
  opt-in action ([release](release.md)).
- **Other browsers and interfaces.** Send and Import were verified on the device with
  Chrome and one audio interface ([browser transfer](browser-transfer-results.md)); Safari
  and Firefox were not tested.
- **Ideas from similar tools** ([prior art](prior-art.md)): transient auto-slicing of a
  long sample into a kit, and a lo-fi preview of how a sample will sound on the device.
- **Accounts and cloud backup.** Phase 6 of the [proposal](web-app-proposal.md); the local
  library's records are already shaped to be the sync unit.

## Sounds

- **The synthesized rimshot ignores its machine.** The rim recipe in
  [drum-synth.ts](../web/scripts/drum-synth.ts) uses no machine character, so every kit's
  rimshot is byte-identical and the shared library sample carries one machine's name
  ("Synth 505 Rim" in the 808 kit). Shaping it per machine means rebuilding the presets
  (`npm run presets`), which existing libraries would not pick up (see above).
- **A controlled comparison with the originals.** The kits were auditioned and accepted,
  not matched against the TR machines ([sound synthesis](sound-synthesis.md)).

## The research toolkit

- **Decoding robustness.** Backups sometimes fail at the default detection threshold of
  0.0063 and decode at 0.01 (aux-nibble-001), or need another recording after a cut-off
  or echoing capture (kit-sharing-001, browser-transfer-001). The harness could try a
  short list of thresholds itself and say which it used, instead of a manual `reanalyze`.
- **Tooling seen elsewhere:** a frame diff, a read-back check against a target, and a
  "capture doctor" for bad recordings (libpo).
- **PO-133.** libpo reports the same frames decode from a PO-133; nothing here was tested on
  one.
- **Dated CLI help.** `python -m po33_re --help` still calls the package "experimental" and
  several commands "experimental" from before the format was decoded; a pass over the help
  text, and a `scripts/README.md` explaining the prepare/check/finalize convention for the
  research scripts (nearly 400), would help newcomers.

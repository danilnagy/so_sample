# Isolate the copy to Sound2

The latest capture includes three user-reported operations: delete Sound8, copy Sound1
back to8, then copy8 to2. It preserves the shared region and matches the previous inline
window, but these extra operations prevent labeling it a clean single-copy validation.
Keep that original and its history; no data is discarded or silently treated as the
requested protocol. The new pair below records the actual recovered before-state.

1. **Delete only Sound2:** select it with **sound + 2**, release those buttons, then hold
   **record** and press **sound**. Sound1 and Sound8 remain the retained reference sounds.
2. Select **Sound8** using **sound + 8**. Keep **Pattern1 empty**, write mode off and
   playback stopped, with all other controls and recording settings unchanged.
3. Record one complete stereo dump as **experiments/empty-001-copy2-clean-a/capture.wav**.
4. **Copy into Sound2:** with Sound8 selected, hold **write + sound** and press **2**,
   then release. Reselect Sound8 and keep the same capture state/settings.
5. Record the second complete dump as **experiments/empty-001-copy2-clean-b/capture.wav**.

These are the delete-selected-sound and copy-selected-sound operations from the
[official guide](https://teenage.engineering/guides/po-33/en). Leave slots1/2/8 populated
afterward. No fresh analogue tone recording or full reset is needed for this pair.
Report any deviation; the fresh before-state is not assumed identical to the old C.

Predictions remain the original two location windows and unchanged Tone-region anchors,
saved separately before either clean capture in clean-copy2-predictions-001.json. The
new before-state must first preserve the reference prefix through177085 and the six
anchor values. If its geometry differs, original absolute-position predictions are
inapplicable, not silently shifted. Relative growth is tested independently within0..128
complete labels per channel; partial endpoint intervals are reported separately.

Completed: both captures were supplied with user confirmation and no reported deviation.
See [results](clean-copy2-results.md) for the unchanged prediction evaluation and
[next control](third-copy-control.md) for the single Sound3 copy capture.

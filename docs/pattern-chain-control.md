# Observe a pattern chain

The device can chain patterns: holding PATTERN and pressing several pattern keys plays
them in turn. Where the chain is stored is unknown. This observation records it.

The harness first plays the verified [selected-pattern](selected-pattern-results.md)
restore, so the device starts from a known state: Pattern 1 rises, Pattern 5 falls, and
Pattern 5 is selected. After the restore, the harness shows these steps:

1. Hold PATTERN.
2. While holding it, press key 1, then key 5.
3. Release PATTERN.

Don't press play before the backup. The harness records playback after the backup.

Registered before the backup:

- **chain_in_global_record_only.** Only bytes of the two global records change.
- **chain_1_5.** Playback alternates Pattern 1 then Pattern 5 from the first loop.
- **chain_5_1.** Playback alternates Pattern 5 then Pattern 1.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/observe-pattern-chain-001
.\.venv\Scripts\python.exe -m scripts.check_pattern_chain_observation
```

- [Registration](../experiments/pattern-chain-registration-001.json)

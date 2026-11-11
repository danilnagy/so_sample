# Chain writer test

From the verified [selected-pattern](selected-pattern-results.md) state, the plan path's
new `set_pattern_chain` operation writes the chain 5, 1, 1. Pattern 1 rises and Pattern 5
falls. **Press only play.**

Registered before the session, each checked over five loops:

- **chain_5_1_1:** falling, rising, rising, falling, rising.
- **first_entry_only:** falling every loop.
- **two_entries_alternate:** falling, rising, falling, rising, falling.

A model holds when at least 4 of 5 loops match it on all 16 steps within 20 cents. The
backup must equal the compiled target exactly.

Run:

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/compiled-chain-writer-001
.\.venv\Scripts\python.exe -m scripts.check_chain_writer_test
```

- [Registration](../experiments/chain-writer-registration-001.json)

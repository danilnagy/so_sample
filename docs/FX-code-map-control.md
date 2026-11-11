# Effect code map: what each FX key stores

The footer layout is known: byte k holds steps 2k+1 (high nibble) and 2k+2 (low
nibble). Three codes are known: FX key 7 stores 6, key 8 stores 7, and clearing stores F.
That suggests code = key - 1. This device-side control maps all fifteen keys at once.

Starting from the verified position-map state, where patterns 2 to 16 are empty, the
person records FX key N into pattern N+1 for N = 1 to 15, then takes one backup. Keys 7
and 8 act as controls. The prediction, registered before the backup, is that each
pattern's footer holds only code N - 1. A key maps to a code when its pattern holds
exactly one non-F code; shorter holds simply cover fewer steps. Any other change is
listed, not interpreted. See the
[registration](../experiments/FX-code-map-registration-001.json) and
[step-by-step instructions](../experiments/observe-FX-code-map-001/instructions.md).

```powershell
.\.venv\Scripts\python.exe -m po33_re hw run experiments/observe-FX-code-map-001
.\.venv\Scripts\python.exe -m scripts.check_fx_code_map
```

This maps stored codes only. What each effect sounds like is not measured here.

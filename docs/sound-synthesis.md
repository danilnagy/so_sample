# Sound synthesis: how the bundled sounds are made

Every sound the app ships (the seven drum kits and the chords, basses and leads of the
ten projects) is synthesized from oscillators and seeded noise by scripts in
`web/scripts/`. No recorded audio is involved, so all of it is covered by the project's
MIT licence. This page documents the approach and every recipe, as a reference for
rebuilding, tuning or reusing them.

| File | Holds |
| --- | --- |
| [`drum-synth.ts`](../web/scripts/drum-synth.ts) | The drum voices and the six machine characters |
| [`kit-tools.ts`](../web/scripts/kit-tools.ts) | The seven kits' key layouts and length caps, and the kit builder |
| [`pack-tools.ts`](../web/scripts/pack-tools.ts) | The shared building blocks and most melodic instruments |
| [`make-more-packs.ts`](../web/scripts/make-more-packs.ts) | Bell, reese bass, melodica, techno stab, dark pad |
| [`make-italo-pack.ts`](../web/scripts/make-italo-pack.ts) | Saw bass and square lead, the sustained instruments of Afterglow |
| [`make-lofi-packs.ts`](../web/scripts/make-lofi-packs.ts), [`make-genre-packs.ts`](../web/scripts/make-genre-packs.ts) | The songs that use them |
| [`build-presets.ts`](../web/scripts/build-presets.ts) | Builds and checks everything into `web/src/presets` |

`cd web && npm run presets` rebuilds the lot.

## Principles

These follow from the PO-33 itself and apply to any sound made for it.

- **Synthesize at the device's rate.** The PO-33 stores 8-bit mu-law codes at 23,437.5 Hz
  ([format reference](format-reference.md)). Every generator runs at that rate, so nothing
  is resampled and nothing above 11.7 kHz is generated: band-limited oscillators stop their
  harmonics at the Nyquist limit (`saw` caps at 40 harmonics or Nyquist).
- **Fill the mu-law range, with headroom.** Mu-law has fine steps near zero and coarse ones
  near full scale, so a sound normalized to a high peak keeps its quiet tail detailed.
  Drums peak at 0.89; melodic sounds go through `finish`, which normalizes and soft-clips
  with `tanh` to a target peak of 0.8 to 0.9.
- **Spend memory where it is heard.** The device holds 241 pages of 4,096 codes (about 42 s)
  for all sixteen sounds. Each drum key has a length cap (below), each hit ends where it
  decays under -54 dB if that comes sooner, and every cut ends with a short linear fade, so
  no hit clicks when it is cut.
- **Respect the four voices.** The PO-33 plays four notes at once and never cuts a sounding
  note ([web playback](web-playback.md)). A long tail holds a voice, so the caps also keep
  busy patterns from dropping notes; the build plays every pattern through the app's engine
  and fails if any note would drop.
- **Bake timbre, lock colour.** A sample is a neutral source. Volume, filter and resonance
  that suit a style are written as parameter locks on the notes, so the same Rhodes chord
  serves lofi and soul, and the device's own filter does the sweeping.
- **One sample, many pitches.** A melodic sample is played across the keys, each key a fixed
  transposition. A chord type is one sample, and the progression comes from the keys
  (below).
- **Deterministic.** Noise comes from a linear congruential generator with a fixed seed
  (`rng` in `pack-tools.ts`; `noise` in `drum-synth.ts`, seeded from the hit's name), so a
  build writes the same codes every time and a changed sound is a deliberate change.

## Building blocks

| Block | Where | What it does |
| --- | --- | --- |
| `rng(seed)`, `noise(n, seed)` | pack-tools, drum-synth | Deterministic white noise from a linear congruential generator (multiplier 1664525, increment 1013904223) |
| `lowpass(x, hz)`, `highpass(x, hz)` | pack-tools | One-pole filters: the high-pass is the input minus its low-pass |
| `bandPass(x, hz, q)` | drum-synth | A two-pole band-pass (RBJ cookbook, constant peak gain) |
| `highPass(x, hz)` | drum-synth | A one-pole RC high-pass |
| `saw(hz, n, detune)` | pack-tools | A band-limited sawtooth: harmonics h = 1 to 40 (or Nyquist) at 1/h |
| `fallingSine(s, from, to, fall, ring, drive)` | drum-synth | A sine gliding exponentially from `from` to `to` Hz with time constant `fall`, decaying with time constant `ring`, optionally driven through `tanh` |
| `metal(n, scale)` | drum-synth | Six square waves at 205.3, 304.4, 369.6, 522.7, 540 and 800 Hz times `scale`, summed: the 808's metal, the source of every hat and cymbal |
| `squarePair(n, a, b)` | drum-synth | Two square waves, the cowbell |
| `shaped(x, ring, attack)` | drum-synth | Exponential decay with an optional linear attack |
| `finish(x, peak, fade)` | pack-tools | Normalize, soft-clip with `tanh`, fade out the last `fade` seconds |
| `normalized(x, peak)` | drum-synth | Normalize to a peak |
| `vinyl(n, seed, clicks, floor)` | pack-tools | Low-passed noise floor plus sparse decaying clicks, for lofi texture |
| `trimmedLength(x, cap)` | drum-synth | Where a hit falls below 0.002 (-54 dB), at most the cap, at least 20 ms |

Envelopes throughout are exponential decays, `exp(-t / tau)`, with linear attacks of 1.5 to
30 ms. Time constants below are these `tau` values in seconds.

## Drums

### How a kit is voiced

A kit is a key layout shared by all seven kits ([presets](presets.md#kits)): 1 kick, 2 kick
2, 3 snare, 4 snare 2, 5 rimshot, 6 clap, 7 closed hat, 8 closed hat 2, 9 open hat, 10 open
hat 2, 11 crash, 12 ride, 13 low tom, 14 mid tom, 15 high tom, 16 percussion. Each key in
`kit-tools.ts` names the TR-series sample it stands for ("TR-808 Low Conga 01"), and
`synthHit` chooses the voice from that name:

1. The **voice** comes from words in the name, checked in this order: `808s` or `BD Long`
   (the 808 bass), `kick`/`BD`, `snare`/`SD`, `rim`, `clap`, `open hat`, `hat`, `ride`,
   `crash`/`cymbal`, `cowbell`, `conga`, `clave`, `maraca`/`shaker`, `tambourine`, `tom`.
   Anything else becomes a short tonal hit.
2. The **variant** is the number at the end of the name: "01" is variant 0, "02" variant 1,
   and so on (modulo 4). A variant nudges pitch and decay so a kit's two kicks or two hats
   differ.
3. The **machine's character** sets the voice's parameters (next section).
4. The hit is normalized to 0.89, trimmed where it decays below -54 dB or at its key's cap,
   faded over the last 40 ms and encoded to mu-law.

Length caps by key, in seconds: kick 0.5, kick 2 0.6, snares 0.3, rimshot 0.15, clap 0.3,
closed hats 0.15, open hats 0.5, crash 0.9, ride 0.7, low tom 0.35, mid and high toms 0.3,
percussion 0.25. A synthesized kit stores 27 to 36 pages (`npx tsx scripts/make-kits.ts <folder>` prints each).

### Machine characters

| Machine | Kick: from → to Hz, fall, ring, drive, click | Snare: tone Hz, ring, noise share, band Hz | Hats: metal scale, noise, band Hz | Toms: low Hz, ring | Tightness |
| --- | --- | --- | --- | --- | --- |
| 505 | 150 → 56, 0.03, 0.16, 1.6, 0.15 | 210, 0.09, 0.6, 4000 | 1.25, 0.5, 7500 | 110, 0.16 | 0.8 |
| 606 | 140 → 62, 0.025, 0.13, 1.2, 0.10 | 230, 0.07, 0.75, 4500 | 1.1, 0.3, 7000 | 120, 0.14 | 0.85 |
| 626 | 160 → 54, 0.03, 0.18, 1.5, 0.15 | 200, 0.10, 0.6, 4200 | 1.2, 0.5, 7200 | 100, 0.18 | 0.85 |
| 707 | 170 → 55, 0.03, 0.20, 1.4, 0.20 | 190, 0.10, 0.55, 4000 | 1.15, 0.55, 7000 | 95, 0.20 | 0.9 |
| 808 | 110 → 48, 0.04, 0.32, 1.0, 0.04 | 180, 0.12, 0.42, 3500 | 1.0, 0.1, 6500 | 85, 0.26 | 1 |
| 909 | 230 → 52, 0.02, 0.24, 1.8, 0.35 | 190, 0.10, 0.68, 5000 | 1.3, 0.65, 8000 | 90, 0.22 | 1 |

The shape of each: the 808 is round and long (a pure sine kick, a tonal snare, pure metal
hats); the 909 is punchy and bright (a fast, high pitch drop, a strong click, a noisy snare,
hats with noise beside the metal); the 606 is thin and short; the 505, 626 and 707 are the
digital machines, a little driven and shorter (tightness scales the decays of the snare's
noise, the clap, hats, cymbals, cowbell and congas). Two kits share the 808 character:
Synth 808 and Synth 808 Percussion.

### The voices

| Voice | Recipe |
| --- | --- |
| Kick | `fallingSine(from → to, fall, ring, drive)`, plus a 4 ms burst of noise high-passed at 1.5 kHz (the click). Variants start 12% higher, end 5% lower and ring 25% longer. |
| 808 bass | `fallingSine(95 → 44 Hz, fall 0.03, ring 0.6)`; each variant ends 3 Hz higher and drives harder. Also the melodic 808 that Late Shift plays across the keys. |
| Snare | Two falling sines (tone × 1.3 falling to the tone, and tone × 1.9 to × 1.75) for the drum's body, mixed with noise band-passed at the character's band and high-passed at 900 Hz for the wires, in the character's noise share. |
| Rimshot | Sines at 1.7 kHz and 520 Hz, very short (ring 12 and 20 ms), high-passed at 300 Hz. |
| Clap | Noise under an envelope of three 6 ms bursts 11 ms apart, then a tail (ring 60 ms), band-passed at 1.1 kHz, Q 1.2. |
| Closed hat | `metal` band-passed at the character's band, high-passed at 5 kHz, plus noise high-passed at 6 kHz in the character's share; ring 22 ms (longer per variant). |
| Open hat | The same, ring 120 ms. |
| Crash | `metal` high-passed at 3.5 kHz and noise at 4 kHz, equal parts, ring 350 ms. |
| Ride | `metal` at 1.5 × scale high-passed at 3 kHz (ring 350 ms), a bell of two sines at 640 and 960 Hz × scale, and a little noise above 7 kHz. |
| Low, mid, high tom | A sine falling from 1.6 × its pitch, plus a 20 ms noise thump band-passed at 4 × the pitch. Pitches step by 1.33 from the character's low tom; the name's Lo/Mid/Hi decides the step where it says, else the key does (13 low, 14 mid, 15 high). |
| Cowbell | `squarePair(540, 800 Hz)` band-passed at 2.6 kHz, ring 60 ms. |
| Congas | A sine falling from 1.4 × its pitch to 165 (low), 250 (mid) or 340 Hz (high), ring 90 ms. |
| Clave | A 2.5 kHz sine, ring 18 ms. |
| Maraca, shaker | Noise high-passed at 6.5 kHz, ring 18 ms (maraca) or 35 ms (shaker), 4 ms attack. |
| Tambourine | `metal` at 2.2 × high-passed at 6 kHz (ring 60 ms) and noise above 8 kHz (ring 80 ms). |

The recipes are the classic analog ones (the 808's bridged-T drums, six-oscillator metal and
filtered noise), simplified: no resonant filters, no circuit modelling.

## Melodic instruments

Melodic samples are rendered at a fixed MIDI pitch and length, and `finish`ed. Chords are
summed voices of the same instrument.

| Instrument | Recipe | Used for |
| --- | --- | --- |
| `epNote` | Four decaying sine partials (ratios 1, 2, 3, 5.04 at 1, 0.28, 0.07, 0.05; tau 1.3, 0.5, 0.35, 0.12 s) plus a second fundamental detuned by 0.4 Hz for a slow chorus; 4 ms attack | The Rhodes |
| `rhodesChord` | `epNote` per voice, each lower voice 8% quieter, low-passed at 5.2 kHz, with vinyl (6 clicks/s) | Lofi and soul chords |
| `rhodesLead` | One `epNote`, low-passed at 6 kHz, light vinyl | Lofi melodies |
| `organChord` | Drawbar sines (ratios 1, 2, 3, 4, 6, 8 at 1, 0.7, 0.45, 0.3, 0.12, 0.08), a 5.8 Hz tremolo of 10%, decay 1.6 s, low-passed at 4.2 kHz, vinyl | Soul and dub chords, dub skanks |
| `pianoStab` | Up to 12 harmonics with slight inharmonic stretch (1 + 0.0004 h²), each decaying faster the higher it is, a 6 ms noise hammer; band 120 Hz to 9 kHz | House chords |
| `stringPad` | Three sawtooths per voice detuned by ±0.6%, two low-passes at 2.6 kHz, 30 ms swell, decay 2.5 s | Detroit pads; Afterglow's pad, gated by note lengths |
| `darkPad` | `stringPad` low-passed again at 1.4 kHz | Trap pads |
| `brassStab` | Sawtooths detuned 0.3%, crossfading from a 4.2 kHz low-pass to a 1.2 kHz one over 150 ms, decay 0.5 s | Soul brass, the techno stab (`technoStab`) |
| `subBass` | A sine with a plucked second harmonic (decay 0.15 s), decay 0.5 s, low-passed at 1.8 kHz | Lofi, soul, dub bass |
| `houseBass` | A sawtooth crossfading from a 1.4 kHz low-pass to 300 Hz over 80 ms, decay 0.35 s | House and techno bass |
| `reeseBass` | Two sawtooths detuned ±0.4%, beating slowly, two low-passes at 900 Hz, decay 1.2 s | Jungle |
| `bleep` | A sine with 20% second harmonic, decay 0.3 s | Detroit and techno hooks |
| `bell` | A sine (decay 0.9 s), an inharmonic partial at 2.76 × (decay 0.25 s) and the octave (decay 0.5 s) | Trap melodies |
| `melodica` | Odd harmonics 1, 3, 5, 7 at 1/h (a soft square), a 5.5 Hz vibrato of 0.4% fading in over 300 ms, low-passed at 3.2 kHz | Dub lines |
| `synthBass` | A sawtooth and its octave below (70/30), 4 ms attack, a slow decay (2 s), two low-passes at 900 Hz and 1.8 kHz; it sustains, so note lengths set its rhythm | Italo octave bass |
| `synthLead` | Odd harmonics 1 to 9 at 1/h (a square), a 5 Hz vibrato of 0.3% fading in over 400 ms, a slow decay (3 s), low-passed at 3 kHz; it sustains | Italo arpeggio |

### Chords and keys

A melodic sound plays its sample at one of sixteen fixed transpositions. Key 5 plays the
sample as recorded, and the keys cover, in semitones from key 5:

| Keys 1 to 4 | Keys 5 to 8 | Keys 9 to 12 | Keys 13 to 16 |
| --- | --- | --- | --- |
| +7, +8, +10, +11 | 0, +2, +3, +5 | -5, -4, -2, -1 | -12, -10, -9, -7 |

(the [format reference](format-reference.md) gives the same layout from key 1). A pack
renders one sample per chord type (a min7, a dom7, a maj7 voicing) and plays each chord of
the progression at the key that transposes it to that chord's root, so two minor chords a
fourth apart are one sample at two keys. `mustKey(semitones)` finds the
key and fails the build if no key reaches that transposition, which is why voicings are
chosen with their roots in mind. A transposition by key also changes the sample's speed, so
a chord played an octave down lasts twice as long.

## From synthesis to the device

1. Generate at 23,437.5 Hz as floating point in -1..1.
2. Normalize (`finish` or `normalized`); for drums, trim at -54 dB or the key's cap.
3. Fade the last 40 ms (drums) or 20 to 80 ms (melodic) linearly to zero.
4. Encode to mu-law codes (`encodeMulaw` in `web/src/core/mulaw.ts`; code 255 is never
   emitted).
5. Pack into a kit or project archive ([archive format](archive-format.md)): one sample per
   distinct sound, shared by every kit and project that uses it.
6. Check: `build-presets.ts` compiles every project, fails if it exceeds 241 pages, and
   plays every pattern through the app's own playback engine, failing if any note would
   drop for want of a voice.

## Reusing this elsewhere

- `drum-synth.ts` is self-contained: its only import is the sample rate. Change `RATE` and
  it renders for any device; the time constants are in seconds and the frequencies in Hz,
  so they carry over. `synthHit(machine, name, key, seconds)` is the entry point; a new
  machine is one more entry in `CHARACTERS`.
- The melodic instruments need only `pack-tools.ts`'s building blocks and `midiHz`.
- For a different memory budget, change the caps in `kit-tools.ts`; the trim keeps short
  hits short whatever the cap.
- For a device with more voices or one that cuts notes, the length caps can be relaxed.
- The drum settings come from the classic designs. They were checked by measurement
  (length, peak, loudness and dominant frequency of every hit), then auditioned in the app
  and accepted for the first release on 2026-11-11; they have not been matched against the
  original machines in a controlled comparison. The build checks numbers (voices, pages),
  not taste, so audition any change: `make-kits.ts` writes the kits alone for that, and
  tuning a machine is a matter of editing its row in `CHARACTERS`.

## What is approximate

- One-pole filters are gentle (6 dB per octave); the originals' resonant filters are not
  modelled.
- The `metal` oscillators are naive square waves, so they alias a little above the band;
  at this sample rate the band-pass and high-pass keep it out of the way.
- Envelopes are single exponentials; real analog decays have more shape.
- The clap's bursts and the hats' decays are fixed per machine, not per variant beyond the
  small nudges listed.

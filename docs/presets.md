# The kits and projects the app comes with

The app comes with seven standard drum kits and ten complete projects, bundled into the
build. Whenever the app loads it adds any of them the library lacks, so every user has
all of them from the first launch on, as ordinary local kits and projects: edited,
renamed, copied and exported like any other. Each record keeps the identity of the
bundled kit or project it came from, so a renamed one still counts as present, a copy is
the user's own, and a deleted one comes back on the next load. Every project fits the
PO-33 and never asks for more than its four voices at once.

## Kits

One kit per TR-series machine, all on the same key layout, so a pattern written for one
plays sensibly on another: 1 kick, 2 kick 2, 3 snare, 4 snare 2, 5 rimshot, 6 clap, 7
closed hat, 8 closed hat 2, 9 open hat, 10 open hat 2, 11 crash, 12 ride, 13 low tom, 14
mid tom, 15 high tom, 16 percussion. Keys a machine cannot fill stay empty; where a
machine offers a near fit it is used (the 626 puts its shaker on key 8 and tambourine on
10, the 808 Percussion kit holds congas, claves, maracas and cowbell). Each hit is cut at
its key's cap, kicks keeping their body and cymbals getting the most, so a kit stores
near 30 of the device's pages. The kits are Synth 505, Synth 606, Synth 626, Synth 707,
Synth 808, Synth 808 Percussion and Synth 909, with samples in a library folder named
after the machine.

The hits are synthesized ([`scripts/drum-synth.ts`](../web/scripts/drum-synth.ts); every
recipe is in [sound synthesis](sound-synthesis.md)), so the kits are free to use and
redistribute. Each key mirrors the hit it replaces in the
TR-series kit layout: the synthesizer picks the voice from the original sample's name (a
"Low Conga 01" becomes a low conga, an "02" a variation of the first) and shapes it with
its machine's character, from the 808's long sine kick and tonal snare to the 909's
clicky kick and noisy snare and the shorter, brighter 505, 626 and 707. The recipes are
the classic analog ones: decaying sines with falling pitch for kicks, toms and congas, six
detuned square waves for the metal of hats and cymbals, band-passed noise for snares,
hats and claps. A kit keeps its identity (`tr-808` and so on) whichever way it was
built, so a library holding one form is not sent the other.

The projects' drum sounds are these kits: a project loads a standard kit on each of its
drum sounds 11 to 14 and plays one role from each (kicks, snares, hats, percussion),
since a sound plays one key per step. A hit is therefore one library sample, however many
kits and projects use it: after the first launch the library holds about 150 samples,
and the Synth 808 folder holds every 808 hit in use, shared by all.

## Projects

| Pack | Style | Key and feel | Kits (11 to 14) | Tempo | Bars | Pages |
| --- | --- | --- | --- | --- | --- | --- |
| Rainy Rhodes | lofi | F major, ii V I vi, melody section, IV turnaround | 808, 707, 626, 808 Percussion | 84, swing 7 | 28 | 174 |
| Night Walk | lofi | D minor, half-time i iv VI V, melody section | 909, 909, 808, 808 Percussion | 76, swing 9 | 20 | 138 |
| Corner Store | soul boom bap | A minor, Am9 Dm9 Fmaj7 E7, organ chops and brass stabs | 808, 909, 707, 626 | 92, swing 9 | 20 | 158 |
| Afterglow | italo disco | A minor, Am F C G; a sustained pad gated by note lengths, an octave bass of one-step notes, a staccato arpeggio with held phrase ends | 707, 808, 707 | 118 | 24 | 107 |
| Warehouse Jack | Chicago house | A minor, piano stabs over an offbeat bass, breakdown | 909, 909, 909, 626 | 122, swing 2 | 28 | 83 |
| Motor City | Detroit house | D minor, string pads over a sixteenth bassline, bleep hook | 909, 808, 909, 808 Percussion | 124 | 20 | 119 |
| Late Shift | trap | F minor, half time, an 808 played across the keys with pitch-lock glides, hat rolls retriggered twice and three times | 808 on all four | 140 | 24 | 61 |
| Rinse Out | jungle | G minor, a two-step break with a dragged snare in the fill, a reese bass whose filter lock opens over the intro | 909, 909, 606, 909 | 170 | 20 | 81 |
| Echo Chamber | dub | A minor, one drop, offbeat skanks, a melodica, retrigger and reverse effects on the dub-out bars | 808, 808, 808, 626 | 75, swing 4 | 24 | 84 |
| Concrete | techno | A minor, four to the floor, a stab whose filter sweeps across each bar at high resonance | 909 on all four | 130 | 28 | 41 |

The pages count the kits as the device stores them: each hit once per project, however
many drum sounds load its kit, since a drum key may reference another kit's buffer
([kit sharing](kit-sharing-results.md)). A project spreading its drums over four machines
stores four kits; one playing a single machine on all four sounds stores it once. A project's own trims on the
keys it plays (a 150 ms trap kick, a 200 ms jungle crash) keep the voices free, which is
why a project may play a hit shorter than its kit does. Between them the ten cover the
device's range: tempos from 75 to 170, swing from none to 10, parameter locks on pitch,
volume, filter and resonance, punch-in effects, drum retriggers, melodic note lengths, a
drum sample used as a melodic instrument, and kits after six TR-series machines.

## Sounds

Every pack uses the same layout, so a pattern from one plays sensibly on another.

| Sound | Holds | Library folder |
| --- | --- | --- |
| 1, 2, 3 (and 6) | Chord samples, one voicing per chord type, played at the keys that transpose it to each chord of the progression | Keys (Rhodes, organ, piano), Pads (strings), Stabs (brass) |
| 4 | Bass: sub, sawtooth, reese or the 808 | Bass |
| 5 | Lead: Rhodes, bleep, bell, melodica or square lead | Leads |
| 11 | A standard kit, playing its kicks | the machine's folder |
| 12 | A standard kit, playing its snare, rim and clap | the machine's folder |
| 13 | A standard kit, playing its hats, shaker or ride | the machine's folder |
| 14 | A standard kit, playing its percussion | the machine's folder |

The chords, basses and leads are synthesized by the generators in `web/scripts/`, and the
drums by `drum-synth.ts`, including the 808 bass Late Shift plays across the keys. Style colour is written as filter and volume locks on the notes. Sounds
9 and 10 are left empty on purpose: the device gives them the lowest voice priority, so
the drums live on 11 to 14 where a busy step drops hats before kicks.

## Shipping

The kits and packs are built into `web/src/presets/` with an `index.json` manifest that
lists them in order; Vite bundles the zips as hashed assets of the build (about 4 MB in
all), so they cache without expiry and a changed pack is a new file:

```
cd web
npm run presets                                  # synthesized drums → src/presets (shipped)
npm run presets -- --pack "<TR pack folder>"     # a sample pack's hits → presets-tr (local only)
```

The second form builds the same kits and projects from a TR-series sample pack's
recordings, for anyone who owns one; it writes to `web/presets-tr/`, which git ignores,
since such packs may not be redistributed. `npm run dev:tr` serves the app with that set
as its bundled presets, for local use; a build in that mode is refused, so it cannot reach
a public site. Its zips are also ordinary archives: import them with Projects, Import
project, or a kit editor's import. A library that already holds a kit or project keeps it
whichever set is served, since both share the same identities. `scripts/make-kits.ts` writes
the kits alone, synthesized or from a pack.

Each pack is scheduled through the app's own playback engine as it is written and the
build fails rather than write one that would drop a note, and each is compiled to confirm
it fits. The kits are defined in `scripts/kit-tools.ts` and voiced in `scripts/drum-synth.ts`; the song specs live in
`scripts/make-lofi-packs.ts`, `scripts/make-genre-packs.ts`, `scripts/make-more-packs.ts` and
`scripts/make-italo-pack.ts`;
`scripts/pack-tools.ts` holds the instruments and the checks; `scripts/build-presets.ts`
writes the set and the index.

On every load the app compares the manifest with the kit and project records' bundled
identities and imports what is missing, kits first, reusing samples that several share by
their audio hash; a first launch opens Rainy Rhodes. A load that cannot fetch a zip (the app itself
loaded, so this is rare) says so in the status line and tries again next time. Opening
the app with `?nopresets` skips the check, for tests and demos that want an empty library.

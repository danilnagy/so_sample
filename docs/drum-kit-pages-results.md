# Page-rounded drum kits and empty-slot import verified

The [page-capacity test](drum-kit-pages-control.md) passed every registered prediction.
The backup equals the compiled target exactly:

- **Sound11** holds its kit in 61440 codes, 15 pages, instead of the device's 102400.
- **Sound12**, previously empty, holds a new kit in 40960 codes, 10 pages, owned by its
  first sound id, 56.

Pattern 1 played Sound12 key k on step k. In all five loops each step lands within 0.1
cents of +100 (k-1), step 1 sounds at 500 Hz within 0.1 cents, and every hit lasts 101.2
to 101.7 ms against 101.3 ms. The person heard a rising run of 16 beeps.

So any whole number of pages up to 102400 codes works as a drum capacity, and an empty
drum slot takes a kit in the device's own layout. The importer's page-rounded default is
hardware verified for Sound11 and Sound12.

- [Registration](../experiments/drum-kit-pages-registration-001.json)
- [Decision](../experiments/drum-kit-pages-decision-001.json)
- [Observation](../experiments/compiled-drum-kit-pages-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-drum-kit-pages-001/project.json`

The next [sample-memory test](drum-memory-control.md) fills Sound13 to Sound16.

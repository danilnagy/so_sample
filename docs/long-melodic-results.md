# A 4.0 s melodic sample plays whole and in order

The [long melodic test](long-melodic-control.md) imported a 4.0 s sample, 93750 codes,
into Sound6 with a page-rounded capacity of 94208 codes. The backup equals the compiled
target exactly. The person heard one long note per loop that stepped up four times.

In all five loops the note lasts 2671.1 to 2672.0 ms against the predicted 2669.7 ms,
and its four quarters sound 0.4 cents from 599.3, 749.2, 899.0 and 1048.8 Hz. Both
registered models, `whole_sample_plays` and `quarters_in_order`, hold.

So melodic samples are not limited to the device's own recording sizes: a 4.0 s sample
in any whole number of pages plays completely, transposed 7 semitones up at key 1 and
pitch code 13. The melodic importer takes `max_frames` and `page_capacity` to allow this.

- [Registration](../experiments/long-melodic-registration-001.json)
- [Decision](../experiments/long-melodic-decision-001.json)
- [Observation](../experiments/compiled-long-melodic-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-long-melodic-001/project.json`

The next [all-melodic-slots test](all-melodic-slots-control.md) imports into every
melodic slot.

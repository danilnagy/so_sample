# Parameter-only locks set the held value

The [parameter-only lock test](param-only-control.md) placed filter locks on empty steps
before unlocked notes. The backup equals the compiled target exactly. Each of the four
unlocked notes played at the lock on the empty step before it, within 0.24 dB of its
reference. The alternative, that only locks on notes count, fails by 9 to 28 dB.

So a parameter-only cell, primary bytes with a zero auxiliary byte, is a real lock. The
device holds the last locked value across steps whether or not a note was on the locking
step. Together with the [no-lock result](no-lock-results.md) and the
[knob observation](sound-knobs-results.md), the rule for an editor is:

- every nonzero parameter code on any step is a lock, note or not;
- a zero code leaves the parameter at the last lock;
- the value before any lock is live device state that a backup cannot set.

The `set_parameter_locks` operation writes such cells and is hardware verified for filter.

- [Registration](../experiments/param-only-registration-001.json)
- [Decision](../experiments/param-only-decision-001.json)
- [Observation](../experiments/compiled-param-only-001/hardware-observation-001.json)
- Current genuine export: `experiments/exported-param-only-001/project.json`

The [polyphony test](polyphony-control.md) measures how many sounds play on one step.

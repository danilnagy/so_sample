"""Hardware-in-the-loop helpers: audio I/O, immediate capture checks and session records.

Nothing here operates the PO-33 itself. A person still presses the device buttons;
these tools play, record, decode and compare so that each round trip is quick and
its evidence is complete. Every record keeps software checks separate from what
the person observed on the device.
"""

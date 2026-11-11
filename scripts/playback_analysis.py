"""Inspect retained calibration sample playback without editing source audio."""

import argparse
from pathlib import Path

from po33_re.analysis.playback import playback_report
from po33_re.artifacts import json_bytes, validate_outputs, write_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    validate_outputs([args.out], [args.audio], False)
    write_bytes(args.out, json_bytes(playback_report(args.audio)))


if __name__ == "__main__":
    main()

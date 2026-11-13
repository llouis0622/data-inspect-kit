"""Uniformly sample JSON Lines records in input order using a bounded reservoir."""

import argparse
import json
import random
import sys
from contextlib import nullcontext


def reject_constant(value):
    raise ValueError(f"{value} is not a JSON number")


def sample(stream, size, seed):
    rng = random.Random(seed)
    reservoir = []
    for index, raw in enumerate(stream):
        try:
            json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
        except (ValueError, RecursionError) as exc:
            raise ValueError(f"line {index + 1}: {exc}") from exc
        if index < size:
            reservoir.append((index, raw))
        elif size:
            slot = rng.randrange(index + 1)
            if slot < size:
                reservoir[slot] = (index, raw)
    return sorted(reservoir)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="-", help="input path, or - for stdin")
    parser.add_argument("-n", "--size", required=True, type=int, help="maximum records to emit")
    parser.add_argument("--seed", type=int, default=0, help="random seed (default: 0)")
    args = parser.parse_args()
    if args.size < 0:
        parser.error("--size must be nonnegative")
    try:
        with nullcontext(sys.stdin.buffer) if args.input == "-" else open(args.input, "rb") as stream:
            selected = sample(stream, args.size, args.seed)
        for _, raw in selected:
            sys.stdout.buffer.write(raw.rstrip(b"\r\n") + b"\n")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()

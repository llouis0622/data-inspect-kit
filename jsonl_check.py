"""Validate a UTF-8 JSON Lines stream and print the number of records."""

import argparse
import json
import sys
from contextlib import nullcontext


def reject_constant(value):
    raise ValueError(f"{value} is not a JSON number")


def check(stream):
    count = 0
    for count, raw in enumerate(stream, 1):
        if not raw.strip():
            raise ValueError(f"line {count}: blank line")
        try:
            json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
        except UnicodeDecodeError as exc:
            raise ValueError(f"line {count}, byte {exc.start + 1}: invalid UTF-8") from exc
        except json.JSONDecodeError as exc:
            raise ValueError(f"line {count}, column {exc.colno}: {exc.msg}") from exc
        except (ValueError, RecursionError) as exc:
            raise ValueError(f"line {count}: {exc}") from exc
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="-", help="input path, or - for stdin")
    args = parser.parse_args()
    try:
        with nullcontext(sys.stdin.buffer) if args.input == "-" else open(args.input, "rb") as stream:
            count = check(stream)
        print(json.dumps({"records": count}))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()

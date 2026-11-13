"""Report key presence and JSON value types across newline-delimited objects."""

import argparse
import json
import sys
from collections import Counter, defaultdict
from contextlib import nullcontext


TYPES = {int: "number", float: "number", bool: "boolean", str: "string",
         list: "array", dict: "object", type(None): "null"}


def reject_constant(value):
    raise ValueError(f"{value} is not a JSON number")


def summarize(stream):
    fields = defaultdict(Counter)
    records = 0
    for records, raw in enumerate(stream, 1):
        try:
            record = json.loads(raw.decode("utf-8"), parse_constant=reject_constant)
        except (ValueError, RecursionError) as exc:
            raise ValueError(f"line {records}: {exc}") from exc
        if not isinstance(record, dict):
            raise ValueError(f"line {records}: expected a JSON object")
        for key, value in record.items():
            fields[key][TYPES[type(value)]] += 1
    summary = {}
    for key, counts in sorted(fields.items()):
        present = sum(counts.values())
        summary[key] = {"present": present, "missing": records - present,
                        "types": dict(sorted(counts.items()))}
    return {"records": records, "keys": summary}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", nargs="?", default="-", help="input path, or - for stdin")
    args = parser.parse_args()
    try:
        with nullcontext(sys.stdin.buffer) if args.input == "-" else open(args.input, "rb") as stream:
            result = summarize(stream)
        print(json.dumps(result, indent=2))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()

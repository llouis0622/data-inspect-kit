"""Validate a UTF-8 CSV file and print its shape as JSON."""

import argparse
import csv
import json


def inspect(stream):
    reader = csv.reader(stream, strict=True)
    try:
        header = next(reader, None)
        if not header:
            raise ValueError("expected a header row")
        width = len(header)
        count = 0
        for row in reader:
            if len(row) != width:
                raise ValueError(
                    f"line {reader.line_num}: found {len(row)} fields, expected {width}"
                )
            count += 1
    except csv.Error as exc:
        raise ValueError(f"line {reader.line_num}: {exc}") from exc
    return {"rows": count, "columns": width, "header": header}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="-", help="CSV path or - for stdin")
    args = parser.parse_args()
    try:
        with open(0 if args.path == "-" else args.path, encoding="utf-8-sig",
                  newline="", closefd=args.path != "-") as stream:
            print(json.dumps(inspect(stream), ensure_ascii=False))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()

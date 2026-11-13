"""Convert a UTF-8 CSV file to JSON Lines on stdout, keeping fields as strings."""

import argparse
import csv
import json
import shutil
import sys
import tempfile


def convert(source, target):
    reader = csv.reader(source, strict=True)
    try:
        header = next(reader, None)
        if not header or any(not name.strip() for name in header):
            raise ValueError("expected non-empty column names in the header")
        if len(set(header)) != len(header):
            raise ValueError("duplicate column names in the header")
        for row in reader:
            if len(row) != len(header):
                raise ValueError(
                    f"line {reader.line_num}: found {len(row)} fields, expected {len(header)}"
                )
            record = dict(zip(header, row))
            target.write(json.dumps(record, ensure_ascii=False) + "\n")
    except csv.Error as exc:
        raise ValueError(f"line {reader.line_num}: {exc}") from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="-", help="CSV path or - for stdin")
    args = parser.parse_args()
    try:
        with open(0 if args.path == "-" else args.path, encoding="utf-8-sig",
                  newline="", closefd=args.path != "-") as source:
            # Stage output so a malformed final row cannot leave a partial JSONL file.
            with tempfile.TemporaryFile(mode="w+", encoding="utf-8", newline="") as output:
                convert(source, output)
                output.seek(0)
                shutil.copyfileobj(output, sys.stdout)
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()

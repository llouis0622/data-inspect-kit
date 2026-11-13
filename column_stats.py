"""Count blank (empty or whitespace-only) fields per CSV column."""

import argparse
import csv
import json


def summarize(stream):
    reader = csv.reader(stream, strict=True)
    try:
        header = next(reader, None)
        if not header:
            raise ValueError("expected a header row")
        blanks = [0] * len(header)
        rows = 0
        for row in reader:
            if len(row) != len(header):
                raise ValueError(
                    f"line {reader.line_num}: found {len(row)} fields, expected {len(header)}"
                )
            for index, field in enumerate(row):
                if not field.strip():
                    blanks[index] += 1
            rows += 1
    except csv.Error as exc:
        raise ValueError(f"line {reader.line_num}: {exc}") from exc

    columns = [
        {"position": i + 1, "name": name, "blank": blanks[i]}
        for i, name in enumerate(header)
    ]
    return {"rows": rows, "columns": columns}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", default="-", help="CSV path or - for stdin")
    args = parser.parse_args()
    try:
        with open(0 if args.path == "-" else args.path, encoding="utf-8-sig",
                  newline="", closefd=args.path != "-") as stream:
            print(json.dumps(summarize(stream), ensure_ascii=False))
    except (OSError, ValueError) as exc:
        parser.exit(1, f"{parser.prog}: {exc}\n")


if __name__ == "__main__":
    main()

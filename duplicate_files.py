#!/usr/bin/env python3
"""Find groups of duplicate dataset files and write one JSON object per group."""

import argparse
from collections import defaultdict
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


def raise_walk_error(error):
    raise error


def find_duplicates(root):
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError(f"expected a directory (not a symbolic link): {root}")

    output = os.fstat(sys.stdout.fileno())
    by_size = defaultdict(list)
    for parent, _, names in os.walk(root, onerror=raise_walk_error):
        for name in names:
            path = Path(parent, name)
            info = path.lstat()
            if stat.S_ISREG(info.st_mode) and not os.path.samestat(info, output):
                by_size[info.st_size].append((path, info))

    for size, candidates in sorted(by_size.items()):
        if len(candidates) < 2:
            continue
        by_hash = defaultdict(list)
        for path, original in candidates:
            digest = hashlib.sha256()
            with path.open("rb") as source:
                before = os.fstat(source.fileno())
                if not os.path.samestat(before, original) or before.st_size != size:
                    raise OSError(f"file changed while scanning: {path}")
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
                after = os.fstat(source.fileno())
                if (after.st_size, after.st_mtime_ns) != (size, before.st_mtime_ns):
                    raise OSError(f"file changed while hashing: {path}")
            by_hash[digest.hexdigest()].append(path.relative_to(root).as_posix())
        for checksum, paths in sorted(by_hash.items()):
            if len(paths) > 1:
                yield {"size": size, "sha256": checksum, "paths": sorted(paths)}


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Compares regular files by byte size and SHA-256. Skips symbolic links "
        "and redirected output. Hard links are listed as distinct paths."
    ))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        for group in find_duplicates(args.directory):
            print(json.dumps(group))
    except (OSError, ValueError) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    main()

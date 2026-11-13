#!/usr/bin/env python3
"""Write a reproducible JSON Lines inventory of a dataset directory."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys


def raise_walk_error(error):
    raise error


def write_manifest(root):
    if not stat.S_ISDIR(root.lstat().st_mode):
        raise ValueError(f"expected a directory (not a symbolic link): {root}")

    output = os.fstat(sys.stdout.fileno())
    for parent, directories, names in os.walk(root, onerror=raise_walk_error):
        directories.sort()
        for name in sorted(names):
            path = Path(parent, name)
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode) or os.path.samestat(info, output):
                continue

            digest = hashlib.sha256()
            with path.open("rb") as source:
                before = os.fstat(source.fileno())
                if not os.path.samestat(info, before):
                    raise OSError(f"file replaced while scanning: {path}")
                for block in iter(lambda: source.read(1024 * 1024), b""):
                    digest.update(block)
                after = os.fstat(source.fileno())
                if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
                    raise OSError(f"file changed while hashing: {path}")

            print(json.dumps({
                "path": path.relative_to(root).as_posix(),
                "size": before.st_size,
                "sha256": digest.hexdigest(),
            }))


def main():
    parser = argparse.ArgumentParser(description=__doc__, epilog=(
        "Scans regular files only. Skips symbolic links and the file receiving "
        "standard output. Paths are relative to the input directory."
    ))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    try:
        write_manifest(args.directory)
    except (OSError, ValueError) as error:
        parser.exit(1, f"{parser.prog}: {error}\n")


if __name__ == "__main__":
    main()

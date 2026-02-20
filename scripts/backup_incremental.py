#!/usr/bin/env python3
"""Create incremental backups for a given file: filename.ext.bak.N

Usage:
    python scripts/backup_incremental.py path/to/file

This script copies the file preserving metadata and prints the created backup path.
"""
import sys
from pathlib import Path
import shutil

def backup_incremental(file_path: str) -> Path:
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(p)
    parent = p.parent
    base = p.name
    prefix = base + ".bak."
    candidates = [f.name for f in parent.iterdir() if f.is_file() and f.name.startswith(prefix)]
    nums = []
    for name in candidates:
        try:
            n = int(name.rsplit('.', 1)[-1])
            nums.append(n)
        except Exception:
            continue
    next_n = max(nums) + 1 if nums else 1
    dest = parent / (prefix + str(next_n))
    shutil.copy2(p, dest)
    return dest

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: backup_incremental.py <file>")
        sys.exit(2)
    file_arg = sys.argv[1]
    try:
        created = backup_incremental(file_arg)
        print(created)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

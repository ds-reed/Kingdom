#!/usr/bin/env python3
"""Run incremental backups for all .py files in the workspace before edits.

This is intended to be called by the assistant before making any edits.
"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY_FILES = [p for p in ROOT.rglob('*.py') if 'site-packages' not in str(p) and '.ipynb_checkpoints' not in str(p)]

created = []
for p in PY_FILES:
    # skip files in scripts/backups to avoid backing up backups
    if p.name.endswith('.bak') or '.bak.' in p.name:
        continue
    # skip ipynb checkpoint files/folders
    if '.ipynb_checkpoints' in str(p):
        continue
    res = subprocess.run([sys.executable, str(Path(__file__).parent / 'backup_incremental.py'), str(p)], capture_output=True, text=True)
    if res.returncode == 0:
        created.append(res.stdout.strip())
    else:
        print(f"Warning: backup failed for {p}: {res.stderr.strip()}")

for c in created:
    print(c)

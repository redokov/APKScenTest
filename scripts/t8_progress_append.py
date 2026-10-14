# -*- coding: utf-8 -*-
"""Append a note file (UTF-8) to tmp/t8/PROGRESS.md. Usage:
python scripts/t8_progress_append.py <note.txt>
"""
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS = os.path.join(ROOT, "tmp", "t8", "PROGRESS.md")


def main():
    note_path = sys.argv[1]
    with io.open(note_path, "r", encoding="utf-8") as f:
        note = f.read()
    if not note.endswith("\n"):
        note += "\n"
    with io.open(PROGRESS, "a", encoding="utf-8", newline="\n") as f:
        f.write(note)
    print("[ok] appended %d chars to PROGRESS.md" % len(note))


if __name__ == "__main__":
    main()

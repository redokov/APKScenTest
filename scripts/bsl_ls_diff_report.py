#!/usr/bin/env python3
"""Diff BSL Language Server reports between two source trees.

Runs `java -jar <bsl-ls> analyze` on each tree (copied into an ASCII-safe temp
dir, because java on Windows mangles non-ASCII argv) and compares the set of
(file, diagnostic, message) entries. Prints:
  * counts by severity for each side,
  * diagnostics present ONLY in the second tree (i.e. regressions),
  * diagnostics that disappeared.

Usage:
  python scripts/bsl_ls_diff_report.py <baseline_dir> <current_dir> [--out tmp/007]
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile

JAR = os.environ.get(
    "BSL_JAR", r"C:\Users\r.edokov\.pi\vendor\jars\bsl-language-server-1.0.7-exec.jar"
)
JAVA = os.environ.get(
    "JAVA", r"C:\Users\r.edokov\.pi\vendor\jdk-21.0.12.1+1\bin\java.exe"
)


def run_analyze(src_dir: str) -> dict:
    """Copy src_dir into an ASCII temp dir, run analyze, return parsed report."""
    tmp_root = os.path.join(tempfile.gettempdir(), "bsl_ls_diff")
    if os.path.isdir(tmp_root):
        shutil.rmtree(tmp_root, ignore_errors=True)
    work = os.path.join(tmp_root, "src")
    shutil.copytree(src_dir, work)
    out_dir = os.path.join(tmp_root, "out")
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        JAVA, "-Xmx2048m", "-Dfile.encoding=UTF-8", "-jar", JAR,
        "analyze", "-s", ".", "-o", out_dir, "-r", "json", "-q",
    ]
    proc = subprocess.run(cmd, cwd=tmp_root, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=1800)
    out = os.path.join(out_dir, "bsl-json.json")
    if not os.path.isfile(out):
        raise RuntimeError("analyze produced no report:\n%s\n%s"
                           % (proc.stdout[-2000:], proc.stderr[-2000:]))
    with open(out, "r", encoding="utf-8-sig") as fh:
        report = json.load(fh)
    shutil.rmtree(tmp_root, ignore_errors=True)
    return report


def flatten(report: dict) -> list:
    """[(relative file, diagnostic code, severity, message)] sorted."""
    rows = []
    for file_info in report.get("fileinfos", []):
        path = (file_info.get("path") or "").replace("file:///", "").replace("%20", " ")
        rel = path.replace("\\", "/").split("/src/")[-1]
        for diag in file_info.get("diagnostics", []):
            rows.append((
                rel,
                diag.get("code", ""),
                str(diag.get("severity", "")),
                (diag.get("message") or "").strip().split("\n")[0][:120],
                (diag.get("range") or {}).get("start", {}).get("line", -1) + 1,
            ))
    rows.sort()
    return rows


def severity_counts(rows: list) -> dict:
    counts = {}
    for _f, _c, severity, _m, _ln in rows:
        counts[severity] = counts.get(severity, 0) + 1
    return counts


def key_rows(rows: list) -> dict:
    """Multiset of (file, code, message) so duplicates are preserved."""
    out = {}
    for f, c, _s, m, ln in rows:
        out.setdefault((f, c, m), []).append(ln)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline")
    ap.add_argument("current")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    base_rows = flatten(run_analyze(args.baseline))
    curr_rows = flatten(run_analyze(args.current))

    base_counts = severity_counts(base_rows)
    curr_counts = severity_counts(curr_rows)

    base_keys = key_rows(base_rows)
    curr_keys = key_rows(curr_rows)

    added, removed = [], []
    for key, cnt in curr_keys.items():
        delta = len(cnt) - len(base_keys.get(key, []))
        if delta > 0:
            added.extend([key + (tuple(sorted(set(cnt))),)] * delta)
    for key, cnt in base_keys.items():
        delta = len(cnt) - len(curr_keys.get(key, []))
        if delta > 0:
            removed.extend([key + (tuple(sorted(set(cnt))),)] * delta)

    lines = []
    lines.append("BASELINE: %s" % json.dumps(base_counts, ensure_ascii=False, sort_keys=True))
    lines.append("CURRENT : %s" % json.dumps(curr_counts, ensure_ascii=False, sort_keys=True))
    lines.append("")
    lines.append("NEW diagnostics (%d):" % len(added))
    for f, c, m, lns in sorted(added):
        lines.append("  + %s:%s [%s] %s" % (f, ",".join(map(str, lns)), c, m))
    lines.append("")
    lines.append("GONE diagnostics (%d):" % len(removed))
    for f, c, m, lns in sorted(removed):
        lines.append("  - %s:%s [%s] %s" % (f, ",".join(map(str, lns)), c, m))

    text = "\n".join(lines)
    print(text)
    if args.out:
        os.makedirs(args.out, exist_ok=True)
        with open(os.path.join(args.out, "bsl-ls-diff.txt"), "w",
                  encoding="utf-8") as fh:
            fh.write(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())

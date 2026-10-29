# -*- coding: utf-8 -*-
"""s005: semantic comparison of two run summary.json files (diff_classes
semantics of scripts/regress_run.py, key = scenario+user).
Usage: python scripts/s005_cmp_runs.py <base-summary.json> <cur-summary.json>
Exit 0 = no REGRESSION/MISSING, exit 2 = blocker classes found."""
import io, json, sys

BAD = ("failed", "broken", "timeout", "unknown")


def diff_classes(base_scen, cur_scen):
    base = {}
    for s in base_scen or []:
        base[(s.get("scenario"), s.get("user"))] = s.get("status")
    out = []
    for s in cur_scen or []:
        key = (s.get("scenario"), s.get("user"))
        cur_st = s.get("status")
        if key not in base:
            cls = "NEW"
        else:
            b = base[key]
            if b == cur_st:
                cls = "="
            elif b in BAD and cur_st == "passed":
                cls = "IMPROVED"
            elif b == "passed" and cur_st in BAD:
                cls = "REGRESSION"
            else:
                cls = "="
        out.append((key[0], key[1], cur_st, cls))
    for key, b in base.items():
        if key not in {(s.get("scenario"), s.get("user")) for s in (cur_scen or [])}:
            out.append((key[0], key[1], "", "MISSING"))
    return out


def main():
    base = json.load(io.open(sys.argv[1], encoding="utf-8"))
    cur = json.load(io.open(sys.argv[2], encoding="utf-8"))
    rows = diff_classes(base.get("scenarios"), cur.get("scenarios"))
    out = io.open("tmp/s005/cmp_runs.txt", "w", encoding="utf-8")
    print("base:", sys.argv[1], file=out)
    print("cur :", sys.argv[2], file=out)
    print("base totals:", base.get("totals"), file=out)
    print("cur  totals:", cur.get("totals"), file=out)
    print(file=out)
    blockers = 0
    for sc, us, st, cls in sorted(rows):
        mark = ""
        if cls in ("REGRESSION", "MISSING"):
            mark = "  <-- BLOCKER"
            blockers += 1
        print("%-28s %-26s %-9s %s%s" % (sc, us, st, cls, mark), file=out)
    print(file=out)
    print("blockers (REGRESSION/MISSING):", blockers, file=out)
    out.close()
    print("rows=%d blockers=%d -> tmp/s005/cmp_runs.txt" % (len(rows), blockers))
    sys.exit(2 if blockers else 0)


if __name__ == "__main__":
    main()

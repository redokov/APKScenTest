# -*- coding: utf-8 -*-
"""S003 T4: unit-тест diff-классов baseline (синтетика, без базы)."""
import importlib.util
import os
import sys

spec = importlib.util.spec_from_file_location(
    "regress_run", os.path.join(os.path.dirname(__file__), "regress_run.py"))
rr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rr)


def scen(name, user, status):
    return {"scenario": name, "user": user, "status": status}


def cls_of(diffs, name, user):
    for d in diffs:
        if d[0] == name and d[1] == user:
            return d[3]
    return None


def main():
    base = [scen("A", "U1", "passed"), scen("B", "U1", "passed"),
            scen("C", "U2", "failed"), scen("D", "U2", "passed")]
    cur = [scen("A", "U1", "passed"), scen("B", "U1", "failed"),
           scen("C", "U2", "passed"), scen("E", "U3", "passed")]
    d = rr.diff_classes(base, cur)
    checks = [
        (cls_of(d, "A", "U1") == "=", "A same -> ="),
        (cls_of(d, "B", "U1") == "REGRESSION", "B pass->failed -> REGRESSION"),
        (cls_of(d, "C", "U2") == "IMPROVED", "C failed->passed -> IMPROVED"),
        (cls_of(d, "E", "U3") == "NEW", "E absent in base -> NEW"),
        (cls_of(d, "D", "U2") == "MISSING", "D absent in cur -> MISSING"),
        (cls_of(d, "D", "U2") is not None, "MISSING row exists"),
        (rr.diff_classes(None, cur) and all(x[3] == "NEW" for x in rr.diff_classes(None, cur)),
         "no baseline -> all NEW"),
        (rr.diff_classes(base, None) and all(x[3] == "MISSING" for x in rr.diff_classes(base, None))
         and len(rr.diff_classes(base, None)) == 4,
         "no current -> all MISSING"),
    ]
    # broken/timeout тоже BAD
    d2 = rr.diff_classes([scen("X", "U", "passed")],
                         [scen("X", "U", "broken")])
    checks.append((cls_of(d2, "X", "U") == "REGRESSION",
                   "pass->broken -> REGRESSION"))
    d3 = rr.diff_classes([scen("Y", "U", "passed")],
                         [scen("Y", "U", "timeout")])
    checks.append((cls_of(d3, "Y", "U") == "REGRESSION",
                   "pass->timeout -> REGRESSION"))
    fails = [msg for ok, msg in checks if not ok]
    for ok, msg in checks:
        print("%s %s" % ("PASS" if ok else "FAIL", msg))
    print("test_regress_diff: %d/%d passed" % (len(checks) - len(fails), len(checks)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())

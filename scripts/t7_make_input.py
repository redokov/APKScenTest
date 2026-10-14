# -*- coding: utf-8 -*-
"""T7: собрать сводный run-каталог tmp/t7/run-report/ из артефактов T6.

Решение T7-1 (см. tmp/t7/PROGRESS.md): реальный прогон T6 жил в
tmp-каталогах (run-a/run-b), а полный fixtures-каталог — в
tests/run-20261011-233413 (без батчей). Для AC T7 («summary.json содержит
статусы всех батчей прогона T6») собираем tmp-копию:

- базис: tmp/t6/run-b (цикл B: batches.json 1 батч ok + allure + logs);
- + батчи цикла A (tmp/t6/run-a/batches.json, 2 timeout-батча) дописаны
  в batches.json (итого 3);
- + fixtures.json / scan.json / features/ / features-manifest.json из
  tests/run-20261011-233413 (секция покрытия отчёта);
- + features/manifest цикла A/B.

Исходные каталоги T6 не изменяются.
"""
import json
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(r"C:\MyProjects\APKScenTest")
RUN_A = ROOT / "tmp" / "t6" / "run-a"
RUN_B = ROOT / "tmp" / "t6" / "run-b"
RUN_T4 = ROOT / "tests" / "run-20261011-233413"
DST = ROOT / "tmp" / "t7" / "run-report"


def read(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def main() -> int:
    for p in (RUN_A, RUN_B, RUN_T4):
        if not p.is_dir():
            print("[FAIL] not found: %s" % p)
            return 1
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(RUN_B, DST)

    # батчи цикла A + B в один batches.json
    b_a = read(RUN_A / "batches.json")
    b_b = read(DST / "batches.json")
    merged = {
        "runId": "t6-cycles-ab",
        "finishedAt": b_b.get("finishedAt", ""),
        "batches": list(b_a.get("batches", [])) + list(b_b.get("batches", [])),
    }
    (DST / "batches.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")

    # run.json: runId сводного прогона
    run = read(DST / "run.json")
    run["runId"] = "t6-cycles-ab"
    (DST / "run.json").write_text(
        json.dumps(run, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")

    # покрытие из полного T4/T5-каталога
    for name in ("fixtures.json", "scan.json", "features-manifest.json"):
        shutil.copyfile(RUN_T4 / name, DST / name)
    for f in (RUN_T4 / "features").glob("*.feature"):
        shutil.copyfile(f, DST / "features" / f.name)

    # features + manifest цикла A
    for f in (RUN_A / "features").glob("*.feature"):
        if not (DST / "features" / f.name).exists():
            shutil.copyfile(f, DST / "features" / f.name)
    ma = read(RUN_A / "features-manifest.json")
    mb = read(DST / "features-manifest.json")
    # у копии run-b manifest перезаписан T4-версией; объединяем все три
    mr = read(RUN_B / "features-manifest.json")
    files = {e["file"]: e for e in mb.get("files", []) + mr.get("files", []) + ma.get("files", [])}
    for e in ma.get("files", []) + mr.get("files", []):
        e2 = dict(e)
        e2["file"] = str(DST / "features" / Path(e["file"]).name)
        files[e2["file"]] = e2
    manifest = {"generatedAt": "2026-10-12T00:00:00",
                "files": list(files.values()),
                "warnings": mb.get("warnings", []) + mr.get("warnings", []) + ma.get("warnings", [])}
    (DST / "features-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1),
        encoding="utf-8", newline="\n")

    total = sum(1 for _ in DST.rglob("*") if _.is_file())
    print("[OK] %s (%d files)" % (DST, total))
    for rel in sorted(str(p.relative_to(DST)) for p in DST.rglob("*") if p.is_file()):
        print("   ", rel)
    return 0


if __name__ == "__main__":
    sys.exit(main())

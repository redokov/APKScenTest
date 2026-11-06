#!/usr/bin/env python3
"""Relocate check (spec 007 T-101/T-102/T-103): комплект работает из чужого корня.

1. Копирует dist/ и tests/ в tmp/relocate-test/ (сохраняя взаимное расположение).
2. Запускает Stage-A драйвер (tmp/t3/epf/АпкРаннер.epf) с настройками ИЗ КОПИИ:
   target = tmp/relocate-test/dist/АпкПодготовкаСценарныхТестов.epf,
   settingsPath = tmp/relocate-test/tests/preprocessor-settings.json,
   runsDir = "" (значит берётся из настроек через projectDir).
3. Проверяет: run-каталог создан ВНУТРИ копии (tmp/relocate-test/tests/run-*),
   то есть относительный projectDir "." разрезолвился от каталога комплекта,
   а не от текущего каталога процесса.

Exit 0 = переносимость подтверждена, 1 = провал.
"""
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
V8 = Path(r"C:\Program Files\1cv8\8.5.4.1683\bin\1cv8.exe")
CONN = r"localhost\dev_erpapk_demo"
USER = "Администратор (ОрловАВ)"
DRIVER_EPF = ROOT / "tmp" / "t3" / "epf" / "АпкРаннер.epf"
RELOC = ROOT / "tmp" / "relocate-test"
TASK = ROOT / "tmp" / "t3" / "runner_task.json"
RESULT = ROOT / "tmp" / "t3" / "runner_result.json"
CLIENT_LOG = ROOT / "tmp" / "007" / "relocate_client.log"
TIMEOUT = 900


def kill_tree(pid):
    subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True)


def main() -> int:
    lines = []
    for what, path in (("driver EPF", DRIVER_EPF), ("dist", ROOT / "dist"), ("tests", ROOT / "tests")):
        if not path.exists():
            print("[FAIL] %s not found: %s" % (what, path), file=sys.stderr)
            return 1

    # 1. relocate
    if RELOC.exists():
        shutil.rmtree(RELOC)
    RELOC.mkdir(parents=True)
    shutil.copytree(ROOT / "dist", RELOC / "dist")
    shutil.copytree(ROOT / "tests", RELOC / "tests",
                    ignore=shutil.ignore_patterns("run-*", "logs"))
    for stale in (RELOC / "tests").glob("run-*"):
        shutil.rmtree(stale, ignore_errors=True)
    lines.append("relocated kit: %s" % RELOC)

    # 2. structural check of the settings file inside the copy
    settings_path = RELOC / "tests" / "preprocessor-settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8-sig"))
    abs_keys = [k for k, v in settings.items()
                if isinstance(v, str) and (len(v) > 1 and v[1] == ":")]
    lines.append("absolute-valued keys: %s" % abs_keys)
    if abs_keys != ["v8cPath"]:
        lines.append("FAIL: в настройках абсолютные пути, кроме v8cPath: %s" % abs_keys)
        print("\n".join(lines))
        return 1
    for key in ("vaEpfPath", "baselinePath", "templatesDir", "coverageMapPath"):
        target = RELOC / settings[key]
        lines.append("%-16s -> %s (%s)" % (key, settings[key], "OK" if target.exists() else "MISSING"))
        if not target.exists():
            lines.append("FAIL: %s не разрешается внутри копии" % key)
            print("\n".join(lines))
            return 1

    # 3. live run: stage-A через копию
    TASK_DEF = {
        "target": str(RELOC / "dist" / "АпкПодготовкаСценарныхТестов.epf"),
        "settingsPath": str(settings_path),
        "runsDir": "",
        "filtersPath": "",
    }
    TASK.write_text(json.dumps(TASK_DEF, ensure_ascii=False, indent=2), encoding="utf-8")
    if RESULT.exists():
        RESULT.unlink()
    before = {p.name for p in (RELOC / "tests").glob("run-*")}

    cmd = [str(V8), "/S", CONN, "/RunModeManagedApplication",
           "/N", USER, "/DisableStartupDialogs", "/Execute", str(DRIVER_EPF)]
    with open(CLIENT_LOG, "wb") as fp:
        proc = subprocess.Popen(cmd, stdout=fp, stderr=subprocess.STDOUT)
    data = None
    try:
        start = time.time()
        while time.time() - start < TIMEOUT:
            if RESULT.exists():
                time.sleep(1)
                break
            if proc.poll() is not None:
                break
            time.sleep(2)
        if RESULT.exists():
            try:
                data = json.loads(RESULT.read_text(encoding="utf-8-sig"))
            except Exception as exc:  # noqa: BLE001
                lines.append("FAIL: битый runner_result.json: %s" % exc)
    finally:
        kill_tree(proc.pid)
        try:
            proc.wait(timeout=10)
        except Exception:  # noqa: BLE001
            pass

    after = {p.name for p in (RELOC / "tests").glob("run-*")}
    new_runs = sorted(after - before)
    lines.append("new run dirs inside relocated kit: %s" % (new_runs or "НЕТ"))
    ok = bool(new_runs)
    if data:
        lines.append("driver result keys: %s" % sorted(data.keys())[:8])
        steps = data.get("steps") or []
        for step in steps[:6]:
            lines.append("  step %s: %s" % (step.get("name"), step.get("status")))
    if not ok:
        lines.append("FAIL: относительный projectDir не разрезолвился в копию комплекта")

    verdict = "PASS" if ok else "FAIL"
    text = "\n".join(["relocate-check: %s" % verdict] + lines)
    print(text)
    out = ROOT / "tmp" / "007" / "relocate-check.txt"
    out.write_text(text + "\n", encoding="utf-8")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

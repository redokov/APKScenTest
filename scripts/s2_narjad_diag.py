# -*- coding: utf-8 -*-
"""s2_narjad_diag.py — T5 спеки 002: COM read-only диагностика авторов нарядов.

28 документов АпкНарядНаСдельнуюРаботу: авторы (Справочник.Пользователи),
их ИдентификаторПользователяИБ -> сопоставление с пользователями ИБ.
Результат: tmp/s2/narjad-diag.json (+ STDOUT ascii-only).
Запуск: python scripts/s2_narjad_diag.py (в отдельном процессе, таймаут снаружи).
"""
import io
import json
import sys

OUT_JSON = r"C:\MyProjects\APKScenTest\tmp\s2\narjad-diag.json"


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    agent = None
    try:
        import win32com.client
        agent = win32com.client.Dispatch("V85.COMConnector").Connect(
            "Srvr='localhost';Ref='dev_erpapk_demo';Usr='\u0410\u0434\u043c\u0438\u043d\u0438\u0441\u0442\u0440\u0430\u0442\u043e\u0440 (\u041e\u0440\u043b\u043e\u0432\u0410\u0412)'")
    except Exception as e:
        print("COM connect FAIL:", repr(e)[:200])
        raise SystemExit(1)

    def s(v):
        try:
            return agent.String(v)
        except Exception:
            return str(v)

    # 1) Пользователи ИБ: имя + UUID (массив 1С не перечисляется в COM - по индексам)
    ib_users = {}
    try:
        users = agent.ПользователиИнформационнойБазы.ПолучитьПользователей()
        cnt = users.Количество()
        for i in range(cnt):
            u = users.Получить(i)
            name = s(u.Имя)
            uid = s(u.УникальныйИдентификатор).lower()
            ib_users[uid] = {"name": name, "ib": True}
    except Exception as e:
        print("IB users read FAIL:", repr(e)[:200])
        raise SystemExit(2)

    # 2) Наряды: авторы и их идентификаторы
    q = agent.NewObject("Query")
    q.Text = (
        "\u0412\u042b\u0411\u0420\u0410\u0422\u042c "
        "\u0414.\u0421\u0441\u044b\u043b\u043a\u0430 \u041a\u0410\u041a Ref, "
        "\u0414.\u041d\u043e\u043c\u0435\u0440 \u041a\u0410\u041a Num, "
        "\u0414.\u0414\u0430\u0442\u0430 \u041a\u0410\u041a DDate, "
        "\u0414.\u041f\u0440\u043e\u0432\u0435\u0434\u0435\u043d \u041a\u0410\u041a Posted, "
        "\u0414.\u0410\u0432\u0442\u043e\u0440 \u041a\u0410\u041a Author, "
        "\u0414.\u0410\u0432\u0442\u043e\u0440.\u041d\u0430\u0438\u043c\u0435\u043d\u043e\u0432\u0430\u043d\u0438\u0435 \u041a\u0410\u041a AuthorName, "
        "\u0414.\u0410\u0432\u0442\u043e\u0440.\u0418\u0434\u0435\u043d\u0442\u0438\u0444\u0438\u043a\u0430\u0442\u043e\u0440\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u044f\u0418\u0411 \u041a\u0410\u041a AuthorIBId "
        "\u0418\u0417 \u0414\u043e\u043a\u0443\u043c\u0435\u043d\u0442.\u0410\u043f\u043a\u041d\u0430\u0440\u044f\u0434\u041d\u0430\u0421\u0434\u0435\u043b\u044c\u043d\u0443\u044e\u0420\u0430\u0431\u043e\u0442\u0443 \u041a\u0410\u041a \u0414 "
        "\u0423\u041f\u041e\u0420\u042f\u0414\u041e\u0427\u0418\u0422\u042c \u041f\u041e \u0414.\u0414\u0430\u0442\u0430 \u0423\u0411\u042b\u0412")

    rows = []
    sel = q.Execute().Choose()
    while sel.Next():
        rows.append({
            "num": s(sel.Num),
            "date": s(sel.DDate)[:19],
            "posted": bool(sel.Posted),
            "author": s(sel.AuthorName),
            "authorRef": s(sel.Author),
            "authorIBId": s(sel.AuthorIBId).lower(),
        })

    # 3) Сопоставление
    matched = [r for r in rows if r["authorIBId"] in ib_users]
    for r in matched:
        r["ibUser"] = ib_users[r["authorIBId"]]["name"]

    authors = {}
    for r in rows:
        a = authors.setdefault(r["author"], {"count": 0, "posted": 0, "ibId": r["authorIBId"]})
        a["count"] += 1
        a["posted"] += 1 if r["posted"] else 0

    result = {
        "total": len(rows),
        "ibUsers": {uid: v["name"] for uid, v in ib_users.items()},
        "authors": authors,
        "matchedDocs": matched,
        "matchedCount": len(matched),
        "postedMatched": [r for r in matched if r["posted"]],
    }

    with io.open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1)

    # ASCII-only stdout
    print("OK total=%d matched=%d postedMatched=%d authors=%d" % (
        result["total"], result["matchedCount"], len(result["postedMatched"]), len(authors)))
    for a, v in sorted(authors.items(), key=lambda kv: -kv[1]["count"]):
        print("AUTHOR total=%d posted=%d ib=%s" % (v["count"], v["posted"], v["ibId"] in ib_users))


if __name__ == "__main__":
    main()

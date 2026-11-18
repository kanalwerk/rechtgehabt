"""Recht gehabt? – DM-Automatik auf den Fall des Tages umschalten.

Liest faelle.json, nimmt den Fall mit geplant_fuer == heute (Europe/Zurich, oder --datum JJJJ-MM-TT),
schreibt dm/aktuell.json (ManyChat setzt damit die Felder «fall» und «fall_titel») und markiert den Fall als
«verwendet». Pushen danach mit git_werkzeug.py push. Läuft nach der Veröffentlichung des Reels (Reel 18:15, Lauf 18:17).

  python3 pipeline/dm_umschalten.py [--datum 2026-11-19]
Ausgabe: «umgeschaltet: 007 …», «schon aktuell: 007» oder «kein Fall für <datum>» (Exit 2).
"""
import datetime
import json
import pathlib
import sys
import zoneinfo

BASIS = pathlib.Path(__file__).resolve().parent.parent


def kurztitel(titel):
    t = titel.replace("­", "")
    return t.split(":")[0].strip().rstrip("?").strip()


def main(a):
    heute = a[a.index("--datum") + 1] if "--datum" in a else \
        datetime.datetime.now(zoneinfo.ZoneInfo("Europe/Zurich")).date().isoformat()
    db_pfad = BASIS / "faelle.json"
    db = json.loads(db_pfad.read_text(encoding="utf-8"))
    faelle = [f for f in db["faelle"] if f.get("geplant_fuer") == heute and f.get("status") in ("geplant", "verwendet")]
    if not faelle:
        print(f"kein Fall für {heute}")
        sys.exit(2)
    f = faelle[0]
    titel = kurztitel(f["texte"]["de"]["titel"])
    doc = {"version": "v2", "content": {"type": "instagram",
           "messages": [{"type": "text", "text": f"Deine Antwort gilt für Fall {f['nr']} «{titel}»."}],
           "actions": [{"action": "set_field_value", "field_name": "fall", "value": f["nr"]},
                       {"action": "set_field_value", "field_name": "fall_titel", "value": titel}],
           "quick_replies": []}}
    ziel = BASIS / "dm" / "aktuell.json"
    alt = ziel.read_text(encoding="utf-8") if ziel.exists() else ""
    neu = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    f["status"] = "verwendet"
    f["verwendet_am"] = heute
    db_pfad.write_text(json.dumps(db, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if alt == neu:
        print(f"schon aktuell: {f['nr']}")
        return
    ziel.write_text(neu, encoding="utf-8")
    print(f"umgeschaltet: {f['nr']} «{titel}»")


if __name__ == "__main__":
    main(sys.argv[1:])

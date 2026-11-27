"""Recht gehabt? – Tagesbeitrag aus faelle.json erzeugen.

  python3 pipeline/fall_post.py <nr> <JJJJ-MM-TT>
Schreibt posts/<datum>/post.json (Reel, DM-Auflösungskarte, 3 Story-Bilder, Bildunterschrift),
dm/fall/<nr>-A.json, -B.json (auch ohne führende Nullen) und setzt im Fall status «geplant» + geplant_fuer.
Danach rendern: python3 pipeline/rendern.py posts/<datum>/post.json <out> --design design.json --ohne-reel
und das Reel: python3 pipeline/reel_hook.py posts/<datum>/post.json <out> --audio musik.wav (Fälle mit texte.de.reel)
und karten/<nr>/aufloesung.png aus <out>/dm_aufloesung.png kopieren.
"""
import json
import pathlib
import sys

BASIS = pathlib.Path(__file__).resolve().parent.parent
PAGES = "https://kanalwerk.github.io/rechtgehabt"
GILT = {"DE": "Gilt für Deutschland", "AT": "Gilt für Österreich", "CH": "Gilt für die Schweiz"}


def dm(nr, richtig_gewaehlt):
    text = ("✅ Recht gehabt! Das Gericht hat entschieden wie du." if richtig_gewaehlt
            else "❌ Diesmal nicht. Das Gericht hat anders entschieden.")
    return {"version": "v2", "content": {"type": "instagram", "messages": [
        {"type": "text", "text": text},
        {"type": "image", "url": f"{PAGES}/karten/{nr}/aufloesung.png"},
        {"type": "text", "text": "Kennst du jemanden, den das interessiert? Schick ihm das Reel. Morgen kommt der nächste Fall."}],
        "actions": [], "quick_replies": []}}


def bildunterschrift(f):
    t = f["texte"]["de"]
    kopf = t["titel"].replace("­", "").split(":")[0].strip()
    frage = t["frage"][0].lower() + t["frage"][1:]
    tags = " ".join(h for h in t["hashtags"] if h != "#rechtgehabt")
    return (f"{kopf} – {frage}\nA: {t['optionen']['A']}\nB: {t['optionen']['B']}\n\n"
            f"Kommentiere A oder B – die Auflösung kommt sofort per DM.\n{t['teilen']}\n\n"
            f"Fall {f['nr']}: {t['quelle']} · {GILT[f['land']]} · Keine Rechtsberatung · Mit KI erstellt\n{tags}")


def post(f, datum):
    t = f["texte"]["de"]
    land, nr = f["land"], f["nr"]
    bild, pos = f"../../img/{f['bild']['pixabay']}.jpg", f["bild"]["pos"]
    opt = [{"key": k, "text": t["optionen"][k]} for k in ("A", "B")]
    titel = {"layout": "titel", "bild": bild, "bild_pos": pos, "position": "unten", "label": f"Fall {nr}",
             "badge": land, "titel": t["titel"], "unter": "Wie hat das Gericht entschieden?"}
    fall = {"layout": "frage", "thema": "hell", "label": "Der Fall", "badge": land, "sachverhalt": t["sachverhalt"],
            "wortmarke": False}
    frage = {"layout": "frage", "thema": "dunkel", "label": "Und das Gericht?", "badge": land, "frage": t["frage"],
             "optionen": opt, "wortmarke": False}
    # Reel seit 20.11.2026: Frage + A/B ab dem ersten Bild, A/B bleiben sichtbar, Aufruf zum Kommentieren
    einstieg = {"layout": "frage", "bild": bild, "bild_pos": pos, "position": "unten", "label": f"Fall {nr}",
                "badge": land, "frage": t["titel"], "optionen": opt, "wortmarke": False,
                "aufruf": "Kommentiere A oder B"}
    sv_kurz = {"layout": "frage", "thema": "hell", "label": f"Fall {nr}", "badge": land,
               "sachverhalt": t["sachverhalt"], "optionen": opt, "wortmarke": False}
    if t.get("reel"):  # seit 27.11.2026: Reel mit Einstieg, Stempel und Emojis -> pipeline/reel_hook.py
        h = t["reel"]
        reel = {"art": "hook", "datei": "reel.mp4", "cover": "cover.jpg", "nr": nr, "land": land, "bild": bild,
                "bild_pos": pos, "vor": h.get("vor", "Ab vor Gericht"), "gross": h["gross"], "stempel": h["stempel"],
                "zeilen": h["zeilen"], "frage": t["frage"], "optionen": t["optionen"]}
    sv_dauer = 6.6 if sum(len(s) for s in t["sachverhalt"]) > 240 else 6.0
    if not t.get("reel"):
        reel = {"datei": "reel.mp4", "cover": "cover.jpg", "schleife": True, "szenen": [
            {"dauer": 4.0, "folie": einstieg},
            {"dauer": sv_dauer, "folie": dict(sv_kurz, aufruf="Kommentiere A oder B")}]}
    return {
        "datum": datum, "thema": f["thema"], "land": land, "quellen": f["quellen"],
        "reel": reel,
        "bilder": [
            {"datei": "dm_aufloesung.png", "format": "karte_lang", "folie": {
                "layout": "aufloesung", "thema": "hell", "badge": land, "label": f"Auflösung · Fall {nr}",
                "ergebnis": {"key": f["richtig"], "text": t["ergebnis"]}, "headline": t["headline"],
                "punkte": t["punkte"], "quelle": t["quelle"], "hinweis": f"{GILT[land]} · Keine Rechtsberatung",
                "bild": bild, "bild_pos": pos}},
            {"datei": "story_1_titel.png", "format": "story", "folie": titel},
            {"datei": "story_2_fall.png", "format": "story", "folie": dict(fall, label=f"Fall {nr}")},
            {"datei": "story_3_frage.png", "format": "story", "folie": dict(
                frage, label=f"Fall {nr}", aufruf="Antworte mit A oder B – die Auflösung kommt per DM.")}],
        "bildunterschrift": bildunterschrift(f)}


def main(a):
    nr, datum = a[0], a[1]
    db_pfad = BASIS / "faelle.json"
    db = json.loads(db_pfad.read_text(encoding="utf-8"))
    f = next(x for x in db["faelle"] if x["nr"] == nr)
    ziel = BASIS / "posts" / datum
    ziel.mkdir(parents=True, exist_ok=True)
    (ziel / "post.json").write_text(json.dumps(post(f, datum), ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for k in ("A", "B"):
        inhalt = json.dumps(dm(nr, k == f["richtig"]), ensure_ascii=False, indent=1) + "\n"
        for name in (nr, str(int(nr))):
            (BASIS / "dm" / "fall" / f"{name}-{k}.json").write_text(inhalt, encoding="utf-8")
    f["status"], f["geplant_fuer"] = "geplant", datum
    db_pfad.write_text(json.dumps(db, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"ok {nr} -> posts/{datum}/post.json · Bildunterschrift {len(bildunterschrift(f))} Zeichen")


if __name__ == "__main__":
    main(sys.argv[1:])

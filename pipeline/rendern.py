"""Kanal-Werkstatt – rendert alle Bilder und das Reel eines Beitrags aus post.json und baut die Sichtprüfung.

Aufruf:
  python3 rendern.py post.json out/ [--design design.json] [--audio musik.wav] [--ohne-reel] [--nur-reel]

post.json (Felder siehe README der Werkstatt):
  "bilder":    [{"datei": "frage.png", "format": "karte", "folie": {...}}, ...]
  "karussell": {"format": "karte", "datei": "karussell_{n}.png", "folien": [{...}, ...]}
  "reel":      {"datei": "reel.mp4", "cover": "cover.jpg", "schleife": true, "szenen": [{"folie": {...}, "dauer": 2.4}, ...]}
  "bildunterschrift": "..."
Ergebnis in out/: Bilder, reel.mp4 + cover.jpg, pruefung/kontaktbogen.png (mit Schutzzonen), render_log.json.
Exit-Code 3 = Problem: Text passt nicht (Überlauf -> kürzen, neu rendern) oder ein Bild fehlt.
Texthinweise (ß, Hashtags, Leerzeichen) stehen im Log und in der Ausgabe.
"""
import argparse
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bausteine as B  # noqa: E402
import werkstatt as W  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("post")
    ap.add_argument("out")
    ap.add_argument("--design")
    ap.add_argument("--audio")
    ap.add_argument("--ohne-reel", action="store_true")
    ap.add_argument("--nur-reel", action="store_true")
    a = ap.parse_args()

    postpfad = pathlib.Path(a.post).resolve()
    base = postpfad.parent
    post = W.lade(postpfad)
    dpfad = pathlib.Path(a.design) if a.design else base / post.get("design", "design.json")
    if not dpfad.exists():
        sys.exit(f"design.json nicht gefunden: {dpfad}")
    d = W.lade(dpfad)
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    pruef = out / "pruefung"
    pruef.mkdir(exist_ok=True)

    auftraege = []
    for b in post.get("bilder", []):
        fmt = b.get("format", "karte")
        w, h = W.FORMATE[fmt][:2]
        auftraege.append({"html": B.seite(b["folie"], d, fmt, base), "w": w, "h": h, "datei": out / b["datei"], "format": fmt})
    k = post.get("karussell")
    if k:
        fmt = k.get("format", "karte")
        w, h = W.FORMATE[fmt][:2]
        for n, f in enumerate(k["folien"], 1):
            auftraege.append({"html": B.seite(f, d, fmt, base), "w": w, "h": h,
                              "datei": out / k.get("datei", "karussell_{n}.png").format(n=n), "format": fmt})

    log = {"bilder": [], "reel": None}
    bogen = []
    if auftraege and not a.nur_reel:
        log["bilder"] = W.rendere_bilder(auftraege)
        for au in auftraege:
            p = pathlib.Path(au["datei"])
            if au["format"] in ("story", "reel"):
                p = W.mit_schutzzonen(p, au["format"], pruef / f"zonen_{p.stem}.png")
            bogen.append((p, pathlib.Path(au["datei"]).name))
            if au["format"] == "profil":  # Vorschau mit Kreisausschnitt wie in Instagram
                from PIL import Image, ImageDraw
                im = Image.open(au["datei"]).convert("RGB")
                maske = Image.new("L", im.size, 0)
                ImageDraw.Draw(maske).ellipse((0, 0, im.width, im.height), fill=255)
                kreis = Image.new("RGB", im.size, (255, 255, 255))
                kreis.paste(im, (0, 0), maske)
                kreis.save(pruef / f"kreis_{p.stem}.png")
                bogen.append((pruef / f"kreis_{p.stem}.png", "Profil im Kreis"))

    r = post.get("reel")
    if r and not a.ohne_reel:
        doc, dauer, meta = B.reel_seite(r, d, base)
        video = out / r.get("datei", "reel.mp4")
        cover = out / r.get("cover", "cover.jpg")
        audio = a.audio or r.get("audio")
        if audio and not pathlib.Path(audio).is_absolute() and not pathlib.Path(audio).exists():
            audio = str(base / audio)
        info = W.rendere_video(doc, dauer, video, audio=audio, cover=cover, cover_t=r.get("cover_t", 0.3))
        info["szenen"] = meta
        log["reel"] = info
        # Prüfbilder: erstes Bild (entscheidet über die Skip-Rate) + je Szene ein Bild gegen Ende
        zeiten = [0.0] + [round(m["t0"] + min(m["dauer"] - 0.35, max(1.0, m["dauer"] * 0.8)), 2)
                          for m in meta if not m.get("schleife")]
        for i, t in enumerate(zeiten):
            roh = W.einzelbild(video, t, pruef / f"reel_{t:05.2f}s.png")
            bogen.append((W.mit_schutzzonen(roh, "reel", pruef / f"zonen_reel_{t:05.2f}s.png"),
                          "Reel · erstes Bild" if i == 0 else f"Reel · {t:.1f} s".replace(".", ",")))
        bogen.append((cover, "Cover"))

    log["texthinweise"] = W.pruefe_texte(post, d.get("schweizer_schreibweise", True))
    log["fehlende_bilder"] = sorted(set(B.FEHLENDE_BILDER))
    if bogen:
        W.kontaktbogen(bogen, pruef / "kontaktbogen.png")
    W.speichere(log, out / "render_log.json")

    probleme = []
    for b in log["bilder"]:
        probleme += [f'{pathlib.Path(b["datei"]).name}: Box «{x["box"]}» läuft über' for x in b["einpassen"] if x["ueberlauf"]]
    if log["reel"]:
        probleme += [f'Reel: Box «{x["box"]}» läuft über' for x in log["reel"]["einpassen"] if x["ueberlauf"]]
    probleme += [f"Bild fehlt (ohne Foto gerendert): {b}" for b in log["fehlende_bilder"]]
    print(f"Bilder: {len(log['bilder'])} · Reel: {'ja' if log['reel'] else 'nein'} · Kontaktbogen: {pruef / 'kontaktbogen.png'}")
    for h in log["texthinweise"]:
        print("Hinweis:", h)
    for p in probleme:
        print("PROBLEM:", p)
    klein = [x for b in log["bilder"] for x in b["einpassen"] if x["faktor"] < 0.75 and not x["ueberlauf"]]
    if klein:
        print(f"Achtung: {len(klein)} Box(en) mussten stark verkleinert werden (< 75 %) – Text kürzen ist besser.")
    sys.exit(3 if probleme else 0)


if __name__ == "__main__":
    main()

"""Kanal-Werkstatt – Fotos von Pixabay suchen, ansehen und laden.

Schlüssel aus der Umgebungsvariable PIXABAY_KEY (Wert steht in der Basis-Konfiguration im Projekt,
nie in Dateien oder Repos schreiben). Pixabay-Inhaltslizenz: kommerziell nutzbar ohne Namensnennung,
aber kein Hotlinking -> Bilder immer herunterladen und selbst ausliefern.
Regeln: nur Fotos, keine KI-Bilder (entsprechende Tags werden ausgeschlossen), keine erkennbaren
Personen oder Logos (das prüft die Sichtprüfung, nicht dieses Skript).

  python3 bilder.py suche "<Suchbegriff>" <ordner> [--n 8] [--ausrichtung horizontal|vertical|all] [--sprache de]
      -> lädt Vorschauen nach <ordner>/, schreibt kandidaten.json und uebersicht.jpg (mit IDs) zum Ansehen
  python3 bilder.py laden <ID> <ziel.jpg>
      -> lädt das grosse Bild (largeImageURL) und gibt die Quellenangabe aus («Pixabay #ID»)
"""
import json
import os
import pathlib
import sys
import urllib.parse
import urllib.request

API = "https://pixabay.com/api/"
KI_TAGS = ("ai generated", "ai-generated", "generated", "ki generiert", "ki-generiert", "midjourney", "dall-e")


def _key():
    k = os.environ.get("PIXABAY_KEY")
    if not k:
        sys.exit("PIXABAY_KEY fehlt (Wert aus der Basis-Konfiguration im Projekt setzen)")
    return k


# Pixabay weist den Standard-User-Agent von Python ab (HTTP 403) -> eigener User-Agent für alle Abrufe
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) kanal-werkstatt/1.0"}


def _json(params):
    q = urllib.parse.urlencode({"key": _key(), **params})
    with urllib.request.urlopen(urllib.request.Request(API + "?" + q, headers=UA), timeout=30) as r:
        return json.loads(r.read().decode())


def _laden(url, ziel):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        pathlib.Path(ziel).write_bytes(r.read())


def suche(begriff, ordner, n=8, ausrichtung="horizontal", sprache="de"):
    ordner = pathlib.Path(ordner)
    ordner.mkdir(parents=True, exist_ok=True)
    daten = _json({"q": begriff, "image_type": "photo", "safesearch": "true", "orientation": ausrichtung,
                   "lang": sprache, "per_page": max(3, min(50, n * 3))})
    treffer = []
    for h in daten.get("hits", []):
        tags = h.get("tags", "").lower()
        if any(t in tags for t in KI_TAGS) or h.get("type") != "photo":
            continue
        datei = ordner / f"{h['id']}.jpg"
        _laden(h["webformatURL"], datei)
        treffer.append({"id": h["id"], "tags": h.get("tags"), "seite": h.get("pageURL"), "datei": str(datei),
                        "breite": h.get("imageWidth"), "hoehe": h.get("imageHeight")})
        if len(treffer) >= n:
            break
    (ordner / "kandidaten.json").write_text(json.dumps(treffer, ensure_ascii=False, indent=1), encoding="utf-8")
    if treffer:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
        from werkstatt import kontaktbogen
        kontaktbogen([(t["datei"], f"#{t['id']}") for t in treffer], ordner / "uebersicht.jpg", breite=320, spalten=4)
    print(json.dumps({"treffer": len(treffer), "uebersicht": str(ordner / "uebersicht.jpg")}, ensure_ascii=False))
    return treffer


def laden(bild_id, ziel):
    daten = _json({"id": str(bild_id)})
    hits = daten.get("hits", [])
    if not hits:
        sys.exit(f"Bild {bild_id} nicht gefunden")
    pathlib.Path(ziel).parent.mkdir(parents=True, exist_ok=True)
    _laden(hits[0]["largeImageURL"], ziel)
    print(json.dumps({"datei": str(ziel), "bild_quelle": f"Pixabay #{bild_id}"}, ensure_ascii=False))


if __name__ == "__main__":
    a = sys.argv[1:]
    if len(a) >= 3 and a[0] == "suche":
        opt = {"n": 8, "ausrichtung": "horizontal", "sprache": "de"}
        for i, x in enumerate(a):
            if x.startswith("--") and i + 1 < len(a):
                opt[x[2:]] = a[i + 1]
        suche(a[1], a[2], int(opt["n"]), opt["ausrichtung"], opt["sprache"])
    elif len(a) == 3 and a[0] == "laden":
        laden(a[1], a[2])
    else:
        print(__doc__)
        sys.exit(1)

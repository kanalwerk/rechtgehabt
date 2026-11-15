"""Kanal-Werkstatt – Musik fürs Reel (für alle Kanäle).

1) Katalog (Standard): Titel aus der Meta Sound Collection im privaten Musik-Repo der gemeinsamen Basis.
   Lizenz: nur in Inhalten auf Facebook/Instagram verwenden, nie separat verbreiten -> Repo bleibt privat,
   ein Reel mit diesen Titeln nie dauerhaft in ein öffentliches Repo legen (siehe Technik-Muster «medien»).
     python3 musik.py katalog <musik-repo> --stimmung inspirierend,filmisch --nicht "Titel A,Titel B" --dauer 12.8 out.wav
   katalog.json (aus katalog.py + stimme.py) enthält pro Titel die gesangsfreie Stelle «start» (geprüft für 12,8 s),
   «stimmung» (ruhig | inspirierend | energisch | filmisch) und «bereiche». Titel mit «ungeeignet» werden nie gewählt.

2) Ersatz: eigene, synthetisch erzeugte Musik (musikbox.py, keine Rechte Dritter), wenn der Katalog fehlt:
     python3 musik.py ersatz --stimmung inspirierend --seed 20261116 --dauer 12.8 out.wav [--nicht-stil 3]
   Freigegebene Stile (Timo, 13.11.2026): 2 Lo-Fi (ruhig), 3 Klavier (inspirierend), 5 Synthwave (energisch),
   8 Filmisch (filmisch).

Ausgabe: JSON (titel bzw. stil, start, stimmung) -> im Verlauf des Kanals speichern (keine Wiederholung in 7 Tagen).
"""
import json
import pathlib
import random
import subprocess
import sys
import tempfile

import numpy as np
from scipy.io import wavfile

SR = 44100
ERSATZ_STILE = {"ruhig": [2], "inspirierend": [3], "energisch": [5], "filmisch": [8]}


def _opt(a, name, std=None):
    return a[a.index(name) + 1] if name in a else std


def _lade(pfad, start, dauer):
    tmp = pathlib.Path(tempfile.mkdtemp()) / "x.wav"
    subprocess.run(["ffmpeg", "-nostdin", "-y", "-loglevel", "error", "-ss", f"{start:.2f}", "-t", f"{dauer:.2f}",
                    "-i", str(pfad), "-ac", "2", "-ar", str(SR), str(tmp)], check=True)
    _, x = wavfile.read(tmp)
    return x.astype(float) / 32768.0


def schneide(pfad, start, out, dauer):
    """Ausschnitt mitten im Titel, weich ein- und ausgeblendet, auf -16 dB RMS gebracht."""
    seg = _lade(pfad, start, dauer)
    n = int(dauer * SR)
    if len(seg) < n:
        seg = np.pad(seg, ((0, n - len(seg)), (0, 0)))
    seg = seg[:n]
    fi, fo = int(0.35 * SR), int(0.9 * SR)
    seg[:fi] *= np.linspace(0, 1, fi)[:, None] ** 0.7
    seg[-fo:] *= np.linspace(1, 0, fo)[:, None] ** 1.5
    seg *= 10 ** (-16 / 20) / max(np.sqrt(np.mean(seg ** 2)), 1e-9)
    pk = np.max(np.abs(seg))
    if pk > 0.95:
        seg *= 0.95 / pk
    wavfile.write(out, SR, (seg * 32767).astype(np.int16))


def katalog(a):
    repo, out = pathlib.Path(a[1]), a[-1]
    dauer = float(_opt(a, "--dauer", 12.8))
    stimmungen = [s for s in (_opt(a, "--stimmung", "") or "").split(",") if s]
    nicht = [t for t in (_opt(a, "--nicht", "") or "").split(",") if t]
    kat = json.load(open(repo / "katalog.json", encoding="utf-8"))
    ok = {n: e for n, e in kat.items() if "start" in e and not e.get("ungeeignet") and n not in nicht}
    pool = [n for n, e in ok.items() if not stimmungen or e.get("stimmung") in stimmungen] or list(ok)
    if not pool:
        print(json.dumps({"fehler": "kein geeigneter Titel"}))
        sys.exit(2)
    titel = _opt(a, "--titel") or random.Random("".join(a)).choice(sorted(pool))
    e = kat[titel]
    schneide(repo / e["datei"], e["start"], out, dauer)
    info = {"quelle": "katalog", "titel": titel, "start": e["start"], "stimmung": e.get("stimmung")}
    if dauer > 12.8:
        info["warnung"] = "Stelle ist nur für 12,8 s auf Gesang geprüft – Ausschnitt anhören"
    print(json.dumps(info, ensure_ascii=False))


def ersatz(a):
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    import musikbox
    out = a[-1]
    musikbox.DUR = float(_opt(a, "--dauer", 12.8))
    seed = int(_opt(a, "--seed", 1))
    stile = ERSATZ_STILE.get(_opt(a, "--stimmung", "inspirierend"), [3])
    nicht = int(_opt(a, "--nicht-stil", 0) or 0)
    wahl = [s for s in stile if s != nicht] or stile
    info = musikbox.variante(wahl[seed % len(wahl)], out, seed)
    info.update({"quelle": "ersatz", "stimmung": _opt(a, "--stimmung", "inspirierend")})
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "katalog" and len(args) >= 3:
        katalog(args)
    elif args and args[0] == "ersatz" and len(args) >= 2:
        ersatz(args)
    else:
        print(__doc__)
        sys.exit(1)

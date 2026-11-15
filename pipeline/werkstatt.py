"""Kanal-Werkstatt – Kernbibliothek (gilt für alle Kanäle).

Rendert HTML zu PNG und MP4 (Playwright + ffmpeg), passt Text automatisch ein, zieht Einzelbilder
aus Videos, baut Kontaktbögen für die Sichtprüfung und prüft Texte nach einfachen Regeln.
Gestaltung und Layouts liegen in bausteine.py (pro Kanal anpassbar), Farben und Schriften in design.json.
Diese Datei bleibt in allen Kanälen gleich – Verbesserungen hier in die Werkstatt zurückführen.
"""
from __future__ import annotations

import base64
import html
import json
import pathlib
import re
import subprocess

NBSP = " "

# Format: (Breite, Höhe, Schutzrand oben, rechts, unten, links) in px.
# Reel: rechts 150 px (Knöpfe), unten 420 px (Name/Bildunterschrift), oben 250 px.
# Story: oben 250 px (Profilzeile), unten 300 px (Antwortfeld).
FORMATE = {
    "karte": (1080, 1350, 84, 88, 84, 88),
    "karte_lang": (1080, 1500, 84, 88, 84, 88),
    "quadrat": (1080, 1080, 80, 80, 80, 80),
    "story": (1080, 1920, 250, 90, 300, 90),
    "reel": (1080, 1920, 250, 150, 420, 90),
    "profil": (1080, 1080, 0, 0, 0, 0),
}
# Schriftgrösse je Format (Story und Reel werden im Vollbild gelesen -> etwas grösser)
SKALA = {"karte": 1.0, "karte_lang": 1.0, "quadrat": 0.92, "story": 1.14, "reel": 1.24, "profil": 1.0}


# ------------------------------------------------------------------ Dateien und Text
def lade(pfad):
    return json.loads(pathlib.Path(pfad).read_text(encoding="utf-8"))


def speichere(obj, pfad):
    pathlib.Path(pfad).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def schuetze(t) -> str:
    """Geschützte Leerzeichen vor « – » und vor «%»: Gedankenstrich und Prozentzeichen nie am Zeilenanfang."""
    t = "" if t is None else str(t)
    return t.replace(" – ", NBSP + "– ").replace(" %", NBSP + "%")


def esc(t) -> str:
    """Text HTML-sicher machen (mit geschützten Leerzeichen, siehe schuetze)."""
    return html.escape(schuetze(t))


def woerter(t) -> str:
    """Text in Wörter (span.w) zerlegen, damit das Reel sie nacheinander einblenden kann.
    Weiche Trennstriche (U+00AD) in langen Wörtern bleiben wirksam."""
    return " ".join(f'<span class="w">{html.escape(w)}</span>' for w in schuetze(t).split(" ") if w)


def bild_uri(pfad) -> str:
    p = pathlib.Path(pfad)
    mime = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "webp": "image/webp",
            "svg": "image/svg+xml", "gif": "image/gif"}[p.suffix.lower().lstrip(".")]
    return f"data:{mime};base64," + base64.b64encode(p.read_bytes()).decode()


def zahl(wert, dezimalen=0, tausender="’", dezimal=",") -> str:
    """12345.6 -> «12’345,6» (Schweizer Schreibweise; für DE/AT tausender='.' setzen)."""
    s = f"{float(wert):,.{dezimalen}f}"
    return s.replace(",", "\x00").replace(".", dezimal).replace("\x00", tausender)


# ------------------------------------------------------------------ Einpassen
# Jeder Container mit data-box (fixe Höhe, overflow:hidden) wird geprüft. Elemente darin mit data-fit
# werden gemeinsam verkleinert, bis nichts mehr überläuft (data-fit="0.6" = höchstens auf 60 %).
# Geprüft wird auch die Breite: Ein Wort, das breiter ist als seine Zeile, zählt als Überlauf.
FIT_JS = r"""
(() => {
  const out = [];
  const textRechts = (el) => { const r = document.createRange(); r.selectNodeContents(el);
    let m = -1e9; for (const q of r.getClientRects()) m = Math.max(m, q.right); return m; };
  // rechte Kante des nächsten Block-Elements (bei span.zahl also die Kante der umgebenden Zeile)
  const kante = (el) => { let b = el; while (b.parentElement && getComputedStyle(b).display.startsWith('inline')) b = b.parentElement;
    return b.getBoundingClientRect().right; };
  const zuBreit = (els, box) => { const rb = box.getBoundingClientRect().right;
    return els.some(el => textRechts(el) > Math.min(kante(el), rb) + 1.5); };
  const zuHoch = (box) => box.scrollHeight > box.clientHeight + 1;
  document.querySelectorAll('[data-box]').forEach(box => {
    const els = [...box.querySelectorAll('[data-fit]')];
    const basis = els.map(el => parseFloat(getComputedStyle(el).fontSize));
    const minf = els.map(el => parseFloat(el.dataset.fit) || 0.6);
    let k = 1;
    while (els.length && (zuHoch(box) || zuBreit(els, box)) && k > 0.35) {
      k = Math.round((k - 0.02) * 100) / 100;
      els.forEach((el, i) => { el.style.fontSize = (basis[i] * Math.max(k, minf[i])) + 'px'; });
      if (els.every((el, i) => k <= minf[i])) break;
    }
    out.push({box: box.dataset.box, faktor: k, ueberlauf: zuHoch(box) || zuBreit(els, box)});
  });
  return out;
})()
"""


# ------------------------------------------------------------------ Rendern
def rendere_bilder(auftraege):
    """auftraege: Liste von {"html", "w", "h", "datei"}. Rendert PNG/JPG, gibt Einpass-Infos zurück."""
    from playwright.sync_api import sync_playwright
    infos = []
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        for a in auftraege:
            pg = b.new_page(viewport={"width": a["w"], "height": a["h"]})
            pg.set_content(a["html"], wait_until="load")
            pg.wait_for_timeout(120)
            fit = pg.evaluate(FIT_JS)
            datei = pathlib.Path(a["datei"])
            datei.parent.mkdir(parents=True, exist_ok=True)
            if datei.suffix.lower() in (".jpg", ".jpeg"):
                pg.screenshot(path=str(datei), type="jpeg", quality=92)
            else:
                pg.screenshot(path=str(datei))
            infos.append({"datei": str(datei), "einpassen": fit})
            pg.close()
        b.close()
    return infos


def rendere_video(html_doc, dauer, datei, w=1080, h=1920, fps=30, audio=None, cover=None, cover_t=0.3):
    """Rendert eine HTML-Animation mit window.render(t) Bild für Bild zu MP4 (H.264, 30 fps).
    Optional: Ton (wird mit Stille aufgefüllt und auf die Videolänge geschnitten) und Titelbild (JPG)."""
    from playwright.sync_api import sync_playwright
    datei = pathlib.Path(datei)
    datei.parent.mkdir(parents=True, exist_ok=True)
    n = int(round(dauer * fps))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-"]
    if audio:
        cmd += ["-i", str(audio), "-af", "apad", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    cmd += ["-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps),
            "-movflags", "+faststart", str(datei)]
    ff = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page(viewport={"width": w, "height": h})
        pg.set_content(html_doc, wait_until="load")
        pg.wait_for_timeout(300)
        fit = pg.evaluate(FIT_JS)
        pg.evaluate("window.vorbereiten && window.vorbereiten()")
        for i in range(n):
            pg.evaluate(f"render({i / fps:.5f})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=93))
        if cover:
            pg.evaluate(f"render({cover_t})")
            pg.screenshot(path=str(cover), type="jpeg", quality=92)
        b.close()
    ff.stdin.close()
    ff.wait()
    if ff.returncode:
        raise RuntimeError("ffmpeg hat einen Fehler gemeldet")
    return {"datei": str(datei), "dauer": dauer, "bilder": n, "einpassen": fit}


# ------------------------------------------------------------------ Prüfen
def einzelbild(video, t, datei):
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{t:.2f}", "-i", str(video),
                    "-frames:v", "1", str(datei)], check=True)
    return pathlib.Path(datei)


def _schrift(px):
    from PIL import ImageFont
    for p in ("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if pathlib.Path(p).exists():
            return ImageFont.truetype(p, px)
    return ImageFont.load_default()


def mit_schutzzonen(pfad, fmt, ziel):
    """Kopie des Bildes mit rot markierten Schutzzonen (dort darf kein Text stehen)."""
    from PIL import Image, ImageDraw
    w, h, so, sr, su, sl = FORMATE[fmt]
    im = Image.open(pfad).convert("RGB").resize((w, h))
    ov = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    rot = (230, 40, 40, 70)
    for box in ((0, 0, w, so), (0, h - su, w, h), (w - sr, so, w, h - su), (0, so, sl, h - su)):
        if box[2] > box[0] and box[3] > box[1]:
            d.rectangle(box, fill=rot)
    Image.alpha_composite(im.convert("RGBA"), ov).convert("RGB").save(ziel)
    return pathlib.Path(ziel)


def kontaktbogen(eintraege, datei, breite=300, spalten=4, rand=22):
    """eintraege: [(bildpfad, beschriftung)] -> ein Übersichtsbild (PNG) zum Ansehen mit Read."""
    from PIL import Image, ImageDraw
    bilder = []
    for pfad, text in eintraege:
        im = Image.open(pfad).convert("RGB")
        hh = round(im.height * breite / im.width)
        bilder.append((im.resize((breite, hh), Image.LANCZOS), str(text)))
    if not bilder:
        return None
    zeilen = [bilder[i:i + spalten] for i in range(0, len(bilder), spalten)]
    th, schrift = 30, _schrift(19)
    hoehen = [max(b.height for b, _ in z) + th for z in zeilen]
    W = rand + min(spalten, len(bilder)) * (breite + rand)
    H = rand + sum(x + rand for x in hoehen)
    bogen = Image.new("RGB", (W, H), (236, 233, 226))
    d = ImageDraw.Draw(bogen)
    y = rand
    for z, hz in zip(zeilen, hoehen):
        x = rand
        for b, text in z:
            d.text((x, y + 2), text[:34], fill=(35, 35, 35), font=schrift)
            bogen.paste(b, (x, y + th))
            d.rectangle([x - 1, y + th - 1, x + b.width, y + th + b.height], outline=(170, 165, 155))
            x += breite + rand
        y += hz + rand
    bogen.save(datei)
    return pathlib.Path(datei)


_TECHNISCH = {"bild", "datei", "url", "bild_pos", "bild_quelle", "layout", "format", "thema", "symbol",
              "farbe", "audio", "cover", "position", "richtig", "key", "design"}


def pruefe_texte(post, schweiz=True):
    """Einfache Textregeln für alle Kanäle. Gibt eine Liste von Hinweisen zurück (leer = alles gut)."""
    hinweise = []

    def texte(x, pfad=""):
        if isinstance(x, str):
            yield pfad, x
        elif isinstance(x, dict):
            for k, v in x.items():
                if k not in _TECHNISCH:
                    yield from texte(v, f"{pfad}.{k}" if pfad else k)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                yield from texte(v, f"{pfad}[{i}]")

    for pfad, t in texte(post):
        if schweiz and "ß" in t:
            hinweise.append(f"{pfad}: «ß» gefunden – Schweizer Schreibweise verlangt «ss»")
        if "  " in t:
            hinweise.append(f"{pfad}: doppeltes Leerzeichen")
        if re.search(r"\bKI-generiert|Symbolbild\b", t):
            hinweise.append(f"{pfad}: enthält «Symbolbild/KI-generiert» – bewusst so gewollt?")
    cap = post.get("bildunterschrift", "")
    if cap:
        tags = re.findall(r"#\w+", cap)
        if len(tags) > 5:
            hinweise.append(f"bildunterschrift: {len(tags)} Hashtags – Instagram erlaubt höchstens 5")
        if len(cap) > 2200:
            hinweise.append(f"bildunterschrift: {len(cap)} Zeichen – höchstens 2200")
        if re.search(r"\d %", cap):
            hinweise.append("bildunterschrift: normales Leerzeichen vor % – geschütztes Leerzeichen (U+00A0) setzen")
    return hinweise

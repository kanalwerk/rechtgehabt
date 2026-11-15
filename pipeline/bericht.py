"""Kanal-Werkstatt – Tagesbericht als HTML-Seite (für alle Kanäle).

Aufruf: python3 bericht.py bericht.json bericht.html
Pfade in bericht.json sind relativ zu bericht.json. Bilder und Videobilder werden verkleinert als data:-URI
eingebettet (externe Hosts sind in Artifact-Seiten gesperrt). Ergebnis ist ein vollständiges HTML-Dokument,
das mit dem Artifact-Werkzeug als Seite «<Kanal> · Tagesbericht» veröffentlicht oder als Datei gesendet wird.

bericht.json:
{
 "kanal": "Fall des Tages", "titel": "Tagesbericht 16.11.2026",
 "status": "probelauf" | "eingeplant" | "veroeffentlicht" | "abgebrochen",
 "eckdaten": [["Thema", "…"], ["Reel", "19:30 Uhr · Metricool #123"], ["Musik", "…"]],
 "elemente": [
   {"titel": "Reel · erstes Bild", "video": "out/reel.mp4", "t": 0.0, "inhalt": "…", "kommentar": "…", "status": "ok"},
   {"titel": "DM-Karte", "bild": "out/dm_aufloesung.png", "inhalt": "…", "kommentar": "…", "status": "hinweis"}
 ],
 "bildunterschrift": "…",
 "quellen": [{"fuer": "Fall", "titel": "…", "url": "https://…"}],
 "reflexion": ["…"], "probleme": ["…"], "notizen": ["…"]
}
status je Element: ok | hinweis | problem
"""
import base64
import html
import io
import json
import pathlib
import subprocess
import sys
import tempfile

from PIL import Image

STATUS = {"ok": "OK", "hinweis": "Hinweis", "problem": "Problem"}
LAUF = {"probelauf": "Probelauf – nichts veröffentlicht", "eingeplant": "Eingeplant in Metricool",
        "veroeffentlicht": "Veröffentlicht", "abgebrochen": "Abgebrochen – nichts gepostet"}


def e(s):
    return html.escape(str(s if s is not None else ""))


def vorschau(pfad, breite=340):
    im = Image.open(pfad).convert("RGB")
    im = im.resize((breite, round(im.height * breite / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=78, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def videobild(video, t, tmp):
    p = pathlib.Path(tmp) / f"f_{t}.png"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", str(p)], check=True)
    return p


def liste(xs):
    return "<ul>" + "".join(f"<li>{e(x)}</li>" for x in xs) + "</ul>" if xs else "<p class='leer'>Keine.</p>"


def main(ber_p, html_p):
    ber_p = pathlib.Path(ber_p)
    base = ber_p.parent
    b = json.loads(ber_p.read_text(encoding="utf-8"))
    zeilen = []
    with tempfile.TemporaryDirectory() as tmp:
        for el in b.get("elemente", []):
            if el.get("video"):
                bild = videobild(base / el["video"], el.get("t", 0), tmp)
            elif el.get("bild"):
                bild = base / el["bild"]
            else:
                bild = None
            src = vorschau(bild) if bild else ""
            st = el.get("status", "ok")
            zeilen.append(f"""<tr class="st-{e(st)}">
  <td class="el"><span class="pill {e(st)}">{e(STATUS.get(st, st))}</span><strong>{e(el.get('titel'))}</strong></td>
  <td class="img">{f'<img src="{src}" alt="{e(el.get("titel"))}">' if src else ''}</td>
  <td class="inh">{e(el.get('inhalt'))}</td>
  <td class="kom">{e(el.get('kommentar'))}</td></tr>""")
    eck = [("Status", LAUF.get(b.get("status"), b.get("status", "")))] + [tuple(x) for x in b.get("eckdaten", [])]
    eck_html = "".join(f"<tr><th>{e(k)}</th><td>{e(v)}</td></tr>" for k, v in eck)
    def quelle(q):
        tag = "<span class='tag'>" + e(q.get("fuer")) + "</span> " if q.get("fuer") else ""
        return (f'<li>{tag}<a href="{e(q.get("url", "#"))}" target="_blank" rel="noopener">'
                f'{e(q.get("titel"))}</a></li>')
    quellen = "<ul>" + "".join(quelle(q) for q in b.get("quellen", [])) + "</ul>"
    tabelle = "" if not zeilen else f"""<section><h2>Vorschau &amp; Prüfung</h2><div class="scroll"><table class="vor">
<thead><tr><th>Element</th><th>Vorschau</th><th>Inhalt</th><th>Kommentar</th></tr></thead><tbody>{''.join(zeilen)}</tbody>
</table></div></section>"""
    cap = (f'<section><h2>Bildunterschrift</h2><pre class="cap">{e(b["bildunterschrift"])}</pre></section>'
           if b.get("bildunterschrift") else "")
    titel = f'{b.get("kanal", "")} · {b.get("titel", "Tagesbericht")}'
    doc = f"""<!DOCTYPE html>
<html lang="de-CH"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(titel)}</title>
<style>
:root{{--bg:#f4f2ee;--panel:#fff;--fg:#15171e;--muted:#5d6170;--line:#dedbd3;--accent:#2f8f83;
  --ok:#2f8f5b;--ok-bg:#e2f2e8;--warn:#a86b00;--warn-bg:#fbefd5;--bad:#b3382c;--bad-bg:#f8e1de;
  --sans:Inter,system-ui,-apple-system,'Segoe UI',sans-serif}}
@media (prefers-color-scheme:dark){{:root{{--bg:#121419;--panel:#1b1e25;--fg:#ecebe7;--muted:#a1a5b2;--line:#2e323c;
  --accent:#5cc0b2;--ok:#6fd39a;--ok-bg:#173325;--warn:#f0b445;--warn-bg:#3a2c10;--bad:#f08a7e;--bad-bg:#3d1c19;color-scheme:dark}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);font-size:15px;line-height:1.5}}
.wrap{{max-width:1120px;margin:0 auto;padding:28px max(16px,env(safe-area-inset-right)) 56px max(16px,env(safe-area-inset-left));
  display:grid;gap:28px}}
h1{{font-size:28px;font-weight:800;letter-spacing:-.02em;margin:0;text-wrap:balance}}
h2{{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:0 0 10px;font-weight:700}}
section{{min-width:0}}
table{{border-collapse:collapse;width:100%;background:var(--panel);border:1px solid var(--line);border-radius:12px;overflow:hidden}}
th,td{{text-align:left;vertical-align:top;padding:10px 14px;border-bottom:1px solid var(--line)}}
tr:last-child>*{{border-bottom:0}}
.eck th{{width:170px;color:var(--muted);font-weight:600}}
.scroll{{overflow-x:auto}} .vor{{min-width:760px}}
.vor thead th{{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);background:var(--bg)}}
.vor td.el{{width:150px}} .vor td.el strong{{display:block;margin-top:6px}}
.vor td.img{{width:190px}} .vor img{{display:block;width:170px;border-radius:8px;border:1px solid var(--line)}}
.vor td.inh{{width:34%}}
.pill{{display:inline-block;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;padding:2px 8px;border-radius:999px}}
.pill.ok{{color:var(--ok);background:var(--ok-bg)}} .pill.hinweis{{color:var(--warn);background:var(--warn-bg)}}
.pill.problem{{color:var(--bad);background:var(--bad-bg)}}
.st-hinweis td.el{{box-shadow:inset 3px 0 0 var(--warn)}} .st-problem td.el{{box-shadow:inset 3px 0 0 var(--bad)}}
.cols{{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:28px}}
.box{{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 18px}}
.box ul{{margin:0;padding-left:18px;display:grid;gap:6px}} .leer{{margin:0;color:var(--muted)}}
a{{color:var(--accent)}} .tag{{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;padding:1px 6px;
  border-radius:4px;background:var(--bg)}}
pre.cap{{margin:0;white-space:pre-wrap;font-family:var(--sans);background:var(--panel);border:1px solid var(--line);
  border-radius:12px;padding:14px 18px}}
</style></head><body><div class="wrap">
<header><h1>{e(titel)}</h1></header>
<section><h2>Eckdaten</h2><table class="eck"><tbody>{eck_html}</tbody></table></section>
{tabelle}
<div class="cols"><section><h2>Reflexion</h2><div class="box">{liste(b.get('reflexion', []))}</div></section>
<section><h2>Probleme</h2><div class="box">{liste(b.get('probleme', []))}</div></section></div>
<div class="cols"><section><h2>Quellen</h2><div class="box">{quellen}</div></section>
<section><h2>Notizen</h2><div class="box">{liste(b.get('notizen', []))}</div></section></div>
{cap}
</div></body></html>"""
    pathlib.Path(html_p).write_text(doc, encoding="utf-8")
    print("ok", html_p, len(doc) // 1024, "KB")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1], sys.argv[2])

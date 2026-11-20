"""Kanal-Werkstatt – Bausteine: Layouts für Karten, Stories, Karussells, Profilbild und Reel-Szenen.

Eine Folie ist ein dict mit "layout" und Inhaltsfeldern (Übersicht in README.md der Werkstatt).
Farben, Schriften, Wortmarke und Stichwort kommen aus design.json. Pro Kanal darf diese Datei
kopiert und angepasst werden (eigene Layouts in LAYOUTS ergänzen); werkstatt.py bleibt gleich.

Layouts: titel, text, karte, aufloesung, frage, zahl, liste, vergleich, aufruf, profil
Themen pro Folie: "hell", "dunkel", "akzent" (mit Foto automatisch "foto").
"""
from __future__ import annotations

import json
import pathlib

from werkstatt import FORMATE, SKALA, bild_uri, esc, woerter, zahl as fmt_zahl

# ------------------------------------------------------------------ Symbole (einfarbig, currentColor)
_S = {
    "sonne": '<circle cx="50" cy="50" r="19" fill="currentColor"/>' + "".join(
        f'<rect x="47" y="6" width="6" height="16" rx="3" fill="currentColor" transform="rotate({a} 50 50)"/>'
        for a in range(0, 360, 45)),
    "regen": '<g fill="currentColor"><circle cx="34" cy="46" r="15"/><circle cx="55" cy="36" r="20"/>'
             '<circle cx="74" cy="49" r="13"/><rect x="19" y="44" width="68" height="18" rx="9"/></g>' + "".join(
        f'<line x1="{x}" y1="74" x2="{x - 5}" y2="90" stroke="currentColor" stroke-width="6" stroke-linecap="round"/>'
        for x in (34, 52, 70)),
    "haken": '<path d="M18 52 L41 75 L84 27" fill="none" stroke="currentColor" stroke-width="11" '
             'stroke-linecap="round" stroke-linejoin="round"/>',
    "kreuz": '<path d="M24 24 L76 76 M76 24 L24 76" fill="none" stroke="currentColor" stroke-width="11" '
             'stroke-linecap="round"/>',
    "waage": '<g fill="none" stroke="currentColor" stroke-width="6" stroke-linecap="round" stroke-linejoin="round">'
             '<path d="M50 16 V84 M32 86 H68 M14 30 H86"/><path d="M20 30 L8 60 M20 30 L32 60 M80 30 L68 60 M80 30 L92 60"/>'
             '<path d="M6 60 Q20 76 34 60 Z M66 60 Q80 76 94 60 Z" fill="currentColor"/></g>'
             '<circle cx="50" cy="14" r="6" fill="currentColor"/>',
    "pin": '<path d="M50 92 C50 92 20 58 20 38 A30 30 0 0 1 80 38 C80 58 50 92 50 92 Z" fill="currentColor"/>'
           '<circle cx="50" cy="38" r="11" fill="var(--hg)"/>',
    "uhr": '<circle cx="50" cy="50" r="38" fill="none" stroke="currentColor" stroke-width="8"/>'
           '<path d="M50 28 V52 L66 62" fill="none" stroke="currentColor" stroke-width="8" stroke-linecap="round"/>',
    "frage": '<circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" stroke-width="8"/>'
             '<path d="M37 39 A13 13 0 1 1 55 51 Q50 54 50 61" fill="none" stroke="currentColor" stroke-width="8" '
             'stroke-linecap="round"/><circle cx="50" cy="74" r="5" fill="currentColor"/>',
    "paragraf": '<text x="50" y="80" text-anchor="middle" font-family="Inter Display" font-weight="800" '
                'font-size="86" fill="currentColor">§</text>',
    "stern": '<path d="M50 8 L61 38 L93 38 L67 57 L77 89 L50 70 L23 89 L33 57 L7 38 L39 38 Z" fill="currentColor"/>',
}


def symbol(name, d, groesse):
    eigen = d.get("symbole", {}).get(name)
    inner = eigen if eigen else _S.get(name, "")
    if not inner:
        return ""
    return f'<svg viewBox="0 0 100 100" width="{groesse}" height="{groesse}" aria-hidden="true">{inner}</svg>'


FEHLENDE_BILDER = []  # wird von rendern.py ausgewertet (fehlendes Bild = Problem, Folie wird ohne Foto gebaut)


def bild(base, rel):
    """data:-URI des Bildes oder "" (und Eintrag in FEHLENDE_BILDER), wenn die Datei fehlt."""
    if not rel:
        return ""
    p = pathlib.Path(base) / rel
    if not p.exists():
        FEHLENDE_BILDER.append(str(rel))
        return ""
    return bild_uri(p)


# ------------------------------------------------------------------ CSS aus design.json
def css(d, fmt):
    w, h, so, sr, su, sl = FORMATE[fmt]
    m = SKALA.get(fmt, 1.0)

    def px(n):
        return round(n * m)

    f = d["farben"]
    ti = d.get("schrift", {}).get("titel", "Inter Display")
    tx = d.get("schrift", {}).get("text", "Inter")
    r = d.get("radius", 32)
    return f"""
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{width:{w}px;height:{h}px;overflow:hidden;background:#000}}
body{{font-family:'{tx}';-webkit-font-smoothing:antialiased;font-kerning:normal}}
.folie{{position:absolute;inset:0;overflow:hidden;background:var(--hg);color:var(--tx)}}
.hell{{--hg:{f['hell']};--tx:{f['dunkel']};--ged:{f['ged_hell']};--fl:{f['flaeche_hell']};--li:{f['ged_hell']}55;
  --ak:{f['akzent']};--akt:{f['akzent_text']}}}
.dunkel{{--hg:{f['dunkel']};--tx:{f['hell']};--ged:{f['ged_dunkel']};--fl:{f['flaeche_dunkel']};--li:{f['ged_dunkel']}55;
  --ak:{f['akzent']};--akt:{f['akzent_text']}}}
.akzent{{--hg:{f['akzent']};--tx:{f['akzent_text']};--ged:{f['akzent_text']}cc;--fl:#ffffff24;--li:#ffffff66;
  --ak:{f['dunkel']};--akt:{f['hell']}}}
.foto{{--hg:{f['dunkel']};--tx:#ffffff;--ged:#ffffffd0;--fl:#ffffff26;--li:#ffffff66;--ak:{f['akzent']};--akt:{f['akzent_text']}}}
.rahmen{{position:absolute;inset:0;padding:{so}px {sr}px {su}px {sl}px;display:flex;flex-direction:column;gap:{px(34)}px}}
.box{{flex:1;min-height:0;overflow:hidden;display:flex;flex-direction:column;gap:{px(30)}px}}
.mitte{{justify-content:center}} .unten{{justify-content:flex-end}} .oben{{justify-content:flex-start}}
.zentriert{{align-items:center;text-align:center}}
.disp{{font-family:'{ti}';font-weight:800;letter-spacing:-.028em;line-height:1.02}}
.kopf{{display:flex;align-items:center;gap:{px(18)}px;flex:none;min-height:{px(52)}px}}
.kopf .sym{{display:flex;color:var(--tx)}}
.label{{font-weight:700;font-size:{px(28)}px;letter-spacing:.16em;text-transform:uppercase;color:var(--ged)}}
.badge{{margin-left:auto;font-weight:700;font-size:{px(26)}px;letter-spacing:.12em;text-transform:uppercase;
  border:3px solid currentColor;border-radius:999px;padding:{px(6)}px {px(18)}px;color:var(--tx)}}
.titel{{font-size:{px(128)}px;line-height:.98;letter-spacing:-.035em}}
.hl{{font-size:{px(82)}px}}
.unter{{font-size:{px(46)}px;font-weight:600;line-height:1.2;letter-spacing:-.01em}}
.txt{{font-size:{px(38)}px;line-height:1.42;font-weight:450}}
.txt p+p{{margin-top:.55em}}
.sv{{font-size:{px(52)}px;line-height:1.36;font-weight:500}}
.pk+.pk{{margin-top:.7em}}
.pt{{font-weight:700;font-size:.62em;letter-spacing:.14em;text-transform:uppercase;color:var(--ged);margin-bottom:.22em}}
.fuss{{flex:none;display:flex;justify-content:space-between;align-items:flex-end;gap:40px;padding-top:{px(22)}px;
  border-top:2px solid var(--li)}}
.quelle{{font-size:{px(23)}px;line-height:1.4;color:var(--ged);max-width:{px(660)}px}}
.wm{{font-family:'{ti}';font-weight:800;font-size:{px(36)}px;letter-spacing:-.02em;white-space:nowrap;margin-left:auto}}
.hg-bild{{position:absolute;inset:0;overflow:hidden}}
.hg-bild img,.kbild img,.half img{{width:100%;height:100%;object-fit:cover;display:block}}
.verlauf{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.42) 0%,rgba(0,0,0,.18) 30%,
  rgba(0,0,0,.55) 62%,rgba(0,0,0,.86) 100%)}}
.kbild{{position:absolute;left:0;right:0;top:0;overflow:hidden}}
.kfade{{position:absolute;left:0;right:0;height:150px;background:linear-gradient(to bottom,transparent,var(--hg))}}
.optionen{{display:flex;flex-direction:column;gap:{px(20)}px}}
.opt{{display:flex;align-items:center;gap:{px(26)}px;background:var(--fl);border-radius:{r}px;padding:{px(22)}px {px(30)}px}}
.key{{flex:none;width:{px(88)}px;height:{px(88)}px;border-radius:50%;display:flex;align-items:center;justify-content:center;
  font-family:'{ti}';font-weight:800;font-size:{px(50)}px;color:#fff;line-height:1}}
.otx{{font-size:{px(42)}px;font-weight:600;line-height:1.2;letter-spacing:-.01em}}
.ergebnis{{display:flex;align-items:center;gap:{px(22)}px;align-self:flex-start;background:{f.get('richtig', '#2F8F5B')};
  color:#fff;border-radius:999px;padding:{px(10)}px {px(30)}px {px(10)}px {px(12)}px;font-weight:700;font-size:{px(34)}px}}
.ergebnis .key{{width:{px(64)}px;height:{px(64)}px;font-size:{px(36)}px;background:#ffffff33}}
.zahl{{font-size:{px(250)}px;line-height:.9;letter-spacing:-.045em;font-variant-numeric:tabular-nums}}
.einheit{{font-size:{px(48)}px;font-weight:700;letter-spacing:-.01em;color:var(--ged)}}
.vgl{{display:flex;gap:{px(24)}px}}
.foto .opt{{background:{f['dunkel']}d9}}
.vgl>div{{flex:1;background:var(--fl);border-radius:{r}px;padding:{px(22)}px {px(26)}px}}
.vgl .vl{{font-size:{px(26)}px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:var(--ged)}}
.vgl .vw{{font-family:'{ti}';font-weight:800;font-size:{px(64)}px;letter-spacing:-.03em;margin-top:6px}}
.liste{{display:flex;flex-direction:column;gap:{px(14)}px}}
.li{{display:flex;align-items:center;gap:{px(22)}px;background:var(--fl);border-radius:{r}px;padding:{px(18)}px {px(26)}px}}
.rang{{flex:none;width:{px(64)}px;font-family:'{ti}';font-weight:800;font-size:{px(52)}px;color:var(--ged)}}
.lname{{flex:1;font-size:{px(40)}px;font-weight:600}}
.lwert{{font-family:'{ti}';font-weight:800;font-size:{px(48)}px;white-space:nowrap}}
.lwert small{{font-family:'{tx}';font-weight:600;font-size:.5em;color:var(--ged);margin-left:.3em}}
.half{{position:absolute;overflow:hidden;background:var(--hg);color:var(--tx)}}
.schleier{{position:absolute;inset:0;background:var(--hg);opacity:.84}}
.hinhalt{{position:absolute;display:flex;flex-direction:column;justify-content:center;gap:{px(24)}px}}
.trenn{{position:absolute;left:0;right:0;display:flex;justify-content:center;align-items:center;z-index:3}}
.trenn span{{font-family:'{ti}';font-weight:800;font-size:{px(44)}px;background:var(--ak);color:var(--akt);
  border-radius:999px;padding:{px(8)}px {px(30)}px}}
.cta-frage{{font-size:{px(104)}px;line-height:1;letter-spacing:-.035em}}
.cta-vor{{font-size:{px(70)}px;letter-spacing:-.025em}}
.blase-wrap{{display:flex;justify-content:center;padding-bottom:{px(40)}px}}
.blase{{position:relative;background:var(--ak);color:var(--akt);font-family:'{ti}';font-weight:800;font-size:{px(170)}px;
  letter-spacing:-.03em;line-height:1;padding:{px(24)}px {px(60)}px {px(38)}px;border-radius:{px(60)}px;white-space:nowrap}}
.blase:after{{content:'';position:absolute;left:{px(84)}px;bottom:-{px(40)}px;border-width:{px(44)}px 0 0 {px(50)}px;
  border-style:solid;border-color:var(--ak) transparent transparent transparent}}
.cursor{{display:inline-block;width:.06em;height:.76em;background:currentColor;margin-left:.06em;vertical-align:-.03em;
  border-radius:3px;opacity:0}}
.cta-nach{{font-size:{px(44)}px;font-weight:600;line-height:1.25}}
.cta-teilen{{font-size:{px(38)}px;font-weight:500;line-height:1.3;color:var(--ged)}}
.handle{{flex:none;text-align:center;font-size:{px(36)}px;font-weight:600;letter-spacing:.03em;color:var(--ged)}}
.prof{{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:24px;
  text-align:center}}
.prof .pz{{font-family:'{ti}';font-weight:800;font-size:{px(170)}px;line-height:.9;letter-spacing:-.045em}}
"""


# ------------------------------------------------------------------ Teile
def kopf(f, d, symbol_std=None):
    teile = []
    s = f.get("symbol", symbol_std)
    if s:
        teile.append(f'<span class="sym">{symbol(s, d, 50)}</span>')
    if f.get("label"):
        teile.append(f'<span class="label">{esc(f["label"])}</span>')
    if f.get("badge"):
        teile.append(f'<span class="badge">{esc(f["badge"])}</span>')
    return f'<div class="kopf">{"".join(teile)}</div>' if teile else ""


def fuss(f, d, wortmarke=True):
    zeilen = []
    if f.get("quelle"):
        zeilen.append(esc(f.get("quelle_vor", "Quelle: ") + f["quelle"]))
    if f.get("hinweis"):
        zeilen.append(esc(f["hinweis"]))
    links = f'<div class="quelle">{"<br>".join(zeilen)}</div>' if zeilen else ""
    rechts = f'<div class="wm">{esc(d.get("wortmarke", ""))}</div>' if wortmarke and d.get("wortmarke") else ""
    return f'<div class="fuss">{links}{rechts}</div>' if (links or rechts) else ""


def hintergrund(f, base, std="dunkel"):
    """Vollflächiges Foto mit Verlauf (Thema «foto») oder nichts (dann Thema der Folie bzw. std)."""
    src = bild(base, f.get("bild"))
    if not src:
        return "", f.get("thema", std)
    return (f'<div class="hg-bild"><img class="anim-zoom" src="{src}" style="object-position:{f.get("bild_pos", "50% 50%")}">'
            f'</div><div class="verlauf"></div>'), "foto"


def absaetze(f, feld="text", cls="txt", fit="0.62"):
    if f.get("punkte") and feld == "text":
        inner = "".join(f'<div class="pk"><div class="pt">{esc(t)}</div><div>{esc(x)}</div></div>' for t, x in f["punkte"])
        return f'<div class="{cls} anim-folge" data-fit="{fit}">{inner}</div>'
    wert = f.get(feld)
    if not wert:
        return ""
    liste = wert if isinstance(wert, list) else [wert]
    return f'<div class="{cls} anim-folge" data-fit="{fit}">' + "".join(f"<p>{esc(a)}</p>" for a in liste) + "</div>"


def optionen(opts, d, richtig=None):
    farben = d["farben"].get("option", ["#2E6DA4", "#C8553D", "#5B8C5A", "#8A5BB0"])
    zeilen = []
    for i, o in enumerate(opts):
        key = o.get("key", "ABCD"[i % 4])
        c = o.get("farbe") or farben[i % len(farben)]
        stil = ' style="opacity:.45"' if richtig and key != richtig else ""
        zeilen.append(f'<div class="opt"{stil}><div class="key" style="background:{c}">{esc(key)}</div>'
                      f'<div class="otx" data-fit="0.6">{esc(o.get("text", ""))}</div></div>')
    return f'<div class="optionen anim-folge">{"".join(zeilen)}</div>'


# ------------------------------------------------------------------ Layouts
def l_titel(f, d, fmt, base):
    hg, thema = hintergrund(f, base)
    teile = []
    if f.get("titel"):
        teile.append(f'<div class="titel disp anim-woerter" data-fit="0.42">{woerter(f["titel"])}</div>')
    if f.get("unter"):
        teile.append(f'<div class="unter anim-ein" data-fit="0.6">{esc(f["unter"])}</div>')
    box = f'<div class="box {f.get("position", "mitte")}" data-box="titel">{"".join(teile)}</div>'
    return thema, hg + f'<div class="rahmen">{kopf(f, d)}{box}{fuss(f, d, f.get("wortmarke", False))}</div>'


def l_text(f, d, fmt, base):
    hg, thema = hintergrund(f, base, "hell")
    teile = []
    if f.get("headline"):
        teile.append(f'<div class="hl disp anim-woerter" data-fit="0.55">{woerter(f["headline"])}</div>')
    teile.append(absaetze(f))
    box = f'<div class="box {f.get("position", "mitte")}" data-box="text">{"".join(teile)}</div>'
    return thema, hg + f'<div class="rahmen">{kopf(f, d)}{box}{fuss(f, d, f.get("wortmarke", True))}</div>'


def l_karte(f, d, fmt, base, label_std=None, symbol_std=None):
    """Karte mit Foto oben (wie die DM-Karten von «Beide wahr»). Auch für die Auflösung eines Quiz."""
    w, h = FORMATE[fmt][:2]
    thema = f.get("thema", "hell")
    foto, oben = "", None
    src = bild(base, f.get("bild"))
    if src:
        bh = f.get("bild_hoehe", 440 if h >= 1350 else 360)
        foto = (f'<div class="kbild" style="height:{bh}px"><img class="anim-zoom" src="{src}" '
                f'style="object-position:{f.get("bild_pos", "50% 50%")}"></div><div class="kfade" style="top:{bh - 149}px"></div>')
        oben = bh - 24
    g = dict(f)
    if label_std:
        g.setdefault("label", label_std)
    teile = []
    if f.get("ergebnis"):
        e = f["ergebnis"]
        teile.append(f'<div class="ergebnis anim-pop"><span class="key">{esc(e.get("key", ""))}</span>'
                     f'{esc(e.get("text", ""))}</div>')
    if f.get("headline"):
        teile.append(f'<div class="hl disp anim-woerter" data-fit="0.62">{woerter(f["headline"])}</div>')
    teile.append(absaetze(f))
    stil = f' style="padding-top:{oben}px"' if oben else ""
    box = f'<div class="box" data-box="karte">{"".join(teile)}</div>'
    return thema, foto + f'<div class="rahmen"{stil}>{kopf(g, d, symbol_std)}{box}{fuss(f, d, True)}</div>'


def l_aufloesung(f, d, fmt, base):
    return l_karte(f, d, fmt, base, label_std="Auflösung", symbol_std="haken")


def l_frage(f, d, fmt, base):
    hg, thema = hintergrund(f, base, "hell")
    # Kanal «Recht gehabt?»: Sachverhalt ohne Frage (Reel-Szene 2) in grösserer Schrift
    sv_cls = "txt sv" if f.get("sachverhalt") and not f.get("frage") else "txt"
    teile = [absaetze(f, "sachverhalt", cls=sv_cls, fit="0.6")]
    if f.get("frage"):
        teile.append(f'<div class="hl disp anim-woerter" data-fit="0.55">{woerter(f["frage"])}</div>')
    if f.get("optionen"):
        teile.append(optionen(f["optionen"], d, f.get("richtig")))
    if f.get("aufruf"):  # gut sichtbare Handlungsaufforderung, z. B. in der Story «Antworte mit A oder B»
        teile.append(f'<div class="cta-nach anim-ein" data-fit="0.6">{esc(f["aufruf"])}</div>')
    box = f'<div class="box {f.get("position", "mitte")}" data-box="frage">{"".join(teile)}</div>'
    return thema, hg + f'<div class="rahmen">{kopf(f, d)}{box}{fuss(f, d, f.get("wortmarke", True))}</div>'


def l_zahl(f, d, fmt, base):
    hg, thema = hintergrund(f, base, "dunkel")
    zf = d.get("zahlformat", {})
    tsd, dzl = zf.get("tausender", "’"), zf.get("dezimal", ",")
    z = f.get("zahl", "")
    if isinstance(z, (int, float)):
        dez = int(f.get("dezimalen", 0))
        attr = (f' data-wert="{z}" data-dez="{dez}" data-tsd="{esc(tsd)}" data-dzl="{esc(dzl)}"')
        anzeige = fmt_zahl(z, dez, tsd, dzl)
        cls = "zahl disp anim-zaehlen"
    else:
        attr, anzeige, cls = "", esc(z), "zahl disp anim-ein"
    teile = []
    if f.get("headline"):
        teile.append(f'<div class="unter anim-ein" data-fit="0.6">{esc(f["headline"])}</div>')
    teile.append(f'<div><span class="{cls}" data-fit="0.4"{attr}>{anzeige}</span></div>')
    if f.get("einheit"):
        teile.append(f'<div class="einheit anim-ein" data-fit="0.6">{esc(f["einheit"])}</div>')
    teile.append(absaetze(f))
    if f.get("vergleich"):
        teile.append('<div class="vgl anim-folge">' + "".join(
            f'<div><div class="vl">{esc(v.get("label", ""))}</div><div class="vw">{esc(v.get("wert", ""))}</div></div>'
            for v in f["vergleich"]) + "</div>")
    box = f'<div class="box {f.get("position", "mitte")}" data-box="zahl">{"".join(teile)}</div>'
    return thema, hg + f'<div class="rahmen">{kopf(f, d)}{box}{fuss(f, d, f.get("wortmarke", True))}</div>'


def l_liste(f, d, fmt, base):
    thema = f.get("thema", "hell")
    teile = []
    if f.get("headline"):
        teile.append(f'<div class="hl disp anim-woerter" data-fit="0.55">{woerter(f["headline"])}</div>')
    zeilen = []
    for i, e in enumerate(f.get("eintraege", []), 1):
        einheit = f'<small>{esc(e["einheit"])}</small>' if e.get("einheit") else ""
        zeilen.append(f'<div class="li"><div class="rang">{esc(e.get("rang", i))}</div>'
                      f'<div class="lname" data-fit="0.6">{esc(e.get("name", ""))}</div>'
                      f'<div class="lwert">{esc(e.get("wert", ""))}{einheit}</div></div>')
    teile.append(f'<div class="liste anim-folge">{"".join(zeilen)}</div>')
    box = f'<div class="box {f.get("position", "mitte")}" data-box="liste">{"".join(teile)}</div>'
    return thema, f'<div class="rahmen">{kopf(f, d)}{box}{fuss(f, d, f.get("wortmarke", True))}</div>'


def l_vergleich(f, d, fmt, base):
    """Zwei Hälften (waagrecht = oben/unten, senkrecht = links/rechts), z. B. gut/schlecht oder damals/heute."""
    w, h, so, sr, su, sl = FORMATE[fmt]
    waag = f.get("richtung", "waagrecht") == "waagrecht"
    teile = f.get("teile", [])[:2]
    html_teile = []
    for i, t in enumerate(teile):
        th = t.get("thema", "hell" if i == 0 else "dunkel")
        if waag:
            pos = f"left:0;right:0;top:{0 if i == 0 else h // 2}px;height:{h // 2}px"
            pad = (f"left:{sl}px;right:{sr}px;top:{so if i == 0 else 60}px;"
                   f"bottom:{60 if i == 0 else su}px")
        else:
            pos = f"top:0;bottom:0;left:{0 if i == 0 else w // 2}px;width:{w // 2}px"
            pad = f"left:{sl if i == 0 else 50}px;right:{50 if i == 0 else sr}px;top:{so}px;bottom:{su}px"
        foto = ""
        src = bild(base, t.get("bild"))
        if src:
            foto = (f'<img class="anim-zoom" src="{src}" style="position:absolute;inset:0;'
                    f'object-position:{t.get("bild_pos", "50% 50%")}"><div class="schleier"></div>')
        k = kopf(t, d)
        hl = f'<div class="hl disp anim-woerter" data-fit="0.5">{woerter(t.get("headline", ""))}</div>' if t.get("headline") else ""
        txt = absaetze(t)
        html_teile.append(f'<div class="half {th}" style="{pos}">{foto}<div class="hinhalt" style="{pad}" '
                          f'data-box="teil{i}">{k}{hl}{txt}</div></div>')
    mitte = ""
    if f.get("mitte"):  # kurzer Text auf der Trennlinie, z. B. «oder» oder «?»
        mitte = (f'<div class="trenn" style="top:{h // 2 - 40}px;height:80px">'
                 f'<span class="anim-pop">{esc(f["mitte"])}</span></div>')
    return f.get("thema", "dunkel"), "".join(html_teile) + mitte


def l_aufruf(f, d, fmt, base):
    """Schluss-Szene: Frage, Stichwort-Sprechblase (wird im Reel getippt), Hinweis, Weiterschick-Zeile."""
    thema = f.get("thema", "dunkel")
    wort = f.get("stichwort") or d.get("stichwort", "INFO")
    teile = []
    if f.get("frage"):
        teile.append(f'<div class="cta-frage disp anim-woerter" data-fit="0.5">{woerter(f["frage"])}</div>')
    if f.get("vor"):
        teile.append(f'<div class="cta-vor disp anim-ein" data-fit="0.55">{esc(f["vor"])}</div>')
    buchst = "".join(f'<span class="b">{esc(ch)}</span>' for ch in wort)
    teile.append(f'<div class="blase-wrap"><div class="blase anim-pop anim-tippen" data-fit="0.45">{buchst}'
                 f'<span class="cursor"></span></div></div>')
    if f.get("nach"):
        teile.append(f'<div class="cta-nach anim-ein" data-fit="0.6">{esc(f["nach"])}</div>')
    if f.get("teilen"):
        teile.append(f'<div class="cta-teilen anim-ein" data-fit="0.6">{esc(f["teilen"])}</div>')
    if f.get("statistik"):
        teile.append(f'<div class="cta-teilen anim-ein" data-fit="0.6">{esc(f["statistik"])}</div>')
    box = f'<div class="box mitte zentriert" data-box="aufruf">{"".join(teile)}</div>'
    handle = f'<div class="handle">{esc(d.get("handle", ""))}</div>' if f.get("handle", True) and d.get("handle") else ""
    return thema, f'<div class="rahmen">{box}{handle}</div>'


def l_profil(f, d, fmt, base):
    """Profilbild (quadratisch; Instagram schneidet einen Kreis aus -> Inhalt mittig halten)."""
    thema = f.get("thema", "dunkel")
    zeilen = f.get("zeilen") or [d.get("wortmarke", "")]
    s = symbol(f["symbol"], d, 180) if f.get("symbol") else ""
    pz = "".join(f'<div class="pz">{esc(z)}</div>' for z in zeilen)
    return thema, f'<div class="prof">{s}<div style="max-width:760px">{pz}</div></div>'


LAYOUTS = {"titel": l_titel, "text": l_text, "karte": l_karte, "aufloesung": l_aufloesung, "frage": l_frage,
           "zahl": l_zahl, "liste": l_liste, "vergleich": l_vergleich, "aufruf": l_aufruf, "profil": l_profil}


def folie_html(f, d, fmt, base):
    lay = f.get("layout", "text")
    if lay not in LAYOUTS:
        raise ValueError(f"Unbekanntes Layout «{lay}». Vorhanden: {', '.join(LAYOUTS)}")
    thema, inner = LAYOUTS[lay](f, d, fmt, pathlib.Path(base))
    return f'<div class="folie {thema} lay-{lay}">{inner}</div>'


def seite(f, d, fmt, base):
    """Vollständiges HTML-Dokument für ein Bild (Karte, Story, Karussell-Folie, Profilbild)."""
    return (f'<!doctype html><html lang="{d.get("sprache", "de-CH")}"><head><meta charset="utf-8">'
            f'<style>{css(d, fmt)}</style></head><body>{folie_html(f, d, fmt, base)}</body></html>')


# ------------------------------------------------------------------ Reel: Szenen + Zeitachse
REEL_JS = r"""
const SZ = __SZENEN__;
const clamp = x => Math.max(0, Math.min(1, x));
const ease = x => 1 - Math.pow(1 - clamp(x), 3);
const pop = x => { x = clamp(x); const c = 1.7; return 1 + (c + 1) * Math.pow(x - 1, 3) + c * Math.pow(x - 1, 2); };
const fmtZ = (v, dez, tsd, dzl) => { const s = v.toFixed(dez).split('.');
  s[0] = s[0].replace(/\B(?=(\d{3})+(?!\d))/g, tsd); return s.length > 1 ? s[0] + dzl + s[1] : s[0]; };
const L = [...document.querySelectorAll('.szene')];
let PLAN = [];
window.vorbereiten = function () {
  PLAN = L.map((el, i) => {
    const sel = '.anim-woerter,.anim-ein,.anim-folge,.anim-pop,.anim-zaehlen';
    const els = [...el.querySelectorAll(sel)];
    let cur = 0.2; const items = [];
    for (const e of els) {
      const c = e.classList; let dur = 0.4;
      if (c.contains('anim-woerter')) dur = 0.3 + 0.1 * e.querySelectorAll('.w').length;
      else if (c.contains('anim-folge')) dur = 0.25 + 0.33 * e.children.length;
      else if (c.contains('anim-zaehlen')) dur = 1.1;
      if (c.contains('anim-tippen')) dur = 0.45 + 0.14 * e.querySelectorAll('.b').length;
      items.push({e, start: cur, dur}); cur += dur * 0.72;
    }
    const platz = Math.max(0.6, SZ[i].dauer - 0.8);
    const k = cur > platz ? platz / cur : 1;
    items.forEach(it => { it.start *= k; it.dur = Math.max(0.25, it.dur * k); });
    return {items, zoom: [...el.querySelectorAll('.anim-zoom')]};
  });
};
function zeige(e, a, dy) { e.style.opacity = a; if (dy) e.style.transform = 'translateY(' + (dy * (1 - a)) + 'px)'; }
function animiere(e, lt, dur, fest) {
  const c = e.classList;
  if (c.contains('anim-woerter')) {
    const ws = e.querySelectorAll('.w'); const schritt = Math.min(0.1, (dur - 0.25) / Math.max(1, ws.length));
    ws.forEach((w, k) => { w.style.opacity = fest ? 1 : ease((lt - k * schritt) / 0.25); });
    zeige(e, 1, 0); e.style.transform = fest ? '' : 'translateY(' + (14 * (1 - ease(lt / 0.5))) + 'px)';
  }
  if (c.contains('anim-ein')) zeige(e, fest ? 1 : ease(lt / 0.35), 18);
  if (c.contains('anim-folge')) [...e.children].forEach((ch, k) => zeige(ch, fest ? 1 : ease((lt - k * 0.33) / 0.3), 20));
  if (c.contains('anim-pop')) { const a = fest ? 1 : pop(lt / 0.45); e.style.transform = 'scale(' + Math.max(0.01, a) + ')';
    e.style.opacity = fest ? 1 : clamp(lt / 0.1); }
  if (c.contains('anim-tippen')) {
    const bs = e.querySelectorAll('.b');
    bs.forEach((b, k) => { b.style.opacity = (fest || lt >= 0.35 + k * 0.14) ? 1 : 0; });
    const cu = e.querySelector('.cursor');
    const fertig = 0.35 + bs.length * 0.14;
    if (cu) cu.style.opacity = (!fest && lt < fertig + 0.5 && Math.floor(lt * 2.6) % 2 === 0) ? 1 : 0;
    if (!fest && lt > fertig + 0.3) e.style.transform = 'scale(' + (1 + 0.03 * Math.sin((lt - fertig) * Math.PI * 2 / 1.1)) + ')';
  }
  if (c.contains('anim-zaehlen')) {
    const v = parseFloat(e.dataset.wert), dez = parseInt(e.dataset.dez || '0');
    e.textContent = fmtZ(v * (fest ? 1 : ease(lt / Math.max(0.3, dur))), dez, e.dataset.tsd, e.dataset.dzl);
  }
}
window.render = function (t) {
  if (!PLAN.length) window.vorbereiten();
  L.forEach((el, i) => {
    const s = SZ[i]; let op;
    if (s.schleife) op = ease((t - s.t0) / s.dauer);
    else if (i === 0) op = t < s.t0 + s.dauer + 0.4 ? 1 : 0;
    else op = (t >= s.t0 && t < s.t0 + s.dauer + 0.4) ? ease((t - s.t0) / 0.3) : 0;
    el.style.opacity = op; el.style.visibility = op > 0 ? 'visible' : 'hidden';
    if (op <= 0) return;
    const tau = t - s.t0, P = PLAN[i];
    const z = s.schleife ? 1.04 : 1.04 + 0.08 * clamp(tau / s.dauer);
    P.zoom.forEach(e => { e.style.transform = 'scale(' + z + ')'; });
    P.items.forEach(({e, start, dur}) => animiere(e, tau - start, dur, s.fest));
  });
};
"""


def reel_seite(reel, d, base):
    """Baut aus reel["szenen"] (je {"folie": {...}, "dauer": s}) eine HTML-Animation.
    Szene 1 ist ab dem ersten Bild vollständig sichtbar (Skip-Rate!). Mit "schleife": true
    blendet am Ende Szene 1 wieder ein, damit das Reel nahtlos von vorne beginnt."""
    base = pathlib.Path(base)
    szenen = reel["szenen"]
    schichten, meta, t = [], [], 0.0
    for i, s in enumerate(szenen):
        dauer = float(s.get("dauer", 3.0))
        schichten.append(f'<div class="szene" style="position:absolute;inset:0;z-index:{i + 1}">'
                         f'{folie_html(s["folie"], d, "reel", base)}</div>')
        meta.append({"t0": round(t, 3), "dauer": dauer, "fest": i == 0})
        t += dauer
    if reel.get("schleife", True) and szenen:
        schichten.append(f'<div class="szene" style="position:absolute;inset:0;z-index:{len(szenen) + 1}">'
                         f'{folie_html(szenen[0]["folie"], d, "reel", base)}</div>')
        meta.append({"t0": round(t - 0.5, 3), "dauer": 0.5, "fest": True, "schleife": True})
    js = REEL_JS.replace("__SZENEN__", json.dumps(meta))
    doc = (f'<!doctype html><html lang="{d.get("sprache", "de-CH")}"><head><meta charset="utf-8">'
           f'<style>{css(d, "reel")}</style></head><body>{"".join(schichten)}<script>{js}</script></body></html>')
    return doc, t, meta

"""Recht gehabt? – Reel mit starkem Einstieg (seit 27.11.2026, Entscheid Timo).

  python3 pipeline/reel_hook.py posts/<datum>/post.json <out> [--audio musik.wav]
Liest post["reel"] mit art «hook»: nr, land, bild, bild_pos, vor, gross, stempel, zeilen [[emoji, text]], frage,
optionen {A, B}. [eckige Klammern] im Text werden gelb markiert. Schreibt <out>/reel.mp4, cover.jpg und
<out>/pruefung/reel_kontaktbogen.png. Ablauf: Einstieg mit Foto und Stempel (2,8 s) · Fall Zeile für Zeile
(je 1,8 s, danach 3 s Lesezeit) · Frage mit A/B und Aufruf (4,4 s).
"""
import base64
import html
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import werkstatt  # noqa: E402

BASIS = pathlib.Path(__file__).resolve().parent.parent


def mark(t):
    t = html.escape(t).replace("­", "&shy;")
    return re.sub(r"\[([^\]]+)\]", r'<span class="mark">\1</span>', t)


def mark_em(t):
    t = html.escape(t).replace("­", "&shy;")
    return re.sub(r"\[([^\]]+)\]", r"<em>\1</em>", t)


CSS = r"""
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;background:#18213A;font-family:'Inter';color:#fff}
.s{position:absolute;inset:0;opacity:0}
.foto{position:absolute;left:-60px;right:-60px;top:-300px;bottom:180px;background-size:cover;transform-origin:45% 45%}
.verlauf{position:absolute;inset:0;background:linear-gradient(180deg,rgba(14,19,36,.55) 0%,rgba(14,19,36,0) 22%,rgba(14,19,36,0) 44%,rgba(14,19,36,.9) 64%,#0e1324 100%)}
.kopf{position:absolute;top:250px;left:80px;right:180px;display:flex;align-items:center;gap:14px}
.fall{font-weight:800;font-size:30px;letter-spacing:.16em;opacity:.9}
.laender{margin-left:auto;display:flex;gap:10px}
.p{font-weight:800;font-size:26px;letter-spacing:.1em;border:3px solid currentColor;border-radius:999px;padding:5px 16px;opacity:.55;background:rgba(14,19,36,.35)}
.p.an{opacity:1;background:#C8372D;border-color:#C8372D;color:#fff}
.hook{position:absolute;left:80px;right:150px;bottom:400px}
.vor{font-weight:800;font-size:46px;letter-spacing:.06em;text-transform:uppercase;color:#FFD34D;margin-bottom:18px}
.gross{font-family:'Source Serif 4';font-weight:900;line-height:.98;letter-spacing:-.035em}
.mark{background:#FFD34D;color:#18213A;padding:0 14px;border-radius:10px;display:inline-block}
.stempel{position:absolute;top:380px;right:130px;max-width:760px;text-align:center;font-weight:900;font-size:78px;line-height:1;
  letter-spacing:.04em;white-space:nowrap;color:#fff;background:#C8372D;padding:12px 30px;border:6px solid #fff;border-radius:14px;box-shadow:0 14px 40px rgba(0,0,0,.45)}
.blitz{position:absolute;inset:0;background:#fff;opacity:0}
.s2{background:#F4EFE4;color:#18213A}
.label{font-weight:800;font-size:30px;letter-spacing:.16em;color:#C8372D}
.zeilen{position:absolute;left:80px;right:150px;top:440px}
.z{display:flex;gap:28px;font-weight:700;line-height:1.13;letter-spacing:-.02em;margin-bottom:58px}
.z .e{flex:none;width:120px;font-family:'Noto Color Emoji';font-size:100px;line-height:1}
.z em{font-style:normal;white-space:nowrap;background:#FFD34D;padding:0 10px;border-radius:8px}
.frage{position:absolute;left:80px;right:150px;top:400px;font-family:'Source Serif 4';font-weight:900;line-height:1.0;letter-spacing:-.03em}
.opts{position:absolute;left:80px;right:150px}
.o{display:flex;align-items:center;gap:30px;background:#232E4C;border-radius:24px;padding:30px 34px;margin-bottom:26px}
.k{flex:none;width:110px;height:110px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:70px}
.ot{font-weight:700;font-size:52px;line-height:1.12}
.cta{margin-top:40px}
.cta1{font-weight:900;font-size:64px;letter-spacing:-.01em}
.cta1 b{color:#FFD34D}
.balken{margin-top:24px;height:14px;border-radius:7px;background:#232E4C;overflow:hidden}
.balken i{display:block;height:100%;background:#FFD34D}
.cta2{margin-top:26px;font-weight:600;font-size:38px;color:#A3ABC0}
"""

JS = r"""
const $=id=>document.getElementById(id);
const cl=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const ein=(t,s,d)=>cl((t-s)/d);
const ease=x=>1-Math.pow(1-x,3);
window.render=function(t){
  $('s1').style.opacity=t<T1?1:0; $('s2').style.opacity=(t>=T1&&t<T2)?1:0; $('s3').style.opacity=t>=T2?1:0;
  const z=1.0+0.14*ease(cl(t/T1)); let sx=0,sy=0;
  if(t>0.42&&t<0.8){const k=(0.8-t)/0.38;sx=Math.sin(t*95)*24*k;sy=Math.cos(t*81)*18*k}
  $('foto').style.transform=`translate(${sx}px,${sy}px) scale(${z})`;
  const st=ein(t,0.25,0.2);
  const pop=st<1?(3.2-2.2*st):(1+0.12*Math.exp(-(t-0.45)*9)*Math.cos((t-0.45)*30));
  const rot=st<1?(-28+19*st):(-9+4*Math.exp(-(t-0.45)*8)*Math.sin((t-0.45)*26));
  $('stempel').style.opacity=st>0?1:0; $('stempel').style.transform=`rotate(${rot}deg) scale(${pop})`;
  $('blitz').style.opacity=(t>0.43&&t<0.62)?0.35*(0.62-t)/0.19:0;
  ZEILEN.forEach((id,i)=>{const e=ease(ein(t,T1+0.1+i*1.8,0.5));$(id).style.opacity=e;$(id).style.transform=`translateY(${(1-e)*50}px)`});
  const f=ease(ein(t,T2,0.45));$('frage').style.opacity=f;$('frage').style.transform=`scale(${0.92+0.08*f})`;
  const a=ease(ein(t,T2+0.6,0.45)),b=ease(ein(t,T2+1.0,0.45));
  $('oa').style.opacity=a;$('oa').style.transform=`translateX(${(1-a)*-160}px)`;
  $('ob').style.opacity=b;$('ob').style.transform=`translateX(${(1-b)*160}px)`;
  $('cta').style.opacity=ease(ein(t,T2+1.6,0.45));
  $('bar').style.width=(100*(1-cl((t-(T2+1.6))/(END-T2-1.6))))+'%';
};
const fr=$('frage'),op=document.querySelector('.opts');op.style.top=(fr.offsetTop+fr.offsetHeight+70)+'px';
render(0);
"""


def seite(r, design, base):
    laender = "".join(f'<span class="p{" an" if l == r["land"] else ""}">{l}</span>' for l in design.get("laender", [r["land"]]))
    kopf = lambda links: f'<div class="kopf">{links}<span class="laender">{laender}</span></div>'
    foto = "data:image/jpeg;base64," + base64.b64encode((base / r["bild"]).resolve().read_bytes()).decode()
    gl = len(re.sub(r"[\[\]]", "", r["gross"]))
    gpx = 122 if gl <= 42 else 108 if gl <= 56 else 96
    zl = sum(len(z[1]) for z in r["zeilen"])
    zpx = 70 if zl <= 200 else 64 if zl <= 250 else 58
    fl = len(r["frage"])
    fpx = 112 if fl <= 26 else 96 if fl <= 40 else 84
    opt_top = 400 + (2 if fl <= 26 else 3) * fpx + 60
    zeilen = "".join(f'<div class="z" id="z{i}" style="font-size:{zpx}px"><span class="e">{html.escape(e)}</span>'
                     f'<span>{mark_em(t)}</span></div>' for i, (e, t) in enumerate(r["zeilen"]))
    n = len(r["zeilen"])
    t1, t2 = 2.8, 2.8 + 0.1 + (n - 1) * 1.8 + 0.5 + 3.0
    ende = t2 + 4.4
    body = f"""
<div class="s" id="s1"><div class="foto" id="foto" style="background-image:url({foto});background-position:{r.get('bild_pos', '50% 50%')}"></div>
 <div class="verlauf"></div>{kopf(f'<span class="fall">FALL {r["nr"]}</span>')}
 <div class="blitz" id="blitz"></div><div class="stempel" id="stempel" style="font-size:{78 if len(r["stempel"]) <= 10 else 64}px">{html.escape(r["stempel"])}</div>
 <div class="hook"><div class="vor">{html.escape(r.get("vor", "Ab vor Gericht"))}</div>
  <div class="gross" style="font-size:{gpx}px">{mark(r["gross"])}</div></div></div>
<div class="s s2" id="s2">{kopf('<span class="label">DER FALL</span>')}<div class="zeilen">{zeilen}</div></div>
<div class="s" id="s3">{kopf(f'<span class="fall">FALL {r["nr"]}</span>')}
 <div class="frage" id="frage" style="font-size:{fpx}px">{mark(r["frage"])}</div>
 <div class="opts" style="top:{opt_top}px">
  <div class="o" id="oa"><span class="k" style="background:#2457C5">A</span><span class="ot">{html.escape(r["optionen"]["A"])}</span></div>
  <div class="o" id="ob"><span class="k" style="background:#D9822B">B</span><span class="ot">{html.escape(r["optionen"]["B"])}</span></div>
  <div class="cta" id="cta"><div class="cta1">Kommentiere <b>A</b> oder <b>B</b> 👇</div>
   <div class="balken"><i id="bar"></i></div><div class="cta2">Auflösung sofort per DM.</div></div></div></div>"""
    js = f"const T1={t1},T2={t2:.2f},END={ende:.2f};const ZEILEN={json.dumps([f'z{i}' for i in range(n)])};" + JS
    return f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>{body}<script>{js}</script></body></html>', ende


def main(a):
    post_pfad, out = pathlib.Path(a[0]), pathlib.Path(a[1])
    audio = a[a.index("--audio") + 1] if "--audio" in a else None
    post = json.loads(post_pfad.read_text(encoding="utf-8"))
    design = json.loads((BASIS / "design.json").read_text(encoding="utf-8"))
    doc, dauer = seite(post["reel"], design, post_pfad.parent)
    out.mkdir(parents=True, exist_ok=True)
    r = werkstatt.rendere_video(doc, round(dauer, 2), out / "reel.mp4", audio=audio, cover=out / "cover.jpg", cover_t=0.8)
    zeiten = [0.0, 0.6, 2.5, dauer * 0.45, dauer * 0.62, dauer - 3.2, dauer - 0.3]
    (out / "pruefung").mkdir(exist_ok=True)
    bilder = []
    for i, t in enumerate(zeiten):
        p = out / "pruefung" / f"reel_{i}.png"
        werkstatt.einzelbild(out / "reel.mp4", t, p)
        bilder.append((p, f"{t:.1f} s"))
    werkstatt.kontaktbogen(bilder, out / "pruefung" / "reel_kontaktbogen.png", spalten=4)
    print(f"Reel {r['dauer']} s · {out / 'reel.mp4'}")


if __name__ == "__main__":
    main(sys.argv[1:])

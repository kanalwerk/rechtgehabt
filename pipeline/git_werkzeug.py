"""Kanal-Werkstatt – Git mit Token, ohne den Token je zu speichern (für alle Kanäle).

Der Token kommt aus der Umgebungsvariable GH_TOKEN (Wert aus der Basis-Konfiguration im Projekt).
Er wird nur als HTTP-Header über GIT_CONFIG_*-Umgebungsvariablen an git übergeben: nie in Dateien,
nie in .git/config, nie in Befehlszeilen-Argumenten, nie in Ausgaben (Fehlermeldungen werden geschwärzt).
api.github.com ist in Claude-Sitzungen meist gesperrt -> alles läuft über git. *.github.io nur per Firecrawl prüfbar.

  python3 git_werkzeug.py klonen <https-url> <ziel>
  python3 git_werkzeug.py pull <ordner>
  python3 git_werkzeug.py push <ordner> "<Commit-Nachricht>"         # add -A, commit, push (nichts zu tun -> ok)
  python3 git_werkzeug.py medien-ablegen <https-url> <datei> <name>  # einzelner Commit ohne Verlauf + force-push
  python3 git_werkzeug.py medien-leeren <https-url> [<name>]          # nur <name> entfernen, ohne Namen alles
Ausgabe von medien-ablegen: die öffentliche URL (GitHub Pages), z. B. https://<konto>.github.io/<repo>/<name>
Das Repo «medien» teilen sich alle Kanäle: Dateien anderer Kanäle bleiben beim Ablegen und Leeren erhalten.
Dateinamen immer mit Kanal und Datum, z. B. «gericht-quiz-2026-11-16.mp4». Tagesläufe mind. 20 Min. versetzt planen.
"""
import base64
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

NAME = os.environ.get("GIT_NAME", "Kanal-Werkstatt")
MAIL = os.environ.get("GIT_MAIL", "werkstatt@users.noreply.github.com")


def _umgebung():
    tok = os.environ.get("GH_TOKEN")
    if not tok:
        sys.exit("GH_TOKEN fehlt (Wert aus der Basis-Konfiguration im Projekt setzen)")
    b = base64.b64encode(f"x-access-token:{tok}".encode()).decode()
    env = dict(os.environ)
    # Vorhandene GIT_CONFIG_*-Einträge der Sitzung (z. B. Proxy-Einstellungen) bleiben erhalten -> anhängen
    n = int(env.get("GIT_CONFIG_COUNT", "0") or 0)
    env.update({"GIT_CONFIG_COUNT": str(n + 2),
                f"GIT_CONFIG_KEY_{n}": "http.https://github.com/.extraheader",
                f"GIT_CONFIG_VALUE_{n}": f"Authorization: Basic {b}",
                f"GIT_CONFIG_KEY_{n + 1}": "credential.helper", f"GIT_CONFIG_VALUE_{n + 1}": "",
                "GIT_TERMINAL_PROMPT": "0",
                "GIT_AUTHOR_NAME": NAME, "GIT_AUTHOR_EMAIL": MAIL,
                "GIT_COMMITTER_NAME": NAME, "GIT_COMMITTER_EMAIL": MAIL})
    return env


def git(*args, cwd=None, pruefen=True):
    r = subprocess.run(["git", *args], cwd=cwd, env=_umgebung(), capture_output=True, text=True)
    if pruefen and r.returncode:
        text = (r.stderr or r.stdout or "").replace(os.environ.get("GH_TOKEN", "\x00"), "***")
        text = re.sub(r"Basic [A-Za-z0-9+/=]+", "Basic ***", text)
        hilfe = " -> Token abgelaufen oder ohne Rechte? Timo erstellt einen neuen (siehe Technik-Muster)." if \
            re.search(r"401|403|Authentication|denied", text) else ""
        sys.exit(f"git {args[0]} fehlgeschlagen: {text.strip()[:600]}{hilfe}")
    return r.stdout


def pages_url(url, name=""):
    m = re.match(r"https://github\.com/([^/]+)/([^/.]+)", url)
    if not m:
        return ""
    konto, repo = m.group(1).lower(), m.group(2)
    basis = f"https://{konto}.github.io" + ("" if repo.lower() == f"{konto}.github.io" else f"/{repo}")
    return f"{basis}/{name}" if name else basis + "/"


def _orphan(url, dateien, weg=None):
    """Neuer Stand als einzelner Commit ohne Verlauf. Vorhandene Dateien (anderer Kanäle) bleiben,
    ausser denen in «weg» (None = alle entfernen) und gleichnamigen neuen Dateien."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    git("clone", "--depth", "1", url, str(tmp))
    behalten = {}
    for p in tmp.iterdir():
        if p.is_file() and p.name not in ("README.md", ".nojekyll") and weg is not None and p.name not in weg:
            behalten[p.name] = p.read_bytes()
    git("checkout", "--orphan", "neu", cwd=tmp)
    git("rm", "-rqf", ".", cwd=tmp, pruefen=False)
    for p in tmp.iterdir():
        if p.name != ".git":
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    for name, inhalt in behalten.items():
        (tmp / name).write_bytes(inhalt)
    (tmp / "README.md").write_text("# medien\n\nKurzzeitige Ablage für Veröffentlichungen. Wird nach dem Abholen geleert.\n",
                                   encoding="utf-8")
    (tmp / ".nojekyll").write_text("", encoding="utf-8")
    for quelle, name in dateien:
        shutil.copy(quelle, tmp / name)
    git("add", "-A", cwd=tmp)
    git("commit", "-qm", "Medien" if (dateien or behalten) else "Leer", cwd=tmp)
    git("branch", "-M", "main", cwd=tmp)
    git("push", "-f", "origin", "main", cwd=tmp)
    shutil.rmtree(tmp, ignore_errors=True)


def main(a):
    if len(a) == 3 and a[0] == "klonen":
        git("clone", a[1], a[2])
        print("ok", a[2])
    elif len(a) == 2 and a[0] == "pull":
        git("pull", "--ff-only", cwd=a[1])
        print("ok")
    elif len(a) == 3 and a[0] == "push":
        git("add", "-A", cwd=a[1])
        if not git("status", "--porcelain", cwd=a[1]).strip():
            print("nichts zu tun")
            return
        git("commit", "-qm", a[2], cwd=a[1])
        git("push", "origin", "HEAD", cwd=a[1])
        print("ok", git("rev-parse", "--short", "HEAD", cwd=a[1]).strip())
    elif len(a) == 4 and a[0] == "medien-ablegen":
        _orphan(a[1], [(a[2], a[3])], weg={a[3]})
        print(pages_url(a[1], a[3]))
    elif len(a) in (2, 3) and a[0] == "medien-leeren":
        _orphan(a[1], [], weg={a[2]} if len(a) == 3 else None)
        print("geleert" + (f": {a[2]}" if len(a) == 3 else ""))
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main(sys.argv[1:])

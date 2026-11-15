# Recht gehabt? (@rechtgehabt)

Automatischer Instagram-Kanal, gebaut mit der Kanal-Werkstatt.

- `pipeline/` – Skripte (Kopie der Werkstatt, Version in `WERKSTATT_VERSION`)
- `posts/JJJJ-MM-TT/` – post.json, Bilder, Prüfbilder, Bericht
- `dm/aktuell.json` – aktueller Fall (Nummer, Titel) für die Nachfrage in ManyChat
- `dm/fall/<nr>-A.json`, `-B.json` – ManyChat Dynamic Block (v2) je Fall und Antwort, bleiben dauerhaft
- `karten/<nr>/aufloesung.png` – Auflösungskarte je Fall
- `faelle.json` – Fall-Datenbank (sprachneutral, Texte je Sprache), Vorrat und verwendete Fälle
- `schriften/` – Source Serif 4 (SIL Open Font License) für die Titel; vor dem Rendern nach ~/.fonts kopieren
- `pipeline/bausteine.py` – Kanal-Anpassung: grössere Schrift in der Sachverhalt-Szene
- `verlauf.json` – was wann lief
- `impressum.html` – Impressum (Link in der Bio)

Keine Tokens oder Schlüssel in dieses Repo. Videos mit Musik aus der Meta Sound Collection nie hier ablegen.

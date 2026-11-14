"""Vorschlag 3 fuer die Onepage-Seite des Chefs (REGELN 38, Rainer 2026-11-14).

"diese Seite soll zum Schluss inklusive Fragen 1 bis n hier auf onepage stattfinden",
"mache es bitte als neuen Vorschlag".

Erzeugt die drei OnePage-Felder (head, body, styles) fuer zwei Seiten auf
hausbau-konfigurator.de:
  landing/       = born2thrill.de/hauskonfigurator (Landingpage, WP-Fassung)
  konfigurator/  = born2thrill.de/konfigurator (Fragen 1 bis n)
"Los geht's" fuehrt auf /vorschlag-konfigurator-3 derselben Domain; WordPress
wird nicht mehr gebraucht (Medien liegen oeffentlich in der Mediathek).

Ausgabe: born2thrill-local-workbench/onepage/vorschlag-3/
Aufruf: python onepage-vorschlag-3.py
"""

import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WP = os.path.join(HERE, "..", "wordpress")
ZIEL = os.path.join(HERE, "..", "onepage", "vorschlag-3")
KONFIG_URL = "/vorschlag-konfigurator-3"
KATALOG_ALT = "/grundriss-katalog/"
KATALOG_NEU = "https://born2thrill.de/grundriss-katalog/"


def lesen(*teile):
    with open(os.path.join(*teile), encoding="utf-8") as f:
        return f.read()


def schreiben(ordner, datei, text):
    os.makedirs(os.path.join(ZIEL, ordner), exist_ok=True)
    with open(os.path.join(ZIEL, ordner, datei), "w", encoding="utf-8", newline="\n") as f:
        f.write(text.strip() + "\n")


def landing():
    q = os.path.join(WP, "landingpage-kollege")
    kopf = lesen(q, "head.html")
    alt = "const FUNNEL_URL = 'https://born2thrill.de/test/';"
    if alt not in kopf:
        raise SystemExit("FUNNEL_URL im Kopf nicht gefunden")
    # new URL() braucht eine absolute Adresse: relativ zur aktuellen Seite aufloesen.
    kopf = kopf.replace(alt, f"const FUNNEL_URL = new URL('{KONFIG_URL}', location.href).href;")
    schreiben("landing", "head.html", kopf)
    schreiben("landing", "body.html", lesen(q, "body.html"))
    schreiben("landing", "styles.css", lesen(q, "styles.css"))


def konfigurator():
    doc = lesen(WP, "konfigurator-neu", "index.html")
    kopf = re.search(r"<head>(.*?)</head>", doc, re.S).group(1)
    stil = re.search(r"<style>(.*?)</style>", kopf, re.S).group(1)
    kopf = re.sub(r"<style>.*?</style>", "", kopf, flags=re.S)
    kopf = re.sub(r"<meta charset[^>]*>|<meta name=\"viewport\"[^>]*>|<title>.*?</title>", "", kopf, flags=re.S)
    body = re.search(r"<body[^>]*>(.*)</body>", doc, re.S).group(1)
    if body.count(KATALOG_ALT) == 0:
        raise SystemExit("Katalog-Link nicht gefunden")
    body = body.replace(f'"{KATALOG_ALT}"', f'"{KATALOG_NEU}"')
    if re.search(r'["\']/(?!/)', body.replace(KONFIG_URL, "")):
        print("Hinweis: weitere seitenrelative Links im Konfigurator")
    schreiben("konfigurator", "head.html", kopf)
    schreiben("konfigurator", "body.html", body)
    schreiben("konfigurator", "styles.css", stil)


if __name__ == "__main__":
    landing()
    konfigurator()
    for o in ("landing", "konfigurator"):
        for d in ("head.html", "body.html", "styles.css"):
            p = os.path.join(ZIEL, o, d)
            print(o, d, os.path.getsize(p))

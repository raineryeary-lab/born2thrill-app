"""Landingpage des Kollegen als eigene Seite born2thrill.de/hauskonfigurator.

Rainer, 2026-11-08: "mach noch eine Seite Hauskonfigurator" -> Landingpage von
https://hausbau-konfigurator.de/vorschlag-landingpage "auf Hauskonfigurator uebernehmen".

Der Kollege pflegt die Seite als eigenes HTML/CSS (OnePage-Felder codeHead,
codeBody, styles). Dieses Skript holt sie (--holen) nach
wordpress/landingpage-kollege/ und erzeugt daraus das Snippet
wordpress/landingpage-hauskonfigurator.php: auf der Seite "hauskonfigurator"
wird das komplette Dokument ohne Theme ausgegeben (eigene globale Styles,
herausloesbar nach REGELN 38). Die Passwortsperre (Snippet 13, Prioritaet 0)
greift vorher.

Aufruf: python landingpage-snippet.py [--holen]
"""

import gzip
import json
import os
import re
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
WORDPRESS = os.path.join(HERE, "..", "wordpress")
QUELLE = os.path.join(WORDPRESS, "landingpage-kollege")
ZIEL = os.path.join(WORDPRESS, "landingpage-hauskonfigurator.php")
URL = "https://hausbau-konfigurator.de/vorschlag-landingpage"
TEILE = (("codeHead", "head.html"), ("codeBody", "body.html"), ("styles", "styles.css"))
TITEL = "Hausbau-Konfigurator: Ihr Haus mit Grundriss, Außenansicht und Preis"
ENDE = "B2T_LANDINGPAGE"


def holen():
    roh = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"})).read()
    if roh[:2] == b"\x1f\x8b":
        roh = gzip.decompress(roh)
    treffer = re.search(r'<script[^>]*id="one-page-data"[^>]*>(.*?)</script>', roh.decode("utf-8"), re.S)
    version = json.loads(treffer.group(1))["version"]
    os.makedirs(QUELLE, exist_ok=True)
    for feld, datei in TEILE:
        with open(os.path.join(QUELLE, datei), "w", encoding="utf-8", newline="\n") as f:
            f.write(version[feld])


def lesen(datei):
    with open(os.path.join(QUELLE, datei), encoding="utf-8") as f:
        return f.read()


# konfigurator-neu-v1 (Rainer, 2026-11-08): "Los geht's" fuehrt in den neuen
# Konfigurator, /test bleibt. Die Datei des Kollegen bleibt unveraendert.
FUNNEL_ALT = "const FUNNEL_URL = 'https://born2thrill.de/test/';"
FUNNEL_NEU = "const FUNNEL_URL = 'https://born2thrill.de/konfigurator/';"


def dokument():
    kopf = lesen("head.html")
    if FUNNEL_ALT not in kopf:
        raise SystemExit("FUNNEL_URL des Kollegen hat sich geaendert -- bitte pruefen")
    kopf = kopf.replace(FUNNEL_ALT, FUNNEL_NEU)
    return ("<!doctype html>\n<html lang=\"de\">\n<head>\n<meta charset=\"utf-8\">\n"
            "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">\n"
            f"<title>{TITEL}</title>\n{kopf}\n<style>\n{lesen('styles.css')}\n</style>\n"
            f"</head>\n<body>\n{lesen('body.html')}\n</body>\n</html>")


def php(html):
    if re.search(rf"^\s*{ENDE}\b", html, re.M):
        raise SystemExit(f"Endmarke {ENDE} kommt im HTML vor")
    return f"""<?php
/**
 * Landingpage Hauskonfigurator (plans/landingpage-hauskonfigurator-v1.md).
 * Erzeugt von born2thrill-local-workbench/scripts/landingpage-snippet.py aus der
 * Seite des Kollegen ({URL}) -- nicht von Hand aendern, neu erzeugen.
 * Gibt auf der Seite "hauskonfigurator" das komplette Dokument ohne Theme aus.
 */
add_action( 'template_redirect', function () {{
	if ( ! is_page( 'hauskonfigurator' ) ) {{
		return;
	}}
	header( 'Content-Type: text/html; charset=utf-8' );
	echo <<<'{ENDE}'
{html}
{ENDE};
	exit;
}}, 20 );
"""


def main():
    if "--holen" in sys.argv:
        holen()
    text = php(dokument())
    with open(ZIEL, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(os.path.abspath(ZIEL), len(text))


if __name__ == "__main__":
    main()

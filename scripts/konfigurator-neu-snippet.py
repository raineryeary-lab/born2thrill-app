"""Neuer Konfigurator auf born2thrill.de/konfigurator (konfigurator-neu-v1).

Rainer, 2026-11-08: "Los geht's" der Landingpage auf einen neuen Konfigurator;
/test bleibt. "test einfach kopieren und das neue nach unseren neuen Vorgaben":
Layout von /test (CSS-Kopie), statt 3D die Comic-Clips; Einstiegsvideo laeuft
sofort, die erste Frage fliegt nach 3 s unten ein.

Fragen und Szenen kommen bei jedem Lauf frisch aus Codex' Stand
(config-comic/website-preview/src/comic-flow.js, storyboards.js) -- eine Quelle.
Ausgabe: wordpress/konfigurator-neu.php (Snippet; komplettes Dokument ohne Theme
auf der Seite "konfigurator", herausloesbar nach REGELN 38) und
wordpress/konfigurator-neu/index.html (dasselbe Dokument eigenstaendig).
Aufruf: python konfigurator-neu-snippet.py
"""

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
WP = os.path.join(HERE, "..", "wordpress")
ORDNER = os.path.join(WP, "konfigurator-neu")
COMIC = r"C:\Users\Admin\Documents\ChatGPT\config-comic\website-preview\src"
ZIEL = os.path.join(WP, "konfigurator-neu.php")
ENDE = "B2T_KONFIGURATOR"
CFG = {
    # Gesamtfilm statt Intro + Schleife (Rainer, 2026-11-08): einmal 0-20 s, danach nur 15-20 s.
    # Alte Dateien bleiben als Rueckfall in der Mediathek (1741 Intro, 1742 Schleife).
    "film": {"url": "https://born2thrill.de/wp-content/uploads/2026/11/konfigurator-film-hq-v1.mp4", "schleifeAb": 15.0},
    "videos": {},
    # v2 (Rainer ueber Codex, 2026-11-08): nur Standbilder als Platzhalter, kein Loop.
    "stills": {
        "01": "https://born2thrill.de/wp-content/uploads/2026/11/konfigurator-grundstueck-warten-v1.png",
        "02": "https://born2thrill.de/wp-content/uploads/2026/11/konfigurator-budget-sparschwein-v1.png",
    },
    "katalog": "/grundriss-katalog/",
    "frageNachMs": 3000,
}


def lesen(pfad):
    with open(pfad, encoding="utf-8") as f:
        return f.read()


def dokument():
    html = lesen(os.path.join(ORDNER, "konfigurator.html"))
    teile = {
        "/*__CSS_TEST__*/": lesen(os.path.join(ORDNER, "hkf-test-kopie.css")),
        "/*__CFG__*/{}": json.dumps(CFG, ensure_ascii=False),
        "/*__FLOW__*/": lesen(os.path.join(COMIC, "comic-flow.js")),
        "/*__BOARDS__*/": lesen(os.path.join(COMIC, "storyboards.js")),
        "/*__JS__*/": lesen(os.path.join(ORDNER, "konfigurator.js")),
    }
    for marke, inhalt in teile.items():
        if marke not in html:
            raise SystemExit(f"Marke fehlt: {marke}")
        html = html.replace(marke, inhalt)
    if "</script" in teile["/*__FLOW__*/"] + teile["/*__BOARDS__*/"] + teile["/*__JS__*/"]:
        raise SystemExit("</script im Skript")
    return html


def php(html):
    if re.search(rf"^\s*{ENDE}\b", html, re.M):
        raise SystemExit("Endmarke im HTML")
    return f"""<?php
/**
 * Neuer Konfigurator (plans/konfigurator-neu-v1.md). Erzeugt von
 * born2thrill-local-workbench/scripts/konfigurator-neu-snippet.py -- nicht von
 * Hand aendern. Gibt auf der Seite "konfigurator" das komplette Dokument aus.
 * Kontakt sendet nichts (Entwurf).
 */
add_action( 'template_redirect', function () {{
	if ( ! is_page( 'konfigurator' ) ) {{
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
    html = dokument()
    with open(os.path.join(ORDNER, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    with open(ZIEL, "w", encoding="utf-8", newline="\n") as f:
        f.write(php(html))
    print(os.path.abspath(ZIEL), len(html))


if __name__ == "__main__":
    main()

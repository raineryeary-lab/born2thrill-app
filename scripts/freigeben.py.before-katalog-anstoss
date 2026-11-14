#!/usr/bin/env python3
"""Bilder, die schon hochgeladen sind, im Katalog scharf schalten.

    python freigeben.py bungalow_039
    python freigeben.py bungalow_039 --zuruecknehmen
    python freigeben.py --stand

Das fehlende Stueck. `publish-renders.py --send` schaltet nur die Bilder frei,
die es in DEMSELBEN Lauf hochlaedt; wer danach freigeben will, hatte keinen
Befehl dafuer. Und der "Freigeben"-Knopf in der Hausakte ruft `approve-plan.py`,
das ins LOKALE Ledger schreibt und WordPress nie anfasst.

Ergebnis, gemessen am 2026-08-20: bungalow_039 hatte 9 Bilder in der Mediathek,
stand im Ledger auf commercial=True -- und im Katalog trotzdem auf `im: 0,
ok: offen`. Von 310 Grundrissen war genau EINER freigegeben. Die Bilder waren
da; sie waren nur an niemanden angeschlossen.

Dieses Skript setzt das `send`-Kennzeichen ueber b2t/v1/freigabe fuer jedes
Bild, das am genannten Plan haengt, und sagt danach, was der Katalog wirklich
meldet -- nicht, was es geschickt hat.
"""

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.dirname(os.path.dirname(HERE))
SITE = os.environ.get("B2T_SITE", "https://born2thrill.de").rstrip("/")


def lade_env_local():
    """WP_USER / WP_APP_PASSWORD aus .env.local nachziehen (wie publish-renders)."""
    pfad = os.path.join(SUITE, "born2thrill-local-workbench", ".env.local")
    try:
        with open(pfad, encoding="utf-8-sig") as handle:
            for zeile in handle:
                if "=" not in zeile or zeile.lstrip().startswith("#"):
                    continue
                name, _, wert = zeile.partition("=")
                name = name.strip()
                if name in ("WP_USER", "WP_APP_PASSWORD") and not os.environ.get(name):
                    os.environ[name] = wert.strip().strip('"').strip("'")
    except OSError:
        pass


def auth_kopf():
    lade_env_local()
    user = os.environ.get("WP_USER")
    passwort = os.environ.get("WP_APP_PASSWORD")
    if not user or not passwort:
        sys.exit("WP_USER und WP_APP_PASSWORD fehlen (Umgebung oder .env.local).")
    roh = "{}:{}".format(user, passwort).encode("utf-8")
    return "Basic " + base64.b64encode(roh).decode("ascii")


def hole(url, auth=None, koerper=None):
    kopf = {"Accept": "application/json"}
    if auth:
        kopf["Authorization"] = auth
    daten = None
    if koerper is not None:
        daten = json.dumps(koerper).encode("utf-8")
        kopf["Content-Type"] = "application/json"
    anfrage = urllib.request.Request(url, data=daten, headers=kopf,
                                     method="POST" if daten else "GET")
    with urllib.request.urlopen(anfrage, timeout=60) as antwort:
        text = antwort.read().decode("utf-8", "replace")
    return json.loads(text) if text.strip() else {}


def bilder(plan):
    return hole("{}/wp-json/b2t/v1/bilder?plan={}"
                .format(SITE, urllib.parse.quote(plan)))


def eintrag(plan):
    liste = hole(SITE + "/wp-json/b2t/v1/grundrisse")
    if isinstance(liste, dict):
        liste = liste.get("items") or liste.get("data") or []
    for e in liste:
        if e.get("id") == plan:
            return e
    return None


def stand():
    liste = hole(SITE + "/wp-json/b2t/v1/grundrisse")
    if isinstance(liste, dict):
        liste = liste.get("items") or liste.get("data") or []
    mit = [e for e in liste if int(e.get("im") or 0) > 0]
    print("%d Grundrisse im Katalog, %d mit freigegebenen Bildern"
          % (len(liste), len(mit)))
    for e in sorted(mit, key=lambda x: x.get("id") or ""):
        print("  %-44s %2d Bilder  ok=%s" % (e.get("id"), e.get("im"), e.get("ok")))
    return 0


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("plan", nargs="?")
    parser.add_argument("--zuruecknehmen", action="store_true",
                        help="das send-Kennzeichen wieder loeschen")
    parser.add_argument("--stand", action="store_true",
                        help="nur zeigen, was der Katalog gerade freigegeben hat")
    args = parser.parse_args()

    if args.stand:
        return stand()
    if not args.plan:
        return stand()

    liste = bilder(args.plan)
    if not isinstance(liste, list) or not liste:
        sys.exit("Fuer %s liegen keine Bilder in der Mediathek. "
                 "Erst hochladen: python go.py %s --hochladen"
                 % (args.plan, args.plan))

    auth = auth_kopf()
    senden = not args.zuruecknehmen
    print("%s: %d Bild(er) %s"
          % (args.plan, len(liste), "freigeben" if senden else "zuruecknehmen"))
    fehler = 0
    for bild in liste:
        bild_id = bild.get("id")
        try:
            hole(SITE + "/wp-json/b2t/v1/freigabe", auth=auth,
                 koerper={"id": bild_id, "send": senden})
            print("  ok    %s" % (bild.get("name") or bild_id))
        except urllib.error.HTTPError as fehlschlag:
            fehler += 1
            print("  FEHLER %s -- %s %s" % (bild_id, fehlschlag.code,
                                            fehlschlag.read()[:120]))

    # Nach Teilfehlern wird NICHT freigegeben: ein halber Bildsatz im Katalog
    # sieht fertig aus und ist es nicht. Erst alle Bilder, dann der Plan.
    if fehler:
        print("")
        print("%d Bild-Freigabe(n) fehlgeschlagen -- der Plan bleibt auf "
              "'offen'. Noch einmal laufen lassen, wenn die Ursache behoben "
              "ist." % fehler)
        return 1

    # Letzter Schritt: den Grundriss selbst sichtbar machen. Die Haken an den
    # Bildern allein reichen nicht -- der Katalog liest `bilder` und `approved`
    # aus kon_grundrisse, und dafuer gibt es die Route b2t/v1/katalog
    # (wordpress/b2t-katalog-freigabe.php nach wp-content/mu-plugins/).
    try:
        hole(SITE + "/wp-json/b2t/v1/katalog", auth=auth,
             koerper={"plan": args.plan,
                      "bilder": len(liste) if senden else 0,
                      "approved": "ja" if senden else "offen"})
    except urllib.error.HTTPError as f:
        if f.code == 404:
            print("")
            print("Die Route b2t/v1/katalog fehlt auf dem Server.")
            print("Ohne sie bleiben die Bilder unsichtbar, egal wie viele "
                  "angehakt sind.")
            print("Einbauen: born2thrill-local-workbench/wordpress/"
                  "b2t-katalog-freigabe.php")
            print("          nach wp-content/mu-plugins/ hochladen.")
        else:
            print("")
            print("Katalog-Route: %s %s" % (f.code, f.read()[:160]))

    # Nicht melden, was geschickt wurde, sondern was der Katalog sagt.
    e = eintrag(args.plan)
    if e is None:
        print("\nDer Katalog kennt %s nicht." % args.plan)
        return 1
    print("\nKatalog sagt jetzt: im=%s  ok=%s  (%s)"
          % (e.get("im"), e.get("ok"), e.get("t") or "?"))
    if senden:
        im = int(e.get("im") or 0)
        if im != len(liste) or e.get("ok") != "ja":
            print("Unvollstaendig: %d von %d Bildern im Katalog, ok=%s."
                  % (im, len(liste), e.get("ok")))
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

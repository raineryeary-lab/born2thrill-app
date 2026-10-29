#!/usr/bin/env python3
"""Garderobe zurueckholen, wenn Codex sie aus einer Lieferung entfernt hat.

Wozu: `garderobe*` (Garderobenpaneel, Bank, Kleidung, Schirmstaender) ist
fertige, im Plan festgelegte Geometrie -- Codex soll sie nur umstylen, nicht
neu erfinden oder verschieben (siehe INNEN_REGEL in make-codex-job.py). Sie
verschwindet trotzdem in praktisch jeder Lieferung (siehe
plans/garderobe-composite-guard-v1.md fuer den Befund an twostorey_045,
zweimal unabhaengig bestaetigt). Diese Datei holt sie zurueck, PIXEL FUER
PIXEL aus dem eigenen, bereits abgenommenen Baseline-Render derselben Kamera --
keine neue Geometrie, keine Erfindung.

`stuff` bleibt bewusst aussen vor: die Platzhalter dort SOLLEN von Codex neu
erfunden werden (STUFF_NACH_RAUM in make-codex-job.py), ein Komposit wuerde
genau das rueckgaengig machen. Dafuer bleibt `kasten_verdacht` in
lieferung-pruefen.py zustaendig.

Aufruf (Vorschau, aendert nichts):
    python schuetze-garderobe.py <plan> <lieferordner>

Aufruf (schreibt tatsaechlich):
    python schuetze-garderobe.py <plan> <lieferordner> --in-place

<lieferordner> ist absolut oder unter renders/<plan>/.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
              "den Datenordner zu erraten. Siehe .env.local.")
DATA = os.path.abspath(_konfiguriert)

BLENDER = os.environ.get(
    "BLENDER_EXE",
    r"C:\Program Files\Blender Foundation\Blender 5.0" + chr(92) + "blender.exe")

OBJEKTMASKE_SKRIPT = os.path.join(HERE, "objektmaske.py")

# Derselbe Stamm-Begriff wie in make-codex-job.py (_stamm): das erste
# Namenssegment, Tuerblaetter ausgenommen (die kommen hier nicht vor).
GARDEROBE_STAMM = "garderobe"

# Wie weit eine bereits gemeldete Position vom gemessenen Mittelpunkt
# abweichen darf, um als "schon richtig" zu gelten -- dann wird nichts
# angefasst. Groszzuegig, weil ein leicht verschobener, aber vorhandener
# Marker kein Fehler ist, den dieses Skript beheben soll.
BEREITS_KORREKT_PX = 40

# Weichzeichnung am Maskenrand, damit die eingesetzten Pixel keine harte
# Kante zeigen.
FEDER_RADIUS_PX = 4


def stamm(name):
    """Das erste Namenssegment -- derselbe Begriff wie in make-codex-job.py."""
    return (name or "").split("-")[0]


def garderobe_nummern(zuordnung):
    """{nummer: name} aus objektindex.json -> Menge der Garderobe-Nummern."""
    return {int(n) for n, name in zuordnung.items()
            if stamm(name) == GARDEROBE_STAMM}


def maske_fuer_nummern(objektindex_bild, nummern):
    """Schwarz/Weiss-Maske (255 = gehoert dazu) aus dem Objektindex-Bild.

    `objektindex_bild` ist das RGB-Bild aus objektmaske.py: der Rotkanal
    traegt die Objektnummer. Werte ausserhalb `nummern` werden 0.
    """
    from PIL import Image
    rot = objektindex_bild.split()[0]
    if not nummern:
        return Image.new("L", objektindex_bild.size, 0)
    tabelle = bytes(255 if wert in nummern else 0 for wert in range(256))
    return rot.point(tabelle)


def centroid_of_mask(maske):
    """(cx, cy) der weissen Pixel, oder None wenn die Maske leer ist."""
    pixel = maske.load()
    breite, hoehe = maske.size
    summe_x = summe_y = anzahl = 0
    for y in range(hoehe):
        for x in range(breite):
            if pixel[x, y] > 127:
                summe_x += x
                summe_y += y
                anzahl += 1
    if not anzahl:
        return None
    return (summe_x / anzahl, summe_y / anzahl)


def skaliere_maske(maske, zielgroesse):
    """Maske auf eine andere Bildgroesse bringen -- NEAREST, keine Mischfarben
    an der Kante, die spaeter als eigenstaendiges (falsches) Objekt zaehlen
    koennten."""
    from PIL import Image
    if maske.size == zielgroesse:
        return maske
    return maske.resize(zielgroesse, Image.NEAREST)


def feder(maske, radius=FEDER_RADIUS_PX):
    """Maskenrand weich zeichnen, fuer einen unauffaelligen Uebergang."""
    from PIL import ImageFilter
    if radius <= 0:
        return maske
    return maske.filter(ImageFilter.GaussianBlur(radius))


def komposit(basis, ziel, maske):
    """`basis`-Pixel dort einsetzen, wo `maske` weiss ist, weich ueberblendet."""
    from PIL import Image
    if basis.size != ziel.size:
        basis = basis.resize(ziel.size, Image.LANCZOS)
    if maske.size != ziel.size:
        maske = skaliere_maske(maske, ziel.size)
    return Image.composite(basis.convert("RGB"), ziel.convert("RGB"), maske)


def betroffene_katalog_namen(marker_check, stammname=GARDEROBE_STAMM):
    """Welche marker_check-Eintraege zu diesem Stamm gehoeren."""
    return [eintrag for eintrag in (marker_check or [])
            if stamm(eintrag.get("name")) == stammname]


def bereits_korrekt(marker_check, centroid, toleranz_px=BEREITS_KORREKT_PX,
                    stammname=GARDEROBE_STAMM):
    """True, wenn jeder betroffene Marker schon 'sichtbar' und nah dran ist.

    Ohne Mittelpunkt (keine Maske, also kein Objekt dieses Stamms in der
    .blend) gibt es nichts zu vergleichen -- dann zaehlt "nichts zu tun" als
    bereits korrekt.
    """
    betroffen = betroffene_katalog_namen(marker_check, stammname)
    if not betroffen:
        return True
    if centroid is None:
        return True
    cx, cy = centroid
    for eintrag in betroffen:
        if eintrag.get("status") != "sichtbar":
            return False
        bei = eintrag.get("bei")
        if not bei or len(bei) != 2:
            return False
        try:
            x, y = float(bei[0]), float(bei[1])
        except (TypeError, ValueError):
            return False
        if ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5 > toleranz_px:
            return False
    return True


def aktualisiere_marker_check(marker_check, centroid, stammname=GARDEROBE_STAMM):
    """Neue Liste: betroffene Eintraege auf 'sichtbar' + gemessenen Mittelpunkt.

    Unbeteiligte Eintraege kommen unveraendert zurueck. Ohne Mittelpunkt (kein
    Objekt dieses Stamms gefunden) bleibt alles wie es war -- ein Status laesst
    sich nicht auf einen Ort setzen, den es nicht gibt.
    """
    if centroid is None:
        return marker_check
    cx, cy = centroid
    ergebnis = []
    for eintrag in (marker_check or []):
        kopie = dict(eintrag)
        if stamm(kopie.get("name")) == stammname:
            kopie["status"] = "sichtbar"
            kopie["bei"] = [round(cx, 1), round(cy, 1)]
        ergebnis.append(kopie)
    return ergebnis


def _blend_cache_schluessel(blend_pfad):
    return hashlib.sha256(os.path.abspath(blend_pfad).encode("utf-8")).hexdigest()[:16]


def objektindex_holen(blend_pfad, cache_ordner):
    """objektindex.png + .json fuer diese .blend, aus dem Cache oder frisch.

    Ein Cache-Eintrag je `geometry_source`-Pfad: mehrere Katalogbilder teilen
    sich oft dieselbe .blend (alle vier Innenstile eines Geschosses), und
    Blender einmal weniger zu starten ist mehrere Sekunden wert.
    """
    from PIL import Image

    ziel = os.path.join(cache_ordner, _blend_cache_schluessel(blend_pfad))
    index_png = os.path.join(ziel, "objektindex.png")
    index_json = os.path.join(ziel, "objektindex.json")
    if not (os.path.exists(index_png) and os.path.exists(index_json)):
        os.makedirs(ziel, exist_ok=True)
        # Nur den Garderobe-Stamm kodieren: ein Obergeschoss wie
        # twostorey_045's hat 301 sichtbare Meshes, weit ueber objektmaske.py's
        # 250er-Grenze -- ungefiltert liesse sich die Maske fuer solche Haeuser
        # gar nicht erst bauen.
        umgebung = dict(os.environ)
        umgebung["OBJEKTMASKE_NUR_STAMM"] = GARDEROBE_STAMM
        lauf = subprocess.run(
            [BLENDER, "--background", blend_pfad, "--python", OBJEKTMASKE_SKRIPT,
             "--", ziel],
            capture_output=True, text=True, timeout=300, env=umgebung)
        if lauf.returncode != 0 or not os.path.exists(index_png):
            raise RuntimeError(
                "objektmaske.py fehlgeschlagen fuer %s:\n%s" % (blend_pfad, lauf.stderr))
    zuordnung = json.load(open(index_json, encoding="utf-8"))
    bild = Image.open(index_png).convert("RGB")
    return bild, zuordnung


def verarbeite_bild(eintrag, ordner, cache_ordner, in_place, bericht):
    """Ein Katalogbild pruefen und, falls noetig, die Garderobe zuruecksetzen.

    Gibt den (moeglicherweise geaenderten) Katalogeintrag zurueck.
    """
    from PIL import Image

    dateiname = eintrag.get("file") or eintrag.get("filename")
    quelle_blend = eintrag.get("geometry_source")
    basis_render = eintrag.get("geometry_reference_render")
    marker_check = eintrag.get("marker_check")

    if not dateiname or not quelle_blend or not basis_render:
        bericht.append("%s: uebersprungen (geometry_source/-reference_render "
                       "fehlt im Katalog -- kein Vergleich moeglich)"
                       % (dateiname or "?"))
        return eintrag
    if marker_check is None:
        bericht.append("%s: kein marker_check in diesem Katalogschema -- "
                       "Garderobe wird trotzdem per Maske geprueft, aber der "
                       "Status kann nicht aktualisiert werden" % dateiname)

    ziel_pfad = os.path.join(ordner, dateiname)
    if not os.path.exists(ziel_pfad):
        bericht.append("%s: Datei fehlt im Lieferordner -- uebersprungen" % dateiname)
        return eintrag
    if not os.path.exists(quelle_blend):
        bericht.append("%s: geometry_source nicht gefunden (%s) -- uebersprungen"
                       % (dateiname, quelle_blend))
        return eintrag
    if not os.path.exists(basis_render):
        bericht.append("%s: geometry_reference_render nicht gefunden (%s) -- "
                       "uebersprungen" % (dateiname, basis_render))
        return eintrag

    objektindex_bild, zuordnung = objektindex_holen(quelle_blend, cache_ordner)
    nummern = garderobe_nummern(zuordnung)
    if not nummern:
        bericht.append("%s: keine Garderobe in dieser .blend -- nichts zu tun"
                       % dateiname)
        return eintrag

    rohmaske = maske_fuer_nummern(objektindex_bild, nummern)
    ziel_bild = Image.open(ziel_pfad)
    maske_skaliert = skaliere_maske(rohmaske, ziel_bild.size)
    mittelpunkt = centroid_of_mask(maske_skaliert)
    if mittelpunkt is None:
        bericht.append("%s: Garderobe existiert in der .blend, ist aber aus "
                       "dieser Kamera unsichtbar (verdeckt) -- nichts zu tun"
                       % dateiname)
        return eintrag

    if marker_check is not None and bereits_korrekt(marker_check, mittelpunkt):
        bericht.append("%s: Garderobe schon korrekt gemeldet -- unveraendert"
                       % dateiname)
        return eintrag

    weiche_maske = feder(maske_skaliert)
    basis_bild = Image.open(basis_render)
    neues_bild = komposit(basis_bild, ziel_bild, weiche_maske)

    if in_place:
        neues_bild.save(ziel_pfad)
    else:
        vorschau_ordner = os.path.join(ordner, "_garderobe-vorschau")
        os.makedirs(vorschau_ordner, exist_ok=True)
        neues_bild.save(os.path.join(vorschau_ordner, dateiname))

    holen = getattr(maske_skaliert, "get_flattened_data", None) or maske_skaliert.getdata
    bericht.append("%s: Garderobe eingesetzt (%d Pixel, Mittelpunkt %.0f,%.0f)%s"
                   % (dateiname, sum(1 for p in holen() if p > 127),
                      mittelpunkt[0], mittelpunkt[1],
                      "" if in_place else " -- Vorschau, nichts geschrieben"))

    if marker_check is not None:
        eintrag = dict(eintrag)
        eintrag["marker_check"] = aktualisiere_marker_check(marker_check, mittelpunkt)
    return eintrag


def main():
    zerleger = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    zerleger.add_argument("plan")
    zerleger.add_argument("ordner", help="Lieferordner, absolut oder unter renders/")
    zerleger.add_argument("--in-place", action="store_true",
                          help="Bilder und catalog.json tatsaechlich ueberschreiben "
                               "(sonst nur Vorschau unter _garderobe-vorschau/)")
    argumente = zerleger.parse_args()

    renders = os.path.join(DATA, "corrections", argumente.plan, "renders")
    ordner = (argumente.ordner if os.path.isabs(argumente.ordner)
              else os.path.join(renders, argumente.ordner))
    if not os.path.isdir(ordner):
        sys.exit("Lieferordner nicht gefunden: %s" % ordner)

    katalog_pfad = os.path.join(ordner, "catalog.json")
    if not os.path.exists(katalog_pfad):
        sys.exit("catalog.json nicht gefunden in %s" % ordner)
    katalog = json.load(open(katalog_pfad, encoding="utf-8"))

    cache_ordner = os.path.join(ordner, "_garderobe-masken-cache")
    bericht = []
    neue_bilder = []
    for eintrag in katalog.get("images", []):
        neue_bilder.append(verarbeite_bild(eintrag, ordner, cache_ordner,
                                           argumente.in_place, bericht))
    katalog["images"] = neue_bilder

    print("\n".join(bericht))

    if argumente.in_place:
        # Das ungepatchte catalog.json bleibt erhalten -- derselbe Gedanke wie
        # VORHER in lieferung-pruefen.py: ein Nachbesserungsschritt darf die
        # Grundlage, gegen die er nachgebessert hat, nicht wegwerfen.
        vorher_pfad = os.path.join(ordner, "catalog.json.vor-garderobe-schutz")
        if not os.path.exists(vorher_pfad):
            os.replace(katalog_pfad, vorher_pfad)
        json.dump(katalog, open(katalog_pfad, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\ncatalog.json aktualisiert (Original: catalog.json.vor-garderobe-schutz)")
    else:
        print("\nVorschau nur -- nichts geschrieben. Mit --in-place tatsaechlich "
              "anwenden.")


if __name__ == "__main__":
    main()

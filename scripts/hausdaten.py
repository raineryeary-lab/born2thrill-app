#!/usr/bin/env python3
"""Eine Wahrheit fuer Dachform und Massstab eines Hauses.

Beide Angaben liegen in ZWEI Dateien nebeneinander:

    projects/<plan>/annotations.json    die Zeichnung des Nutzers
    projects/<plan>/gebaeudemass.json   die spaeter eingetragene Messung

Das ist Absicht und bleibt so: die Annotation ist der unveraenderliche
Eigenbestand, eine nachtraegliche Messung ist eine eigene Tatsache ueber
dasselbe Haus und muss korrigierbar sein, ohne die Zeichnung anzufassen.

Vorher fuehrte jeder Leser die beiden Dateien selbst zusammen -- fuenfmal, mit
drei verschiedenen Vorrangregeln. Dasselbe Haus galt an einer Stelle als
"Dachform gesetzt" und an einer anderen als "fehlt", und go.py sah im Sidecar
nur nach roof_type_classic: ein Haus mit ausschliesslich moderner Dachform galt
als dachlos.

VORRANGREGEL, ueberall gleich und PRO FELD:
annotations.json gewinnt; ist das Feld dort leer, zaehlt gebaeudemass.json.

Das ist nicht frei gewaehlt, sondern das Verhalten des Bauens
(build-simplifier-render-plan.load_annotations) -- der Bau ist die Wahrheit,
die Anzeigen richten sich danach, nicht umgekehrt. Beim Massstab gilt sie pro
GESCHOSS: ein gemessenes Erdgeschoss schlaegt den eingetragenen Wert, ein
Obergeschoss, das nur im Sidecar steht, geht trotzdem nicht verloren.

Gelesen wird nur. Geschrieben wird weiter dort, wo es heute geschieht
(floorplan-simplifier/app.py, gebaeudemass.py, dachform.py).

Die JS-Seite hat dieselbe Regel und dieselben Feldnamen in
src/lib/floorplan-workbench/hausdaten.mjs.
"""

import hashlib
import json
import os

# Feldname in den Dateien -> Feldname im Ergebnis.
DACHFORM_FELDER = (("dachform_modern", "roof_type_modern"),
                   ("dachform_classic", "roof_type_classic"))

# Woran man erkennt, dass ueberhaupt ein Gebaeudemass eingetragen wurde --
# unabhaengig von der Dachform. Die Dachform in die Massstabs-Pruefung zu
# mischen war genau der Fehler der Statusroute.
MASS_FELDER = ("floor_scale", "rahmen_m", "gebaeude_breite_m", "gebaeude_tiefe_m")


def lies_json(pfad, standard=None):
    try:
        with open(pfad, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return standard


def gesetzt(wert):
    """Leere Zeichenketten, leere Objekte und None zaehlen als nicht gesetzt."""
    if wert is None:
        return False
    if isinstance(wert, str):
        return bool(wert.strip())
    if isinstance(wert, (dict, list, tuple)):
        return len(wert) > 0
    return bool(wert)


def _waehle(annotationen, sidecar, feld):
    """Ein Feld nach der Vorrangregel: Annotation vor Sidecar."""
    if gesetzt(annotationen.get(feld)):
        return annotationen[feld], "annotations"
    if gesetzt(sidecar.get(feld)):
        return sidecar[feld], "gebaeudemass"
    return None, None


def _massstab(annotationen, sidecar):
    """floor_scale pro Geschoss zusammenfuehren, gemessen gewinnt."""
    aus_sidecar = sidecar.get("floor_scale") or {}
    aus_annotation = annotationen.get("floor_scale") or {}
    if not isinstance(aus_sidecar, dict):
        aus_sidecar = {}
    if not isinstance(aus_annotation, dict):
        aus_annotation = {}
    zusammen = {}
    for quelle in (aus_sidecar, aus_annotation):
        for geschoss, wert in quelle.items():
            if gesetzt(wert):
                zusammen[geschoss] = wert
    if not zusammen:
        return {}, None
    aus_zeichnung = any(gesetzt(wert) for wert in aus_annotation.values())
    return zusammen, "annotations" if aus_zeichnung else "gebaeudemass"


def hausdaten(projekt_ordner, streng=False):
    """Dachform, Massstab und Gebaeudemass eines Projektordners.

    streng=True verlangt eine lesbare annotations.json (der Bau darf nicht
    stillschweigend auf einem leeren Haus weiterarbeiten).
    """
    annotationen = lies_json(os.path.join(projekt_ordner, "annotations.json"))
    if streng and not isinstance(annotationen, dict):
        raise SystemExit("keine lesbare annotations.json in " + projekt_ordner)
    sidecar = lies_json(os.path.join(projekt_ordner, "gebaeudemass.json"))

    a = annotationen if isinstance(annotationen, dict) else {}
    g = sidecar if isinstance(sidecar, dict) else {}

    ergebnis = {"annotationen": annotationen if isinstance(annotationen, dict) else None,
                "gebaeudemass": g,
                "herkunft": {}}
    for ziel, feld in DACHFORM_FELDER:
        wert, herkunft = _waehle(a, g, feld)
        ergebnis[ziel] = wert
        ergebnis["herkunft"][ziel] = herkunft
    ergebnis["floor_scale"], ergebnis["herkunft"]["floor_scale"] = _massstab(a, g)
    ergebnis["hat_gebaeudemass"] = any(gesetzt(g.get(feld)) for feld in MASS_FELDER)
    # annotation_space (Seitenverhaeltnis) folgt derselben Regel -- ohne sie
    # findet der Bau bei den 119 Haeusern ohne Vorlage kein Bildmass.
    ergebnis["annotation_space"], ergebnis["herkunft"]["annotation_space"] = _waehle(
        a, g, "annotation_space")
    return ergebnis


# Der Eingangshash: Zeichnung UND Gebaeudemass.
#
# Das Sidecar liefert Massstab, Seitenverhaeltnis und Dachform. Wird dort
# korrigiert, aendert sich die Geometrie, der Annotationshash aber nicht -- eine
# in falscher Groesse gebaute Lieferung galt weiter als aktuell. Die Formel
# stand dreimal von Hand da (build-simplifier-render-plan.py, batch-build.py,
# render-furnished-dollhouse.py): wer sie an einer Stelle aendert, baut, was die
# andere fuer alt haelt. Deshalb steht sie jetzt hier, einmal.
def sidecar_hash(projekt_ordner):
    """sha256 der gebaeudemass.json, oder None wenn keine daneben liegt."""
    try:
        with open(os.path.join(projekt_ordner, "gebaeudemass.json"), "rb") as handle:
            return hashlib.sha256(handle.read()).hexdigest()
    except OSError:
        return None


def input_hash(annotation_hash, side_hash):
    """Beide Eingaenge zu einem Hash. Ohne Annotationshash gibt es keinen --
    dann ist nicht bekannt, wovon gebaut wurde, und das wird nicht erfunden."""
    if not annotation_hash:
        return None
    return hashlib.sha256(("%s:%s" % (annotation_hash, side_hash or "-"))
                          .encode("utf-8")).hexdigest()


def eingangshash(projekt_ordner, annotation_hash):
    """input_hash fuer einen Projektordner -- Sidecar wird selbst gelesen."""
    return input_hash(annotation_hash, sidecar_hash(projekt_ordner))


def hat_dach(projekt_ordner):
    daten = hausdaten(projekt_ordner)
    return bool(daten["dachform_modern"] or daten["dachform_classic"])


def hat_massstab(projekt_ordner):
    return bool(hausdaten(projekt_ordner)["floor_scale"])

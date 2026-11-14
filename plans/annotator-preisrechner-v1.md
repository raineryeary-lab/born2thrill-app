# annotator-preisrechner-v1

Rainer, 2026-11-07: "cant you build another price calculator in the anotater?"
(Anlass: Beispielhaeuser fuer leere Felder nachzeichnen, z. B. Bungalow 3 Zimmer ueber 600 Tsd.)

## Ziel
Im Annotator, Tab Architektur, unter Massstab: ein Kasten "Preis", der beim Zeichnen
live zeigt, was die Matrix fuer dieses Haus ausrechnen wuerde:
gezeichnete Flaeche, Wohnflaeche, Zimmer, umbauter Raum, Haustyp und drei Preise
(heute 3000 EUR/m2 mit Konfigurator-Feld, Markt x Faktor 1,3, 1080 EUR/m3) mit
Budgetspalte (bis 450 / 450-600 / ueber 600 Tsd.).

## Wie
- konfigurator-matrix.py: haus_werte(plan, d=None) und haustyp(plan, d=None) nehmen die
  ungespeicherte Zeichnung an; neue Funktion vorschau(plan, d). Ohne d unveraendert.
- app.py: POST /api/preis?project=... laedt die Matrix (skript_laden), rechnet vorschau.
  Schreibt nichts.
- static/preisrechner.js + Kasten in annotate.html: rechnet neu, sobald sich die
  Zeichnung aendert (dirtyRevision), hoechstens alle 1,5 s.

## Nicht
Kein Preisfeld zum Eintippen, keine Aenderung an konfigurator.json, an der CSV oder an der Website.

## Tests
born2thrill-local-workbench/scripts/konfigurator_matrix_vorschau.test.py,
floorplan-simplifier/tests/test_preisrechner.py

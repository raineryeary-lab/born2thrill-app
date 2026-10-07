# DATENSATZ-3-2-4-NEUZEICHNUNG-001

## Anlass

Rainer, 2026-08-28: "ich kann keine Moebel setzen" -- der Moebel-Tab von
`german_catalog_review_bungalow_3_2_4_b_100_1` bleibt leer. Ursache:

    GET /api/floorplan-workbench/generate?...&reference=german_catalog_review_bungalow_3_2_4_b_100_1
    422  {"error":"Reference is not quality-passed, training-ready, and explicitly annotated."}

Das Haus steht in beiden Datensaetzen. `simplifier-reference.ts` baut
`ALL_REFERENCE_PROJECTS` aus beiden ueber eine Map, der
Rekonstruktions-Eintrag steht hinten und gewinnt. Dort stand
`package_status: "annotated"`, das Tor verlangt `training_ready`.

Rainer, 2026-08-28: "ich habe alles frisch neu gezeichnet". Die Zeichnung
liegt vor: `annotations.json` vom 2026-08-28 16:46 UTC, darin selbst
`package_status: "training_ready"` und `quality_checks.passed: true`.
Der Datensatz war also stale, nicht die Zeichnung.

## Umfang

NUR der eine Projekteintrag in
`born2thrill-local-workbench/data/simplifier-v2/reconstruction-dataset.json`,
ersetzt durch das Ergebnis von `export_generator_dataset.py` fuer dasselbe
Projekt.

Ausdruecklich NICHT: ein vollstaendiger Neuexport. Zur Probe in einen
Testordner ausgefuehrt, wuerde er `dataset.json` von 314 auf 104 Projekte
kuerzen -- 210 Projekte fielen heraus. Das ist ein eigener Vorgang mit
eigener Entscheidung.

Ausdruecklich NICHT: der stale Eintrag desselben Hauses in `dataset.json`
(dort `source_rights_status: not_restricted`, 7 Raeume, alte Geometrie).
Er wird von der Rekonstruktionsfassung ueberstimmt und ist damit
wirkungslos; ihn zu entfernen ist eine Aussage ueber Rechte und braucht
eine eigene Entscheidung. Als Folgepunkt in der Roadmap.

Ausdruecklich NICHT: das Tor in
`src/app/api/floorplan-workbench/generate/route.ts`. Es arbeitet richtig.

## Aenderung am Eintrag

    annotation_sha256  f29929e8...  ->  019a5155...   (= sha256 der neuen Datei)
    package_status     annotated    ->  training_ready
    Raeume             7            ->  6   (Kind und Diele weg, Gast dazu)
    Elemente           16           ->  14

Rechtefelder bleiben unveraendert: `source_rights_status:
restricted_reference`, `usage_scope: internal_reference_only`,
`reconstruction_only: true`, `approval_status: annotated_reference`.
Die Neuzeichnung begruendet keine kommerzielle Eignung.

## Abnahme

1. `curl .../generate?...&reference=german_catalog_review_bungalow_3_2_4_b_100_1`
   liefert 200 statt 422.
2. Der Moebel-Tab zeigt den Grundriss.
3. `node --test` und die Python-Suiten bleiben gruen.
4. Kein anderes Projekt im Datensatz veraendert sich (Diff ueber alle 55).

## Rollback

`reconstruction-dataset.json.vor-3-2-4-neuzeichnung` zuruecckopieren.

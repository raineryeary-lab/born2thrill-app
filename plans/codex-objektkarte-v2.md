# Objektkarte auf der Hausseite zeigen

Status: IMPLEMENTED (Rainer, 2026-08-27 -- schickt die Hausseite direkt nach
CODEX-OBJEKTKARTE-001)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

`codex-objektkarte-v1.md` legt die Karte neben die .blend und nennt sie im
Auftrag beim Namen. Auf der Hausseite steht damit ein Dateiname in einem
Ordner -- genau die Antwort, die Rainer am 2026-08-20 schon einmal
zurueckgewiesen hat ("you gave me that link ...\go-baseline"). Die Karte
gehoert sichtbar auf die Seite, unter "An Codex", neben die .blend-Knoepfe.

## Current evidence and behavior

`src/app/haus/page.tsx:815` zeigt einen Knopf je .blend. Fuer Bilder aus dem
go-baseline-Ordner gibt es keine Route: `api/floorplan-workbench/bild` loescht
ein Bild in WordPress, es liefert keins aus.

## Exact scope

1. Neu: `src/app/api/floorplan-workbench/objektkarte/route.ts` -- GET, liefert
   `OBJEKTKARTE-*.png` aus `<data>/corrections/<plan>/renders/go-baseline`.
   Lokal-Schranke wie die uebrigen Workbench-Routen. Der Dateiname kommt NICHT
   aus der Anfrage: die Route sucht sich die Datei im Ordner selbst, damit
   `datei` kein Weg aus dem Ordner heraus sein kann.
2. `api/floorplan-workbench/auftrag/route.ts` gibt zusaetzlich `karte`
   (Dateiname oder null) zurueck.
3. `src/app/haus/page.tsx` zeigt die Karte unter "An Codex", wenn es eine gibt.

## Files in scope

- `src/app/api/floorplan-workbench/objektkarte/route.ts` (neu)
- `src/app/api/floorplan-workbench/auftrag/route.ts`
- `src/app/haus/page.tsx`
- `scripts/../src/lib` -- nein, unberuehrt

## Explicitly out of scope

Generator, Regelwerk, Renderer, Upload, WordPress, Rechte-Gate.

## API, schema, and data-contract effects

`GET /api/floorplan-workbench/auftrag` bekommt das zusaetzliche Feld `karte`.
Additiv. Neue Route liefert nur `image/png`.

## Acceptance criteria

- Die Karte erscheint unter "An Codex", sobald ein Auftrag geschrieben ist.
- Ohne Karte aendert sich an der Seite nichts.
- Ein Plan- oder Dateiname mit Pfadbestandteilen wird abgewiesen.

## Tests and verification commands

`npm run test:house-state` und `npx tsc --noEmit` muessen gruen bleiben.
Sichtprobe im Browser an `german_catalog_review_bungalow_3_2_3_b_100_1`.
Negativprobe: `?plan=../..` wird abgewiesen.

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder umgeschrieben.

## Protected and risky paths

Die Route liest aus dem Datenordner und liefert Bytes aus. Sie akzeptiert
keinen Dateinamen von aussen und liest nur `OBJEKTKARTE-*.png`.

## Rights, provenance, privacy, and security impact

Keine. Lokal-only, eigener Render, keine Weitergabe.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder mailen,
ohne zu einer freigegebenen korrigierten Korpusreferenz zu passen?

**Nein.** Die Route liest genau eine Datei und gibt sie an den lokalen Browser
aus. Sie schreibt nichts, ruft weder Upload noch Freigabe auf und beruehrt
weder Katalog noch WordPress.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

(keine)

## Verification

- `npm run test:house-state` 8/8, `npx tsc --noEmit` ohne Ausgabe.
- Browser an `german_catalog_review_bungalow_3_2_3_b_100_1`, Reiter "An Codex":
  `.karte img` laedt mit naturalWidth 2000 / naturalHeight 1500.
- Negativprobe gegen die Route:
  `?plan=../..` -> 400, `?plan=..%2f..` -> 400,
  `?plan=onehalfstorey_020` (kein Auftrag) -> 404 mit Klartext,
  `?plan=german_catalog_review_bungalow_3_2_3_b_100_1` -> 200 image/png.

## Rollback

Neue Route loeschen, die zwei Zusaetze in `auftrag/route.ts` und `page.tsx`
zuruecknehmen.

## Unresolved questions

Keine.

## Approval record

Rainer, 2026-08-27, schickt unmittelbar nach der Fertigmeldung die Hausseite
`http://localhost:3000/haus?plan=german_catalog_review_bungalow_3_2_3_b_100_1`.

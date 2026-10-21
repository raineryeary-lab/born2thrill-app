# Möbel: Warnung bei leerem Raum vor „Weiter zu Bauen“

Status: IMPLEMENTED (2026-10-09)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-09: "können wir wenn ein raum ohne möbel ist bitte
warnmeldung beim 'weiter zum Bauen' drücken".

## Current evidence and behavior

- `src/app/floorplan-workbench/furniture.tsx` ~Z. 750–766: der Knopf
  „Weiter zu Bauen“ / „Speichern und weiter“ (nur eingebettet in der
  Hausakte) speichert ggf. und schickt `postMessage({typ:"moebel-gespeichert"})`
  — ohne jede Prüfung auf leere Räume.
- Dieselbe Datei hat schon `punktInPolygon()`, `mitteVon()` und `verlorene()`
  (Möbel außerhalb der Räume) — die Gegenrichtung „Raum ohne Möbel“ fehlt.
- `FurniturePalette` bekommt `rooms` (dasselbe Geschoss wie die
  Zeichenfläche) und `symbols` schon als Props.
- Möbel werden pro Geschoss geladen (`useFurniture(reference, floorId)`);
  im Editor ist nur das aktuelle Geschoss bekannt.

## Repository baselines

born2thrill-local-workbench, Branch `agent/furnished-render-and-annotation-schema`,
HEAD `5be1a4e`, Arbeitsbaum schmutzig (Rainers Änderungen bleiben unberührt).

## Exact scope

1. Neue reine Funktion `leereRaeume(symbols, rooms)` in furniture.tsx: Räume
   (Polygon ≥ 3 Punkte), in denen keine Möbelmitte liegt (`mitteVon` +
   `punktInPolygon`). Räume, die üblicherweise leer bleiben, werden
   ausgenommen (Liste siehe offene Frage 2).
2. Beim Klick auf „Weiter zu Bauen“ / „Speichern und weiter“: gibt es leere
   Räume, erscheint `window.confirm`:
   „Ohne Möbel: Bad, Kind 2. Trotzdem weiter zu Bauen?“
   OK → wie bisher weiter. Abbrechen → bleibt im Möbel-Editor, nichts
   gespeichert, nichts weitergemeldet.
3. Alle Geschosse: aktuelles mit ungespeichertem Stand, die anderen per
   `load_furniture` nachgeladen; Räume aus `render_geometry` (dieselbe
   Geometrie wie die Zeichenfläche). Meldung mit EG/OG/KG/DG-Präfix.

## Files in scope

- `src/app/floorplan-workbench/furniture.tsx`
- `src/app/floorplan-workbench/page.tsx`
- `scripts/moebel-punkte.test.mjs` (Tests angehängt, Logik gespiegelt wie
  dort üblich)

## Explicitly out of scope

- „Speichern“-Knopf (speichert nur, springt nicht) — keine Warnung.
- Nicht eingebetteter Korrektur-Editor („An Render senden“).
- Bauen selbst blockieren — es bleibt eine Warnung, kein Verbot.

## API, schema, and data-contract effects

Keine.

## Acceptance criteria

1. Raum ohne Möbel → Rückfrage mit Raumnamen; Abbrechen bleibt stehen.
2. Alle Räume möbliert → kein Dialog, Verhalten wie bisher.
3. Ausgenommene Räume (z. B. Flur) lösen keine Warnung aus.

## Tests and verification commands

Angehängt an `scripts/moebel-punkte.test.mjs`:
- Raum mit Möbel innen → nicht leer; Raum ohne → leer; Möbel knapp
  außerhalb → Raum leer; ausgenommener Raumname → nicht gemeldet.

    node --test --test-isolation=none scripts/moebel-punkte.test.mjs

Browser: Hausakte, Möbelschritt, Raum leer lassen, „Weiter zu Bauen“ →
Dialog, Abbrechen → bleibt. Keine bestehenden Tests geändert.

## Protected and risky paths

Der Weiter-Knopf steuert die Hausakte. Abbrechen darf weder speichern noch
`postMessage` senden.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

No. Nur eine zusätzliche Rückfrage vor einem bestehenden Schritt; sie kann
Weitergehen nur verhindern, nie auslösen.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

—

## Rollback

`leereRaeume()` und den `confirm`-Block im onClick entfernen.

## Unresolved questions (beantwortet)

1. Nur das aktuelle Geschoss prüfen, oder alle Geschosse (dafür müssten die
   Möbel der anderen Geschosse beim Klick nachgeladen werden)?
2. Welche Räume dürfen leer sein? Vorschlag: Flur, Diele, Treppe, Galerie,
   Luftraum, Abstellraum, Garage, Carport, Balkon, Terrasse.

## Approval record

Rainer, 2026-10-09: "1 alle geschosse 2 so wie du es vorschlägst ist gut dann
mach das so".

## Verification (2026-10-09)

- `node --test --test-isolation=none scripts/moebel-punkte.test.mjs` → 38 pass,
  0 fail (5 neue Tests „leerer Raum“).
- `npx tsc --noEmit`: keine Fehler in page.tsx / furniture.tsx.
- Browser, `/floorplan-workbench?reference=onehalfstorey_020&mode=furniture-embed`:
  - echte Daten, alle 10 Räume möbliert → kein Dialog, weiter.
  - OG im Browser leer simuliert (Antwort von load_furniture abgefangen,
    nichts geschrieben) → „Ohne Möbel: OG: Bad, OG: Eltern / Schlafen,
    OG: Kind, OG: Kind.“ — Flur nicht gemeldet.
    Abbrechen → keine Weitermeldung; OK → Weitermeldung.
- Zusätzlich geändert: `page.tsx` (Prop `leereRaeumeAllerGeschosse`).

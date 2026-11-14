# Eine Wahrheit für Dachform und Maßstab (annotations.json + gebaeudemass.json)

Status: APPROVED (Rainer, 2026-08-25: "FIX THE CODE use a RALPH Loop Fix it FIX IT")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Dachform und Maßstab liegen in zwei Dateien. Jeder Leser führt sie selbst
zusammen -- fünfmal, mit **drei verschiedenen Vorrangregeln**. Das Ergebnis:
dasselbe Haus gilt an einer Stelle als "Dachform gesetzt" und an einer anderen
als "fehlt". Ziel: **eine** Zusammenführung, die alle benutzen.

## Current evidence and behavior

`german_catalog_review_bungalow_3_2_1_b_100_1`:
`annotations.json` hat `roof_type_modern: null`, `roof_type_classic: null`;
`gebaeudemass.json` hat seit 2026-08-20 `flachdach` / `walmdach`.

Die fünf Zusammenführungen, heute gelesen:

| Stelle | Vorrang | Problem |
|---|---|---|
| `scripts/build-simplifier-render-plan.py:224` | annotations, gebaeudemass füllt Lücken | (Referenzverhalten -- das wird gebaut) |
| `scripts/werkbank.py:92` | **gebaeudemass zuerst**, dann annotations | genau umgekehrt zum Bau |
| `scripts/go.py:66-71` | annotations, sonst gebaeudemass | prüft in gebaeudemass **nur** `roof_type_classic`; ein Haus mit nur `roof_type_modern` gilt als dachlos |
| `src/app/api/floorplan-workbench/state/route.ts:73-74` | nur Vorhandensein | mischt Dachform in die Maßstabs-Prüfung |
| `scripts/dachform.py:107` | eigene Prüfung | vierte Variante |

Dasselbe Muster beim Maßstab (`floor_scale`): `go.py:60-63`, `state/route.ts:73`,
`werkbank.py:90`.

## Repository baselines

Repo `born2thrill-local-workbench`, kein Git im Arbeitsverzeichnis; Baseline ist
der Dateistand 2026-08-25. Daten: `E:\born2thrill-local-workbench-data`,
Projekte: `C:\dev\Floorplan-tools\floorplan-simplifier\projects`.

## Exact scope

1. **`scripts/hausdaten.py`** (neu) -- eine Quelle für beide Seiten:
   - `hausdaten(projekt_ordner) -> dict` mit `dachform_modern`, `dachform_classic`,
     `floor_scale`, `gebaeudemass`, und `herkunft: {feld: "annotations"|"gebaeudemass"|None}`.
   - **Vorrangregel, überall gleich: pro Feld gewinnt `annotations.json`; ist es
     dort leer, zählt `gebaeudemass.json`.** Das ist das Verhalten des Bauens --
     der Bau ist die Wahrheit, die Anzeigen richten sich danach, nicht umgekehrt.
   - Leere Zeichenketten zählen als nicht gesetzt.
2. **`src/lib/floorplan-workbench/hausdaten.mjs`** (neu) -- dieselbe Regel, dieselben
   Feldnamen, für die Next-Routen.
3. Die fünf Stellen oben rufen nur noch den Helfer auf. Kein `||`-Gefrickel mehr.
4. `go.py:hat_dach` prüft danach automatisch beide Stile.

## Files in scope

- `scripts/hausdaten.py` (neu), `scripts/hausdaten.test.py` (neu)
- `src/lib/floorplan-workbench/hausdaten.mjs` (neu), `hausdaten.test.mjs` (neu)
- `scripts/build-simplifier-render-plan.py`, `scripts/go.py`, `scripts/werkbank.py`,
  `scripts/dachform.py`
- `src/app/api/floorplan-workbench/state/route.ts`
- `package.json` (ein Testskript `test:hausdaten`)

## Explicitly out of scope

- Die beiden Dateien zusammenlegen oder Daten migrieren. Nur das **Lesen** wird
  vereinheitlicht; geschrieben wird weiter wie bisher.
- `floorplan-simplifier/app.py` (schreibt `annotations.json`).
- Renderer, Zertifikate, Upload, Freigabe.

## API, schema, and data-contract effects

Keine. Keine Datei ändert ihr Format, nichts wird migriert.

## Acceptance criteria

1. Dachform nur in `gebaeudemass.json` -> alle fünf Stellen melden "gesetzt", mit
   demselben Wert.
2. Dachform in beiden, verschiedene Werte -> überall gewinnt `annotations.json`.
3. Nur `roof_type_modern` in `gebaeudemass.json` -> `go.py:hat_dach` ist wahr
   (heute falsch).
4. Maßstab genauso: nur in `gebaeudemass.json` -> kein "vermessung_noetig".
5. `german_catalog_review_bungalow_3_2_1_b_100_1` meldet an allen fünf Stellen
   `modern=flachdach, classic=walmdach` -- am echten Haus nachgemessen, nicht nur
   im Test.
6. Kein bestehender Test wird gelöscht, übersprungen oder abgeschwächt.

## Tests and verification commands

```
python scripts/hausdaten.test.py
node --test --test-isolation=none src/lib/floorplan-workbench/hausdaten.test.mjs
python scripts/build-simplifier-render-plan.test.py
npm run test:house-state
npx tsc --noEmit
```

Neue Tests: die vier Fälle aus den Acceptance-Kriterien 1-4, je einmal in Python
und in JS, mit Wegwerf-Projektordnern.

## Protected and risky paths

`build-simplifier-render-plan.py` erzeugt den Bauplan. Ein Vorzeichenfehler in
der Vorrangregel baut Häuser mit dem falschen Dach. Deshalb: Referenzverhalten
ist ausdrücklich das heutige Verhalten des Bauens, und Kriterium 5 prüft ein
echtes Haus.

## Rollback

Die neuen Dateien löschen und die fünf Aufrufstellen auf die alten Ausdrücke
zurücksetzen; es wird nichts migriert, also gibt es keine Datenrückabwicklung.

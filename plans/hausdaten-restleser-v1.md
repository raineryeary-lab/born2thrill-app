# Die restlichen Selbst-Zusammenführer auf hausdaten umstellen

Status: APPROVED (Fortsetzung von [hausdaten-eine-wahrheit-v1.md]; Rainer,
2026-08-25: "FIX THE CODE ... FIX IT" — derselbe Defekt, nur die Stellen, die
der erste Plan ausdrücklich nicht nannte)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

`hausdaten.py` / `hausdaten.mjs` sind da und in fünf Lesern im Einsatz. Vier
weitere Leser führen `floor_scale` weiterhin selbst zusammen — und zwar
**alles-oder-nichts statt pro Geschoss**. Ein Haus mit Maßstab für das
Erdgeschoss in der Annotation und für das Obergeschoss im Sidecar wird dort
falsch beurteilt.

## Current evidence and behavior

Roadmap-Eintrag `HAUSDATEN-RESTLESER-001`. Betroffen:

- `scripts/batch-build.py:83-86`
- `scripts/workflow.py:70-72`
- `scripts/masse-server.py:47` — sieht **nur** in die Annotation, das Sidecar gar nicht
- handgeschriebene Sidecar-Hashes in `scripts/render-furnished-dollhouse.py`
  und `scripts/run_project.py`

## Repository baselines

Dateistand 2026-08-25 nach hausdaten-eine-wahrheit-v1 (dort: alle Tests grün,
233 Projekte ohne Unterschied im Bauplan).

## Exact scope

1. Die vier Leser rufen `hausdaten()` auf, mit derselben Vorrangregel:
   **pro Feld** gewinnt `annotations.json`, sonst `gebaeudemass.json`.
2. `floor_scale` wird **pro Geschoss** zusammengeführt, nicht als ganzes Objekt.
   Wenn `hausdaten.py` das heute als ganzes Objekt macht, wird es dort
   nachgezogen — samt Test — und die bestehenden fünf Leser erben es.
3. `masse-server.py` liest zusätzlich das Sidecar.

## Files in scope

- `scripts/hausdaten.py`, `scripts/hausdaten.test.py`
- `src/lib/floorplan-workbench/hausdaten.mjs`, `hausdaten.test.mjs`
  (nur falls Punkt 2 die gemeinsame Regel ändert — dann beide Seiten gleich)
- `scripts/batch-build.py`, `scripts/workflow.py`, `scripts/masse-server.py`,
  `scripts/render-furnished-dollhouse.py`, `scripts/run_project.py`

## Explicitly out of scope

- `floorplan-simplifier/app.py` (eigener Roadmap-Eintrag
  `SIMPLIFIER-HAUSDATEN-SYNC-001`)
- Datenmigration, Dateiformate, Renderer-Geometrie, Upload, Freigabe
- Der vorbestehende Toolchain-Hash-Drift der 50 Zertifikate

## API, schema, and data-contract effects

Keine.

## Acceptance criteria

1. Maßstab nur im Sidecar -> alle vier Leser sehen ihn.
2. Maßstab je Geschoss aus verschiedenen Quellen -> zusammengeführt, nicht
   verworfen; die Annotation gewinnt pro Geschoss.
3. `masse-server.py` findet einen Maßstab, der nur im Sidecar steht.
4. Über alle 233 Projekte: die alte und die neue Auswertung ergeben für jeden
   der vier Leser dasselbe, außer wo Kriterium 1-3 die Verbesserung ist —
   jede Abweichung einzeln benannt.
5. Kein bestehender Test gelöscht, übersprungen oder abgeschwächt.

## Tests and verification commands

```
python scripts/hausdaten.test.py
node --test --test-isolation=none src/lib/floorplan-workbench/hausdaten.test.mjs
python scripts/build-simplifier-render-plan.test.py
python scripts/go.test.py
npm run test:house-state
npx tsc --noEmit
```

## Protected and risky paths

`batch-build.py` und `run_project.py` entscheiden, ob gebaut wird.
`render-furnished-dollhouse.py` baut. Deshalb Kriterium 4 über alle Projekte,
bevor irgendetwas als fertig gilt.

## Rollback

Aufrufstellen auf die alten Ausdrücke zurücksetzen; nichts wird migriert.

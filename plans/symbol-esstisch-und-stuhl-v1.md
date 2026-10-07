# Zwei neue Symbole: Esstisch ohne Stühle, Esszimmerstuhl

Status: APPROVED (Rainer, 2026-08-25: "i would also like to have a dining
table without chairs plus a dining room chair")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Heute gibt es nur `essgruppe_6` — Tisch **mit** sechs abgeleiteten Stühlen, als
Block. Wer einen Tisch an die Wand stellen oder Stühle einzeln setzen will,
kann das nicht. Zwei einzelne Symbole dazu.

## Current evidence and behavior

- `symbol-catalog.mjs`: `essgruppe_6` (1710 × 1600, `assembly: true`) ist das
  einzige Esszimmer-Symbol.
- `build-simplifier-render-plan.py:135`: `"essgruppe_6": {"height": 750,
  "type": "dining_set"}`; `:147`: `"essgruppe_stuhl": {"height": 844,
  "type": "dining_chair"}` — der Stuhl existiert also bereits als **interner**
  Schlüssel, den der Bau aus der Essgruppe ableitet (`:2914-2953`), aber nicht
  als Symbol, das man setzen kann.
- `data/symbol-model-picks.json` hat schon beide Modelle:
  - `essgruppe_6.modern` → `cgaxis black and white modern dining table`,
    1522 × 914, Notiz: **"table only … 6 velvet chairs derived by the plan
    builder"** — der Tisch allein ist also bereits das Modell.
  - `essgruppe_stuhl.modern` → `cgaxis dark grey velvet dining chair`, 563 × 593.
- `MODEL_FACING_DEG` kennt weder `essgruppe_stuhl` noch einen Esstisch →
  beide fallen auf 0 zurück, wie die abgeleiteten Stühle heute schon.

## Exact scope

1. `symbol-catalog.mjs` (und die Zwillingsdatei `legacy/symbol-catalog.js`,
   weil `symbol-catalog.test.mjs` beide Schlüssel für Schlüssel vergleicht):
   - `s("esstisch", "Esstisch (ohne Stühle)", "essen", { w: 1600, d: 900,
     mode: "indicative" })`
   - `s("esszimmerstuhl", "Esszimmerstuhl", "essen", { w: 560, d: 590,
     mode: "indicative" })`
   - beide in `ROOM_SYMBOL_SETS.wohnen` (der Bereich Wohnen/Essen/Kochen).
2. `build-simplifier-render-plan.py`:
   - `"esstisch": {"height": 750, "type": "dining_table"}`
   - `"esszimmerstuhl": {"height": 844, "type": "dining_chair"}`
   Beide Typen haben in `TYPE_FINISH` bereits ein Finish (`dining_table` →
   wood-oak) und stehen nicht in `FLUSH_TYPES`.
3. `data/symbol-model-picks.json`: beide Schlüssel auf die **bereits
   vorhandenen** Modelle zeigen. Für `classic` gibt es weder einen nackten
   Tisch noch einen eigenen Stuhl — dort dasselbe Modell, mit Notiz. Ein
   eigener classic-Pick ist eine spätere Aufgabe, kein Blocker.

## Files in scope

- `src/lib/generator/symbol-catalog.mjs`
- `src/app/floorplan-workbench/legacy/symbol-catalog.js`
- `scripts/symbol-catalog.test.mjs`
- `scripts/build-simplifier-render-plan.py`
- `data/symbol-model-picks.json`

## Explicitly out of scope

- `essgruppe_6` und ihre abgeleiteten Stühle bleiben unverändert.
- Ein eigenes classic-Modell für Tisch und Stuhl.
- Eine eigene Palettenrubrik (siehe `plans/symbol-stuff-v1.md`: die
  Kategorienliste steckt in einem bestehenden Test).

## API, schema, and data-contract effects

Zwei neue Katalogschlüssel und zwei Einträge in den Modell-Picks. Bestehende
Möbeldokumente bleiben gültig.

## Acceptance criteria

1. `getSymbol("esstisch")` und `getSymbol("esszimmerstuhl")` existieren,
   Platzierung `stamp`.
2. Beide erscheinen in der Symbolliste für „Wohnen / Essen / Kochen".
3. Beide lösen ein echtes Modell auf (nicht den prozeduralen Kasten).
4. `essgruppe_6` verhält sich unverändert.
5. Im Editor sichtbar geprüft: beide stehen in der Palette.

## Tests and verification commands

```
node --test --test-isolation=none scripts/symbol-catalog.test.mjs
python scripts/build-simplifier-render-plan.test.py
npx tsc --noEmit
```

## Protected and risky paths

`symbol-model-picks.json` steuert, welches Modell gebaut wird. Ein falscher
Pfad heißt: Möbel fehlt im Render. Kriterium 3 prüft deshalb die Auflösung,
nicht nur den Eintrag.

## Rollback

Die zwei Katalogeinträge, die zwei `SYMBOL_3D`-Zeilen und die zwei Picks
entfernen. Keine Daten betroffen.

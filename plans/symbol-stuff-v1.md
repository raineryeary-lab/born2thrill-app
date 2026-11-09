# Neues Möbelsymbol „Stuff" — freies Rechteck, in jedem Raum

Status: APPROVED (Rainer, 2026-08-25: "i need a new symbol type for
furnishing, this one is called stuff" → Form: freies Rechteck, Räume: alle)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Ein Allzweck-Platzhalter: aufziehen wie die Kücheninsel, beliebige Größe, in
jeder Raumkategorie wählbar. Für alles, wofür es kein eigenes Symbol gibt.

## Current evidence and behavior

- Der Katalog liegt in `src/lib/generator/symbol-catalog.mjs`
  (`furniture.tsx:23` liest ihn; die Kopie unter
  `src/app/floorplan-workbench/legacy/symbol-catalog.js` wird von nichts mehr
  importiert — geprüft, keine Treffer).
- Rechteck-Symbole gibt es genau eines: `kuecheninsel`
  (`placement: "rect"`, `symbol-catalog.mjs:79`).
- Der Bau entscheidet an ZWEI Stellen, ob ein Rechteck gebaut wird —
  `build-simplifier-render-plan.py:2024` und `:2758`, beide hart auf
  `key == "kuecheninsel"`. Ein zweites Rechteck-Symbol würde dort still zum
  Pfad und damit zum schrägen Balken — derselbe Fehler wie heute Mittag,
  siehe `plans/kuecheninsel-rechteck-v1.md`. Deshalb wird die Entscheidung
  jetzt eine benannte Menge.
- `render-furnished-dollhouse.py:3618` setzt auf JEDES Rechteck eine
  Granit-Arbeitsplatte. Für eine Küchenzeile ist das richtig (der Pfad-Zweig
  eine Zeile darüber prüft `type == "counter"`), für einen Allzweckkasten
  nicht.

## Exact scope

1. `symbol-catalog.mjs`: `s("stuff", "Stuff", "wohnen", { placement: "rect",
   height_mm: 800 })`, und `"stuff"` in **allen** Einträgen von
   `ROOM_SYMBOL_SETS`.
2. `build-simplifier-render-plan.py`:
   - `SYMBOL_3D["stuff"] = {"height": 800, "type": "storage_shelving", "depth": 600}`
     (`storage_shelving` hat in `TYPE_FINISH` bereits ein Holz-Finish und steht
     **nicht** in `FLUSH_TYPES`, bleibt also, wo es hingesetzt wurde).
   - Neue Menge `RECT_BUILD = {"kuecheninsel", "stuff"}`, benutzt an beiden
     Stellen statt des Schlüsselvergleichs.
3. `render-furnished-dollhouse.py`: Arbeitsplatte nur noch bei
   `type == "counter"`, gleiche Regel wie im Pfad-Zweig.

## Files in scope

- `src/lib/generator/symbol-catalog.mjs`
- `scripts/symbol-catalog.test.mjs` (neue Tests)
- `scripts/build-simplifier-render-plan.py`
- `scripts/build-simplifier-render-plan.test.py` (die heute Mittag von mir
  angelegten Insel-Tests prüfen den Ausdruck wörtlich und werden auf die
  neue Menge nachgezogen — sie sind aus derselben Sitzung und die Änderung
  ist eine bewusste Erweiterung, keine Abschwächung: die Aussage „beide
  Zweige entscheiden gleich" und „die Punktzahl entscheidet nicht" bleibt)
- `scripts/render-furnished-dollhouse.py`

## Explicitly out of scope

- Höhe im Editor einstellbar machen. Heute kommt die Höhe aus `SYMBOL_3D`;
  800 mm ist gesetzt und in einer Zeile änderbar. Eigener Wunsch, wenn nötig.
- Ein eigenes Vorschaubild (`/symbols/stuff.png`) — Rechtecke werden als
  Rechteck gezeichnet, nicht als Bild.
- Die tote Kopie `legacy/symbol-catalog.js`.

## API, schema, and data-contract effects

Keine. Ein neuer Schlüssel im Katalog; bestehende Möbeldokumente bleiben gültig.

## Acceptance criteria

1. `getSymbol("stuff")` existiert, `placement === "rect"`.
2. `"stuff"` steht in jedem Eintrag von `ROOM_SYMBOL_SETS`.
3. Ein gezeichnetes `stuff` erscheint im Bauplan mit `build: "rect"`.
4. `kuecheninsel` bleibt `rect`, `kuechenzeile` bleibt `path`.
5. Im Editor sichtbar geprüft: „Stuff" steht in der Liste, lässt sich aufziehen,
   erscheint als Rechteck.

## Tests and verification commands

```
node --test --test-isolation=none scripts/symbol-catalog.test.mjs
python scripts/build-simplifier-render-plan.test.py
npx tsc --noEmit
```

## Protected and risky paths

Beide `build`-Entscheidungen im Hauptpfad aller Möbel. Kriterium 4 hält fest,
dass sich für die bestehenden Symbole nichts ändert.

## Rollback

Katalogeintrag, `SYMBOL_3D`-Zeile und die Menge entfernen; die
Arbeitsplatten-Bedingung zurücknehmen. Keine Daten betroffen.

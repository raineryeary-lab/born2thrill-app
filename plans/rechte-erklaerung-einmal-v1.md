# Rechteerklärung: einmal fragen, dann merken

Status: APPROVED (Rainer, 2026-08-25: "can we change this last window, did you
change this image or is it yours yes/no" → "ok")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Die Rechtefrage ist keine Qualitätsprüfung, sondern eine Entscheidung. Sie wird
heute bei jedem der 55 gesperrten Häuser neu gestellt und ist nur über ein
Kommandozeilen-Flag (`--rechte-bestaetigt`) zu beantworten, das man kennen muss.
Ziel: **einmal fragen, Antwort mit Datum und Grund festhalten, danach nie wieder
fragen** — und zwar dort, wo Rainer ohnehin steht, im Schritt „Hochladen &
Freigeben".

## Current evidence and behavior

- `scripts/approve-plan.py:194-206` lehnt ab, wenn
  `german-catalog-source.json → usage_rights.commercial_use_allowed` `false` ist.
  Einziger Ausweg: `--rechte-bestaetigt`.
- `scripts/publish-renders.py:172-193` (`check_rights`) macht dasselbe für
  `--send`, gegen das Corpus-Ledger.
- Betroffen: **55 Häuser**, alle aus dem Datensatz `Team Massivhaus catalog`
  (gezählt über alle `german-catalog-source.json`, 2026-08-25).
- `src/app/haus/page.tsx:747-759` fragt bereits nach einer Begründung, gibt sie
  an `approve-plan.py --reason` weiter (`pipeline/route.ts:139`) — **ohne**
  Rechteerklärung, deshalb die Ablehnung, die Rainer heute gesehen hat.
- Warum die Sperre existiert (`approve-plan.py` Kopf): am 2026-08-01 wurden
  genau diese 55 Projekte pauschal mit der Begründung "real plan has explicit
  generator rights" freigegeben, während ihre eigenen Herkunftsnachweise
  `rights-unconfirmed` sagten. Das darf sich nicht unbemerkt wiederholen.

## Exact scope

1. **`scripts/rechte.py`** (neu) — Erklärungen lesen und schreiben.
   Ablage: `<FLOORPLAN_WORKBENCH_DATA_DIR>/rechte-erklaerungen.json`.
   Eintrag: `geltung` (`plan` | `datensatz`), `wert`, `antwort` (`ja` | `nein`),
   `grund`, `wer`, `wann`, sowie `herkunft_sagte` — was der Nachweis zum
   Zeitpunkt der Erklärung sagte. Der Widerspruch wird also mitprotokolliert,
   nicht überschrieben.
   - `erklaerung_fuer(plan)`: erst plan-eigene Erklärung, sonst die des
     Datensatzes aus `german-catalog-source.json`.
   - Nur `antwort == "ja"` öffnet. `nein` wird festgehalten und lehnt ab, ohne
     erneut zu fragen.
2. `approve-plan.py` und `publish-renders.py` fragen vor der Ablehnung
   `rechte.erklaerung_fuer(plan)`. Liegt ein Ja vor: durchlassen und
   protokollieren, wer wann was erklärt hat. `--rechte-bestaetigt` bleibt
   unverändert bestehen.
3. **`src/app/api/floorplan-workbench/rechte/route.ts`** (neu) — GET: was gilt
   für diesen Plan; POST: Antwort festhalten.
4. **`src/app/haus/page.tsx`** — im Schritt „Hochladen & Freigeben" steht die
   Frage **vor** dem Freigeben-Knopf, solange keine Erklärung vorliegt:
   *„Hast du diesen Grundriss selbst gezeichnet oder so verändert, dass er dein
   Werk ist?"* mit Begründungsfeld, Ja/Nein, und einem Haken „gilt für alle
   Häuser aus «Team Massivhaus catalog»". Liegt eine Erklärung vor, steht dort
   nur noch eine Zeile, wer sie wann abgegeben hat.

## Files in scope

- `scripts/rechte.py` (neu), `scripts/rechte.test.py` (neu)
- `scripts/approve-plan.py`, `scripts/publish-renders.py`
- `src/app/api/floorplan-workbench/rechte/route.ts` (neu)
- `src/app/haus/page.tsx`
- `package.json` (`test:rechte`)

## Explicitly out of scope

- `german-catalog-source.json` wird **nicht** geändert. Der Herkunftsnachweis
  bleibt, was er ist; die Erklärung steht daneben, nicht darüber.
- Quellbilder löschen (Rainer, 2026-08-25 vorgeschlagen; abgeraten: 48,9 MB
  gesamt, und `image_size()` braucht die Vorschau als Maßgrundlage).
- Corpus-Ledger, Renderer, Upload-Mechanik, Katalog.

## API, schema, and data-contract effects

Eine neue Datei im Datenordner. Kein bestehendes Format ändert sich.

## Acceptance criteria

1. Ohne Erklärung: `approve-plan.py` lehnt genau wie heute ab.
2. Nach einem Ja für den Plan: `approve-plan.py` läuft ohne
   `--rechte-bestaetigt` durch und schreibt in das Ledger, wer wann erklärt hat.
3. Ein Ja für den **Datensatz** gilt für alle 55 Häuser, ohne 55 Einträge.
4. Ein **Nein** lehnt ab und fragt nicht erneut.
5. `--rechte-bestaetigt` funktioniert weiter wie bisher.
6. Die Erklärung hält fest, was der Herkunftsnachweis zum Zeitpunkt sagte.
7. Am laufenden Server sichtbar geprüft: Frage erscheint, Antwort verschwindet
   die Frage, Freigeben läuft danach durch — nicht nur im Test.

## Tests and verification commands

```
python scripts/rechte.test.py
python scripts/hausdaten.test.py
npm run test:house-state
npx tsc --noEmit
```

## Protected and risky paths

Das ist der Pfad zur Kundenfreigabe. Die Sperre darf **nicht** aufweichen: ohne
menschliche Antwort passiert nichts, ein Ja wird namentlich und mit Datum
festgehalten, und der widersprechende Herkunftsnachweis wandert mit in den
Eintrag. Genau der Vorfall vom 2026-08-01 (55 Pauschalfreigaben mit falscher
Begründung) muss nachvollziehbar bleiben, wenn er noch einmal passiert.

## Rollback

`rechte.py`, die Route und die Tests löschen, die zwei Skripte und die Seite
zurücksetzen. Die Erklärungsdatei ist reine Ergänzung; nichts wird migriert.

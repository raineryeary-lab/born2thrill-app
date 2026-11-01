# LIEFERN-STATUS-SICHTBAR-001: Tab "Hochladen & Freigeben" zeigt, was erledigt ist und was fehlt

Status: DONE 2026-10-30 (Rainer: "ja"; 12 Tests OK, im Browser an drei Häusern geprüft, kein Knopf gedrückt)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-30: "auf den localhost 3020 ist es nie erkennbar auf der hochladen freigene site was jetzt ncoh nicht gemacht ist wiseo sthet nicht 'jetzt hochladen' 'ist hochgeladen' 'jetzt freigeben' 'ist freigegeben am...'"

Der Tab in `/haus` soll für das offene Haus sofort sagen: was ist gemacht, was fehlt noch.

## Current evidence and behavior

- `src/app/haus/page.tsx:1428-1495`: Der Tab zeigt immer dieselben Knöpfe "Hochladen" und "Freigeben", egal wie der Stand ist. Text oben: "Bilder in den Katalog, danach die Rechte erklären."
- Die Daten liegen schon vor, aber nicht in diesem Tab:
  - `bilder` (online, je Bild `send`), `page.tsx:338`, geladen in `bilderLaden` (Zeile 648).
  - `geordnet.nichtHochgeladen` (fertige lokale Bilder, die noch nicht online sind), Zeile 347.
  - `aktuell.approved` ("ja"/"offen" aus dem Katalog), `state/route.ts:373`.
- Das Freigabedatum steht nur im lokalen Ledger: `data/simplifier-v2/corpus-ledger.json`, Feld `approval_recorded_at`, geschrieben von `scripts/approve-plan.py:271`. Gemessen: 98 von 98 freigegebenen Einträgen haben ein Datum. Der Katalog meldet 101 auf "ja", es gibt also bis zu 3 Häuser ohne Datum.
- `/api/floorplan-workbench/rechte` GET liefert das Datum noch nicht.
- Der Katalog (`b2t/v1/bilder`) liefert kein Upload-Datum. Rainer hat auch nur beim Freigeben ein Datum verlangt.

## Repository baselines

- Repo `born2thrill-local-workbench`, Branch `agent/furnished-render-and-annotation-schema`, HEAD 5be1a4e.
- `src/app/haus/page.tsx` und `rechte/route.ts`: Stand wird vor der Umsetzung geprüft, Sicherungen `.before-liefern-status`.

## Exact scope

1. Neue reine Funktion `lieferStand({ online, fehlenLokal, frei, katalogOk, freigegebenAm })` in `src/lib/floorplan-workbench/liefer-stand.mjs`.
2. `rechte/route.ts` GET gibt zusätzlich `freigegeben_am` aus (`approval_recorded_at` des Ledgers, sonst null). Nur lesen.
3. Der Tab zeigt zwei Zeilen statt der bisherigen Ansicht:

| Stand | Hochladen |
|---|---|
| nichts online | Knopf **Jetzt hochladen** |
| lokal fehlen noch N Bilder | Knopf **Jetzt hochladen** · "N Bilder fehlen noch" |
| alles online | grün **Ist hochgeladen** · "10 Bilder", kleiner Knopf "Nochmal hochladen" |

| Stand | Freigeben |
|---|---|
| nichts online | ausgegraut **Erst hochladen** |
| online, nicht frei | Knopf **Jetzt freigeben**, Begründungsfeld wie bisher |
| teilweise frei | Knopf **Jetzt freigeben** · "6 von 10 Bildern frei" |
| Katalog "ja" und alle Bilder frei | grün **Ist freigegeben am 30.10.2026**, kein Knopf |
| wie oben, aber ohne Datum | grün **Ist freigegeben** · "Datum nicht erfasst" |

4. Während der Stand lädt: "Stand wird geladen …", nicht "fehlt noch". Ist der Katalog nicht erreichbar: "Stand unbekannt", die Knöpfe bleiben wie heute.

## Files in scope

- `src/lib/floorplan-workbench/liefer-stand.mjs` (neu)
- `scripts/liefer-stand.test.mjs` (neu)
- `src/app/api/floorplan-workbench/rechte/route.ts`
- `src/app/haus/page.tsx`
- `born2thrill-app-repo/plans/ROADMAP.md`

## Explicitly out of scope

- `publish-renders.py`, `freigeben.py`, `approve-plan.py`, das WordPress-Plugin.
- Der neue Schaltzustand ändert nicht, was die Knöpfe tun.
- Die Rechtefrage bleibt, wie sie ist.
- Hausliste und Overview-Seite.
- Upload-Datum (Katalog liefert keins).

## API, schema, and data-contract effects

`rechte` GET bekommt ein optionales Feld `freigegeben_am`. Kein neues Speicherformat.

## Acceptance criteria

- Jede Zeile der zwei Tabellen ist durch einen Test belegt.
- "Ist freigegeben" erscheint nie, wenn der Katalog "offen" sagt oder ein Bild nicht frei ist.
- Kommen neue Bilder dazu, springt die Anzeige auf "Jetzt hochladen" bzw. "Jetzt freigeben" zurück.
- Nach Hochladen oder Freigeben aktualisiert sich der Stand ohne Neuladen der Seite.
- Im Browser auf localhost:3020 an drei Häusern geprüft, nur ansehen, ohne einen der Knöpfe zu drücken: nichts online, online nicht frei, freigegeben.

## Tests and verification commands

Neu: `scripts/liefer-stand.test.mjs`. Keine bestehenden Tests werden geändert, übersprungen oder gelöscht.

```bash
node --test scripts/liefer-stand.test.mjs
```

## Protected and risky paths

`/haus` löst Upload und Freigabe aus. Die Änderung betrifft die Anzeige, die Aufrufe `pipeline("hochladen")` und `pipeline("freigeben")` bleiben unverändert.

## Rights, provenance, privacy, and security impact

Keine. Die Anzeige liest nur. Rechte und Freigabe bleiben Rainers Entscheidung.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? **No.** Es kommt kein neuer Upload- oder Freigabeweg dazu, nur eine Anzeige und ein gelesenes Feld.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

Keine.

## Rollback

Neue Dateien entfernen, `.before-liefern-status`-Sicherungen zurückspielen.

## Unresolved questions

- Bis zu 3 Häuser haben kein Freigabedatum. Sie zeigen "Datum nicht erfasst".

## Approval record

Approved 2026-10-30.

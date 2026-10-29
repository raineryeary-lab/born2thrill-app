# Eine Wahrheit je Haus: Lieferung annehmen

Status: APPROVED (Rainer, 2026-08-27, "fix it")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Drei Stellen im Code erfinden drei Ordnernamen, und keine kennt die andere:

| Wer | Name |
|---|---|
| `make-codex-job.py` schreibt in den Auftrag | `codex-<plan>-<datum>` |
| `publish/route.ts` liest fuer den Bilder-Tab | `codex-final-*`, neuester gewinnt |
| `codex-rueckgabe/route.ts` kopiert nach | `codex-final-<stempel>` |
| `publish-renders.py` laedt hoch | was in `--dir` steht |

Folge: der Auftrag schickt Codex in einen Ordner, den der Bilder-Tab nie
ansieht. `bungalow_039` hat acht `codex-final-*`-Ordner; "neuester gewinnt"
sortiert alphabetisch und waehlt `codex-final-2026-08-26-v2` statt des
juengeren `codex-final-2026-08-26-2110`.

Es soll genau EINE Wahrheit je Haus geben: der angenommene Lieferordner,
festgehalten in `renders/ANGENOMMEN.json`.

## Exact scope

1. Neu `scripts/lieferung-pruefen.py`: prueft einen Lieferordner gegen
   `codex-job.json` -- geforderte Dateien vorhanden, Pixelmasze, sha256 gegen
   `catalog.json`, `marker_check` vollstaendig und farbrichtig, keine
   Zusatzdateien. Mit `--annehmen` schreibt es `renders/ANGENOMMEN.json`.
2. Neu `scripts/lieferung-pruefen.test.py`.
3. Neu `src/app/api/floorplan-workbench/annehmen/route.ts`:
   GET listet die Lieferordner mit ihrem Pruefergebnis, POST nimmt einen an.
4. `src/app/api/floorplan-workbench/publish/route.ts`: `localRenders()` liest
   `ANGENOMMEN.json`. Fehlt sie, bleibt das bisherige Verhalten
   (`codex-final-*`, neuester) -- sonst wuerden 232 Haeuser schlagartig leer.
5. `src/app/haus/page.tsx`: im Schritt "Hochladen & Freigeben" die Liste der
   Lieferordner mit Befund und einem Knopf "annehmen".

## Files in scope

- `scripts/lieferung-pruefen.py` (neu)
- `scripts/lieferung-pruefen.test.py` (neu)
- `src/app/api/floorplan-workbench/annehmen/route.ts` (neu)
- `src/app/api/floorplan-workbench/publish/route.ts`
- `src/app/haus/page.tsx`

## Explicitly out of scope

- `publish-renders.py` (`--dir` bleibt; der Knopf reicht den Pfad spaeter an)
- Renderer, Bauplan, Regelwerk, WordPress, Rechte-Gate
- Aufraeumen der acht Altordner von `bungalow_039`

## API, schema, and data-contract effects

Neu `renders/ANGENOMMEN.json` (`zf-angenommen-v1`): Plan, Ordnername,
Job-Id, Zeitpunkt, Dateien mit sha256. Additiv, niemand liest sie bisher.
`GET /api/floorplan-workbench/publish` liefert unveraendert `local`.

## Acceptance criteria

- Ein Ordner mit fehlender Datei, falschem Masz, falschem sha256 oder
  lueckenhaftem `marker_check` wird NICHT angenommen und der Grund benannt.
- Nach der Annahme zeigt der Bilder-Tab genau diesen Ordner.
- Ohne `ANGENOMMEN.json` aendert sich fuer ein Haus nichts.

## Tests and verification commands

`python scripts/lieferung-pruefen.test.py`
- vollstaendige Lieferung -> keine Beanstandung
- fehlende Datei / falsches Masz / falscher sha256 -> je eine Beanstandung
- `marker_check` fehlt, unvollstaendig, doppelt, Status passt nicht zur Farbe
- Zusatzdatei im Ordner
- ohne `--annehmen` wird nichts geschrieben

Dazu `npm run test:house-state` und `npx tsc --noEmit`.
Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder umgeschrieben.

## Protected and risky paths

`ANGENOMMEN.json` wird nur bei null Beanstandungen geschrieben. Der Pruefer
veraendert keine Bilddatei und loescht nichts.

## Rights, provenance, privacy, and security impact

Keine. Rein lokal, kein Upload, keine Freigabe.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder mailen,
ohne zu einer freigegebenen korrigierten Korpusreferenz zu passen?

**Nein.** Der Pruefer liest und schreibt eine Zeigerdatei. Er ruft weder
`publish-renders.py` noch `approve-plan.py`, erzeugt keine Geometrie und
setzt keinen Kundenhaken. Die Annahme macht Bilder lokal sichtbar, nicht
oeffentlich.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

(leer)

## Rollback

Neue Dateien loeschen, die zwei Zusaetze in `publish/route.ts` und
`page.tsx` zuruecknehmen, `ANGENOMMEN.json` entfernen.

## Unresolved questions

Keine.

## Approval record

Rainer, 2026-08-27: "fix it" auf den Vorschlag "Knopf Lieferung annehmen,
schreibt ANGENOMMEN.json, Bilder-Tab und Upload lesen nur noch das".

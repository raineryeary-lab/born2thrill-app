# Haus-Stand sichtbar: Codex-Pakete und hochgeladene Bilder ueberall

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Pro Haus an allen Stellen (Haus-Seite, Uebersicht, Haeuser-Liste) sichtbar machen: (a) wie viele Bilder online sind und welche zuletzt dazukamen, (b) welche Codex-Pakete im .codex-Ordner liegen und noch nicht hochgeladen sind. Rainer: "bitte ueberall sichtbar machen, es macht es unheimlich schwer alles auf Stand zu bekommen."

## Current evidence and behavior

- `codex-rueckgabe/route.ts` findet Pakete nur, wenn der **Ordnername die plan_id enthaelt** (`eintrag.includes(plan)`, Zeile 90). Codex-Pakete heissen aber `b331-complete-...`, `b332-two-exteriors-...` -- die plan_id steht nur in `catalog.json` (`plan_id`). Diese Pakete sind deshalb im Tab "An Codex" unsichtbar. Das ist die Hauptursache.
- Der Tab "Bilder" in `haus/page.tsx` laedt den WordPress-Katalog einmal beim Planwechsel (Zeile 476). Nach einem Upload ausserhalb der Seite (publish-renders.py) bleibt die Anzeige alt bis F5. Beim ersten Aufruf war sie zudem leer, weil `/state` ueber ~244 Haeuser langsam ist und `plan` erst danach gesetzt wird.
- `/state` liefert pro Haus `catalogue_images` (Anzahl), aber keine Info ueber wartende Codex-Pakete oder den letzten Upload.
- Beobachtet am 2026-10-03: Plan `..._3_3_2_b_100_2` hatte nach meinem Upload (IDs 661/662) ploetzlich 6 weitere Bilder (IDs 663-668, ohne "-review"), Herkunft unklar. Heute unsichtbar, weil nirgends ein Upload-Verlauf angezeigt wird.

## Repository baselines

born2thrill-local-workbench, Branch/HEAD 5be1a4e. Vorhandene Aenderungen im Arbeitsbaum (nicht anfassen): `.claude/launch.json`, `data/simplifier-v2/corpus-ledger.json`, `data/simplifier-v2/dataset.json` und weitere, noch nicht von mir geprueft. Vor der Umsetzung `git status` einschliesslich untracked erneut aufnehmen.

## Exact scope

1. `codex-rueckgabe/route.ts`: Treffer auch dann, wenn `catalog.json` im Paketordner `plan_id === plan` hat (zusaetzlich zur Namenssuche). Fuer reine ZIPs ohne entpackten Ordner: `catalog.json` per Python-zipfile lesen. Einmal pro Anfrage einen Index aller Pakete bauen (nicht pro Haus neu durchlaufen). Rueckgabe je Paket: Bilderliste mit Status aus catalog.json, `hochgeladen` pro Bild (Dateistamm kommt in einem WordPress-Bildnamen des Plans vor).
2. Neuer lesender Endpunkt oder Erweiterung von `/state`: pro Haus `codex_wartend` (Anzahl Bilder aus Paketen, die noch nicht online sind) und `letzter_upload` (aus WordPress-Mediendatum, falls die Route es liefert; sonst weggelassen und hier gemeldet). Index mit 60 s Cache, damit `/state` nicht langsamer wird.
3. `haus/page.tsx`: Stand-Zeile pro Haus in der Liste ("12 online | 2 Codex wartend"); Tab "Bilder" laedt den Katalog neu beim Tab-Wechsel und beim Zurueckkehren ins Fenster (`visibilitychange`) und zeigt Ladezustand statt "Noch keine Bilder", solange `plan` oder Fetch noch nicht fertig sind; Tab "An Codex" zeigt gefundene Pakete mit je "noch nicht hochgeladen / hochgeladen".
4. `floorplan-workbench/overview/page.tsx`: gleiche zwei Zahlen pro Hausreihe.
5. Anzeige "unbekannte Bilder": Bilder im Katalog, die nicht aus einem bekannten Paket oder einem lokalen Render stammen (z. B. IDs 663-668), mit Hinweis kennzeichnen. Nur anzeigen, nichts loeschen.

## Files in scope

- `src/app/api/floorplan-workbench/codex-rueckgabe/route.ts` (+ Test)
- `src/app/api/floorplan-workbench/state/route.ts` (additive Felder)
- `src/app/haus/page.tsx`
- `src/app/floorplan-workbench/overview/page.tsx`
- neue Hilfsdatei `src/lib/floorplan-workbench/codex-pakete.mjs` (+ Test)

## Explicitly out of scope

- Hochladen, Freigeben, "an Kunden", `--send`, Loeschen von WordPress-Bildern. Es wird nichts veroeffentlicht.
- Aenderungen an `publish-renders.py`, an Renderern, Geometrie, Annotator.
- Automatisches Einlesen/Kopieren von Paketen ohne Klick.
- Klaerung, wer IDs 663-668 hochgeladen hat (nur sichtbar machen).

## API, schema, and data-contract effects

Additive Felder in `/state` (`codex_wartend`, ggf. `letzter_upload`) und in der `codex-rueckgabe`-Antwort (`bilder[]`, `plan_id_aus_catalog`). Bestehende Felder unveraendert. `catalog.json` wird nur gelesen, nie geschrieben.

## Acceptance criteria

1. `b331-complete-2300ecd5-20261003` und `b332-two-exteriors-20261003-v3` erscheinen bei ihren Plaenen (`..._3_3_1_b_100_2`, `..._3_3_2_b_100_2`) im Tab "An Codex", obwohl der Ordnername die plan_id nicht enthaelt.
2. Bereits hochgeladene Bilder werden als "hochgeladen" markiert, die uebrigen als "wartend".
3. Haus-Liste und Uebersicht zeigen online/wartend pro Haus.
4. Tab "Bilder" zeigt nach externem Upload ohne F5 den neuen Stand (Fensterfokus/Tab-Wechsel) und nie "Noch keine Bilder" waehrend des Ladens.
5. `/state` bleibt innerhalb von +2 s gegenueber heute.
6. Kein Schreibzugriff auf WordPress oder catalog.json durch die neuen Pfade.

## Tests and verification commands

Neue Tests: `codex-pakete.test.mjs` (plan_id-Treffer ohne Namens-Treffer; ZIP ohne Ordner; uploaded-Erkennung per Dateistamm; defekte/fehlende catalog.json wird uebersprungen), Erweiterung des `codex-rueckgabe`-Tests. Bestehende Tests werden nicht geaendert. Ausfuehrung: `node --test` fuer die genannten Dateien; danach Sichtpruefung im Browser auf :3020 fuer beide Plaene.

## Protected and risky paths

`/state` ist langsam (WordPress-Abfragen); Zusatzscan des .codex-Baums muss gecacht sein. `.codex`-Zugriff nur lesend und nur in den bestehenden `suchorte()`.

## Rights, provenance, privacy, and security impact

Keine Rechte-/Provenienzaenderung. Nur lesende Anzeige; Pfadpruefung bleibt wie in der Route. Review-Bilder bleiben "nicht an Kunden", keine Statusaenderung.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Nein. Alle Aenderungen sind lesende Anzeige von Dateilisten und Katalogzaehlern; es wird keine Geometrie erzeugt, veroeffentlicht oder versendet.

## Customer, email, database, deployment, and external effects

Keine. Nur lesende GET-Aufrufe gegen WordPress (wie heute).

## Failed-hypothesis log

Keine bisher.

## Rollback

Die fuenf Dateien auf den Stand von HEAD 5be1a4e zurueckfuehren, neue Hilfsdatei und Tests loeschen. Keine Daten betroffen.

## Unresolved questions

- Soll "wartend" nur Bilder zaehlen, deren Paket-Status `review_pending_user_approval` ist, oder alle nicht hochgeladenen? (Vorschlag: alle nicht hochgeladenen.)
- Gibt die WordPress-Route ein Upload-Datum pro Bild her? Falls nein, entfaellt `letzter_upload`.

## Approval record

Not approved. Stop before implementation.

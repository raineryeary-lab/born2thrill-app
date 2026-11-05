# MOEBEL-EIN-SPEICHERN-001: Ein Klick auf Speichern speichert alle Geschosse

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-30, nach onehalfstorey_xvv1 (beide Geschosse veraltet): "that stupid save on one screen should be save". Verstanden als: Im Möbel-Schritt speichert ein Klick das ganze Haus, nicht jedes Geschoss einzeln.

## Current evidence and behavior

- `furniture.tsx:409` `save()` speichert nur das offene Geschoss (`floor_id: floorId`).
- `furniture.tsx:157-160` leert beim Geschosswechsel den Stand. Ungespeicherte Änderungen des anderen Geschosses gehen dabei verloren; in `page.tsx` wurde keine Abfrage dafür gefunden. Noch im Browser zu bestätigen.
- `furniture.tsx:459` zeigt "Räume geändert — einmal speichern." nur für das offene Geschoss. Das andere Geschoss bleibt unsichtbar veraltet.
- Der Bau hält bei fremdem Stempel an (`build-simplifier-render-plan.py:811-817`).
- Gemessen an xvv1, 13:35: Möbel-Schritt lädt, "Speichern" ist anklickbar, Dateien von 10:51 und 10:54 unverändert.
- `page.tsx:1906-1918` liest schon alle Geschosse (`ladeMoebel`), ebenso `renderGeo.floors[i].geometry_identity`.

## Repository baselines

- Repo `born2thrill-local-workbench`, Branch `agent/furnished-render-and-annotation-schema`, HEAD 5be1a4e.
- `page.tsx` und `corrections/route.ts` sind schon geändert (M), viele weitere Dateien offen. Stände bleiben erhalten, Sicherungen `.before-ein-speichern`.

## Exact scope

1. Geschosswechsel im Möbel-Schritt behält ungespeicherte Änderungen im Speicher (je Geschoss ein Entwurf).
2. "Speichern" und "Speichern und weiter" speichern nacheinander:
   - das offene Geschoss,
   - jedes Geschoss mit Entwurf,
   - jedes Geschoss, dessen Datei einen alten Stempel trägt.
3. Jeder Speichervorgang geht wie heute durch `save_furniture`, mit der angezeigten Kennung des jeweiligen Geschosses aus `renderGeo`. Die Sperre gegen zwischendurch umgezeichnete Räume bleibt also für alle Geschosse aktiv.
4. Meldung nach dem Speichern nennt jedes Geschoss einzeln, z. B. "Erdgeschoss: 24 gespeichert. Obergeschoss: 21 gespeichert, Stempel erneuert, nicht angesehen — bitte prüfen."
5. Scheitert ein Geschoss: Meldung nennt es, "Speichern und weiter" bleibt stehen, Entwürfe bleiben erhalten.
6. Kurze Anzeige, solange ein anderes Geschoss veraltet ist: "Obergeschoss: Räume geändert".

## Files in scope

- `src/app/floorplan-workbench/furniture.tsx`
- `src/app/floorplan-workbench/page.tsx`
- `src/lib/generator/furniture-document.mjs` (reine Hilfsfunktion: welche Geschosse zu speichern sind)
- `scripts/furniture-document.test.mjs`
- `born2thrill-app-repo/plans/ROADMAP.md`

## Explicitly out of scope

- `corrections/route.ts`, Bau-Sperre im Renderer, gespeicherte Möbelpositionen.
- Der Knopf "Geometrie neu erzeugen" und die Meldung für leere Häuser (getrennter Punkt, siehe Roadmap).
- Küchenplan KUECHE-EINRICHTEN-AN-ZEILE-001.

## API, schema, and data-contract effects

Keine. Vorhandene Aktion `save_furniture`, ein Aufruf je Geschoss.

## Behaviour change to accept

Ein Klick erneuert auch den Stempel von Geschossen, die Rainer nicht angesehen hat. Bisher zwang der Stempel zum Hinsehen: Stehen Möbel nach dem Umzeichnen falsch, hält der Bau dort nicht mehr an (das war der Fall twostorey_047, 21 Möbel im falschen Raum). Der Hinweis in der Meldung ersetzt diese Sperre für solche Geschosse. Koordinaten ändern sich dabei nicht.

## Acceptance criteria

- Änderung im Erdgeschoss, Wechsel ins Obergeschoss, Änderung dort, ein Klick: beide Dateien tragen beide Änderungen.
- Zwei veraltete Geschosse, nichts geändert, ein Klick: beide Stempel aktuell, Möbel-Koordinaten unverändert, Warnung auf /haus weg.
- Räume zwischendurch umgezeichnet: Speichern lehnt ab, wie bisher.
- Aktuelles Geschoss ohne Änderung wird nicht neu geschrieben.
- Leere Einrichtung überschreibt keine gefüllte (bestehende 409-Sperre).
- Prüfung im Editor an einem Testhaus oder nach Rainers Ja an xvv1.

## Tests and verification commands

Neue Tests in `scripts/furniture-document.test.mjs` für die Auswahl der Geschosse sowie ein Nahttest, dass `save` sie benutzt. Keine bestehenden Tests werden geändert.

```bash
node --test scripts/furniture-document.test.mjs scripts/moebel-vorschlag.test.mjs
```

## Protected and risky paths

`page.tsx` wird auch von anderen Sitzungen bearbeitet: vor dem Ändern Stand prüfen.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? **No.** Die Änderung schreibt nur Möbeldateien über die bestehende Route. Sie berührt keine Wände, Räume oder Öffnungen und keinen Upload.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

Keine.

## Rollback

Die `.before-ein-speichern`-Sicherungen zurückspielen.

## Unresolved questions

- Entschieden: Variante 1.
- Zusätzlich gebaut, weil nötig: Der Rückgängig-Verlauf gehört jetzt zum Geschoss. Vorher blieb er beim Wechsel stehen und Strg+Z konnte den Stand des anderen Geschosses zurückholen.

## Approval record

Rainer, 2026-10-30: "1" (Variante 1: ein Klick erneuert auch Stempel ungesehener Geschosse).

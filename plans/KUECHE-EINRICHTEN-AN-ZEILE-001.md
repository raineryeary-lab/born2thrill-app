# KUECHE-EINRICHTEN-AN-ZEILE-001: "Bereich einrichten" Küche nutzt die gezeichnete Küchenzeile und setzt die Insel

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-30: "bereich einrichten for kitchen isnt working i want to have kochfeld spüle hochschrank herd refridgerator and the kücheninsel please dont do the küchenzeile". Auf die Rückfrage gewählt: Option 1.

Rainer zeichnet die Küchenzeile selbst. Einrichten setzt darauf Spüle und Kochfeld, an ihr Ende Hochschrank Herd und Kühlschrank, und davor die Kücheninsel. Ohne gezeichnete Zeile setzt es nichts und meldet "Küchenzeile zuerst zeichnen".

## Current evidence and behavior

- `src/lib/generator/moebel-vorschlag.mjs:596` `kueche(ctx)` erzeugt immer selbst eine Küchenzeile (`ctx.gesetzt.push({symbol: "kuechenzeile", ...})`, Zeile 644).
- Die Kücheninsel kommt in `moebel-vorschlag.mjs` nicht vor.
- Gemessen am 4,0 x 3,5 m Testraum mit schon vorhandener Zeile an y=0: `richteBereichEin` legt eine zweite Zeile an die Gegenwand ([[4000,3200],[1200,3200]]).
- Ursache: `vorhandene` sind nackte Rechtecke (`page.tsx:1845`, `1783`), und `erzeugeKontext` gibt ihnen den Schlüssel "vorhanden" (`moebel-vorschlag.mjs:238`). Das Werkzeug weiss also nicht, dass dort eine Zeile steht.
- `DARF_UEBERLAPPEN` (Zeile 181) erlaubt Spüle/Kochfeld nur auf Rechtecken mit Schlüssel "kuechenzeile".
- Die Insel ist ein Rechteck aus zwei Gegenecken in `points_mm` (`plans/kuecheninsel-rechteck-v1.md`), Bauhöhe 900 (`build-simplifier-render-plan.py:137`).

## Repository baselines

- Repo `born2thrill-local-workbench`, Branch `agent/furnished-render-and-annotation-schema`, HEAD 5be1a4e.
- Vorher schon offen: `page.tsx` geändert (M), `moebel-vorschlag.mjs` und `moebel-vorschlag.test.mjs` ungetrackt. Diese Stände bleiben erhalten, Sicherungen `.before-kueche-zeile`.
- `C:\dev\Floorplan-tools` selbst ist kein Git-Repository.

## Exact scope

1. `vorhandene` dürfen optional `symbol` und `points_mm` tragen. `erzeugeKontext` übernimmt `symbol` als Schlüssel statt "vorhanden".
2. `page.tsx` gibt beide Felder an beiden Aufrufstellen mit (Bereich einrichten, Alle Räume einrichten).
3. `kueche(ctx)` wird neu geschrieben:
   - Sucht die Küchenzeile im Bereich (Mitte des längsten Abschnitts liegt im Polygon; bei mehreren die längste). Keine da: nichts setzen, `weggelassen` = "Küchenzeile zuerst zeichnen".
   - Erzeugt nie eine Küchenzeile.
   - Vorderseite der Zeile: zur Raumseite, weg von der nächsten Wand.
   - Spüle und Kochfeld auf den längsten geraden Abschnitt, wie bisher bei 30 % und 75 %.
   - Kühlschrank und Hochschrank Herd an ein freies Ende der Zeile, Kühlschrank ganz aussen, Fronten in dieselbe Richtung wie die Zeile. Passen nicht beide, kommt der Hochschrank allein, der Rest wird gemeldet.
   - Insel parallel zur Zeile, mittig davor, 1200 mm Gang. Grösse 1800 x 900, wenn nötig 1500 oder 1200 x 900. Zu echten Wänden auf der anderen Seite bleiben mindestens 800 mm. Passt nichts: "Kücheninsel (zu wenig Platz)".
   - Steht ein Teil schon im Bereich, wird es nicht doppelt gesetzt.
4. Tests wie unten.

## Files in scope

- `src/lib/generator/moebel-vorschlag.mjs`
- `src/app/floorplan-workbench/page.tsx`
- `scripts/moebel-vorschlag.test.mjs`
- `born2thrill-app-repo/plans/ROADMAP.md`

## Explicitly out of scope

- Gespeicherte Möbel, Häuser, Kameras, Builds.
- `build-simplifier-render-plan.py`, Renderer, Blender.
- Treppe als Hindernis bei "Bereich einrichten" (eigener offener Roadmap-Punkt).
- Aufteilen von "Wohnen / Essen / Kochen" (Roadmap, Möbel v2).

## API, schema, and data-contract effects

- `vorhandene[]` bekommt zwei optionale Felder. Keine Änderung an gespeicherten Dateien.
- Der Vorschlag bleibt ungespeichert, bis Rainer speichert. "Zurück" nimmt ihn zurück.

## Behaviour change to accept

"Alle Räume einrichten" nutzt dieselbe Regel:
- Küche ohne Zeile: nichts wird gesetzt, Meldung "Küchenzeile zuerst zeichnen". Bisher kam eine Zeile.
- Küche mit Zeile: bleibt wie bisher als "schon eingerichtet" ausgelassen. Dort "Bereich einrichten" benutzen.

## Acceptance criteria

- Mit gezeichneter Zeile: Ergebnis enthält spuele, kochfeld, hochschrank_herd, kuehlschrank, kuecheninsel und KEINE kuechenzeile.
- Ohne Zeile: `moebel` leer, Meldung "Küchenzeile zuerst zeichnen".
- Spüle und Kochfeld liegen auf der Zeile, hohe Geräte und Insel nicht.
- `rotation_deg` der hohen Geräte zeigt zur Raumseite, für alle vier Wandrichtungen.
- Insel-Gang 1200 mm, Insel achsparallel, `points_mm` aus zwei Gegenecken.
- Zweiter Klick setzt nichts doppelt.
- Prüfung im echten Editor, gegen den echten Stand: Vorschlag auf einem Haus mit Zeile ansehen, NICHT speichern.

## Tests and verification commands

Neu in `scripts/moebel-vorschlag.test.mjs`: je ein Test für die Kriterien oben, dazu L-förmige Zeile, Fenster am Zeilenende, zu kleiner Raum für die Insel.

Bestehende Tests, die geändert werden müssen (Rainer hat mit Option 1 das Verhalten geändert):
- Zeile 218 "Kueche: Zeile an der Wand, Hochschrank ...": prüft eine erzeugte Zeile. Wird auf eine vorgegebene Zeile umgestellt, die übrigen Prüfungen bleiben.
- Zeile 238 "Kueche: zu kurze Wand -> keine Zeile, Meldung": erwartet die Meldung "Küchenzeile". Wird zu "Küchenzeile zuerst zeichnen".
- Zeile 258 "Kueche: kurze Zeile hat trotzdem Spuele UND Kochfeld": bekommt eine vorgegebene 2-m-Zeile.

Keine anderen Tests werden geändert, übersprungen oder gelöscht.

```bash
node --test scripts/moebel-vorschlag.test.mjs scripts/buero-sofa.test.mjs
```

## Protected and risky paths

`page.tsx` wird auch von anderen Sitzungen bearbeitet: vor dem Ändern Stand prüfen.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference? **No.** Die Änderung erzeugt nur einen ungespeicherten Möbelvorschlag im Editor. Sie berührt keine Wände, Räume oder Öffnungen und keinen Upload.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

Keine.

## Rollback

Die drei `.before-kueche-zeile`-Sicherungen zurückspielen.

## Unresolved questions

- Inselmass 1800 x 900 und Gang 1200 mm sind meine Vorgabe.
- Kochfeld bleibt auf der Zeile, nicht auf der Insel.

## Änderungen gegenüber dem Plan bei der Umsetzung

- Maße aus 81 von Rainer gezeichneten Küchen statt Schätzung: Gang erst 1100 mm (Median), dann 900 und 800; Insel 2000 x 1000, dann 1600 x 1000, dann 1200 x 900; parallel zuerst, dann quer, auch mit Abstand von der Zeile. Gemessen an 40 Küchen, in denen Rainer selbst eine Insel gezeichnet hat: Die Regel findet in 32 Platz.
- Offen, braucht Rainers Ja: Der bestehende Test "alle Raumtypen aus der Auswahl haben eine Regel" (Zeile 329) verlangt Möbel in einer Küche ohne Zeile. Das widerspricht diesem Plan. Vorschlag: Der Test übergibt für `kueche` eine Zeile. Nicht geändert, weil der Plan nur drei Tests freigab; er bleibt rot.
- Kurven (91 von 141 Zeilen haben mehr als 2 Punkte): Spüle und Kochfeld auf den längsten Schenkel, nicht in die Ecke; L und U sperren nur ihre Schenkel, nicht das Hüllrechteck.
- Steht am Zeilenende eine Wand: hohe Geräte an eine freie Wand der Küche, sonst gemeldet.
- "Alle Räume einrichten": Eine Küche, in der nur die Zeile steht, gilt nicht mehr als "schon eingerichtet".

## Approval record

Rainer, 2026-10-30: "komm schon bauen nicht dann gleich wieder vergessen". Dazu: "küche bracuht kücheninsel kochfeld spüle hohschrank fridge".

## Korrektur 2026-10-30

Die Annahme "ohne Zeile setzt es nichts" war falsch. Rainer: "i want to have kochfeld spuele hochschrank herd refridgerator and the kuecheninsel please dont do the kuechenzeile". Die fuenf Teile kommen jetzt auch ohne gezeichnete Zeile. Der Bereich findet ausserdem die Zeile im selben Raum, und das Ergebnis steht sichtbar unter den Knoepfen.

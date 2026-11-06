# Alle Räume einrichten: Kombiräume

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-01: "do anything with kochen like wohnen essen koschen or essen kochen add all of our kichten stuff" und "the same with essen jsut add the table". Regel 30 in `REGELN.md`.

## Current evidence and behavior

- `raumtypAusName` gibt für Kombiräume `null` zurück, `richteAlleRaeumeEin` lässt sie aus (`moebel-vorschlag.mjs:976-980`).
- 188 Räume heißen "Wohnen / Essen / Kochen", dazu "Essen / Kochen" (3), "K�che / Essen" (2), "Wohnen / Essen / K�che" (1). Der Name "K�che" ist kaputt kodiert und muss mit erkannt werden.

## Exact scope

- Im Knopf "Alle Räume einrichten": Kochen oder Küche im Namen eines Kombiraums setzt die fünf Küchenteile, Essen im Namen setzt den Tisch. Wohnen wird dort nicht eingerichtet.
- Erst die Küche, dann der Tisch. Vorhandene Teile kommen nicht doppelt.
- `raumtypAusName` und "Bereich einrichten" bleiben wie sie sind.

## Files in scope

- `src/lib/generator/moebel-vorschlag.mjs`
- `scripts/moebel-vorschlag.test.mjs`
- `C:\dev\Floorplan-tools\REGELN.md`

## Explicitly out of scope

Bild-Generator, gespeicherte Häuser, Architektur, Upload.

## Tests

Neue Tests für Kombiräume. Zwei alte Tests hielten den aufgehobenen Beschluss "Kombiraum bleibt aus" fest und werden auf Rainers Wort angepasst, die Prüfung für Luftraum, Terrasse und Räume ohne Typ bleibt. `node --test scripts/moebel-vorschlag.test.mjs`. Danach Probelauf an einem echten Haus ohne Speichern.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Answer: no. Der Knopf macht nur Möbelvorschläge im Editor, gespeichert wird erst mit "Speichern". Kein Weg zu Veröffentlichung oder E-Mail.

## Rollback

`moebel-vorschlag.mjs.before-kombi-raeume` und `moebel-vorschlag.test.mjs.before-kombi-raeume` zurückkopieren, Regel 30 entfernen.

## Approval record

Rainers Anweisung vom 2026-11-01 im Chat.

## Umsetzung und Abweichungen

- Zusätzlich: Der Tisch hält 900 mm Gang zur Küche, geht das nicht, steht er dichter.
- Zusätzlich, nach Sichtprüfung: Hochschrank und Kühlschrank suchen bei einer Zeile von Wand zu Wand die nächste freie Wand statt der ruhigsten und stehen beisammen. Das gilt auch für reine Küchen.
- Geprüft: `node --test scripts/moebel-vorschlag.test.mjs`, 103 echte Kombiräume, Knopf im echten Editor an `bungalow_007` und `bungalow_040_43`, nichts gespeichert.

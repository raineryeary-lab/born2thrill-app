# Möbel: Bereich markieren, Raumtyp wählen, automatisch einrichten (Prototyp)

Status: IMPLEMENTED (Prototyp, 2026-10-09)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-09: "in the furniture section i click on a room or mark an
area and you automatically furnish this area, if something is wrong i can grab
it and move it or rotate … temporarily mark an area then per dropdown … select
the room type … we would leave the furniture to the right as is".

Prototyp: Im Möbel-Editor einen Bereich markieren, einen Raumtyp wählen, und
der Editor setzt einen **Vorschlag** aus normalen Palettenmöbeln. Danach
gelten die bestehenden Werkzeuge (verschieben, drehen, löschen, Zurück).
Erst drei Raumtypen, damit Rainer das Gefühl prüfen kann, bevor alle elf
gebaut werden.

## Current evidence and behavior

- `src/app/floorplan-workbench/furniture.tsx` `useFurniture()`: jede Änderung
  läuft über `mutate()` (Z. ~197) und ist **ein** Schritt in `verlauf` →
  `zurueck()` nimmt ihn zurück. Eine ganze Einrichtung in einem `mutate()`
  ist also mit einem Klick auf „Zurück“ weg.
- Gespeichert wird nur über `save()` (Knopf). Möbel liegen getrennt von der
  Korrektur und bewegen `geometry_hash` nicht (Kopfkommentar furniture.tsx).
- `PlacedSymbol` = `{ symbol, position_mm, rotation_deg, mirrored,
  footprint_mm }` — genau das, was ein Vorschlag erzeugen muss.
- `src/lib/generator/symbol-catalog.mjs`: Palette mit gemessenen Maßen und
  Wandverhalten (`wallBehaviour`: flush / gap / free). `snapStampToWalls()` in
  furniture.tsx stellt ein Stück schon korrekt an eine Raumkante.
- Grundriss im Editor: `floor.rooms[].polygon` (mm), `floor.walls[]`,
  `floor.openings[]` mit `opening_type` door/window/passage und `wall_id`.
  Türen und Fenster sind also bekannt.
- `src/lib/generator/furniture-placement.mjs` (Version 1, Aug.): andere
  Katalogschlüssel (`bed_double` statt `doppelbett`), ein Stück pro Kante,
  keine Tür-/Fensterprüfung. Wird **nicht** verwendet, nur als Idee.
- Lücke im Katalog: es gibt keinen Nachttisch. Der Prototyp nutzt dafür
  `stuff` (Allzweck-Kasten) oder lässt ihn weg — siehe offene Fragen.

## Repository baselines

- born2thrill-local-workbench, Branch `agent/furnished-render-and-annotation-schema`,
  HEAD `5be1a4e`. Arbeitsbaum schmutzig (286 Einträge, u. a. page.tsx und
  furniture.tsx mit Rainers nicht committeten Änderungen) — wird nicht
  angefasst außer an den unten genannten Stellen.

## Exact scope

1. **Werkzeug „Bereich einrichten“** im Möbel-Editor (Knopf über der
   Palette; Palette selbst unverändert).
   - Rechteck aufziehen **oder** in einen Raum klicken (nimmt dessen Polygon).
   - Bereich wird gestrichelt angezeigt, nur temporär, nie gespeichert.
   - Dropdown mit Raumtyp; vorbelegt aus dem Raumnamen, wenn geklickt
     (`bucketForRoomLabel`). Knopf „Einrichten“, Esc bricht ab.
2. **Reine Funktion `richteBereichEin(bereich, raumtyp, grundriss)`** in neuer
   Datei `src/lib/generator/moebel-vorschlag.mjs` → Liste `PlacedSymbol`.
   Kein React, kein DOM, damit testbar.
3. **Regeln für drei Raumtypen:**
   - **Schlafzimmer:** Doppelbett, Kopfteil an der längsten Wand ohne Tür und
     möglichst ohne Fenster, mittig; Kleiderschrank an eine andere freie Wand.
   - **Bad:** Wanne oder Dusche in eine Ecke (Wanne nur, wenn die Wand ≥ 1,7 m
     frei ist), Waschtisch und Wand-WC an freie Wandstücke.
   - **Wohnzimmer:** Sofa (3-Sitzer, Ecksofa wenn Platz) an eine lange freie
     Wand, Lowboard + Fernseher gegenüber, Couchtisch dazwischen.
   Gemeinsame Regeln: nichts vor einer Tür (Freiraum 900 mm vor dem
   Türblatt), nichts Hohes vor einem Fenster, nichts überlappt, alles bleibt im
   Bereich. Passt ein Stück nicht, wird es **weggelassen und im Statustext
   genannt**, nicht gequetscht.
4. **Einfügen** in **einem** `mutate()`-Aufruf → ein Zurück entfernt alles.
   Statustext: „N Möbel vorgeschlagen — anpassen oder Zurück. Nicht
   gespeichert.“

## Files in scope

- neu `src/lib/generator/moebel-vorschlag.mjs` (+ `.d.ts` wie die Nachbarn)
- neu `scripts/moebel-vorschlag.test.mjs`
- `src/app/floorplan-workbench/furniture.tsx` (Knopf, Dropdown, `placeMany`
  über `mutate`)
- `src/app/floorplan-workbench/page.tsx` (Bereich aufziehen / Raum anklicken
  im Möbel-Canvas)
- `package.json` (Testskript `test:moebel-vorschlag`)

## Explicitly out of scope

- Die übrigen 8 Raumtypen (Esszimmer, Küche, Diele, HWR, Kinderzimmer, Gast,
  Du/Bad, WC) — Folgeschritt nach Rainers Urteil über den Prototyp.
- Küchenzeile automatisch zeichnen (Pfad-Möbel).
- Neue Katalogeinträge (z. B. Nachttisch).
- Automatisches Einrichten ganzer Häuser ohne Klick, Batch über den Katalog.
- `furniture-placement.mjs` und der 3D-Render-Pfad bleiben unverändert.

## API, schema, and data-contract effects

Keine. Vorgeschlagene Möbel sind gewöhnliche `PlacedSymbol`-Einträge;
Speicherformat, API und Render-Plan bleiben gleich.

## Acceptance criteria

1. Raum anklicken oder Rechteck ziehen → Bereich sichtbar, Raumtyp wählbar.
2. „Einrichten“ setzt Möbel nur innerhalb des Bereichs, ohne Überlappung,
   nicht im Türfreiraum.
3. Jedes Stück lässt sich wie ein von Hand gesetztes verschieben/drehen/löschen.
4. **Ein** Klick auf „Zurück“ entfernt den ganzen Vorschlag.
5. Ohne „Speichern“ bleibt die gespeicherte Möbeldatei unverändert.
6. Zu kleiner Bereich → weniger Möbel + Hinweis, kein Absturz, kein Quetschen.

## Tests and verification commands

Neu `scripts/moebel-vorschlag.test.mjs` (zuerst geschrieben):
- Schlafzimmer 3,5 × 4 m, Tür an kurzer Wand → Bett an langer Wand, nicht im
  Türfreiraum.
- Bad 2 × 2,5 m → keine Wanne (Wand zu kurz), Dusche statt dessen.
- Wohnzimmer 5 × 4 m → Sofa und Lowboard an gegenüberliegenden Wänden.
- Kein Paar von Vorschlägen überlappt; alle Bounds im Bereich.
- 1 × 1 m Bereich → leere/kurze Liste + Liste der weggelassenen Stücke.

    node --test --test-isolation=none scripts/moebel-vorschlag.test.mjs
    node --test --test-isolation=none scripts/moebel-punkte.test.mjs
    node --test --test-isolation=none scripts/symbol-catalog.test.mjs   # falls vorhanden

Danach im Browser auf onehalfstorey_020: alle drei Raumtypen einrichten,
Screenshot, Zurück, neu laden → Datei unverändert. Keine bestehenden Tests
geändert.

## Protected and risky paths

- `mutate`/`verlauf` in furniture.tsx: nur benutzt, nicht verändert.
- Klickbehandlung im Möbel-Canvas (page.tsx `onPointerDown`) ist schon dicht
  belegt (Stempel, Lauf, Rechteck, Marquee). Neues Werkzeug nur aktiv, wenn
  es gewählt ist; sonst unveränderter Ablauf.

## Rights, provenance, privacy, and security impact

Keine. Keine neuen Daten, keine externen Dienste.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

No. Der Vorschlag erzeugt nur Möbel-Präsentationsdaten im ungespeicherten
Editorzustand; Wände, Räume, Öffnungen und `geometry_hash` werden nur gelesen.
Gespeichert wird ausschließlich durch Rainers Klick auf „Speichern“; Render,
Freigabe und Versand laufen über die unveränderten Pfade. Test 5 der
Abnahme prüft, dass ohne Speichern nichts geschrieben wird.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

—

## Rollback

Neue Dateien löschen; die Ergänzungen in furniture.tsx, page.tsx und
package.json entfernen (jeweils als zusammenhängender Block markiert mit
`MOEBEL-BEREICH-EINRICHTEN-001`).

## Unresolved questions

1. Nachttische: `stuff`-Kasten als Platzhalter neben dem Bett, oder weglassen
   bis es ein echtes Symbol gibt?
2. Bad: lieber Dusche oder Wanne bevorzugen, wenn beides passt?
3. Klick in einen Raum, der schon Möbel hat: zusätzlich einrichten oder
   vorher fragen?

## Approval record

Rainer, 2026-10-09: "ok" zum Plan; Antworten auf die offenen Fragen:
"1 nehmen 2 Dusche 3 fragen" — Nachttisch = Stuff-Kasten, Dusche vor Wanne,
bei vorhandenen Möbeln im Bereich vorher fragen.

## Umsetzung (2026-10-09)

- `src/lib/generator/moebel-vorschlag.mjs`: `richteBereichEin()`, Regeln für
  Schlafzimmer / Bad / Wohnzimmer, `raumtypAusName()`, `RAUMTYPEN`.
  Dusche → Dusche gross → Dusche 80x80 → erst dann Wanne.
- `furniture.tsx`: `placeMany()` (ein `mutate`), Bedienfeld
  `BereichEinrichten` mit Raumtyp-Auswahl, Einrichten, ↶ Zurück, Fertig.
- `page.tsx`: Klick = Raum unter dem Zeiger, Ziehen = Rechteck
  (Capture-Phase, damit ein Klick auf ein Möbel nicht dieses greift);
  gestrichelte Anzeige; Rückfrage bei vorhandenen Möbeln im Bereich.
- `package.json`: `test:moebel-vorschlag`.

## Verification (2026-10-09)

- `scripts/moebel-vorschlag.test.mjs` 12/12, `moebel-punkte.test.mjs` 38/38,
  `symbol-catalog.test.mjs` 12/12; `tsc --noEmit` ohne Fehler in den Dateien.
- Browser, onehalfstorey_020 OG (gespeicherte Möbel im Test leer simuliert,
  Speichern im Test blockiert, danach neu geladen):
  Eltern/Schlafen → Bett + 2 Nachttische + Kleiderschrank;
  Bad → Dusche in der Ecke, Waschtisch, WC;
  Kind als Wohnzimmer → Sofa, Lowboard + TV gegenüber, Couchtisch.
  Zweites Einrichten im selben Raum → Rückfrage „schon 4 Möbel“, Abbrechen
  ändert nichts; ↶ Zurück → 4 → 0. Rechteck aufziehen → 3 Möbel im Rechteck.

## Bekannte Grenzen

- Bad: alle drei Teile landen oft an derselben Wand (die „ruhigste“) — für
  große Bäder wirkt das gedrängt.
- Möbel stehen nur an achsparallelen Wänden, in 90°-Schritten.
- Nur die drei Raumtypen; die übrigen acht folgen nach Rainers Urteil.

## Nachtrag 2026-10-09: eigene Bereiche, Esszimmer, Küche

Rainer: "i have to be able to create my own areas … this bereich can be
wohnzimmer and esszimmer and kitchen, but i need to be able to tell you if it
is a dining or a living or a kitchen". Freigabe: "ja".

- Bereich zeichnen ist jetzt der Normalfall: Ecken klicken (rechtwinklig zur
  vorigen), Doppelklick oder Enter schließt ab; Rechteck aufziehen geht
  weiter. Shift+Klick nimmt den ganzen Raum (Abkürzung), Esc verwirft.
- Raumtypen: Wohnzimmer, Esszimmer, Küche, Schlafzimmer, Bad.
  - Esszimmer: Essgruppe 6 frei in der Mitte, lange Seite längs; passt sie
    nicht, Esstisch einzeln + so viele Stühle wie passen, Rest gemeldet.
  - Küche: längster freier Wandabschnitt (Türen sperren, Fenster nicht);
    ab 3 m Kühlschrank + Hochschrank am fensterfreien Ende, ab 1,8 m nur
    Hochschrank; Zeile max. 3,6 m als Lauf (Mittellinie 300 mm vor der
    Wand); Spüle bei 30 %, Kochfeld bei 75 %.
- Echte Wand vor offener Kante: Kanten eines gezeichneten Bereichs, die auf
  keiner Raumkante liegen, werden zuletzt gewählt (`raumKanten`).
- `raumtypAusName("Wohnen / Essen / Kochen")` liefert jetzt null statt
  "wohnzimmer" — **bestehender Test von heute bewusst geändert**, weil genau
  dieses Verhalten Rainers Einwand war.
- `rechteckVon()` zählt bei Läufen die Tiefe quer zur Laufrichtung mit
  (vorher Breite 0 → vorhandene Küchenzeilen wurden übersehen).

Verifikation: `moebel-vorschlag.test.mjs` 17/17 (5 neu), zusammen mit
`moebel-punkte` und `symbol-catalog` 67/67; `tsc` ohne Fehler in den Dateien.
Browser, onehalfstorey_020 EG, „Wohnen / Essen / Kochen“ (Möbel im Test leer
simuliert, Speichern blockiert, danach neu geladen): Wohnbereich als
Rechteck → Sofa, Couchtisch, Lowboard + TV; Essbereich als Rechteck →
Essgruppe mittig; Küchenbereich per vier Eckklicks + Doppelklick →
Kühlschrank, Hochschrank, Zeile, Spüle, Kochfeld an der Außenwand.

## Nachtrag 2026-10-09 (2): restliche Raumtypen, Spüle/Kochfeld, Badewanne

Rainer: "ok do the rest of the rooms the kitchen was missing the spüle the
kochstelle and the bathroom was missing the badewanne".

- **Spüle/Kochfeld:** wurden gesetzt, waren aber unsichtbar — beide PNGs grau
  auf grauer Küchenzeile. Jetzt eigene Zeichnung (`KuechenTeil` in
  furniture.tsx): Spüle blau mit Becken, Kochfeld schwarz mit vier orangen
  Ringen, beide beschriftet. Zusätzlich reserviert die Küche erst 1,8 m
  Platte für Spüle + Kochfeld, die hohen Geräte bekommen nur den Rest; bei
  kurzer Platte stehen Spüle und Kochfeld nebeneinander statt Kochfeld weg.
- **Bad:** Dusche UND Badewanne (vorher Dusche statt Wanne) — **bestehender
  Test geändert** auf Rainers ausdrücklichen Wunsch; neuer Typ **Du/Bad** nur
  Dusche.
- **Neue Typen:** Diele (Garderobe + Schrank 40 an der Wand), HWR
  (Waschmaschine + Trockner nebeneinander, Schrank 60), Kinderzimmer
  (Einzelbett in der Ecke, ein Nachttisch, Kinder-Schreibtisch an der
  Fensterwand, Kleiderschrank), Gast (= Schlafzimmer), WC (Wand-WC +
  Handwaschbecken). Auswahl in Rainers Reihenfolge.
- `raumtypAusName`: WC → wc, Flur/Diele → diele, Kind → kinderzimmer,
  Gast → gast, HWR/HTR → hwr, Dusch… → duschbad (**Test von heute geändert**:
  "WC" und "Flur" lieferten vorher null).
- Möbel ohne PNG (Lowboard, Sideboard, Garderobe, Esstisch, Esszimmerstuhl,
  Doppelwaschtisch) zeigen jetzt wenigstens ihren Namen im Rahmen.

Verifikation: `moebel-vorschlag.test.mjs` 26/26, mit `moebel-punkte` und
`symbol-catalog` 76/76; `tsc` ohne Fehler. Browser onehalfstorey_020
(gespeicherte Möbel leer simuliert, Speichern blockiert, danach neu geladen):
EG Küchenbereich → 5 Teile, Spüle + Kochfeld sichtbar; WC → 2, HWR → 3,
Diele → 2 (Typ jeweils aus dem Namen vorgewählt); OG Bad → Dusche, Wanne,
WC, Waschtisch; Eltern → 4; beide Kind → Bett in der Ecke, Nachttisch,
Schreibtisch am Fenster, Schrank.

## Nachtrag 2026-10-09 (3): Büro

Rainer: "büro fehlt". Neuer Typ **Büro**: Schreibtisch an der Fensterwand,
Schreibtischstuhl davor mit Blick zum Tisch (darf 150 mm unter die Platte),
Sideboard oder Schrank 40 an eine andere Wand. Name „Büro/Arbeit/Office“ →
buero (**Test von heute geändert**: „Büro“ lieferte vorher null).

Dabei gefunden und behoben: Türen/Fenster liegen in den Daten auf der
Wandmitte, die Raumkante auf der Innenseite — im Büro von onehalfstorey_020
liegt das Fenster 120 mm INNERHALB der Raumkante, die Fensterwand galt als
fensterlos und der Tisch landete an der Innenwand. Die Freiflächen vor
Öffnungen beginnen jetzt 300 mm hinter der Öffnung; Regressionstest mit den
echten Koordinaten.

Verifikation: 78/78 Tests (moebel-vorschlag 28, moebel-punkte 38,
symbol-catalog 12), tsc sauber; Browser onehalfstorey_020 EG Büro (Möbel
leer simuliert, Speichern blockiert, neu geladen): Tisch am Fenster, Stuhl
davor, Sideboard an der Innenwand.

## Nachtrag 2026-10-09 (4): Ecksofa im Wohnzimmer

Rainer: "please use the eckcouch for wohnzimmer". Wohnzimmer nimmt jetzt das
Ecksofa in eine Ecke (Lehne an der Wand, Liege zur Ecke, über `mirrored`);
passt es nicht (braucht 2,8 m Wand), wie bisher 3- oder 2-Sitzer. Couchtisch
und Lowboard zielen auf das Sitzteil neben der Liege; der Couchtisch darf in
den leeren Teil des Ecksofa-Rahmens.

Dabei gefunden: das Ecksofa-Symbol ist andersherum gezeichnet als alle
anderen — Vorderseite lokal -y. Rainer setzt es von Hand entsprechend
(onehalfstorey_020 EG: Oberwand, 180°, gespiegelt; Lowboard/Bett/Schreibtisch
dort mit der üblichen Drehung). Der Vorschlag dreht es deshalb um 180°, und
der Vorderseitenpfeil des Ecksofas ist im Editor gedreht (zeigte bisher auch
bei handgesetzten Ecksofas in die Wand). **Bestehender Test von heute
angepasst:** Wohnzimmer erwartet Ecksofa statt 3-Sitzer, und Ecksofa und
Lowboard haben gegenüber die GLEICHE Drehung.

Nicht geprüft: wie der 3D-Bau ein so gedrehtes Ecksofa stellt — es ist
dieselbe Drehung wie Rainers handgesetztes, daher erwartet gleich.

Verifikation: 80/80 Tests, tsc sauber; Browser EG Wohnbereich: Ecksofa in
der Ecke unten links, Lehne an der Wand, Liege an der Unterwand, Couchtisch
vor dem Sitzteil, Pfeil in den Raum.

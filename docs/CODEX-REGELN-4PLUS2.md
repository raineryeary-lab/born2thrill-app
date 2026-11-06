# Codex-Regelwerk — House Visual Catalog 4+2

Quelle: Rainers Handoff-Datei vom 2026-08-26
(`Desktop\____handoff for 4 + 2.txt`), zusammengefuehrt und entdoppelt am
2026-08-27.

Hausspezifisches steht NICHT hier, sondern im Auftrag: Objektnamen, Pfade,
Dateinamen, Bildzahl, Pixelmasze. Dieses Regelwerk gilt fuer alle Haeuser
gleich. Wer die Regeln aendern will, aendert diese Datei -- nicht den
Generator und nicht die CODEX-AUFTRAG.md eines einzelnen Hauses.

Aus der Vorlage entfernt, weil fuer EIN Haus geschrieben: die feste
Garderobe-Id, die Beschreibung eines bestimmten Betts, die L-Form der Kueche,
"the large wardrobe", die feste Dateinamenliste, die feste Stuhlzahl. Neu
hinzugekommen: Aufloesung, Oberflaechen tragen den Stil, Sanitaerobjekte
duerfen nicht verschwinden, Atmosphaere und Licht, das Geschoss darunter, die
Pflichtliste je Innenbild.

Hinweis: die Vorlage begann mitten in einer Aufzaehlung; der Anfang der
Stuff-Regeln fehlte in der Quelle und ist hier sinngemaesz ergaenzt.

---

# 1 — Was unantastbar ist

## 1.1 Architektur

- The newest `.blend` of THIS house is the sole authority for the building
  geometry.
- Preserve every wall, room boundary, floor area, opening, window, exterior
  glazed element, cut plane, stair opening and railing exactly.
- Never add, remove, relocate, resize or reinterpret architectural elements.
- Preserve the saved Dollhouse camera, framing, crop and viewing direction.
- Do not import a room arrangement from another house or reference image.

## 1.2 Tueren und Oeffnungen

- Every door and opening remains exactly as stored in the current house's
  `.blend`: door count, object identity, position, width, height, hinge side,
  swing direction, opening angle and number of leaves.
- A single-leaf door always remains a single-leaf door. Never create double
  doors, paired panels or an additional leaf.
- Never create, remove, widen, narrow, relocate, close or reinterpret any
  doorway, window, glazed opening or wall opening; never turn a doorway into an
  open passage or place a door where none exists.
- Never conceal or obstruct a doorway, its swing area or the circulation route
  through it.
- Die **Objektkarte** markiert jedes Tuerblatt BLAU. Blau heisst: bleibt
  stehen. Ein aufgeschlagenes Tuerblatt darf stilgerecht neu gestaltet, aber
  nicht weggelassen und nicht mit einem Moebelstueck ueberbaut werden. Am
  2026-08-27 verschwand `wall-12-door` in zwei Bildern hintereinander unter der
  Garderobe, weil beide 190 Pixel nebeneinander liegen.
- Tueren und Oeffnungen werden am INHALT geprueft, nicht am Pixel: gleiche
  Anzahl, gleiche Lage, gleiche Breite, gleiche Anschlagseite, gleiche
  Aufschlagrichtung, gleiche Zahl der Fluegel wie im Render. Ein Bildmodell
  darf eine Tuer neu zeichnen, solange all das stimmt. Der frueher hier
  geforderte pixelgenaue Vergleich ist gestrichen (2026-08-27): er hat das
  Verfahren verboten, das die guten Bilder erzeugt hat.
- Any output with altered door or opening geometry is automatically rejected
  and must never become canonical.

## 1.3 Sanitaer und Kuechentechnik

- Bathtub, shower tray and enclosure, WC, washbasin, kitchen sink and cooktop
  are part of the architecture, not decoration.
- They may be restyled with the selected style. They may never be omitted:
  appearance yes, removal no.

---

# 2 — Was ersetzt werden soll

## 2.1 Grundsatz

- Furniture in the `.blend` represents the required furniture TYPE, location,
  footprint, scale and orientation. It is symbolic.
- Replacement with a finished, realistic, style-appropriate variant is the
  norm, not the exception.
- **Garderobe and Stuff objects are ALWAYS replaced.** A box that is still a
  box in the delivered image is a rejected delivery.
- Replacement furniture performs the same function as its source symbol. Never
  replace an object with a different furniture category.

## 2.2 Die Platzierung bleibt gesperrt

- Every replacement stays within the source object's footprint or an explicitly
  defined replacement zone.
- Preserve the source object's centre, approximate dimensions, long-axis
  alignment and orientation.
- Do not rearrange the floorplan. Do not move furniture into doors, windows,
  circulation routes or neighbouring rooms.
- Do not add seating that changes circulation or room capacity.

## 2.3 Bett

- Realistic, style-appropriate bed with readable frame or upholstered surround,
  mattress, duvet, pillows and an optional restrained throw. Never an
  undifferentiated dark mass.
- Centre, rectangular footprint, dimensions, long-axis alignment and rotation
  come from the newest `.blend`. Never rotate the bed by 90 or 180 degrees, and
  never turn it during an unrelated material, kitchen or furniture edit.
- Headboard and foot end follow the bed object in THIS house's `.blend`. Never
  take the head end from a reference image of another house, and never infer it
  from an older generated image.
- Preserve clear access from the bedroom door and to any storage furniture in
  that room.

## 2.4 Essgruppe

- Keep exactly the dining furniture the `.blend` holds: one table and as many
  chairs as there are chair objects. Do not add or drop a seat.
- Table centre, footprint, size and orientation stay fixed.
- Chair centres, scale and user-corrected rotations are authoritative from the
  newest `.blend`. Every chair faces inward toward the table. Never rotate,
  duplicate, remove or relocate chairs, and never turn them during an unrelated
  edit.
- Style table and chairs as one coherent set that also coordinates with the
  kitchen and the living-room furniture. Never leave them as placeholder forms.

## 2.5 Kueche

- Preserve the kitchen run exactly as built in THIS house's `.blend` --
  straight, L-shaped or U-shaped, whichever it is -- together with island,
  worktop, cooktop, sink, faucet, appliance blocks and clearances.
- Replace or finish the symbolic cabinet forms at the same positions: believable
  individual doors and drawers, consistent panel gaps, toe-kicks, restrained
  handles or integrated pulls, a coherently finished island base.
- Cabinet finishes match the named style. Never leave carcasses as featureless
  blocks.
- Do not introduce additional runs, upper cabinets or appliances unless
  explicitly requested.

## 2.6 Fernseher und Medienmoebel

- A real slim television at the source position, footprint and orientation:
  thin bezel, subtle glass reflection, clear separation from the console.
- Screen off. No logo, no text, no displayed picture.
- Never a solid black rectangle.
- Style the media console to match the room.

## 2.7 Schraenke

- Replace symbolic wardrobe and closet boxes with realistic, finished storage:
  believable doors, panels, handles or integrated pulls.
- Exact source footprint, position, scale and orientation.
- Bedroom wardrobes remain bedroom wardrobes, hall storage remains hall
  storage. Never place a wardrobe in an entrance, doorway or circulation route.

## 2.8 Garderobe

- Die **Objektkarte** im Auftragsordner (`OBJEKTKARTE-*.png`) zeigt mit einem
  nummerierten Marker, wo die Garderobe liegt. Erst dort nachsehen, dann
  arbeiten. Im Rohrender nach der Form zu suchen ist kein zulaessiger Weg.
- **Die Tuerblatt-Falle.** Ein aufgeschlagenes Tuerblatt sieht im Rohrender aus
  wie ein Schrankbrett. Am 2026-08-27 stand die Garderobe deshalb in vier
  Bildern eines Hauses an drei verschiedenen Stellen: zweimal ersetzte sie die
  Haustuer, zweimal wurde eine zweite Garderobe an einer Dielenwand erfunden.
  Was auf der Karte keinen Marker traegt, ist keine Garderobe -- dort wird
  nichts ersetzt und nichts hinzugefuegt.
- Locate the garderobe object named in the Auftrag and replace only that object,
  entirely within its footprint.
- Build a real entrance arrangement for the available space: slim cabinet, coat
  rail or hooks, two or three visible coats, a compact bench or shoe shelf with
  shoes, a narrow umbrella stand.
- Do not place Garderobe elements elsewhere merely because they seem close to
  the entrance. Never block a door, a door swing or a route.

## 2.9 Stuff

- Auch fuer Stuff gilt die **Objektkarte**: jeder Stuff-Platzhalter hat dort
  einen Marker. Ein Stuff-Moebel entsteht nur an einem Marker, nie an einer
  Stelle, die im Bild leer aussieht.
- Locate each stuff object named in the Auftrag and replace it inside its own
  projected footprint.
- Room-appropriate content: HWR and utility take shelves, closed storage,
  baskets and laundry supplies; living and bedrooms take restrained low
  storage, books, plants, lamps, drawers or decor suited to the room.
- Every replacement matches the selected style.
- Do not drop decoration on empty floor area with nothing to belong to, and
  never use a replacement to block a door, a window or a route.

---

# 3 — Was jedes Innenbild erfuellen muss

Eine Liste zum Abhaken. Fehlt ein Punkt, ist das Bild nicht fertig -- nicht
"fast fertig".

**1. Das ganze Geschoss, nicht nur der Wohnbereich.**
Jeder Raum wird gestaltet: Schlafzimmer, Kinderzimmer, Bad, Gaeste-WC, HWR,
Diele, Abstellraum. Ein Raum, der als grauer Rohrender stehenbleibt, waehrend
nebenan gestylt wurde, ist ein abgelehntes Bild. Der Rohrender ist der
Ausgangspunkt fuer ALLE Raeume, nicht der Endzustand fuer die unwichtigen.

Je Raum mindestens: Bodenbelag mit erkennbarem Material, Moebel mit Textur,
eine Lichtquelle oder ein Lichtabfall, ein Ausstattungsstueck (Teppich, Bild,
Pflanze, Handtuecher, Waeschekorb, Buecher).

**2. Vier Entwuerfe, nicht vier Farbtoene.**
Zwischen den vier Bildern MUESSEN sich unterscheiden: Bodenbelag (Material,
nicht nur Farbe), Kuechenfronten (Material und Gliederung), Polstermoebel
(Farbe UND Stoff -- Leinen, Bouclé, Samt, Leder), Textilien (Teppich, Kissen,
Bettwaesche, Vorhaenge), die Akzentfarbe, die Bilder an den Waenden.

Pruefung: waeren alle vier Bilder schwarzweiss, muessten sie immer noch als
vier verschiedene Einrichtungen erkennbar sein. Wenn nicht, sind es Farbfilter.

**3. Alles hat eine Oberflaeche.**
Kein Moebelstueck bleibt eine glatte Farbflaeche. Polster zeigen Gewebe und
Naehte, Betten Falten in Decke und Kissen, Holz Maserung, Arbeitsplatten Stein,
Fliesen Fugen.

**4. Styling gehoert dazu.**
Ausstattung, die zu einem vorhandenen Objekt gehoert, wird erwartet: Teppich
unter der Sitzgruppe, gerahmtes Bild ueber dem Sideboard, Schale oder Vase auf
dem Esstisch, Maentel an der Garderobe, Handtuecher am Waschtisch, Buch und
Leuchte auf dem Nachttisch. Es soll ein bewohntes Haus sein.

**5. Was zusammensteht, ist ein Satz.**
Rainer, 2026-08-30, an einem frisch erzeugten Grundriss: Zweisitzer und
Dreisitzer derselben Sitzgruppe hatten verschiedene Bezugsstoffe.

Moebel, die als Gruppe im selben Raum stehen, tragen DASSELBE Material und
DIESELBE Farbe:

- Zweisitzer, Dreisitzer und Sessel einer Sitzgruppe
- die Stuehle eines Esstisches untereinander
- die Schrankfronten einer Kuechenzeile samt Insel
- die Nachttische links und rechts vom Bett

So werden Moebel gekauft, und so liest sich ein Raum. Zwei verschiedene Stoffe
in einer Gruppe sehen nicht nach Gestaltung aus, sondern nach zwei getrennten
Anschaffungen -- und der Blick bleibt daran haengen statt am Grundriss.

Absichtlich abweichen darf genau EIN Stueck je Raum, als gesetzter Akzent
(ein Sessel in der Akzentfarbe zu einem einfarbigen Sofa). Zwei Sofas
derselben Gruppe sind kein Akzent, sondern ein Fehler.

**6. Die vier Grundrisse zeigen DASSELBE Haus, gleich moebliert.**
Rainer, 2026-08-30, an german_catalog_review_bungalow_3_3_2_b_100_2: in drei
von vier Bildern standen Sitzgruppe und Essgruppe woanders als im Bauplan --
in zweien vertauscht, im dritten war die Essgruppe an die Kuecheninsel
gewandert.

Was sich zwischen den vier Bildern unterscheiden darf, ist der STIL: Material,
Farbe, Stoff, Holzton, Leuchten, Teppichmuster, Dekoration.

Was sich NICHT unterscheiden darf, ist die Anordnung. Jedes Objekt der
Objektkarte steht in ALLEN VIER Bildern an DERSELBEN Stelle -- dort, wo die
Objektkarte es zeigt. Ein Sofa bleibt ein Sofa und bleibt, wo es steht; es
wird nicht zum Esstisch, und es wandert nicht in eine andere Ecke.

Der Grund ist nicht Ordnungsliebe. Der Kunde sieht vier Bilder EINES Hauses
und soll seinen Grundriss wiedererkennen. Vier verschiedene Anordnungen sind
vier verschiedene Wohnungen.

Pruefung, bevor du lieferst: nimm die Objektkarte, nimm die px-Angabe eines
Moebelstuecks und sieh in JEDEM der vier Bilder an dieser Stelle nach. Steht
dort etwas anderes, ist das Bild falsch -- nicht der Plan.

**Ein glatter Quader ist ein Moebel, keine Wand.**
Rainer, 2026-08-31, an german_catalog_review_bungalow_3_3_4_b_100_2: im
Elternschlafzimmer fehlte der Kleiderschrank in ALLEN VIER Bildern, und das
Bett lag an seiner Stelle.

Auf die Frage, was er an der Stelle sieht, antwortete Codex selbst:

> "Ein glatter, merkmalloser Quader ist semantisch mehrdeutig: Der Bearbeiter
> kann ihn fuer Wand, Platzhalter oder unwichtiges Bauteil halten."

Das ist eine faire Antwort, und sie beschreibt den Rohrender richtig: unsere
Modelle sind dort oft merkmallos. Deshalb gilt ab jetzt:

- Was in der Objektkarte einen Marker traegt, IST ein Objekt -- egal wie es
  im Rohrender aussieht. Ein weisser Quader mit Marker ist ein Schrank, keine
  Wand.
- Im Zweifel entscheidet der **Tiefenpass** (`*-depth.png`), nicht die
  Plausibilitaet: ein Schrank steht rund 500 mm vor der Wand, eine Wand ist
  buendig. Im Farbbild sind beide ein weisser Quader, im Tiefenbild zwei
  verschiedene Grauwerte.
- Tiefenpass, Kantenpass und Objektkarte liegen seit dem 2026-08-31 in der
  Dateiliste des Auftrags. Sie lagen vorher schon im Ordner, wurden aber nie
  genannt -- der Tiefenpass kam im ganzen Auftrag null Mal vor.

Findest du zu einem Marker im Rohrender kein Objekt, ist das eine MELDUNG,
kein Freibrief. Schreib es hin, statt den Raum neu zu erfinden.

**Der Objektmaskenpass sagt WAS, der Tiefenpass sagt WIE WEIT.**
Rainer, 2026-09-07: Vorschlag, eine Objektmaske wie Cryptomatte bei VRay
mitzuliefern, damit die Zuordnung nicht geraten werden muss.

Seit dem 2026-09-07 liegt zusaetzlich `*-idmask.png` im Auftrag. Jede
Moebelkategorie hat darin EINE feste Flaechenfarbe -- zwei Stuehle vom
gleichen Typ sehen in der Maske gleich aus, egal wo im Raum sie stehen.
Wand, Rahmen und Boden sind einheitlich dunkelgrau, Hintergrund ist
schwarz.

- Die Farbe zu jeder Kategorie steht im Manifest (`*.manifest.json`) unter
  `idmask_legend`, z. B. `{"kuehlschrank": [0.95, 0.3, 0.1], ...}`. Das ist
  die Wahrheit -- schaetz die Kategorie nie aus dem RGB-Ton selbst.
- Zwei benachbarte Objekte gleicher Kategorie (zwei gleiche Stuehle nebeneinander)
  verschmelzen in der Maske zu einer Flaeche. Das ist kein Fehler -- nutz in
  dem Fall die Objektkarte, um die Einzelposition wiederzufinden.
- Wie beim Tiefenpass gilt: die Maske entscheidet im Zweifel, nicht die
  Plausibilitaet des Farbbilds.

**Ersetzen ja. Verschieben nein.**
Rainer, 2026-08-30, nach einem Tag mit vier Runden fuer ein einziges Haus:
"versuchen wir es beim naechsten mal, sachen als Platzhalter weiterhin
ansehen, aber nicht neu positionieren."

Das ist die ganze Regel, und sie gilt fuer BEIDE Markerfarben:

- ROT heisst: hier steht ein Platzhalter, mach ein richtiges Moebel daraus.
  An DERSELBEN Stelle. Ein Kasten wird zu einer Garderobe, nicht zu einer
  Garderobe zwei Meter weiter.
- BLAU heisst: das Objekt bleibt. Material, Farbe, Stoff, Holzton und
  Beleuchtung sind deine Entscheidung. Der Platz ist es nicht.

Du darfst also jedes Stueck neu aussehen lassen. Du darfst keines
umstellen -- auch dann nicht, wenn dir eine andere Anordnung besser gefaellt.
Der Grundriss ist vermessen; was darin steht, steht dort aus einem Grund.

**7. Ein Marker gilt nur, was du wirklich gesehen hast.**
Im selben Fall meldete die catalog.json in allen vier Bildern 34 von 34
Markern als sichtbar, mit identischen bei-Koordinaten -- abgeschrieben aus dem
Bauplan. Drei der vier Bilder waren falsch.

`status: "sichtbar"` heisst: DU hast an dieser Stelle im GELIEFERTEN Bild das
benannte Objekt gesehen. Die Koordinaten aus dem Auftrag zu uebernehmen und
alles abzuhaken ist keine Pruefung, sondern eine falsche Auskunft -- und sie
wiegt schwerer als der Fehler selbst, weil sie ihn verdeckt.

Bist du unsicher, schreibe `unklar`. Steht das Objekt woanders, schreibe
`verschoben` und die Stelle, an der es wirklich steht. Beides ist in Ordnung.
Falsch abhaken ist es nicht.

---

# 4 — Atmosphaere und Licht

Flache Ergebnisse scheitern immer am selben: gleichmaessig ausgeleuchtet, Ton
in Ton, ohne einen einzigen eingeschalteten Leuchtkoerper.

**Licht.** Die Leuchten im Raum sind AN und sichtbar: Pendelleuchte ueber dem
Esstisch, Wandleuchte ueber der Sitzgruppe, Tisch- oder Stehleuchte neben dem
Sofa, Lichtband unter den Oberschraenken, Bilderleuchte, kleines Licht in der
Diele. Jede wirft einen warmen Lichtkegel, der auf Boden oder Wand sichtbar
ist. Das Licht faellt zu den Ecken hin ab.

**Schatten.** Jedes Moebelstueck hat einen Kontaktschatten. Ohne ihn schwebt
alles.

**Kontrast.** Boden, Wand und Arbeitsplatte liegen nicht Ton in Ton. Dunkler
Holzboden gegen hellen Putz, Terrazzo in den Nassraeumen, Stein auf der
Arbeitsplatte.

**Eine Akzentfarbe je Stil**, zwei- bis dreimal wiederholt. Nicht mehr als eine.

Was NICHT gemeint ist: Nebel, Lichtstrahlen, Farbfilter, dramatische
Vignettierung. Der graue Studiohintergrund wird in Helligkeit und Farbton
an die anderen Bilder desselben Satzes angeglichen; weder dunkel noch
grellweiss. Die Kamera bleibt unveraendert.

**Nicht uebersaettigt.** Farben bleiben natuerlich und gedeckt, wie ein gutes
Architekturfoto: keine knalligen, leuchtenden oder "aufgedrehten" Farben, kein
HDR-Look, kein Orangestich, kein giftiges Gruen. Lieber etwas zu ruhig als zu
bunt. Das gilt fuer JEDES Bild, innen wie aussen. Im Einzelnen: kein
Orangestich ueber Fassade oder Holz; kein knallgruener Rasen, kein
uebertriebener Sonnenuntergang; Putz bleibt warmweiss bzw. elfenbein; die
Aussenleuchten sind sanft warm, ohne die ganze Szene gelb zu faerben;
Materialstruktur und lesbare Belichtung bleiben erhalten.

---

# 5 — Die vier Stile

Vier echte Entwuerfe. Ein Farbfilter oder eine Belichtungsaenderung ist kein
Stil. Jeder Stil ist durchgaengig ueber Kueche, Essgruppe, Wohnmoebel, Bett,
Schraenke, Garderobe und Stuff.

1. **Warm Modern** — Nussbaum oder warme Eiche, sand- und karamellfarbene
   Textilien, Ton- und Keramikakzente, warm geaderter Stein, zeitgenoessische
   Detaillierung.
2. **Dark Modern** — Graphit, geraeuchertes Holz, tiefes Taupe und dunkler
   Stein mit warmen Lichtern; lesbar und wertig, niemals matschig oder
   unterbelichtet. EIN warmer Akzent, z.B. Cognac-Leder, an zwei bis drei
   Stellen. Alle Wandflaechen bleiben hell: Innenwaende, Aussenwaende
   und Schnittflaechen; auch Wandfliesen hell. Dunkle Farben gelten fuer
   Moebel und andere Einrichtungsoberflaechen, nicht fuer Waende. Die
   Haustuer bleibt in jeder Stilversion anthrazit. Rainers Beschluss
   vom 2026-10-30, REGELN.md Nr. 25.
3. **Soft Scandinavian** — helle Natureiche, Warmweiss, Haferton-Textilien,
   gedecktes Salbeigruen, heller Stein oder Terrazzo, Naturfasern, weiches
   diffuses Tageslicht.
4. **Classic** — das traditionelle Gegenstueck zu den drei modernen Saetzen:
   Massivholz in Eiche oder Kirsche, gerahmte und kassettierte Schrankfronten
   (keine glatten Platten), gepolsterte Sitzmoebel in Leinen oder Samt,
   gepolsterte Esszimmerstuehle mit Holzbeinen, Messing- oder Bronzegriffe,
   gemusterter Teppich, gerahmte Bilder. Warm und
   gesetzt, kein Landhauskitsch -- und kein moderner Raum mit alten Moebeln
   darin. Ohne diese Merkmale ist es kein Classic, sondern Warm Modern in warm.

---

# 6 — Das Geschoss darunter

Bei jedem Obergeschoss-Bild steht das Geschoss darunter als Sockel mit im
Modell: Aussenwaende in voller Hoehe, ungeschnitten, MIT allen Fenstern und
Tueren, ohne Moebel (Objekte `sockel-wall-*`).

- Der Sockel bleibt im Bild. Ohne ihn schwebt das Obergeschoss.
- Seine Fenster- und Tueroeffnungen bleiben offen. Nicht zumauern, nicht
  glaetten, nicht uebermalen.
- Der Sockel wird NICHT moebliert und NICHT geschnitten. Er ist Kulisse.
- Ragt er unten aus dem Bild, ist das in Ordnung. Die Kamera bleibt auf dem
  gerenderten Geschoss.

---

# 7 — Aussenaufnahmen

## 7.1 Harte Regeln

- Je ein Bild pro Dachform (4). 1,5-Geschosser: 2 Satteldach-Bilder, klassisch
  und modern.
- Vollformat, 24-35 mm, Stativhoehe, ISO 100, f/8-f/11.
- Kamera waagerecht, senkrechte Gebaeudekanten senkrecht.
- Drei-Viertel-Ansicht der besten Fassade, ganzes Gebaeude im Bild.
- Architektur exakt erhalten. `exterior` bleibt im Dateinamen.

## 7.2 Beispiel

Referenzbild:
https://born2thrill.de/wp-content/uploads/2026/08/onehalfstorey_020-07-exterior-modern.png

Es bestimmt Licht, Tageszeit, Umgebung und Stimmung -- niemals die Architektur
des aktuellen Hauses, und nicht das Bildformat.

**Tageszeit.** Blaue Stunde kurz nach Sonnenuntergang: oben tiefes Blau, zum
Horizont warm aufgehellt, lockere Wolkenbaender in Pfirsich und Grau. Kein
Mittagslicht, kein schwarzer Nachthimmel.

**Kuenstliches Licht als Hauptdarsteller.** Warme Wandleuchten in
regelmaessigem Abstand, jede mit sichtbarem Lichtkegel nach oben und unten.
Alle Wandleuchten sind gleich und haengen auf einheitlicher Hoehe, bezogen auf
die vorhandene Fenster-/Tuersturzhoehe. Zusaetzliche Leuchten nur dort, wo
Rainer sie markiert hat; vorhandene Leuchten bleiben, solange nichts anderes
gesagt ist. Die Lichtkegel nach oben und unten sind glaubwuerdig und
zurueckhaltend warm.
Fenster von innen warm erleuchtet, aber nicht ausgebrannt -- die Putzstruktur
bleibt sichtbar. Deckenspots im Carport, Pollerleuchten laengs der Wege,
Bodenstrahler, die einzelne Baeume anleuchten.

**Materialien.** Weisser Putz mit sichtbarer Koernung, anthrazitfarbene
Fensterrahmen, dunkle Haustueren mit schlanken senkrechten Griffen, schmales
dunkles Attikaband.

**Aussenanlagen.** Gemaehter Rasen im Vordergrund, Beete mit Graesern und
niedrigen Straeuchern, grossformatige hellgraue Betonplatten, dunkle
Kiesstreifen.

**Gartenmoebel.** Terrassen werden im Verhaeltnis zu ihrer Groesse
moebliert. Eine grosse Terrasse wirkt bewusst eingerichtet und benutzbar --
nicht spaerlich mit einem kleinen Sofa. Je nach Platz und Rainers Vorgabe:
Essplatz (Tisch mit Stuehlen), Sitzgruppe (Sofa, Sessel, Couchtisch) und/oder
Liegebereich (Liegen, Beistelltisch, Sonnenschirm) -- nicht jede Terrasse
braucht alle drei. Hochwertige, aufeinander abgestimmte Aussenmoebel,
Material und Farbe passend zum Stil (Modern: dunkles Alu, Teak, Anthrazit;
Classic: Holz, Naturtoene), zurueckhaltende Accessoires; nichts Buntes, kein
Plastik. Moebel stehen NUR auf den vorhandenen befestigten Flaechen.
Terrassenmasse, Gebaeude, Fenster, Tueren und Zugaenge bleiben; die Pflasterung
wird fuer Moebel nicht vergroessert, nichts steht vor Fenstern oder Tueren.

**Passende Details.** Die Szene wirkt bewohnt durch kleine, stimmige Details:
Kissen und eine Decke auf den Gartenmoebeln, ein Windlicht oder eine Laterne,
Kerzen, eine Schale oder Karaffe auf dem Tisch, Kraeuter- oder Blumentoepfe,
ein Fussabtreter und eine Pflanze an der Haustuer. Alles im Farbton des Stils,
dezent und sparsam -- Akzente, kein Kram. Nichts davon verdeckt Fenster,
Tueren oder Fassade.

**Requisiten.** Hoechstens ein dunkles Fahrzeug unter dem Carport, dazu die
Gartenmoebel und Details oben. Keine Menschen, keine Tiere, keine Schrift, keine Marken.

**Stimmung.** Ruhig, wohlhabend, bewohnt. Kein Nebel, kein Regen, keine Filter.

Bei `classic` gilt dasselbe Licht- und Umgebungsbild, nur mit dem Dach und den
Materialien, die das aktuelle Haus vorgibt.

---

# 8 — Wie gearbeitet wird

Dieser Abschnitt beschreibt das Verfahren, das die bisher besten Bilder erzeugt
hat: `onehalfstorey_020`, 2026-07-23, Bildmodell `gpt-image`, Ganzbild, ohne
Maske. Er ersetzt die frueheren Maskenregeln vollstaendig.

- Grundbild ist der Blender-Render DIESES Hauses und DIESES Geschosses. Ohne
  Grundbild wird nichts erzeugt.
- Das Grundbild geht an ein Bildmodell und wird in EINEM Durchgang als Ganzbild
  bearbeitet. Ganzbild-Bearbeitung ist ausdruecklich erlaubt und ist der
  Normalweg fuer Innenbilder.
- Masken sind nicht noetig und werden nicht verlangt. Dass ein Werkzeug keinen
  Maskenparameter hat, ist kein Hindernis und kein Grund auszuweichen.
- Die Szene in Blender umzubauen und deterministisch neu zu rendern ist KEIN
  gleichwertiger Weg. Blender liefert die Geometrie, nicht die Gestaltung:
  Stoffe, Bettzeug, Teppiche, Kuechenfronten, Deko und Lichtstimmung entstehen
  im Bildmodell. Ein reiner Blender-Neurender scheitert an Abschnitt 11
  ("Ausfuehrung") und ist keine Lieferung.
- Nachbessern heiszt: eine zweite Ganzbild-Bearbeitung AUF DEM BEANSTANDETEN
  BILD SELBST, deren Prompt genau eine Sache benennt und "no other changes"
  verlangt. So wurde 05 EG Dark Modern korrigiert. Nicht auf Blender
  zurueckfallen.

## 8.2 Was bei einer Nachbesserung NIE passiert

Eine Ganzbild-Bearbeitung wuerfelt jedes Mal das ganze Geschoss neu. Wer ein
fertiges Bild noch einmal aus dem Render erzeugt, riskiert jedes Zimmer darin,
das schon richtig war. Am 2026-08-27 kostete das drei Runden: jede Korrektur
reparierte eine Stelle und zerstoerte eine andere -- erst die Garderobe, dann
das Tuerblatt, dann die Badewanne, dann der Schreibtisch.

- **Ein angenommenes Bild wird NIE neu erzeugt.** Es wird ausschliesslich auf
  sich selbst nachgebessert, oder es bleibt unangetastet.
- Eine Nachbesserung betrifft **genau die Dateien, die der Auftrag nennt**.
  Jede andere Datei im Lieferordner wird nicht angefasst -- auch nicht "zur
  Einheitlichkeit", auch nicht, wenn sie besser werden koennte.
- Wird eine Datei im Lieferordner ersetzt, kommt die alte Fassung vorher unter
  einen eigenen Namen (`-vorher-<uhrzeit>`). Eine angenommene Lieferung darf
  nicht spurlos ueberschrieben werden.
- Neu erzeugen statt nachbessern ist nur erlaubt, wenn der Auftrag es
  ausdruecklich verlangt.
- Die Architektur wird ueber den Prompt gehalten, nicht ueber Pixel: jeder
  Prompt beginnt mit einer ARCHITECTURE-LOCK-Zeile, siehe 8.1.
- Geprueft wird am INHALT: gleiche Kamera, gleicher Ausschnitt, gleicher
  Grundriss, gleiche Anzahl und Lage von Tueren und Fenstern, gleiche Treppe.
  Bild und Render nebeneinanderlegen und zaehlen. Ein Pixelvergleich
  geschuetzter Bereiche ist nicht mehr das Kriterium und darf keine Lieferung
  mehr blockieren.
- Globale Licht- und Farbpolitur bleibt erlaubt und erzeugt keine neuen
  Bildinhalte.

## 8.1 Aufbau des Prompts

Jeder Innenbild-Prompt hat dieselben fuenf Teile, in dieser Reihenfolge. Die
Vorlage ist der tatsaechlich benutzte Wortlaut der 020-Bilder.

1. Zweck: "Use case: style-transfer plus professional furniture redesign."
2. Ziel: welches Bild bearbeitet wird -- Geschoss, Haus, Renderstand.
3. ARCHITECTURE LOCK: Kamera, Ausschnitt, Waende, Raumgrenzen, Treppe,
   Gelaender, Tueren, Fenster, Oeffnungen, Kuechen-Arbeitszonen und Wege
   bleiben. Wortlaut: "Do not change the floorplan."
4. Stil in Materialien statt in Adjektiven: Holzart, Steinart, Metall,
   Polsterfarbfamilie, Wandton, Lichtstimmung. Danach Raum fuer Raum, was
   entstehen soll -- mit Stueckzahl, wo eine Zahl gilt ("EXACTLY SIX chairs,
   two per long side and one at each end").
5. Freistellung und Verbote in einem Satz: weiszer oder hell-neutraler
   Studiogrund, weiche Kontaktschatten, keine Landschaft, kein Himmel, keine
   Menschen, keine Schrift. Danach eine "Avoid"-Zeile mit den bekannten
   Fehlern: fehlende Stuehle, ueberdimensionierte Moebel, schwebende Objekte,
   versperrte Oeffnungen, unpassende Kuechenfronten, veraenderte Architektur.

Ein getrennter Negativ-Prompt ist nicht noetig; die Verbote stehen im Prompt.
Stufe oder Denoise werden nicht gesetzt.

---

# 9 — Format und Dateien

- Jedes Bild hat am Ende genau die Pixelmasze, die der Auftrag je Datei nennt.
  Nicht beschneiden, kein Letterboxing, gleiches Seitenverhaeltnis.
- Das Bildmodell gibt ein kleineres Bild aus, als der Auftrag verlangt (z.B.
  1448 x 1086 statt 2000 x 1500). Das ist in Ordnung: hochskalieren auf die
  geforderten Masze. Nicht strecken, nicht beschneiden, keine Raender anlegen.
- **Toleranz beim Seitenverhaeltnis: 0,5 %.** Ein Bildmodell liefert ganze
  Pixel, ein exakt gleiches Verhaeltnis ist damit oft gar nicht erreichbar.
  1672 x 941 ist 1,77683, gefordert sind 1,77778 -- 0,053 % Abweichung, also
  dasselbe Bild in 16:9. Solche Ausgaben werden hochskaliert und nicht
  beanstandet. Erst darueber ist es ein Fehler, und der wird nicht durch
  Beschneiden geheilt.
  (Ergaenzt 2026-08-27: die frueher hier geforderte exakte Gleichheit hat eine
  fertige Lieferung blockiert, die in Wahrheit korrekt war.)
- PNG fuer die endgueltigen Dateien.
- Genau die Dateinamen aus dem Abschnitt "Rueckgabe" des Auftrags -- vier
  Innenstile je Geschoss plus vier Aussenansichten, also 8 Dateien beim
  Bungalow und 12 bei zwei Geschossen; 1,5-Geschosser: 2 Aussenansichten, 10
  Dateien. Dazu `catalog.json`. Nicht mehr und nicht
  weniger. Mehrgeschossige Haeuser tragen das Geschoss im Namen (`-eg` / `-og`).

---

# 10 — Qualitaetsbeispiele aus angenommenen Lieferungen

Diese Bilder zeigen NUR die gewuenschte Ausfuehrungsqualitaet -- Materialien,
Detaillierung, Licht, Ausstattung. Sie sagen nichts ueber Grundriss,
Raumaufteilung, Moebelpositionen oder Tueren des aktuellen Hauses. Wer daraus
einen Raum uebernimmt, liefert ein abgelehntes Bild.

Was sie NICHT sind: kein Korpus-Reference. Nicht quality-passed, nicht
training-ready, nicht annotiert, kein Rechtenachweis, keine Vorlage fuer
Grundriss oder Moeblierung.
(Umbenannt 2026-08-28: der Abschnitt hiess "Referenzbilder". "Reference" ist
in dieser Suite ein Korpus-Grundriss mit Rechtestatus -- das Wort auf
Marketing-Ausgabe zu uebertragen vermischt genau das, was `rechte.py`
trennt.)

Alle vier stammen aus der am 2026-08-28 angenommenen Lieferung fuer
`onehalfstorey_020`:

- **Warm Modern**
  https://born2thrill.de/wp-content/uploads/2026/08/onehalfstorey_020-03-floorplan-warm-modern-eg.png
- **Dark Modern**
  https://born2thrill.de/wp-content/uploads/2026/08/onehalfstorey_020-04-floorplan-dark-modern-eg.png
- **Soft Scandinavian**
  https://born2thrill.de/wp-content/uploads/2026/08/onehalfstorey_020-05-floorplan-soft-scandinavian-eg.png
- **Classic**
  https://born2thrill.de/wp-content/uploads/2026/08/onehalfstorey_020-06-floorplan-classic-eg.png

Sie entstanden nach dem Verfahren aus Abschnitt 8: Blender-Render als
Grundbild, ein Ganzbild-Durchgang im Bildmodell, keine Maske. Wer diese
Qualitaet erreichen will, arbeitet so und nicht anders.

Ausdruecklich KEIN Massstab sind die Lieferungen aus `bungalow_039` vom
2026-08-26/27: gleichmaessig ausgeleuchtet, Ton in Ton, keine eingeschaltete
Leuchte, kaum Ausstattung. Sie wurden abgelehnt.

---

# 11 — Pruefliste vor der Annahme

Das Bild wird abgelehnt, wenn einer dieser Punkte zutrifft:

**Farbe**
- Das Bild ist uebersaettigt: knallige oder leuchtende Farben, HDR-Look,
  Orangestich oder giftiges Gruen.

**Geometrie**
- Eine Wand, Oeffnung, Tuer oder ein Fenster liegt woanders, hat eine andere
  Groesze, ist dazugekommen oder verschwunden -- verglichen mit dem Render,
  am Inhalt gezaehlt und nicht am Pixel gemessen.
- Ein Obergeschoss-Bild hat das Geschoss darunter verloren, oder dessen Fenster
  und Tueren wurden zugemauert, sodass das Geschoss schwebt.
- Der Boden ist angeschnitten, die Kamera hat sich geaendert, oder das Ergebnis
  ist eine Bildtafel statt eines Bildes.

**Vollstaendigkeit**
- Ein im `.blend` vorhandenes Sanitaer- oder Kuechenobjekt fehlt im Bild. Ein
  Bad ohne Wanne UND Dusche ist eine abgelehnte Lieferung.
  (Ergaenzt 2026-08-26: fuenf Lieferungen in Folge zeigten ein Bad ohne beides,
  obwohl beide in der Quelle stehen.)
- Ein Garderoben- oder Stuff-Platzhalter ist noch als Kasten zu sehen.
- Ein Moebelstueck steht in einem der vier Grundrisse woanders als in den
  anderen dreien oder als in der Objektkarte. Die vier Bilder unterscheiden
  sich im Stil, nicht in der Anordnung (Regel 10.6).
  (Ergaenzt 2026-08-30: german_catalog_review_bungalow_3_3_2_b_100_2, drei von
  vier Bildern mit vertauschter oder verschobener Sitz- und Essgruppe.)
- Ein Marker steht in der catalog.json auf `sichtbar`, obwohl an der genannten
  Stelle etwas anderes zu sehen ist. Falsch abgehakt wiegt schwerer als der
  Fehler selbst, weil es ihn verdeckt (Regel 10.7).
- Ein Raum blieb im Rohrender-Zustand, waehrend ein anderer Raum desselben
  Bildes gestylt wurde. Schlafzimmer, Bad, HWR, Diele und Abstellraum zaehlen
  als Raeume.

**Platzierung**
- Die Garderobe steht nicht auf ihrem Marker aus der Objektkarte, oder sie
  versperrt eine Tuer oder einen Weg.
- Eine Garderobe, ein Stuff-Moebel oder ein anderes Moebelstueck steht an einer
  Stelle, die auf der Objektkarte keinen Marker hat. Erfundene Moebel sind
  keine Ausstattung.
- Ein Tuerblatt aus dem Render ist im Bild verschwunden, weil an seiner Stelle
  ein Moebelstueck steht.
- Bett- oder Stuhlausrichtung weicht vom `.blend` ab.
- Die Zahl der Esszimmerstuehle weicht vom `.blend` ab, oder einer schaut nicht
  zum Tisch.
- Deko wurde auf leerer Bodenflaeche abgelegt, ohne zu einem Objekt zu gehoeren.
  (Ausstattung an einem vorhandenen Objekt ist Pflicht, kein Fehler.)

**Ausfuehrung**
- Die vier Bilder waeren in Schwarzweiss dasselbe Zimmer -- also Farbfilter
  statt Entwuerfe.
- Classic fehlen seine Pflichtmerkmale: kassettierte Fronten, gemusterter
  Teppich, gerahmte Bilder, Messing- oder Bronzegriffe, gepolsterte Stuehle.
- Kuechenkorpusse sind flaechige Bloecke ohne Tueren und Schubladen.
- Das Bild ist ein reiner Blender-Neurender: kein Bildmodell-Durchgang, daher
  graue oder einfarbige Moebel ohne Stoff, Muster und Materialstruktur.
- Der Fernseher ist eine schwarze Platte.
- Das Bett ist eine unlesbare dunkle Masse.
- Polster, Bettzeug, Holz oder Stein erscheinen als glatte Farbflaeche ohne
  Materialstruktur.
- Moebel, die als Gruppe zusammenstehen, tragen verschiedene Materialien:
  Zweisitzer und Dreisitzer derselben Sitzgruppe in verschiedenen Stoffen,
  Esszimmerstuehle untereinander verschieden, Kuecheninsel anders als die
  Zeile, Nachttische links und rechts ungleich. Ein gesetzter Akzent ist
  erlaubt -- genau EIN Stueck je Raum. Zwei Sofas derselben Gruppe sind kein
  Akzent (siehe Abschnitt 10, Punkt 5).
- Das Bild ist flach: keine eingeschaltete Leuchte, kein sichtbarer Lichtkegel,
  keine Kontaktschatten, Boden und Wand Ton in Ton, keine Bilder, kein Teppich,
  keine Pflanzen. **Ein korrektes, aber lebloses Bild ist kein angenommenes
  Bild.**

## 11.1 Selbstpruefung -- Pflicht, nicht Kuer

Die Liste oben zu kennen genuegt nicht. Vor der Abgabe geht Codex die
Markerliste der Objektkarte durch und haelt je Marker fest, was im Bild zu
sehen ist. Das Ergebnis wird MITGELIEFERT, in `catalog.json` je Bild:

    "marker_check": [
      {"n": 1,  "name": "badewanne-15",  "status": "sichtbar"},
      {"n": 3,  "name": "garderobe-25",  "status": "ersetzt"},
      {"n": 14, "name": "wall-12-door",  "status": "sichtbar"},
      ...
    ]

**Zu jedem blauen Marker gehoert `bei`: der Pixel, an dem du das Objekt IM
GELIEFERTEN BILD siehst.**

    "marker_check": [
      {"n": 4,  "name": "eckbadewanne-16", "status": "sichtbar", "bei": [812, 640]},
      {"n": 36, "name": "trockner-13",     "status": "sichtbar", "bei": [1018, 934]},
      {"n": 2,  "name": "garderobe-17",    "status": "ersetzt"}
    ]

Rote Marker brauchen kein `bei` -- dort ist das Ausgangsobjekt gerade weg.

Der Grund steht in drei Zeilen Geschichte: am 2026-08-27 war eine Badewanne
als "sichtbar" gemeldet und fehlte, am 2026-08-28 ein Schreibtisch in drei von
vier Bildern, am 2026-08-29 Waschmaschine und Trockner in zwei von vieren.
Jedes Mal war die Liste vollstaendig und jedes Mal falsch.

Eine Behauptung laesst sich nicht pruefen, eine Koordinate schon. Wer sie
hinschreibt, muss hinsehen -- und das ist der ganze Zweck. Die Stelle wird
gegen die Markerposition gehalten; liegt sie weit daneben, ist es entweder ein
anderes Objekt oder eine erfundene Zahl.

Erlaubte Werte: `sichtbar` fuer blaue Marker, `ersetzt` fuer rote. Jeder
Marker der Karte kommt genau einmal vor. Fehlt einer, oder steht dort etwas
anderes, ist die Lieferung unvollstaendig und wird zurueckgewiesen, bevor
ueberhaupt jemand das Bild ansieht.

Grund: am 2026-08-27 verschwand die Badewanne aus zwei Bildern, obwohl sie
Marker 1 traegt. Ein Marker allein aendert nichts -- er muss abgehakt werden.

## 11.2 Nach jeder Korrektur wird die GANZE Liste neu geprueft

Eine Korrektur ist erst fertig, wenn Abschnitt 11 und 11.1 fuer das
korrigierte Bild vollstaendig neu durchlaufen wurden. Nicht nur die
korrigierte Stelle. Drei Runden in Folge haben genau daran gescheitert: die
benannte Stelle war richtig, und daneben fehlte etwas Neues.

Nichts wird gezeigt, unter dem endgueltigen Namen gespeichert, in den Katalog
geschrieben oder als fertig bezeichnet, bevor es jeden zutreffenden Punkt
besteht.

---

## 11.3 Pflicht-Checkpunkte -- mit Nachweis, nicht nur gelesen

Diese Punkte stehen groesstenteils schon oben. Sie wurden trotzdem
wiederholt verfehlt. Deshalb sind sie Checkpunkte: jeder wird abgehakt UND in
`catalog.json` unter `checkpunkte` mit Ergebnis festgehalten. Fehlt ein
Eintrag oder steht dort "nein", ist die Lieferung abgelehnt.

1. **`blend_frisch`** -- "Neu laden" heisst: die `.blend` wirklich oeffnen und
   neu rendern. Ihren SHA-256 gegen den Auftrag pruefen und einen frischen
   Render ansehen, BEVOR gestaltet wird. Eintrag: Hash und "frisch gerendert".
   Nach einer ersetzten .blend gelten alte PNGs, Objektkarten und Vertrags-
   hashes nicht als aktueller Nachweis. Aenderungszeit und Hash feststellen,
   die neue Datei oeffnen und den frischen Render als Geometriequelle nutzen.
   Im Treppenbereich Wandflaechen, Treppenloch, Gelanderseite und Austritt
   einzeln vergleichen: keine Schrankfronten auf der Treppenhauswand und
   kein Gelaender auf der falschen Seite oder quer ueber dem Laufweg.
2. **`oeffnungen`** -- nach JEDER Bearbeitung jede Tuer, jeden Durchgang und
   jede Oeffnung mit dem Render vergleichen, besonders Kueche--Diele.
   Eintrag: Anzahl im Render = Anzahl im Bild.
3. **`fronten`** -- fuer jedes Moebel mit Vorderseite (Hochschraenke, Herd,
   Kuehlschrank, Spuele, Waschtisch, WC, Schraenke): Richtung der Front im
   Bild = "Front zeigt im Bild nach ..." aus dem Auftrag. Eintrag je Objekt.
4. **`korrekturen_gesperrt`** -- eine angenommene Korrektur (z. B. Kueche,
   Bettgroesse, Oeffnungen) gilt in ALLEN vier Stilen. Eintrag: welche
   Korrekturen, in welchen Bildern geprueft.
5. **`farbe_hintergrund`** -- nach JEDER Generierung ansehen: Hintergrund
   neutral weiss bis hellgrau, Farben gedeckt (Abschnitt 4). Eintrag je Bild.
6. **`quellfehler`** -- ist die Geometrie der Quelle fehlerhaft: das Problem
   Rainer zeigen und seine Wahl abwarten, BEVOR eine aeltere Fassung benutzt
   wird. Die Ausnahme wird festgehalten (Haus, Problem, Rainers Wahl).
7. **`upload`** -- nach dem Upload bestaetigen, dass ALLE geforderten Bilder
   bei der richtigen `plan_id` liegen, und melden, ob die Kundenfreigabe aus
   ist. Eintrag: Anzahl, `plan_id`, "Kundenfreigabe: aus/an".


# 12 — Lieferung

- Zwischenstaende tragen eigene Namen (`-v2`, `-review`) und duerfen die
  geforderten Dateinamen erst belegen, wenn sie angenommen sind.
- **Du lieferst einmal.** Ist der Zwischenstand angenommen, wird er auf der
  lokalen Maschine auf die geforderten Namen gebracht -- die Datei selbst wird
  umbenannt, die Bytes bleiben unveraendert. Es gibt keine zweite Runde und
  keinen `-final`-Ordner.
  (Geaendert 2026-08-28: davor stand hier, wie ein Finalsatz zu erzeugen sei.
  Das war eine Runde mehr statt weniger. Zweimal in Folge hing eine sonst
  fehlerfreie Lieferung allein am Dateinamen -- `onehalfstorey_020` mit
  `-review` und `-review-2`, `german_catalog_review_bungalow_3_2_4_b_100_1`
  mit `-review`. Der Name zaehlt an genau einer Stelle: er wird zum
  WordPress-Slug. Das gehoert nicht zu Codex.)
- **Ein angenommenes Bild wird nie neu gerendert.** Jeder neue Durchgang ist
  ein neuer Wuerfelwurf; dabei ist bei `onehalfstorey_020` dreimal die
  Badewanne aus einem fertigen Bad verschwunden.
- `catalog.json` enthaelt je Bild den `marker_check` aus Abschnitt 11.1.
- `catalog.json` enthaelt genau einen Eintrag je gefordertem Bild, mit
  Quell-Blend, Dateiname, Bildart, Stil bzw. Geschoss, SHA-256 und Zustand.
- SHA-256 wird erst nach dem endgueltigen Bild berechnet und vor der Uebergabe
  gegen die Datei geprueft; nach jeder Ersetzung neu.
- Die Bilder kommen in den im Auftrag genannten Lieferordner, nicht nach
  `go-baseline`.
- **Erste Fassung einzeln, danach nur mit Go weiter.** (Rainer, 2026-10-30)
  Eine Aussenansicht und je Geschoss ein Innenbild werden NACHEINANDER
  erstellt und gezeigt. Erst das ausdrueckliche OK zum aktuellen Bild
  abwarten, bevor das naechste Geschoss oder die naechste Ansicht entsteht.
  Kein paralleles Vorarbeiten an der ersten Fassung. Ein OK gilt nur fuer
  genau das gezeigte Bild. Erst nach Annahme der ersten Fassung UND Rainers
  Go die restlichen Stile und Dachansichten fertigstellen, pruefen und mit
  `publish-renders.py` hochladen. Bei Beanstandung nur die verlangte
  Korrektur bearbeiten und wieder das OK abwarten. Upload erst mit allen
  geforderten Bildern und gepruefter `catalog.json`.
  `upload_performed: true` erst nach erfolgreichem Upload und nachdem
  geprueft ist, dass die Bilder bei der richtigen `plan_id` liegen.
  Immer ohne `--send`, ohne Kunden-E-Mails, ohne Aenderung an Rechte- oder
  Bildfreigaben -- die Freigabe fuer Kunden bleibt bei Rainer.
  (Ersetzt "Codex laedt nichts hoch"; der Auftragsgenerator verlangt den
  Upload durch Codex schon seit 2026-10-07.)

---

# 13 — Ergaenzungen aus der Praxis (Handoff 2026-10-29)

Gesammelt aus den laufenden Codex-Lieferungen bis 2026-10-29. Gilt fuer alle
Haeuser. Widerspricht etwas hier einer frueheren Regel, gilt diese Fassung --
ausser bei Upload und Lieferung: dort gilt Abschnitt 12 (erste Fassung
gemeinsam pruefen, danach laedt Codex selbst hoch).

## 13.1 Quellen und Architektur

- Immer die neueste gelieferte `.blend` tatsaechlich oeffnen. Objektliste,
  Objektkarte, Tiefen- und ID-Maskenpass pruefen; Moebel nie anhand ihrer
  Silhouette erraten.
- Grundriss, Waende, Oeffnungen, Treppenloch, Gelaender und gespeicherte
  Kamera erhalten. Das Treppenloch folgt dem Modell und dem Gelaenderverlauf.
- Tuerblaetter einschliesslich Anschlag und Oeffnungswinkel aus der aktuellen
  `.blend` uebernehmen. Eine pauschale Aenderung auf 22° gilt NICHT.
- Aussenwandflaechen in Dollhouse-Bildern nahtlos: keine sichtbaren
  Geschossfugen, durchscheinenden Innenwandanschluesse, Streifen oder
  herausstehenden Fragmente. Echte Oeffnungen bleiben.
- Die Haustuer bleibt anthrazit, auch im sichtbaren Sockelgeschoss unter einem
  Obergeschoss-Bild. Sie darf nicht verkuerzt wirken; ihre Oberkante wie in der
  Quelle.

## 13.2 Moebel und Kueche

- Moebelposition, Anzahl, Groesse und Frontrichtung sind in allen vier Stilen
  gleich. Fronten folgen Objektpfeil und `.blend`; zeigt die Front weg, keine
  Tueren oder Geraete auf die sichtbare Rueckseite verlegen.
- Backofen- und Kuehlschrank-Hochschrank bleiben zwei getrennte
  Einbausaeulen, je 600 x 600 x 2400 mm. Die Geraete sitzen in der Front,
  zwischen zwei Seitenwangen, mit Schrankfronten oberhalb und unterhalb des
  Geraets.
- Nebeneinanderstehende Hochschraenke zeigen Front an Front in dieselbe
  Richtung und stehen buendig an der Kuechenzeile.
- Das Karomuster im Rohbild ist nur ein Platzhalter fuer eine Schrankfront,
  der ersetzt wird. Es sagt nichts ueber die Richtung -- die Richtung kommt
  aus Objektpfeil und `.blend`.
- Die Kuechenzeile mit ihrer tatsaechlichen L- oder U-Form vollstaendig
  uebernehmen. Keine Arbeitsplatte und keinen Schenkel weglassen.
- Kuechenzeile, Insel und Hochschraenke passen zusammen; Zeile und Insel haben
  dieselbe Arbeitsplatte.
- Garderoben sind erkennbare Einrichtung: sichtbare Maentel, Sitzbank,
  Schuhablage -- innerhalb ihres vorgesehenen Platzes.
- Schraenke bleiben als Moebel erkennbar, nicht als glatte Wandbloecke. Keine
  willkuerlich unterschiedlichen Hoehen; massgeblich ist die Quelle.

- Speisekammer: vorhandene Schrankfussabdruecke als erkennbare Vorratsregale
  mit Lebensmitteln, Einmachglaesern, Flaschen, Koerben und Obst/Gemuese
  ausarbeiten; nicht nur geschlossene Tueren zeigen.
- Treppen: hochwertige Vollholzoptik, kraeftige Stufen, sichtbare Maserung
  und passende Holzhandlaeufe. Keine Aenderung an Verlauf, Stufenzahl,
  Treppenloch oder Gelaenderseite der aktuellen .blend.

## 13.3 Begehbarer Schrank mit Glasschiebetueren

- Alle `glasschiebetuer-*`-Objekte sind EIN zusammengehoeriges Moebel,
  raumhoch (2400 mm), mit der im Auftrag angegebenen Zahl von Schiebefluegeln.

- Offene Regale und Kleiderstangen an der Rueckwand, ueber die im Modell
  vorgesehene Breite.
- Gefaltete Waesche, Kleidung auf Buegeln und Schuhe sichtbar ausarbeiten.
- Keine geschlossenen Fronten vor den Regalen, keine zusaetzliche Deckplatte
  oder Rueckwand, die den Einblick verdeckt.
- Vorn mattes bzw. satiniertes Glas, schmale Aluminiumrahmen. Es sind
  Schwebetueren: nur oben eine Laufschiene, keine Leiste am Boden.
- Ein Fluegel steht halb geoeffnet ueber seinem Nachbarfluegel. Bei drei
  Fluegeln ist es der mittlere. Kein Fluegel verschwindet in einer Wand.
- Abstand und Fussabdruck kommen aus der `.blend`. Nur wo das Modell keinen
  Abstand vorgibt: Rainers Vorgabe verwenden, nicht schaetzen. Bei bungalow_xvv6
  sind es in der aktuellen .blend rund 1,1 m freier Zugriffsgang. Rueckseiten
  direkt an die Wand, offene Faechern und Kleidung zum Gang; keine Platte
  zwischen Kleidung und Zugriff, Glas niemals durch Kleidung.

## 13.4 Materialien und Bildwirkung

- Realistische, zurueckhaltende Saettigung (siehe Abschnitt 4). Keine
  uebertrieben orangefarbenen Holzboeden, keine grellen Aussenanlagen.
- Dollhouse-Hintergrund im zum Bildsatz passenden Grau: Referenzbild
  desselben Hauses abgleichen, weder dunkel noch grellweiss; kein
  willkuerlicher Farbstich und keine ueberstrahlten Lichtsaeume.
- Weiche Kontaktschatten; keine seltsamen Raender, Flecken oder geometrischen
  Schattenartefakte um das Haus.
- Fliesen als erkennbare einzelne grossformatige Keramik-/Feinsteinzeugplatten
  mit klaren Formaten, schmalen sichtbaren Fugen und Keramikoberflaeche. Keine
  fugenlose Sprenkel- oder Linoleumflaeche, keine kleinteiligen unruhigen Muster.
- Sichtbare Materialstruktur, warme eingeschaltete Leuchten, sorgfaeltige
  Ausstattung. Classic wirkt hochwertig und klassisch, nicht kitschig.

## 13.5 Aussenansichten

- Terrassen grosszuegig und hochwertig ausstatten: zusammenpassende Lounge,
  Essplatz, Sonnenliegen, grosser Sonnenschirm, Grill und sorgfaeltige
  Accessoires nach vorhandenem Platz. Keine sparsame Alibi-Moeblierung.
  Alles auf bestehenden befestigten Flaechen, Zugaenge frei, keine
  Vergroesserung der Terrasse. Balkonverglasung und Gelaender vollstaendig
  aus der Quelle beziehungsweise Rainers bestaetigter Korrektur uebernehmen.
- Balkonbruestungen nach Stil: Classic klassisch, Normal Edelstahl mit
  horizontalen Staeben, Modern Glas. Nicht ueberall Glas.
- Tegalit-Dachdeckung: flache, sauber gegliederte anthrazitfarbene Dachsteine;
  keine groben Wellen, keine ueberzeichnete Dachtextur.
- Versetztes Pultdach: das senkrechte Verbindungsstueck endet an der
  Aussenwand und laeuft nicht durch den Dachueberstand. Abschluss mit
  Zink-Stehfalz; der obere Dachueberstand bleibt.
- Hanghaus: Aussenflaechen auf ihrer tatsaechlichen Geschosshoehe. Keine
  schwebenden Einfahrten oder Wege.

## 13.6 Korrekturen und Freigabe

- Angenommene Bilder nie erneut aus dem Rohbild erzeugen. Korrekturen am
  juengsten betreffenden Bild selbst, moeglichst eine Aenderung je Durchgang;
  NUR das Verlangte aendern, alles andere bleibt. Fruehere Fassungen behalten
  eigene Namen. Eingezeichnete Markierungen kommen restlos aus dem gelieferten
  Bild. Danach das ganze Bild gegen alle Anforderungen pruefen (11.2).
- Ausschnittkorrekturen mit dem Bildmodell. Skalieren und Neupositionieren per
  Python ist ausdruecklich abgelehnt.
- Keine erfundenen Sichtnachweise. Verdeckte Objekte nie als sichtbar abhaken.
- Kein ungepruefter Satz als "interne Vorschau" -- diese Ausnahme ist
  abgelehnt.
- Ein als Paket bestelltes Bildset wird erst veroeffentlicht, wenn ALLE
  bestellten Bilder fertig und geprueft sind. Fehlt eines, wird nichts
  hochgeladen.
- Nach jedem Upload pruefen, dass die hochgeladenen Bilder zur richtigen
  `plan_id` gehoeren (vorhandene, konfigurierte Zugangsdaten verwenden).
- Bei einem beauftragten Bildaustausch ersetzen die korrigierten Bilder die
  falschen veroeffentlichten Fassungen; beide duerfen nicht nebeneinander als
  gueltig stehenbleiben.
- `catalog.json`: verlangt der Auftrag einen Oeffnungsnachweis, steht als
  `nachweis` die Mesh-Anzahl, die du in der tatsaechlich geoeffneten `.blend`
  gezaehlt hast. Verlangt er den Vertragshash, steht je Bild zusaetzlich zum
  Bild-SHA-256 der `contract_sha256` aus `codex-job.json`, und nach der
  Freigabe der Zustand `approved`.
- Fertig gemeldet wird erst nach vollstaendiger Korrektur und Pruefung. Den
  Upload macht Codex danach selbst, nach dem OK zur ersten Fassung
  (Abschnitt 12), ohne
  `--send`, ohne Kunden-E-Mails, ohne Aenderung an der Rechtefreigabe.

### Praezisierungen aus bungalow_xvv6 (2026-10-31)

- Aussen: zurueckhaltende Saettigung, dezente unscharfe Vordergrundpflanzen,
  Tiefenschaerfe mit scharfem und vollstaendig sichtbarem Haus.
- Fremde helle Wandfragmente ueber Treppen sowie herausragende Holz-/Stein-
  streifen an Fassaden entfernen. Echte Stufen, Gelaender und Waende erhalten.
- Nach neuem Blender-Stand frisch oeffnen und rendern; daraus arbeiten.
  Aeltere generierte Fassungen sind keine Quelle fuer geaenderte Geometrie.

### Präzisierungen aus twostorey_xvv6 (2026-11-01)

- Möbelposition, Fußabdruck, Größe und Ausrichtung aus der aktuellen .blend bleiben auch bei Bildkorrekturen und Stilwechseln verbindlich.
- Kein Bodenbelag außerhalb der Außenwände. Außenfensterbänke: EG Granit, OG anthrazitfarbenes Blech. Vollständige Fensterrahmen; kein Verschwinden in Wänden.
- Hintergrund neutral grau, niemals blau oder mit Blau-/Cyanstich.
- Ankleide: erkennbare Kleidung mit Stofffalten und Bügeln, gefaltete Wäsche; keine plattenartigen Platzhalter oder zusätzliche Kleiderreihe. Gang und Regalausrichtung erhalten. Glas-Schwebetüren mit Laufschiene nur oben, keine Bodenschiene.
- Die vier vorhandenen Stilpaletten beibehalten. Gedeckte natürliche Holzfarben, kein Orange-Stich, keine fleckige Bildqualität. Materialien ausarbeiten; Möbel nicht durchgehend als graue Blöcke darstellen.

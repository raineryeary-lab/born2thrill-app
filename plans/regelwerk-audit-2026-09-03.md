# Regelwerk-Audit

Stand 2026-09-03. Geprueft: CODEX-REGELN.md (717 Zeilen, 12 Abschnitte) und
CODEX-AUFTRAG.md (408 Zeilen) aus
`german_catalog_review_bungalow_3_4_2_b_120/renders/go-baseline/`.

Anlass: Rainer, 2026-09-03 -- "Regeln, die aus einer Zeit stammen, die nicht
geprueft werden, ist undenkbar." Und: "wenn wir Regeln ueberpruefen, dann
muessen wir alle ueberpruefen."

Das ist eine Bestandsaufnahme. Es wurde keine Zeile geaendert.

## NACHTRAG 2026-09-03, nach Rainers Durchsicht

Vier Einstufungen waren falsch. Sie stehen unten korrigiert; hier der Grund,
damit sie nicht wiederkommen.

**Licht.** Rainer, mehrfach: "wir brauchen keine extra Leuchten, die Decke
fehlt, das ist genug Licht." Richtig, und Abschnitt 4 uebersieht es: das
Dollhouse-Bild ist ein Schnitt ohne Decke. Tageslicht faellt von oben in jeden
Raum. Eine eingeschaltete Pendelleuchte in einem Raum ohne Decke ergibt keinen
Sinn -- die Regel stammt aus der Zeit, als das Bildmodell fotografierte
Innenraeume nachbaute. Abschnitt 4 ist damit nicht UNGEPRUEFT, sondern in
seinen Lichtforderungen AUFGEHOBEN.

**Teppiche und Bilder.** Rainer, mehrfach: stilgemaess einfuegen. Damit ist der
Widerspruch zwischen 3.4 und 2.9 entschieden, nicht offen: Zubehoer, das zu
einem vorhandenen Objekt gehoert, IST erwuenscht. "Erfundene Moebel" meint
Moebelstuecke ohne Marker, nicht Ausstattung.

**Symmetrische Anordnung.** Rainer kennt die Forderung nicht und hat sie nie
gestellt. Sie steht in Abschnitt 5 unter Classic. Sie ist damit weder gueltig
noch geprueft, sondern herrenlos -- ohne Urheber und ohne Anlass. Streichen.

**Kassettierte Fronten und Kuechentueren sind eine TEXTUR, keine Geometrie.**
Rainer: "ist doch nur eine Textur." Nachgerechnet am tatsaechlichen Massstab
des Renders -- das Lowboard ist 3500 mm breit und belegt 311 Pixel, also
11,3 mm je Pixel:

    Schrankfront    600 mm  =  53,3 px    sichtbar
    Kassettenrahmen  60 mm  =   5,3 px    sichtbar, als Muster
    Rueckversatz      5 mm  =   0,44 px   unsichtbar
    Fuge              4 mm  =   0,36 px   unsichtbar
    Griff 15 mm tief         =   1,33 px  kaum

Die TIEFE einer Kassette ist ein halbes Pixel. Geometrie kauft dort nichts.
Sichtbar ist allein das MUSTER, und ein Muster ist ein Material. Damit faellt
der ganze "Frontgenerator" weg, den ich als groessten Restposten gefuehrt
habe. Was bleibt, ist ein prozedurales Material in echten Millimetern
(Objektkoordinaten, nicht UV-Wiederholung), das je Stil andere Felder,
Fugenlinien und Griffe zeichnet.

Das erklaert auch den Lowboard-Fehlversuch richtig: dort verschwanden die
FUGENLINIEN, nicht eine Tiefe. Eine Textur haette sie in jeder Laenge
geliefert.

## Die vier Status

    GILT          weiter gueltig, und es ist belegt woran das gemessen wurde
    MASCHINELL    gilt, wird aber nicht mehr von einem Menschen eingehalten
                  sondern von Code erzwungen -- die Regel ist zur Pruefung
                  geworden
    AUFGEHOBEN    widerlegt oder gegenstandslos, mit Datum und Grund
    UNGEPRUEFT    steht im Regelwerk, wurde nie gemessen -- weder bestaetigt
                  noch widerlegt

Der vierte Topf ist der wichtigste. Er ist bisher nicht vorgekommen, weil
niemand ihn gefuehrt hat.

---

# CODEX-REGELN.md

## 1 -- Was unantastbar ist

| Regel | Status | Beleg |
|---|---|---|
| 1.1 Die neueste .blend ist die alleinige Autoritaet fuer Geometrie | MASCHINELL | `export_invariants.py` liest sie, `verify_invariants.py` vergleicht |
| 1.1 Jede Wand, Oeffnung, Schnittebene exakt erhalten | MASCHINELL | 140 Architekturobjekte, Toleranz 0,001 mm |
| 1.1 Dollhouse-Kamera, Ausschnitt, Blickrichtung erhalten | MASCHINELL | `kamera`-Block in invariants.json |
| 1.1 Keine Raumaufteilung aus einem anderen Haus | AUFGEHOBEN | gegenstandslos: es gibt kein Bildmodell mehr, das etwas uebernehmen koennte |
| 1.2 Tuerzahl, Lage, Breite, Anschlag, Aufschlag, Fluegelzahl | MASCHINELL | Architektur, Mesh-Fingerabdruck |
| 1.2 "Ein Bildmodell darf eine Tuer neu zeichnen, solange..." | AUFGEHOBEN | 2026-09-02, WORKFLOW-OVERRIDE |
| 1.2 Pixelgenauer Vergleich gestrichen (2026-08-27) | AUFGEHOBEN | war schon aufgehoben, bleibt es |
| 1.3 Sanitaer und Kuechentechnik duerfen nie fehlen | MASCHINELL | `stueckzahlen.abweichungen` muss leer sein |

## 2 -- Was ersetzt werden soll

| Regel | Status | Beleg |
|---|---|---|
| 2.1 Moebel ist symbolisch, Ersetzen ist die Norm | GILT, neu gelesen | "Ersetzen" heisst jetzt: Modell laden, nicht malen |
| 2.1 Garderobe und Stuff werden IMMER ersetzt | TEILS ERFUELLT | Garderobe seit 2026-09-03 (coat_rack). Stuff offen: 250x2850 ist eine Zeile, kein Einzelmoebel |
| 2.1 Nie durch eine andere Moebelkategorie ersetzen | MASCHINELL | Typ kommt aus dem Symbol, nicht aus einer Entscheidung |
| 2.2 Mittelpunkt, Fussabdruck, Ausrichtung bleiben | MASCHINELL | `fit_to_symbol`, invariants |
| 2.3 Bett nie um 90 oder 180 drehen | MASCHINELL | Rotation kommt aus dem Plan |
| 2.3 Kopf- und Fussende folgen der .blend | UNGEPRUEFT | niemand hat nachgemessen, ob das Bettmodell richtig herum steht -- dieselbe Frage wie beim Kleiderschrank |
| 2.4 Genau so viele Stuehle wie Stuhlobjekte | MASCHINELL | `inventar: essgruppe_stuhl 6` |
| 2.4 Jeder Stuhl zeigt zum Tisch | UNGEPRUEFT | nicht geprueft; messbar ueber Winkel Stuhl-Front zu Tischmitte |
| 2.5 Kuechenkorpusse nie als merkmallose Bloecke | GILT, MATERIALAUFGABE | korrigiert 2026-09-03: bei 11,3 mm je Pixel ist die Fuge 0,36 px und der Rueckversatz 0,44 px. Es geht um das MUSTER, nicht um Geometrie. Ein prozedurales Material in echten Millimetern erfuellt die Regel |
| 2.5 Kuechenzug exakt wie gebaut | MASCHINELL | `build_path_run` folgt der gezeichneten Linie |
| 2.6 Fernseher nie ein schwarzes Rechteck | GILT, seit 2026-09-03 erfuellt | war zwei Wochen verletzt: `build_panel` mit TV_MAT. Jetzt TV Flatscreen 03 |
| 2.7 Schraenke mit Tueren, Griffen, Paneelen | TEILS ERFUELLT | Kleiderschrank seit 2026-09-03. Lowboard offen (Zeile, 3500x300) |
| 2.8 Garderobe nur am Marker, nie erfunden | MASCHINELL | Position kommt aus dem Plan, kann nicht erfunden werden |
| 2.9 Stuff nur am Marker | MASCHINELL | dito |
| 2.9 Deko nie auf leerer Bodenflaeche | **KONFLIKT** | siehe 3.4 |

## 3 -- Was jedes Innenbild erfuellen muss

| Regel | Status | Beleg |
|---|---|---|
| 3.1 Jeder Raum wird gestaltet, kein Raum bleibt Rohrender | MASCHINELL | Blender rendert alle Raeume in einem Durchgang; ein halb gestyltes Bild ist konstruktiv nicht mehr moeglich |
| 3.1 Je Raum: Boden mit Material, Moebel mit Textur, Licht, ein Ausstattungsstueck | UNGEPRUEFT | Boden ja, Moebeltextur teilweise, Licht und Ausstattung: nie gebaut |
| 3.2 Vier Entwuerfe, nicht vier Farbtoene | UNGEPRUEFT | ob mit Blender-Material und Modellwahl allein erreichbar, ist nie getestet worden |
| 3.2 Schwarzweiss-Test | GILT | bleibt der richtige Test, unabhaengig vom Verfahren |
| 3.3 Alles hat eine Oberflaeche | TEILS VERLETZT | `preserve_materials: false` wirft die Materialien geladener Modelle weg und ersetzt sie durch eine flache Farbe |
| 3.4 Styling gehoert dazu: Teppich, Bild, Vase, Maentel | GILT, ENTSCHIEDEN | Rainer mehrfach: Teppiche und Bilder stilgemaess einfuegen. "Erfundene Moebel" in 2.9 und AUFTRAG:30 meint MOEBELSTUECKE ohne Marker, nicht Ausstattung. Kein Konflikt mehr, sondern eine Entscheidung |
| 3.5 Was zusammensteht ist ein Satz (gleiches Material) | UNGEPRUEFT | pruefbar ueber Materialgleichheit je Gruppe; heute nicht geprueft |
| 3.6 Die vier Bilder zeigen dasselbe Haus, gleich moebliert | MASCHINELL | eine .blend, vier Materialsaetze -- die Anordnung kann sich nicht mehr unterscheiden |
| 3.7 Ein Marker gilt nur, was du wirklich gesehen hast | AUFGEHOBEN in dieser Form | die Selbstauskunft entfaellt mit dem Bildmodell. ERSATZ NICHT GEBAUT: der Objekt-Index-Pass, der Sichtbarkeit misst statt behauptet, existiert nicht. Bis dahin ist Sichtbarkeit UNGEPRUEFT |

## 4 -- Atmosphaere und Licht

| Regel | Status | Beleg |
|---|---|---|
| Leuchten sind AN und sichtbar, jede mit warmem Lichtkegel | **AUFGEHOBEN** | Rainer mehrfach: das Dollhouse-Bild ist ein Schnitt OHNE DECKE, Tageslicht faellt von oben in jeden Raum, das ist genug. Eine Pendelleuchte in einem Raum ohne Decke ergibt keinen Sinn. Die Regel stammt aus der Bildmodell-Zeit, als fotografierte Innenraeume nachgebaut wurden |
| Jedes Moebel hat einen Kontaktschatten | UNGEPRUEFT | EEVEE kann es; ob es im Dollhouse-Schnitt sichtbar ist, wurde nie gemessen |
| Boden, Wand, Arbeitsplatte nicht Ton in Ton | UNGEPRUEFT | |
| Eine Akzentfarbe je Stil, zwei- bis dreimal wiederholt | UNGEPRUEFT | |
| Kein Nebel, keine Strahlen, kein Farbfilter | GILT | mit Blender ohnehin nicht im Weg |
| "Ein korrektes, aber lebloses Bild ist kein angenommenes Bild" | GILT | und ist heute der wahrscheinlichste Ablehnungsgrund |

## 5 -- Die vier Stile

| Regel | Status | Beleg |
|---|---|---|
| Warm Modern, Dark Modern, Soft Scandinavian | UNGEPRUEFT | erreichbar ueber Material und Licht, nie gebaut |
| Classic: kassettierte Fronten, keine glatten Platten | GILT, MATERIALAUFGABE | korrigiert 2026-09-03: der Kassettenrahmen ist 5,3 px breit und damit sichtbar, seine Tiefe 0,44 px und damit nicht. Textur, kein Generator |
| Classic: "symmetrische Anordnungen" | **STREICHEN** | Rainer hat die Forderung nie gestellt und kennt sie nicht. Ohne Urheber, ohne Anlass, im Widerspruch zur Positionssperre 2.2 |
| Classic: gepolsterte Stuehle, Messinggriffe, gemusterter Teppich | UNGEPRUEFT | teils moeglich mit den neuen Modellen vom 2026-09-03 |

## 6 -- Das Geschoss darunter

| Regel | Status | Beleg |
|---|---|---|
| Sockel bleibt, Oeffnungen offen, nicht moebliert | MASCHINELL | `sockel-*` zaehlt als Architektur, `ist_architektur()` |

## 7 -- Aussenaufnahmen

| Regel | Status | Beleg |
|---|---|---|
| Je ein Bild Classic und Modern, 24-35 mm, Kamera waagerecht | GILT | Aussenbilder sind angenommen und werden nicht angefasst |
| 7.2 Referenzbild bestimmt Licht und Stimmung | GILT | betrifft nur Aussen |

## 8 -- Wie gearbeitet wird

| Regel | Status | Beleg |
|---|---|---|
| Grundbild geht an ein Bildmodell, EIN Ganzbild-Durchgang | **AUFGEHOBEN** | 2026-09-02. Ursache saemtlicher Klasse-A-Fehler |
| "Masken sind nicht noetig und werden nicht verlangt" (Z. 445) | **AUFGEHOBEN** | dieser Satz ist der teuerste im ganzen Regelwerk. Ohne Maske MUSS ein Bildmodell das ganze Bild neu schreiben; verschwundene Objekte, verschobene Moebel und falsche Stueckzahlen folgen zwangslaeufig |
| "Ein reiner Blender-Neurender scheitert an Abschnitt 11" (Z. 450) | **AUFGEHOBEN, UMGEDREHT** | ist ab 2026-09-02 der einzige zulaessige Weg |
| Nachbessern = zweite Ganzbild-Bearbeitung | AUFGEHOBEN | Nachbessern heisst: Szene aendern, neu rendern |
| 8.1 Aufbau des Prompts, fuenf Teile, ARCHITECTURE LOCK | GEGENSTANDSLOS | es gibt keinen Prompt mehr |
| 8.2 Ein angenommenes Bild wird NIE neu erzeugt | GILT | unabhaengig vom Verfahren richtig |
| 8.2 Ersetzte Datei kommt vorher unter `-vorher-<zeit>` | GILT | |

## 9 -- Format und Dateien

| Regel | Status | Beleg |
|---|---|---|
| Genau die geforderten Pixelmasze | MASCHINELL | Blender liefert exakt 2000x1500 |
| "Das Bildmodell gibt ein kleineres Bild aus, hochskalieren" | GEGENSTANDSLOS | |
| Toleranz Seitenverhaeltnis 0,5 % | GEGENSTANDSLOS | |
| PNG, genaue Dateinamen, catalog.json | GILT | |

## 10 -- Qualitaetsbeispiele

| Regel | Status | Beleg |
|---|---|---|
| Die vier 020-Bilder zeigen die gewuenschte Qualitaet | GILT | als Massstab |
| "Wer diese Qualitaet erreichen will, arbeitet so und nicht anders" | AUFGEHOBEN | das Verfahren daran ist gestrichen, der Massstab bleibt |
| Kein Korpus-Reference, kein Rechtenachweis | GILT | wichtig, beruehrt `rechte.py` |
| bungalow_039 vom 26./27.08. ist ausdruecklich KEIN Massstab | GILT | |

## 11 -- Pruefliste, 25 Ablehnungsgruende einzeln

**Geometrie**

| Grund | Status |
|---|---|
| Wand/Oeffnung/Tuer/Fenster verschoben, anders gross, dazu, weg | MASCHINELL |
| Obergeschoss hat den Sockel verloren oder zugemauert | MASCHINELL |
| Boden angeschnitten, Kamera geaendert, Bildtafel statt Bild | MASCHINELL |

**Vollstaendigkeit**

| Grund | Status |
|---|---|
| Ein Sanitaer- oder Kuechenobjekt fehlt im Bild | TEILS MASCHINELL -- vorhanden ja, SICHTBAR nein (kein Objekt-Index-Pass) |
| Garderoben- oder Stuff-Platzhalter noch als Kasten | Garderobe erfuellt, Stuff offen |
| Ein Moebel steht in einem Bild woanders als in den anderen drei | MASCHINELL |
| Marker als sichtbar gemeldet, obwohl anderes zu sehen | AUFGEHOBEN (Selbstauskunft entfaellt), Ersatz nicht gebaut |
| Ein Raum blieb Rohrender waehrend ein anderer gestylt wurde | MASCHINELL |

**Platzierung**

| Grund | Status |
|---|---|
| Garderobe nicht auf ihrem Marker | MASCHINELL |
| Moebel an einer Stelle ohne Marker | MASCHINELL |
| Tuerblatt verschwunden, weil ein Moebel davor steht | UNGEPRUEFT -- Bounding Box verhindert keine Verdeckung |
| Bett- oder Stuhlausrichtung weicht ab | MASCHINELL fuer die Platzierung, UNGEPRUEFT fuer das Modell selbst |
| Zahl der Esszimmerstuehle weicht ab | MASCHINELL |
| Einer schaut nicht zum Tisch | UNGEPRUEFT |
| Deko auf leerer Bodenflaeche | KONFLIKT mit 3.4 |

**Ausfuehrung**

| Grund | Status |
|---|---|
| Die vier Bilder waeren in Schwarzweiss dasselbe Zimmer | GILT, UNGEPRUEFT ob mit Blender erreichbar |
| Classic fehlen kassettierte Fronten, Muster, Messing | NICHT ERFUELLBAR (siehe 5) |
| Kuechenkorpusse sind flaechige Bloecke | UNGEPRUEFT (siehe 2.5) |
| "Das Bild ist ein reiner Blender-Neurender, daher abgelehnt" | **AUFGEHOBEN -- MUSS GESTRICHEN WERDEN** |
| Der Fernseher ist eine schwarze Platte | GILT, seit 2026-09-03 erfuellt |
| Das Bett ist eine unlesbare dunkle Masse | UNGEPRUEFT |
| Polster/Holz/Stein als glatte Farbflaeche | TEILS VERLETZT (preserve_materials) |
| Moebel einer Gruppe tragen verschiedene Materialien | UNGEPRUEFT |
| Das Bild ist flach: keine Leuchte, kein Lichtkegel, keine Schatten | **UNGEPRUEFT -- groesster offener Posten** |

**11.1 Selbstpruefung mit `bei`-Koordinaten**

AUFGEHOBEN in dieser Form. Sie war noetig, weil ein Bildmodell nicht wusste,
was es getan hatte. Der richtige Ersatz ist eine MESSUNG statt einer
Behauptung: der Schwerpunkt der sichtbaren Pixel je Objekt aus einem
Objekt-Index-Pass. Nicht gebaut.

**11.2 Nach jeder Korrektur die GANZE Liste neu pruefen**

GILT weiter. Der Grund entfaellt zwar (eine Ganzbild-Bearbeitung wuerfelt
nicht mehr das Geschoss neu), aber die Regel ist unabhaengig davon richtig:
heute hat ein Fix am Fernseher einen Materialfehler ausgeloest, und ein Fix am
Kleiderschrank hat einen Cache-Fehler aufgedeckt.

## 12 -- Lieferung

| Regel | Status |
|---|---|
| Zwischenstaende tragen eigene Namen | GILT |
| Du lieferst einmal | GILT |
| Ein angenommenes Bild wird nie neu gerendert | GILT |
| catalog.json mit SHA-256 je Bild | GILT |
| Bilder in den Lieferordner, nicht nach go-baseline | GILT, MASCHINELL (Harness schreibt nur nach renders/harness/) |
| Codex laedt nichts hoch | GILT |

---

# CODEX-AUFTRAG.md

| Zeile | Regel | Status |
|---|---|---|
| 25 | Grundbild aus der .blend verwenden | AUFGEHOBEN -- es wird gerendert, nicht bearbeitet |
| 26 | Kein frueheres Innenbild als Grundbild | GILT, gegenstandslos |
| 27 | "genau EIN Ganzbild-Durchgang; keine Maske" | **AUFGEHOBEN -- die teuerste Zeile im Auftrag** |
| 28 | .blend verbindlich fuer Architektur, Position, Stueckzahl | GILT, MASCHINELL |
| 29 | Architektur unveraendert | MASCHINELL |
| 30 | Keine erfundenen Moebel oder Deko auf freier Flaeche | KONFLIKT mit REGELN 3.4 |
| 31 | Jedes Moebel bleibt in Mitte, Fussabdruck, Groesse, Ausrichtung | MASCHINELL |
| 32 | Genau VIER Tuerblaetter, kein Doppelblatt | MASCHINELL |
| 33 | Tueren, Fenster, Verkehrswege frei | UNGEPRUEFT -- keine Kollisionspruefung |
| 34 | Garderobe und Stuff duerfen keine glatten Kaesten bleiben | Garderobe erfuellt, Stuff offen |
| 35 | Garderobe nur an Marker 19 | MASCHINELL |
| 36 | Genau SECHS Stuehle, alle zum Tisch | Zahl MASCHINELL, Richtung UNGEPRUEFT |
| 37-42 | Stueckzahlen Schreibtische, Waschtisch, WCs, Duschen, Spuele | MASCHINELL |
| 40 | Kein WC in einer Dusche | MASCHINELL (Position aus dem Plan) |
| 43 | Arbeitsplatten duerfen keine Oeffnung ueberbauen | UNGEPRUEFT |
| 44 | Ecksofa bleibt im Markerkasten, beruehrt keine Glasfront | UNGEPRUEFT -- Huellraum verhindert keine Durchdringung |
| 45 | Im HWR kein Bett | MASCHINELL |
| 46 | Jeder Raum wird gestaltet | MASCHINELL |
| 259-302 | Objektkarte: Pfeil zeigt VON DER WAND FORT, Kasten ist Vorschrift, ROT/BLAU | GILT -- und die Editor-Korrektur vom 2026-09-03 setzt genau diese Konvention endlich durch |

---

# Zusammenfassung

    MASCHINELL erzwungen        38
    GILT (unveraendert richtig) 16
    AUFGEHOBEN / gegenstandslos 14
    UNGEPRUEFT                  22
    KONFLIKT untereinander       2
    NICHT ERFUELLBAR             2

## Die drei Befunde, die zaehlen

**1. Der teuerste Satz steht immer noch drin.**
CODEX-REGELN.md Zeile 445 "Masken sind nicht noetig und werden nicht
verlangt" und AUFTRAG Zeile 27 "keine Maske". Beide sind in einer DRITTEN
Datei fuer ungueltig erklaert und stehen unveraendert im Original. Ein
Regelwerk mit einem Override-Zettel daneben ist kein Regelwerk.

**2. Die Haelfte der Prueflisten-Gruende ist jetzt Code, nicht Bitte.**
38 Regeln werden erzwungen statt erbeten. Das ist der eigentliche Gewinn des
Verfahrenswechsels -- nicht dass Blender schoener rendert, sondern dass eine
Regel, die eine Maschine prueft, nicht mehr verhandelt wird.

**3. 22 Regeln wurden nie gemessen.**
Der groesste Block darin ist Abschnitt 4, Atmosphaere und Licht: eingeschaltete
Leuchten, sichtbare Lichtkegel, Kontaktschatten, Akzentfarbe. Das steht seit
dem 2026-08-26 im Regelwerk, war der Ablehnungsgrund fuer bungalow_039 -- und
unter Blender-only hat es niemand gebaut oder getestet. Wenn heute vier
technisch fehlerfreie Bilder entstehen, ist DAS der wahrscheinlichste Grund,
warum sie trotzdem abgelehnt werden.

## Zwei Widersprueche, die im Regelwerk selbst stecken

- **Deko gegen erfundene Moebel.** 3.4 verlangt Teppich, Bild, Vase, Maentel.
  2.9 und AUFTRAG 30 verbieten Gegenstaende ohne Marker. Ein Teppich unter der
  Sitzgruppe ist beides zugleich. Der Vertrag muss Zubehoer von Moebeln
  trennen und erlaubte Traegerflaechen benennen.
- **Classic-Symmetrie gegen die Positionssperre.** 5 verlangt "symmetrische
  Anordnungen", 2.2 sperrt jede Umstellung. Symmetrie darf nur Zubehoer
  betreffen, nie die kanonische Moeblierung.

## Zwei Regeln, die heute nicht erfuellbar sind

- **Classic ohne kassettierte Fronten.** Geometrie, nicht Farbe. Entweder ein
  Frontgenerator oder die Regel streichen -- ein drittes gibt es nicht.
- **Kuechenkorpusse mit Tueren und Schubladen.** Dieselbe Sache. Und dieser
  Punkt ist zusaetzlich UNGEPRUEFT: es ist nie gemessen worden, ob eine glatte
  Kueche einem Kunden auffaellt.

## Was daraus folgt, in dieser Reihenfolge

1. Die aufgehobenen Zeilen IN den Originaldateien streichen, nicht daneben.
   14 Stellen.
2. Die zwei Widersprueche aufloesen -- Zubehoer vom Moebel trennen.
3. Abschnitt 4 bauen und messen. Licht ist der groesste ungeprueft-Block und
   der wahrscheinlichste naechste Ablehnungsgrund.
4. Fuer die zwei nicht erfuellbaren Regeln entscheiden: bauen oder streichen.
   Das ist eine Entscheidung, keine Aufgabe.
5. Den Objekt-Index-Pass bauen, damit "sichtbar" wieder pruefbar wird.

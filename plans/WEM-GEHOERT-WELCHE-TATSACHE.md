# Wem gehoert welche Tatsache?

Rainer, 2026-08-29: "das was langfristig am besten ist fuer unser Projekt, ich
will gerne spaeter diese Grundriss-Generation automatisiert aufstellen."

Nur gelesen und gezaehlt, nichts geaendert. Anlass war zweimal derselbe
Fehler an einem Tag: eine Frage, die an mehreren Stellen eigenstaendig
beantwortet wurde. Fuer eine Automatik ist genau das die gefaehrliche
Fehlerklasse -- nichts stuerzt ab, es wird still etwas Veraltetes bedient.

Gemessen ueber 275 Projektordner, `dataset.json` (314 Eintraege) und
`reconstruction-dataset.json` (55).

---

## 1. `package_status` -- das echte Problem

Entscheidet, ob ein Haus in den Moebel-Editor darf (Tor in
`api/floorplan-workbench/generate/route.ts`).

Drei Quellen:

    annotations.json          im Projektordner, wird beim Speichern geschrieben
    dataset.json              Momentaufnahme, generated_at 2026-08-02
    reconstruction-dataset    Momentaufnahme, generated_at 2026-07-31

Zur Laufzeit liest `simplifier-reference.ts` NUR die beiden Datensaetze und
legt sie ueber eine Map zusammen -- der Rekonstruktions-Eintrag gewinnt, weil
er hinten steht. Die Projektdatei, also das, was der Zeichner zuletzt
gespeichert hat, wird nicht gefragt.

Zahlen:

    185   alle vorhandenen Quellen einig
     48   Widerspruch, ALLE in derselben Richtung:
          Projekt sagt `annotated`, dataset sagt `training_ready`
     42   Projektordner ohne annotations.json
     17   im Projekt, in keinem Datensatz
     87   im dataset, aber KEIN Projektordner (die `*_queue_*`-Eintraege)

Zwei Folgen, in entgegengesetzte Richtungen:

- **Zu freizuegig.** 48 Haeuser duerfen moebliert werden, obwohl ihre eigene
  Annotation `annotated` sagt. Die Automatik wuerde sie anfassen.
- **Zu streng.** Am 2026-08-28 blockierte der umgekehrte Fall
  `german_catalog_review_bungalow_3_2_4_b_100_1`: die Zeichnung war frisch und
  `training_ready`, der Rekonstruktionseintrag stand auf `annotated`. Der
  Moebel-Tab blieb leer. Ich habe damals EINEN Eintrag von Hand ersetzt -- das
  ist keine Loesung, das ist ein Pflaster.

**Der Exporter ist keine Loesung, solange das ungeklaert ist.**
`export_generator_dataset.py` gegen `floorplan-simplifier/projects` liefert 104
Projekte. Ein Neuexport wuerde `dataset.json` von 314 auf 104 kuerzen. Ein Teil
davon sind die 87 Geister, die es wirklich nicht mehr gibt -- der Rest ist
ungeklaert und muss vor dem ersten Neuexport verstanden sein.

**Vorschlag:** die Projektdatei ist der Schreiber, die Datensaetze sind
abgeleitet. Dann muss (a) der Exporter wieder laufen duerfen, ohne Bestand zu
verlieren, und (b) das Tor entweder aus der Projektdatei lesen oder aus einem
Datensatz, der nicht vier Wochen alt ist.

---

## 2. Massstab -- besser als befuerchtet

    173   nirgends gesetzt
     53   nur in gebaeudemass.json
      5   nur in annotations.json
      2   in beiden, identisch
      0   Widerspruch

Es gibt also KEINEN Konflikt, nur eine faktische Ordnung: das Beiblatt
`gebaeudemass.json` besitzt den Massstab, die Annotation ist ein seltener
Rest aus frueher.

`build-simplifier-render-plan.py` mischt beim Bauen das Beiblatt in den
Annotations-Dict; danach liest alles eine Quelle. Der Zeichner tat das bis zum
2026-08-28 nicht -- deshalb zeigte das Breiten-Menue bei
`german_catalog_review_bungalow_3_2_4_b_100_1` "kein Massstab", obwohl er
danebenlag. Behoben.

**Das eigentliche Problem ist kein Konflikt, sondern eine Luecke:** 173 von 275
Haeusern haben ueberhaupt keinen Massstab. Ohne ihn gibt es keine Wandstaerken
und keinen Render. Fuer eine Automatik ist das der harte Deckel, nicht die
Frage, welche Datei gewinnt.

---

## 3. Dachform -- kein Konflikt, aber ein irrefuehrendes Etikett

    231   nur in gebaeudemass.json
      2   nur in annotations.json
      0   Widerspruch

Auch hier besitzt das Beiblatt die Tatsache. `dachform.py` haelt im Kopf fest,
warum: `roof_type_*` steht in genau zwei Annotationen, alle anderen Haeuser
gaben dem Renderer nichts.

Ein Schoenheitsfehler mit Folgen: `build-simplifier-render-plan.py` schreibt
in die `delivery-manifest.json`

    "roof_type_source": "annotation"

auch dann, wenn der Wert aus dem Beiblatt kam -- denn zu dem Zeitpunkt steht er
schon im Annotations-Dict. Der Wert stimmt, das Etikett luegt. Wer spaeter
Herkunft nachvollziehen will, sucht an der falschen Stelle.

---

## 4. Bilderzahl im Katalog -- WordPress-seitig

    b2t/v1/bilder?plan=<id>     zaehlt live       richtig (10 / 6 / 6)
    b2t/v1/grundrisse Feld `im` gespeicherter Wert falsch (20 / 14 / 0)

Der Workbench liest die Bulk-Route und gibt getreu weiter. Das Feld wird beim
Loeschen und Hochladen ueber die Medien-API nicht nachgefuehrt; ein
Cache-Buster aendert nichts, es ist gespeichert, nicht gecacht.

Kosmetisch, solange ein Mensch hinsieht -- aber es ist dieselbe Klasse:
gespeichert statt abgeleitet.

---

## Die Regel, die alle vier loest

Entweder **ableiten statt speichern**, oder **genau ein Schreiber und alle
anderen lesen**.

`renders/ANGENOMMEN.json` ist seit dem 2026-08-27 der Fall "ein Schreiber":
`lieferung-pruefen.py --annehmen` schreibt, alle anderen lesen ueber
`angenommener-ordner.mjs`. Seit dem 2026-08-29 raet keine Stelle mehr am
Ordnernamen. Das ist das Muster, das die anderen vier brauchen.

Reihenfolge nach Schaden fuer eine spaetere Automatik:

    1. package_status      Bestand und Tor -- kann still zwei Drittel verlieren
       + die 173 fehlenden Massstaebe (Luecke, kein Konflikt)
    2. roof_type_source    Etikett richtigstellen, damit Herkunft nachvollziehbar bleibt
    3. Bilderzahl `im`     WordPress-Snippet, braucht einen Login

---

## Nachtrag: warum der Exporter 104 statt 314 liefert

Nachgerechnet mit denselben Toren wie `export_project()`, ueber alle 275
Projektordner:

    105   geht durch
     58   rechtlich beschraenkt -- gehoert nur in den Rekonstruktionsdatensatz
     56   quality_checks.passed != true
     42   keine annotations.json (darunter `_verworfen-2026-08-23`, `bungalow_040`)
     12   package_status = draft
      2   keine training-data.json

Dazu die 87 Eintraege im `dataset.json`, die gar keinen Projektordner mehr
haben (die `*_queue_*`-Reihe). 314 = 105 durchgehende + 87 Geister + der Rest,
der an einem der Tore haengt.

**Es ist also kein Bestandsverlust, sondern ein Kassensturz.** Der Exporter
zaehlt richtig; `dataset.json` ist vier Wochen alt und traegt Haeuser, die es
so nicht mehr gibt.

### Der grosse Posten sind fehlende Marker, keine kaputten Daten

Die 56 mit `quality_checks.passed != true` haengen an genau einer Sorte
Warnung:

     23   House has no exterior/front door marker on an outer boundary
      9   upperfloor: Kind has no door/opening marker
      8   groundfloor: WC has no window marker
      8   groundfloor: Speisekammer has no door/opening marker
      5   groundfloor: Kochen has no door/opening marker
      ...

Das sind Zeichenluecken, kein Datenschaden: an einer Aussenwand fehlt die
Haustuer, an einem Zimmer die Tuer, an einem Bad das Fenster. Jede davon ist
im Zeichner in einer Minute gesetzt.

Und es erklaert die 48 Widersprueche aus Abschnitt 1: `dataset.json` sagt fuer
diese Haeuser `training_ready`, weil sie das am 2026-08-02 waren. Ihre
Annotation sagt heute `annotated`, weil die Qualitaetspruefung seither nicht
mehr durchgeht. Nicht der Datensatz luegt -- er ist bloss alt.

### Was daraus folgt

Ein Neuexport ist ungefaehrlich, sobald klar ist, dass die 87 Geister
verschwinden sollen. Er nimmt keinem Haus etwas weg, das es noch gibt.

Die eigentliche Arbeit sind die 56 fehlenden Marker. Das ist die Liste, an der
sich fuer eine spaetere Automatik entscheidet, wie viele Haeuser ueberhaupt
verfuegbar sind -- zusammen mit den 173 ohne Massstab.

---

## Nachtrag 2: die 87 sind keine Geister -- und es gibt keine Sicherung

Rainer, 2026-08-29: "hast du auch G: durchsucht?" Nein, hatte ich nicht -- ich
hatte nur den Baum unter `C:\dev\Floorplan-tools` abgesucht. Nachgeholt:

    C:  ganzes Laufwerk, Tiefe 8            nichts
    G:  Google-Drive-Kopie, 137 Projekte    keiner der 87
    E:  corrections/                        3 von 87, und nur `revisions/`
    D:                                      nichts

**Erst der Inhalt der Eintraege**: alle 87 tragen echte Geometrie -- Geschosse,
Raeume mit Polygon und Beschriftung, Elemente mit Typ und Punkten,
`quality_status: passed`, `source_kind: real_annotated`. 77 davon sind
zweigeschossig.

Damit ist zweimal falsch, was ich vorher geschrieben hatte:

1. "Geister, die es nicht mehr gibt" -- nein, es sind Haeuser mit vollstaendiger
   Geometrie.
2. "Ein Neuexport ist ungefaehrlich" -- nein, er wuerde 84 Datensaetze
   loeschen, von denen es keine zweite Kopie gibt.

Die drei mit einem Ordner auf E: (`measured_twostorey_bach_001`,
`twostorey_051`, `twostorey_queue_5_1_4_sv_130`) haben dort eine
`revisions/revision-0001.json` -- korrigierte Millimetergeometrie mit Waenden,
Oeffnungen und Treppenkern, also eine SPAETERE Stufe als die Annotation. Auch
das ist kein Ersatz fuer den Projektordner, aber fuer diese drei waere die
Geometrie doppelt vorhanden.

### Was in den Eintraegen fehlt, falls man Projektordner daraus baut

    quality_checks       egal, rechnet der Zeichner neu
    training-data.json   ableitbar aus den Rechtefeldern
    floor_alignment      WEG -- und 77 der 87 sind zweigeschossig

Die Ausrichtmarken sind der harte Verlust: ohne sie lassen sich Ober- und
Erdgeschoss nicht uebereinanderlegen.

### Empfehlung

Der Exporter muss ZUSAMMENFUEHREN statt zu ersetzen. Was er in `projects/`
sieht, wird aktualisiert; was er nicht sieht, bleibt stehen und bekommt eine
Markierung. Dann darf er wieder laufen, `package_status` wird wieder aktuell,
und niemand verliert etwas.

Eine Rekonstruktion der Projektordner lohnt nur fuer einzelne Haeuser, die
wirklich wieder gezeichnet werden sollen -- und die 77 zweigeschossigen
brauchten neue Ausrichtmarken.

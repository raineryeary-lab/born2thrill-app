# Interior wall geometry: off-axis snap and T-junction closing

Status: COMPLETE (implementiert und verifiziert 2026-08-23)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Innenwaende sauber machen. Rainer, 2026-08-23, mit Screenshot des OBERGESCHOSSES
von `onehalfstorey_029` im Moebel-Editor: eine schraege Wand an der Grenze
Flur/Kind, die orthogonal sein muesste; Innenwaende, die vor der Wand aufhoeren,
die sie treffen sollten (offene T-Stoesse); kleine Knicke, wo zwei eigentlich
kollineare Innenwaende zusammenkommen.

Der Aussenwand-Teil desselben Problems ist heute frueher schon geschlossen
worden (`_close_exterior_corners`); der wird hier nicht angefasst.

## Current evidence and behavior

GEMESSEN, nicht geraten. Kommando:

```
FLOORPLAN_WORKBENCH_DATA_DIR='E:\born2thrill-local-workbench-data' \
  python scripts/build-simplifier-render-plan.py onehalfstorey_029 modern <tmp>.json
```

### (a) Die schraege Wand — `floors[1].walls` (upperfloor), wall_type interior

| id | start_mm | end_mm | Laenge | Winkel | Abweichung von der Achse |
|----|----------|--------|--------|--------|--------------------------|
| wall-0 | 7051.6, 10084.8 | 7051.6, 6287.6 | 3797.2 | 90.00 | 0.00 |
| wall-1 | 7051.6, 5124.2 | 7051.6, 808.8 | 4315.4 | 90.00 | 0.00 |
| wall-2 | 7025.0, 5124.2 | 2937.7, 5124.2 | 4087.3 | 0.00 | 0.00 |
| wall-3 | 7096.0, 6187.9 | 9049.0, 6187.9 | 1953.0 | 0.00 | 0.00 |
| **wall-4** | **9152.4, 6366.2** | **11398.4, 5993.5** | **2276.7** | **170.58** | **9.42** |
| wall-5 | 7096.0, 3909.8 | 11385.7, 3909.8 | 4289.7 | 0.00 | 0.00 |

`wall-4` ist die schraege Wand aus dem Screenshot. Sie gehoert zu genau
demselben Raumpaar wie `wall-3` (Rooms `...666466` / `...681063`) — es ist
EINE Trennwand, die in zwei Stuecken herauskommt, und das zweite Stueck steht
9.42 Grad schief. Genau daher auch der "Knick": zwischen `wall-3`-Ende
(x=9049.0, y=6187.9) und `wall-4`-Anfang (x=9152.4, y=6366.2) liegen 103.4mm
in x und 178.3mm in y.

Der bestehende `_merge_collinear_walls` merged die beiden NICHT, weil der
Linien-Offset der schraegen Wand zu weit weg liegt. Rechnerisch: nach dem
Geradeziehen von `wall-4` auf y = (6366.2+5993.5)/2 = 6179.85 liegt sie 8.05mm
neben `wall-3` (< MERGE_LINE_OFFSET_TOLERANCE_MM 150) und ihr Anfang 103.4mm
hinter `wall-3`s Ende (< MERGE_GAP_TOLERANCE_MM 300) — sie verschmelzen dann
von selbst zu einer Wand.

### (b) Offene T-Stoesse — Innenwand-Enden vor einer Wandachse

Gemessen: fuer jedes Innenwand-Ende der naechste Schnittpunkt in
Verlaengerungsrichtung mit einer anderen Wandachse (>= 30 Grad, Fusspunkt
innerhalb der Zielwand +- 300mm).

onehalfstorey_029, upperfloor:

| Wand | Ende | Luecke (mm) | Ziel |
|------|------|-------------|------|
| wall-0 | start | 120.0 | wall-6 (exterior) |
| wall-0 | end | 99.7 | wall-3 (interior) |
| wall-1 | end | 120.0 | wall-9 (exterior) |
| wall-2 | start | 26.6 | wall-1 (interior) |
| wall-2 | end | 120.0 | wall-8 (exterior) |
| wall-3 | start | 44.4 | wall-0 (interior) |
| wall-4 | end | 108.8 | wall-10 (exterior) |
| wall-5 | start | 44.4 | wall-1 (interior) |
| wall-5 | end | 120.0 | wall-10 (exterior) |

onehalfstorey_029, groundfloor: eine einzige Luecke, `wall-1` start 56.9mm auf
`wall-0`. Der Rest des Erdgeschosses ist sauber oder steht (ohne Luecke) ueber.

Die wiederkehrenden **120.0mm** sind exakt die halbe Aussenwandstaerke
(DEFAULT_WALL_THICKNESS_MM/2). Ursache ist strukturell und nicht zufaellig:
Innenwaende entstehen aus den Raum-INNENKANTEN, Aussenwaende werden um eine
halbe Staerke nach aussen geschoben — also endet jede Innenwand systematisch
120mm vor der Aussenwand-Mittellinie.

Zum Vergleich mitgemessen (Regressionsbasis):

- bungalow_039 groundfloor: 7 Luecken, 10.3 .. 55.4mm, alle Innenwand-auf-Innenwand.
- twostorey_030 groundfloor: 5 Luecken, 10.4 .. 95.7mm; upperfloor: 10 Luecken,
  47.2 .. 170.6mm (davon 6x exakt 120.0).
- bungalow_040_66 groundfloor: 9 Luecken, 36.3 .. 184.8mm.

### (c) Korpusweite Winkelverteilung (fuer die Toleranzwahl)

Alle 94 baubaren Simplifier-Projekte durchgerechnet, 582 Innenwaende. 67 davon
sind nicht achsparallel. Abweichung von der naechsten Achse, sortiert:

```
5.56  5.72  6.39  6.99  7.12  7.34  7.91  8.00  8.36  8.36  8.86
9.09  9.42(<- onehalfstorey_029)  9.46  10.00  10.26  10.43
                <<< MESSBARE LUECKE: nichts zwischen 10.43 und 21.58 >>>
21.58  21.79  24.72  ... 35.38 ... 39.28 ... und 34 Stueck im Band 40..45
```

Nichts unter 5.56 Grad, weil `_regularize_outline_points` (Toleranz 6 Grad)
die Raumpolygone schon vorher geradezieht. Das Band 40..45 sind die echten
45-Grad-Diagonalen, die auf keinen Fall angefasst werden duerfen.

Die Luecke zwischen 10.43 und 21.58 Grad ist der Grund fuer die Toleranzwahl
unten: 12.0 Grad liegt mitten in einem gemessenen leeren Band, also gibt es auf
diesem Korpus keinen Grenzfall.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`, kein Git-Repo-Root
  im Sinne von `git rev-parse` sauber nutzbar? Doch: HEAD = `5be1a4e18956b9fb2e158bee82aa159898356e89`.
- Vorbestehende, NICHT von dieser Aufgabe stammende Aenderungen im Worktree
  (bleiben unangetastet): `data/simplifier-v2/corpus-ledger.json`,
  `data/simplifier-v2/dataset.json`, `package.json`,
  `scripts/build-simplifier-render-plan.py` (die heute frueher gelandete
  `_close_exterior_corners`-Arbeit), `scripts/render-furnished-dollhouse.py`.
- Testlauf vor der Aenderung: `python scripts/build-simplifier-render-plan.test.py`
  -> 17 Tests, OK.

## Exact scope

1. Nahe-achsparallele INNENwaende exakt achsparallel machen, um ihren
   Mittelpunkt gedreht (`_orthogonalize_interior_walls`).
2. Innenwand-Enden auf die Wandachse verlaengern, auf die sie erkennbar
   zulaufen (`_close_interior_t_junctions`).
3. Reihenfolge in `build_walls`: orthogonalisieren -> `_merge_collinear_walls`
   -> `_close_exterior_corners` -> T-Stoesse schliessen. Das Geradeziehen VOR
   dem Merge, damit die auseinandergefallene Trennwand (a) von selbst wieder
   eine wird; das T-Schliessen ZULETZT, damit es auf die endgueltigen
   Aussenwand-Ecken zielt.

### Toleranzen (begruendet aus der Messung oben)

| Konstante | Wert | Begruendung |
|-----------|------|-------------|
| `INTERIOR_ANGLE_SNAP_TOLERANCE_DEG` | 12.0 | groesser als die 6 Grad von `_regularize_outline_points` (sonst wirkungslos), und mitten in der gemessenen leeren Bandluecke 10.43..21.58 Grad. 45-Grad-Diagonalen liegen 33 Grad ausserhalb. |
| `T_JUNCTION_GAP_MM` | 400 | groesste gemessene echte Luecke im Korpus 184.8mm (bungalow_040_66) bzw. 170.6mm (twostorey_030); 400mm ist derselbe Wert, den `MAX_PARTITION_GAP_MM` und `OUTLINE_WELD_DISTANCE_MM` schon als "das ist noch dieselbe Wand"-Mass benutzen. |
| `T_JUNCTION_MIN_ANGLE_DEG` | 30.0 | identisch zu `_close_exterior_corners`: flacher ist keine echte Ecke. |
| `T_JUNCTION_TARGET_OVERRUN_MM` | 300 | der Fusspunkt darf bis 300mm ueber das Ende der Zielwand hinausliegen (L-Ecke), aber nicht weiter. Gleiche Groessenordnung wie `MERGE_GAP_TOLERANCE_MM`. |

### Warum das auf sauberer Geometrie beweisbar nichts tut

- Snap: eine Wand, deren Endpunkte schon dieselbe x- (bzw. y-) Koordinate
  haben, bekommt als Mittelwert genau diese Koordinate zurueck — bitidentisch.
  Eine Wand ausserhalb der Toleranz wird gar nicht erst betrachtet.
- T-Stoss: nur VERLAENGERT wird (Schnittpunkt muss in Verlaengerungsrichtung
  und mehr als 1mm entfernt liegen), nie gekuerzt und nie seitlich verschoben.
  Ein Ende, das schon auf der Zielachse sitzt, hat Abstand 0 und faellt unter
  die 1mm-Schwelle. Ueberstehende Enden (029 groundfloor `wall-3` steht 162mm
  ueber `wall-11` hinaus) bleiben unangetastet — Trimmen ist ausdruecklich
  NICHT Teil dieser Aufgabe.
- Beide Schritte laufen in Runden gegen eine EINGEFRORENE Kopie der Wandliste,
  damit das Ergebnis nicht von der Listenreihenfolge abhaengt.

## Files in scope

- `scripts/build-simplifier-render-plan.py`
- `scripts/build-simplifier-render-plan.test.py`
- `plans/interior-wall-geometry-v1.md` (diese Datei)

## Explicitly out of scope

- `C:\dev\Floorplan-tools\floorplan-simplifier\walls.py` — die Zwillingskopie
  von `_merge_collinear_walls`/`_outline_to_walls`. Sie hat schon heute kein
  `_close_exterior_corners`; die Divergenz ist damit vorbestehend und gehoert
  in ein eigenes Sync-Plan-Item (Roadmap).
- Aussenwaende, `_close_exterior_corners`, Dachumriss.
- Das Kuerzen ueberstehender Innenwand-Enden.
- Die zwei als `exterior` klassifizierten Waende bei x=7145.0 und x=6976.0 im
  029-Obergeschoss (y 5124.2..6287.6): zwei parallele 240er Waende 169mm
  auseinander, wo eine Innenwand hingehoert. Das ist der `partnered`-Fallback
  in `build_walls`, ein anderer Fehler — Roadmap.
- WordPress, Publishing, E-Mail, Datenbank, externe Systeme: nichts davon wird
  beruehrt.

## API, schema, and data-contract effects

Keine. Waende behalten `id/start_mm/end_mm/thickness_mm/wall_type/rooms`.
Oeffnungen werden in `build_floor_walls_and_openings` ERST NACH `build_walls`
auf die Waende gematcht (`nearest_wall`), ihr normiertes `position` wird also
gegen die bereits korrigierte Wand berechnet — kein Versatz von Tueren.

## Acceptance criteria

1. `onehalfstorey_029` upperfloor: keine Innenwand mehr mit einer
   Achsabweichung zwischen 0 und 12 Grad. `wall-4` (9.42 Grad) verschwindet als
   eigenstaendige Wand und geht in der Trennwand von `wall-3` auf.
2. `onehalfstorey_029` upperfloor: keine offenen T-Stoesse ueber 1mm mehr.
3. `bungalow_039` und `twostorey_030`: keine Innenwand veraendert ihre Achse;
   Wandanzahl und Wandtyp-Verteilung unveraendert oder mit weniger Luecken.
4. Beide Suites gruen.

## Tests and verification commands

Neu in `scripts/build-simplifier-render-plan.test.py`, Klasse
`InteriorWallGeometryTests` (reine Unit-Tests auf den beiden neuen Funktionen,
plus zwei Integrationszusicherungen auf dem echten `bungalow_039`):

1. `test_off_axis_interior_wall_is_straightened` — Wand 9.42 Grad schief wird
   exakt achsparallel, Mittelpunkt bleibt.
2. `test_already_orthogonal_interior_wall_is_untouched` — bitidentisch.
3. `test_exterior_wall_is_never_straightened` — nur interior.
4. `test_legitimate_diagonal_is_left_alone` — 45 Grad und 21.6 Grad (der
   naechste echte Korpuswert) bleiben unveraendert.
5. `test_t_junction_gap_is_closed` — 120mm-Luecke auf eine Aussenwandachse
   wird geschlossen.
6. `test_t_junction_overshoot_is_not_trimmed` — ein ueberstehendes Ende bleibt.
7. `test_parallel_wall_is_not_a_t_junction_target` — kein Andocken an eine
   parallele Wand.
8. `test_gap_beyond_tolerance_is_left_open` — 900mm Luecke bleibt offen.
9. `test_clean_geometry_is_a_no_op` — eine schon saubere Wandliste kommt
   unveraendert zurueck.
10. `test_bungalow_039_interior_walls_are_axis_true` — echtes Projekt: keine
    Innenwand mit Achsabweichung 0 < d <= 12 Grad.
11. `test_bungalow_039_has_no_open_interior_t_junctions` — echtes Projekt.

Bestehende Tests werden nicht geloescht, uebersprungen, abgeschwaecht oder
umgeschrieben. Insbesondere bleibt
`test_no_two_same_type_walls_sit_on_the_same_line_unmerged` unveraendert
gueltig; das Geradeziehen laeuft VOR dem Merge, kann also keine neuen
unverschmolzenen Doppel-Linien erzeugen.

Verifikationskommandos:

```
python scripts/build-simplifier-render-plan.test.py
FLOORPLAN_WORKBENCH_DATA_DIR='E:\born2thrill-local-workbench-data' python scripts/go.test.py
```

Plus ein Vorher/Nachher-Diff der Innenwandlisten von `onehalfstorey_029`,
`bungalow_039`, `twostorey_030` und `bungalow_040_66`.

## Protected and risky paths

- `build_walls` ist der einzige Wand-Erzeuger fuer BEIDE Konsumenten:
  `geometry_only()` (Moebel-Editor-Planansicht) und den vollen Render-Plan.
  Eine Regression hier ist im Editor und im Render gleichzeitig sichtbar.
- Oeffnungs-Matching (`nearest_wall`, Schwelle 1200mm) haengt an den
  Wandkoordinaten. Verlaengerungen von <= 400mm koennen ein `wall_id` nur
  von einer Wand auf dieselbe verlaengerte Wand aendern, nie eine Tuer
  verwaisen lassen — verifiziert durch den Vorher/Nachher-Vergleich der
  `unmatched`-Listen aller vier Projekte.

## Rights, provenance, privacy, and security impact

Keine. Es werden keine Quellannotationen veraendert, nichts importiert,
nichts exportiert, keine Rechtelage beruehrt.

## Floorplan-suite invariant

> Can any changed path generate, publish, or email geometry without matching an
> approved corrected corpus reference?

**Nein.** `build_walls` ist eine reine Funktion `(rooms, outline) -> walls`.
Sie liest keine Datenbank, schreibt keine Datei, ruft nichts Externes.
Publikation und E-Mail haengen unveraendert am WordPress-Handgate; keine der
geaenderten Zeilen liegt auf diesem Pfad. Beweis: `git diff` beruehrt nur
`scripts/build-simplifier-render-plan.py` (Funktionen `_orthogonalize_interior_walls`,
`_close_interior_t_junctions`, letzte Zeile von `build_walls`) und die
Testdatei.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

Keine — die Ursache wurde gemessen, nicht geraten (Abschnitt "Current
evidence and behavior").

## Rollback

`git checkout -- scripts/build-simplifier-render-plan.py scripts/build-simplifier-render-plan.test.py`
wuerde AUCH die heute frueher gelandete `_close_exterior_corners`-Arbeit
zuruecknehmen (gleiche Datei, noch nicht committet). Sicherer Rollback dieser
Aufgabe allein: die drei neuen Bloecke
(`INTERIOR_ANGLE_SNAP_TOLERANCE_DEG`-Konstantenblock,
`_orthogonalize_interior_walls`, `_close_interior_t_junctions`) loeschen und die
Rueckgabezeile von `build_walls` auf
`return _close_exterior_corners(_merge_collinear_walls(walls))` zuruecksetzen,
sowie die Testklasse `InteriorWallGeometryTests` entfernen.

## Unresolved questions

- Sollen ueberstehende Innenwand-Enden spaeter auch gekuerzt werden
  (029 groundfloor `wall-3` steht 162mm ueber die Aussenwand hinaus)? Fuer den
  Screenshot-Fehler nicht noetig; als Roadmap-Punkt vermerkt.

## Verification record (2026-08-23, nach der Implementierung)

### onehalfstorey_029, upperfloor, Innenwaende — vorher / nachher

| vorher | nachher |
|--------|---------|
| 6 Innenwaende, davon 1 schief (9.42 Grad) | 5 Innenwaende, davon 0 schief |
| 9 offene T-Stoesse, 26.6 .. 120.0mm | 0 offene T-Stoesse |
| wall-3 y=6187.9 x 7096.0..9049.0 (1953.0mm) **+** wall-4 schraeg 9152.4,6366.2 -> 11398.4,5993.5 | **eine** Wand y=6187.9 x 6976.0..11505.7 (4529.7mm) |
| wall-0 x=7051.6 y 10084.8..6287.6 | x=7051.6 y 10204.8..6187.9 (beide Enden angeschlossen) |
| wall-1 x=7051.6 y 5124.2..808.8 | x=7051.6 y 5124.2..688.8 |
| wall-2 y=5124.2 x 7025.0..2937.7 | y=5124.2 x 7145.0..2817.7 |
| wall-5 y=3909.8 x 7096.0..11385.7 | y=3909.8 x 7051.6..11505.7 |

029 groundfloor: eine einzige Aenderung (`wall-1` start y 6047.2 -> 6104.1,
+56.9mm); Aussenwaende bitidentisch.

### Regression auf den anderen Projekten

Alle Aenderungen sind ausschliesslich VERLAENGERUNGEN von Innenwand-Enden.
Keine Wand wurde gekuerzt, keine seitlich verschoben, keine Aussenwand
angefasst, kein Wandtyp geaendert, keine Wandanzahl ausser dem einen Merge in
029 OG geaendert.

| Projekt | Waende | Innenwaende | Oeffnungen | unmatched | veraenderte Innenwaende |
|---------|--------|-------------|------------|-----------|-------------------------|
| onehalfstorey_029 groundfloor | 15 -> 15 | 7 -> 7 | 16 -> 16 | 0 -> 0 | 1 (+56.9mm) |
| onehalfstorey_029 upperfloor | 12 -> 11 | 6 -> 5 | 10 -> 10 | 0 -> 0 | alle 5, plus 1 Merge |
| bungalow_039 groundfloor | 13 -> 13 | 9 -> 9 | 15 -> 15 | 0 -> 0 | 6, je 10.3 .. 55.4mm |
| twostorey_030 groundfloor | 10 -> 10 | 6 -> 6 | 10 -> 10 | 0 -> 0 | 4, je 10.4 .. 95.7mm |
| twostorey_030 upperfloor | 11 -> 11 | 5 -> 5 | 10 -> 10 | 0 -> 0 | 5, je 83.6 .. 170.6mm |
| bungalow_040_66 groundfloor | 20 -> 20 | 8 -> 8 | 20 -> 20 | 0 -> 0 | 6, je 36.3 .. 184.8mm |

Keine Tuer und kein Fenster ist verwaist (`unmatched` bleibt ueberall 0), und
die Oeffnungszahlen sind unveraendert.

### Korpusweit (94 Projekte)

|  | vorher | nachher |
|--|--------|---------|
| Innenwaende gesamt | 582 | 570 (12 nahe-kollineare Paare verschmelzen jetzt) |
| nicht achsparallel | 67 | 50 |
| davon <= 12 Grad (Zittern) | 17 | **0** |
| davon 20.6 .. 45 Grad (echte Schraegen) | 50 | 50 — **unveraendert** |

Histogramm nachher: `{20: 3, 25: 3, 30: 4, 35: 6, 40: 34}` — identisch mit
vorher in genau diesen Baendern. Keine einzige echte Diagonale wurde angefasst.

### Moebelstaende bleiben gueltig

`level_geometry_identity` hasht die RAUMPOLYGONE, nicht die Waende. Diese
Aenderung fasst keine Raumpolygone an, also entwertet sie keinen gespeicherten
Moebelstand. Geprueft:

```
--geometrie-id onehalfstorey_029 groundfloor -> b23a75c0af00...5e87f716
--geometrie-id onehalfstorey_029 upperfloor  -> 4954ab0865f2...48a0eb7ea
```

stimmen mit `geometry_identity` in
`E:\born2thrill-local-workbench-data\corrections\onehalfstorey_029\furniture\floor-0.json`
und `floor-1.json` ueberein. Rainer muss nichts neu moeblieren.

### Suites

```
python scripts/build-simplifier-render-plan.test.py    -> Ran 30 tests, OK
FLOORPLAN_WORKBENCH_DATA_DIR=... python scripts/go.test.py -> Ran 4 tests, OK
```

(vorher: 17 Tests; 13 neue kamen mit dieser Aufgabe dazu, kein bestehender
Test wurde geloescht, uebersprungen, abgeschwaecht oder geaendert.)

Ein `go.py`-Bau wurde NICHT ausgefuehrt: er dauert rund zehn Minuten und die
Maschine wird von der Hauptsitzung benutzt. Die Geometrie ist am Render-Plan
selbst verifiziert, und der Render-Plan ist die einzige Geometriequelle fuer
das Render.

## Approval record

Beauftragt am 2026-08-23 von Rainer ueber die Hauptsitzung, mit ausdruecklicher
Vorgabe von Reihenfolge (erst messen, dann Plan, dann Tests, dann Code) und
Testfaellen. Diese Datei ist das geforderte Planprotokoll.

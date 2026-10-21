# Der kleine Schenkel bekommt ein Pultdach statt eines eigenen Satteldachs

Status: REVIDIERT 2026-10-08 nach Rainers eigener .blend-Fassung — freigegeben

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-08, an `bungalow_040_31`: "this satteldach is wrong. it has
2 roofs" -- dann die Vorgabe: "auf dem kleinen Dach müsste ein Pultdach sein
das parallel zum anderen Dach läuft, auf gleicher höhe wie das andere Dach"
und "wie C nur ist der first genau da wo die Floorplan segmente zusammenkommen".

## Current evidence and behavior

Gemessen aus
`E:\...\bungalow_040_31\renders\go-baseline\exterior-satteldach-baseline.blend`
(Firstrichtung je Fluegel aus den Giebelwaenden von `roof-walls` gelesen, nicht
aus dem Seitenverhaeltnis geraten):

| Fluegel | First | Spannweite | Traufe | First | Neigung |
|---|---|---|---|---|---|
| gross | parallel y | 12,48 m | 2750 | 4810 | 18,3 Grad |
| Anbau | parallel x |  3,19 m | 2750 | 3287 | 18,6 Grad |

Die NEIGUNG stimmt bereits ueberein -- `scale_profile_to_span()` wird im
Chevron-Zweig aufgerufen (render-exterior.py:1963) und haelt sie gleich.

Der Fehler ist die FIRSTRICHTUNG. `chevron_roof_construction()` gibt jedem
Nebenfluegel bewusst die GEGENACHSE des Fluegels, an dem er haengt
(render-exterior.py:1890-1925, BFS ueber "teilt eine Kante"), mit der
Begruendung, ein Anbau laufe architektonisch quer zum Haupthaus. Dadurch
bekommt der Anbau ein eigenes Satteldach mit zwei eigenen Giebeln -- und das
liest sich als zweites Haus.

ERSTE DIAGNOSE WAR FALSCH und ist hier festgehalten: ich hatte die
Firstrichtung aus dem Seitenverhaeltnis der Bounding-Box abgeleitet und daraus
29,7 Grad gegen 19,7 Grad gerechnet -- also eine Neigungsdifferenz behauptet,
die es nicht gibt. Die Giebelwaende sagen die Richtung eindeutig; danach ist
die Neigung gleich. Korrigiert, bevor etwas gebaut wurde.

## REVISION 2026-10-08 — die Vorgabe oben war falsch verstanden

Rainer hat die .blend selbst geaendert (12:35) und gesagt "look at it then you
will understand". Gemessen aus seiner Fassung
(`exterior-satteldach-rainer-edit-2026-10-08-1235.blend`):

- `roof-pitch` Teil 0 reicht jetzt von y 964 bis **12550** -- EIN Dach ueber
  das ganze Haus, auch ueber den Anbau.
- Querschnitt in x: Traufe 574/2750, **First x=8165 / z=4810**, Traufe
  13818/2750. Der First ist von der Mitte des grossen Schenkels (x=7196) auf
  die **Westkante des Anbaus** gewandert.
- Die OSTflaeche laeuft bis y=12550 durch, die WESTflaeche hoert bei y=9174
  auf. Ueber dem Anbau ist das Dach also genau EINE Flaeche -- in derselben
  Ebene wie das Hauptdach. Das ist sein "Pultdach parallel zum anderen Dach,
  auf gleicher Hoehe".
- Das eigene Anbaudach ist weg (48-mm-Rest).

Ich hatte die Naht in **y** gesucht (y=8674). Gemeint war die in **x**. Daher
die drei Sackgassen davor; sie stehen unten als Beleg und sind erledigt.

Rainer, 2026-10-08, zur Neigung: "ist doch egal, aber es ist fast zu hoch".
Also: Firsthoehe NICHT uebernehmen, sondern aus der gespeicherten Neigung auf
der KURZEN Seite rechnen -- 2750 + 5653 x tan(18,3 Grad) = **4616 mm**, rund
200 mm niedriger als seine 4810. Ost 18,3 Grad, West 13,8 Grad, Traufe rundum
2750.

## Exact scope (REVIDIERT)

EIN asymmetrisches Satteldach ueber den GANZEN Grundriss, statt eines Dachs je
Fluegel:

1. Firstachse: die Achse, in die der Anbau das Haus verlaengert (hier y).
2. Firstlage: auf der Grundrisskante, an der der Anbau anfaengt, auf
   Wandaussenkante (hier x = 8238).
3. Firsthoehe: Traufhoehe + kuerzerer Schenkel x tan(Profilneigung).
4. Zwei Flaechen, je bis zur Traufe, jede gegen die Haelfte des Grundrisses
   plus Ueberstand geschnitten -- dieselbe Machart wie
   VERSATZ-WAND-ENDET-MIT-DEM-DACH-001.
5. Giebel und Fuellwaende folgen dem Schnitt, buendig mit der Wandaussenkante.
6. Der Anbau bekommt KEIN eigenes Dach und KEINE eigenen Giebel.

## Ueberholt: der urspruengliche Plan (Beleg, nicht mehr umzusetzen)

Im Chevron-Zweig: ein Nebenfluegel (jeder Fluegel ausser dem groessten)
bekommt statt eines Satteldachs ein PULTDACH mit

1. **gleicher Neigung** wie der Hauptfluegel (aus demselben Profil, weiter
   ueber `scale_profile_to_span()`),
2. **hoher Kante genau auf der Nahtlinie** -- der gemeinsamen Kante mit dem
   Fluegel, an dem er haengt. Nicht die Wandaussenkante, nicht um den
   Ueberstand versetzt,
3. **Traufe auf der Traufhoehe des Hauptdachs** (`WALL_TOP_Z`), damit die
   Trauflinie um das ganze Haus auf einer Hoehe laeuft,
4. **Fallrichtung** vom Haus weg.

Fuer `bungalow_040_31`: hohe Kante 3,803 m, Traufe 2,750 m, Neigung 18,3 Grad.

Gilt nur, wenn der Nebenfluegel GENAU EINE gemeinsame Kante mit einem anderen
Fluegel hat. Bei mehreren (Anbau zwischen zwei Schenkeln) gibt es keine
eindeutige Fallrichtung -- dort bleibt es beim heutigen Satteldach, und das
steht als offener Punkt im Roadmap.

## Files in scope

- `born2thrill-local-workbench/scripts/roof_profile.py`
  (`chevron_roof_construction` und das Pultdach je Nebenfluegel)
- `born2thrill-local-workbench/scripts/render-exterior.py`
  (Dachform je Fluegel bestimmen und uebergeben)
- `born2thrill-local-workbench/scripts/roof_profile.test.py` (nur Ergaenzungen)

## Explicitly out of scope

- `flachdach`, `walmdach`, `doppelpultdach` -- andere Formen, andere Wege
- Der Versatz-Zweig (VERSATZ-WAND-ENDET-MIT-DEM-DACH-001, gestern geaendert)
- Rechteckige Haeuser -- dort gibt es keinen Nebenfluegel
- Haeuser mit gezeichneten Firstlinien (`_vp_own_lines`): dort hat Rainer die
  Richtung selbst bestimmt und sie bleibt
- Die Fluegel-Zerlegung selbst (`decompose_rectangles`, `snap_wings_to_real_walls`)

## API, schema, and data-contract effects

Keine. Nur Geometrie in der erzeugten .blend.

## Acceptance criteria

An `bungalow_040_31`, satteldach:

1. `roof-pitch` hat genau EINE Firstlinie; der Anbau hat keinen eigenen First
   und keine eigenen Giebel.
2. Die hohe Kante des Anbaudachs liegt auf y = 8,674 m (Naht), Toleranz 10 mm.
3. Ihre Hoehe betraegt 3,803 m, Toleranz 20 mm.
4. Die Traufe des Anbaus liegt auf 2,750 m, dieselbe Hoehe wie die Traufe des
   Hauptdachs, Toleranz 10 mm.
5. Die Neigung beider Flaechen ist gleich, Toleranz 0,5 Grad.
6. Keine offene Wandoberkante (Strahlentest aus VERSATZ-WAND-ENDET-MIT-DEM-
   DACH-001 laeuft unveraendert durch).
7. Die uebrigen 23 Haeuser mit Chevron-Satteldach bauen weiter und werden
   vorher/nachher gemessen; keines verliert eine Dachflaeche.

## Tests and verification commands

Neu in `roof_profile.test.py`:
- `test_nebenfluegel_bekommt_pultdach`
- `test_hohe_kante_liegt_auf_der_nahtlinie`
- `test_traufe_auf_hauptdach_traufhoehe`
- `test_gleiche_neigung_wie_der_hauptfluegel`
- `test_anbau_zwischen_zwei_fluegeln_bleibt_satteldach`

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder
umgeschrieben.

Befehle:
- `python scripts/roof_profile.test.py`
- `python scripts/roof_wings.test.py`
- `python scripts/roof_wings_multi.test.py`
- Neubau nach SCRATCH, danach Geometrie-Dump gegen die Tabelle oben

## Protected and risky paths

`chevron_roof_construction()` ist seit 2026-09-29 die tragende Konstruktion
fuer Satteldach/Pultdach auf L-Grundrissen und hat mehrere gescheiterte
Vorgaenger. Ihre Kernzusage -- jede Fluegelkante liegt auf Hoehe 0, deshalb
braucht die Naht keine Verrechnung -- gilt fuer ein Pultdach mit hoher Kante
AUF der Naht NICHT mehr: dort ist die Kante auf 3,803 m statt 0. Die Naht
muss also ausdruecklich geschlossen werden (Wandstueck unter der hohen Kante),
sonst entsteht genau das Loch, das die Funktion bisher vermied. Das ist der
Hauptrisikopunkt und bekommt Kriterium 6.

## Rights, provenance, privacy, and security impact

Keiner.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

Nein. Reine Renderer-Geometrie, kein Veroeffentlichen, kein Versand. Gebaut
wird nach Scratch.

## Customer, email, database, deployment, and external effects

Keine.

## Repository baselines

- `born2thrill-local-workbench`, Branch `agent/furnished-render-and-annotation-schema`
- `roof_profile.py`, `render-exterior.py`, `roof_profile.test.py` sind in
  diesem Arbeitsbaum UNTRACKED -- Rollback ueber `*.before-anbau-pultdach`.

## Rollback

```
cd born2thrill-local-workbench/scripts
cp roof_profile.py.before-anbau-pultdach       roof_profile.py
cp render-exterior.py.before-anbau-pultdach    render-exterior.py
cp roof_profile.test.py.before-anbau-pultdach  roof_profile.test.py
```

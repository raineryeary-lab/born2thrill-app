# Versatzwand endet, wo das hohe Dach endet -- und das untere Dach bekommt dort seinen Ueberstand

Status: IMPLEMENTED (2026-10-07)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-07, an `german_catalog_review_bungalow_4_1_3_wb_105`
(Build von heute 13:14 auf E:): "es fehlt eigentlich der Ueberstand an der
unteren Pultdach deswegen geht die Wand hoch".

Am versetzten Pultdach steht auf 4,1 m Laenge eine Wand mit offener Oberkante
im Freien, und das untere Dach endet daneben mit einem 60-mm-Stummel statt mit
einer Traufe.

## Current evidence and behavior

Gemessen aus
`E:\born2thrill-local-workbench-data\corrections\german_catalog_review_bungalow_4_1_3_wb_105\renders\go-baseline\exterior-doppelpultdach-baseline.blend`
(Blender, Weltkoordinaten in mm):

| Objekt | x von | x bis | Breite |
|---|---|---|---|
| `roof-walls` (Versatzwand, OK 4300) | 1768 | 15927 | 14159 |
| `roof-pitch` hohe Flaeche | 2134 | 12166 | 10032 |

4127 mm Wand ohne Dach darueber. Der obere Schenkel des L endet laut `walls-0`
bei x = 11796; die Wand laeuft 4131 mm darueber hinaus.

Ueberstaende im selben Bau (`overhang` = 370 mm):

| Kante | Wand | Dach | Ueberstand |
|---|---|---|---|
| vorne y | 1535 | 1165 | 370 |
| rechts x | 15927 | 16297 | 370 |
| hinten y | 10671 | 11041 | 370 |
| hohe Flaeche ueber den Versatz | 6517 | 6017 | 500 |
| **untere Flaeche am Versatz** | **6517** | **6577** | **60** |

Dazu: die beiden Flaechen ueberlappen sich 560 mm in y (Teil 0 bis y = 6577,
Teil 1 ab y = 6017), und die Wandoberkante (4300) liegt 107 mm ueber der
Unterkante der hohen Flaeche (4193).

Beide Zahlen kommen aus zwei Zeilen in `render-exterior.py`
(VERSATZ-WHOLE-HOUSE-001-Zweig, ab Zeile 1492):

1. Zeile ~1670 -- das untere Dach wird immer 60 mm hinter der Versatzwand
   gekappt, unabhaengig davon, ob dort eine Wand steht:
   `_lo_end = _cw + (-0.06 if _high0 else 0.06)` und
   `_allowed = _halfplane(_allowed, _is_low_c, _lo_end)`.
2. Zeile ~1712 -- die Wand wird gegen den GANZEN Grundriss geschnitten
   (`_face_poly` aus `footprint`), die Daecher dagegen je gegen ihre eigene
   Haelfte (`_parts[...]`, um `overhang` aufgeweitet). Zwei verschiedene
   Schnittformen fuer eine Naht.

Ursache beider: das Profil ist EIN 2D-Schnitt, der ueber die volle Spannweite
gezogen wird. Bei einem L gibt es jenseits des oberen Schenkels keine hohe
Flaeche mehr -- der Schnitt wird trotzdem weitergezogen.

## Exact scope

Im `doppelpultdach`-Zweig von `render-exterior.py` (nur dort):

1. **Versatzwand endet mit dem hohen Dach.** Der Schnittkoerper fuer
   `roof-walls` wird im Bereich des Versatz-Sprungs nicht mehr aus dem ganzen
   `footprint` gebildet, sondern aus der Haelfte, auf der die hohe Flaeche
   liegt (`_parts[not _high0]`), auf die Wandaussenkante gesetzt. Ausserhalb
   davon behaelt die Wand die Hoehe der NIEDRIGEN Seite -- dort ist es ein
   gewoehnliches Pultdach, kein Versatz.
2. **Unteres Dach bekommt seinen Ueberstand, wo keine Wand steht.** `_lo_end`
   gilt nur innerhalb der Spanne, in der die Versatzwand tatsaechlich steht.
   Ausserhalb wird die untere Flaeche wie jede andere Traufe um `overhang`
   (370 mm) ueber die Wandaussenkante gefuehrt.
3. **Ueberlappung schliessen.** Die untere Flaeche endet unter der hohen; wo
   beide stehen, darf die Unterkante der hohen nicht unter die Wandoberkante
   fallen. Wandoberkante = Unterkante hohe Flaeche minus Dichtmass, statt
   fester `h - 0.10`.

## Files in scope

- `born2thrill-local-workbench/scripts/render-exterior.py` (nur der
  `_versatz_built`-Zweig, ca. Zeile 1492-1721)
- `born2thrill-local-workbench/scripts/roof_wings.test.py` (nur Ergaenzungen)
- NACHGETRAGEN 2026-10-07: `born2thrill-local-workbench/scripts/roof_wings.py`
  (nur Ergaenzungen: `halbebene`, `versatz_spanne`, `versatz_gilt_bei`). Der
  Plan nannte nur die Testdatei; die Entscheidung "wie weit reicht der Versatz"
  gehoert aber in eine reine Funktion, sonst ist sie ohne Blender nicht
  prueffbar. Keine bestehende Funktion in dieser Datei wurde angefasst.

## Explicitly out of scope

- `roof_profile.py` und die Profil-Aufloesung
- Jede andere Dachform (flachdach, walmdach, satteldach, pultdach)
- Der Chevron-/Wings-Zweig und `ROOF-SWEEP-CONSTRUCTOR-001`
- Rechteckige Haeuser (`is_rectangle`) -- dort gibt es den Fall nicht
- Die Dachform-Auswahl in der UI (`dachform/route.ts` kennt
  `doppelpultdach` gar nicht; eigener Befund, eigener Plan)

## API, schema, and data-contract effects

Keine. Nur Geometrie in der erzeugten .blend.

## Acceptance criteria

Gemessen an `4_1_3_wb_105`, doppelpultdach:

1. `roof-walls` reicht in x nicht weiter als `roof-pitch`s hohe Flaeche,
   Toleranz 10 mm. (heute: 3761 mm zu weit)
2. Die untere Flaeche steht dort, wo keine Versatzwand darueber steht,
   370 mm +/- 10 mm ueber die Wandaussenkante vor. (heute: 60 mm)
3. Keine Wandoberflaeche von `roof-walls` liegt offen -- jede Oberkante ist
   von einer Dachflaeche gedeckt oder liegt auf Traufhoehe der niedrigen Seite.
4. ZURUECKGEZOGEN 2026-10-07, falsch aufgestellt. Die Wandoberkante liegt
   107 mm ueber der Dachunterkante -- die Wand steckt also im Dachpaket, und
   genau so gehoert es. Haette man es "korrigiert", waere ein 30-mm-Schlitz
   zwischen Wandkopf und Dachunterseite entstanden. Die offene Oberkante im
   Bild kam vollstaendig aus Kriterium 1, nicht hieraus. Nicht geaendert.
5. Die beiden Flaechen ueberlappen sich in c nur unter der hohen Flaeche,
   nicht im Freien.
6. `3_5_1_b_145` und `4_3_1_wb_125` bauen weiter und bleiben bei ihren heutigen
   Massen -- Nachweis durch Vorher/Nachher-Dump derselben Objekte.

## Tests and verification commands

Neu in `roof_wings.test.py`:
- `test_versatzwand_endet_mit_dem_hohen_dach` -- L-Grundriss, Wandspanne <= Dachspanne
- `test_untere_flaeche_hat_traufe_wo_keine_wand_steht` -- 370 mm statt 60 mm
- `test_keine_offene_wandoberkante`
- `test_hohe_flaeche_liegt_ueber_der_wandoberkante`

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder umgeschrieben.

Befehle:
- `python scripts/roof_wings.test.py`
- `python scripts/roof_profile.test.py` (muss unveraendert gruen bleiben)
- Neubau der drei Haeuser nach SCRATCH (nicht ueber die zertifizierte
  Lieferung), danach Geometrie-Dump und Abgleich gegen die Tabellen oben.

## Protected and risky paths

`render-exterior.py` erzeugt die ausgelieferte Aussenansicht. Der
`doppelpultdach`-Zweig hat am 2026-09-29 und 2026-10-04 je einen Neubau
hinter sich; die heutigen Masse von `3_5_1_b_145` und `4_3_1_wb_125` sind der
Bezugspunkt und werden vorher weggeschrieben.

Gebaut wird in einen Scratch-Ordner. Die zertifizierte Lieferung auf E: wird
NICHT ueberschrieben, solange der Plan nicht abgenommen ist.

## Rights, provenance, privacy, and security impact

Keiner.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

Nein. Die Aenderung sitzt im Renderer hinter dem bereits abgenommenen
Korrektur-Plan; sie erzeugt keine neue Geometriequelle, veroeffentlicht nichts
und verschickt nichts. Gebaut wird nach Scratch.

## Customer, email, database, deployment, and external effects

Keine. Kein Commit, kein Push, kein Upload.

## Repository baselines

- `born2thrill-local-workbench`, Branch `agent/furnished-render-and-annotation-schema`, Base SHA `5be1a4e`
- Arbeitsbaum schmutzig (274 Eintraege, Renderer/Modell-Pipeline vom 2026-09-03).
  `render-exterior.py` ist davon NICHT betroffen und wird nicht aufgeraeumt.
- Datenwurzel ist `E:\born2thrill-local-workbench-data` (aus `.env.local`),
  nicht der gleichnamige Ordner unter `C:\dev\Floorplan-tools`.

## Rollback

KORREKTUR 2026-10-07: der Plan nannte `git checkout --`. Das geht nicht --
`render-exterior.py`, `roof_wings.py` und `roof_wings.test.py` sind in diesem
Arbeitsbaum UNTRACKED (`??`), git kennt keinen Vorzustand. Stattdessen liegen
Sicherungen nach der Hausregel `*.before-<vorhaben>` daneben:

```
cd born2thrill-local-workbench/scripts
cp render-exterior.py.before-versatz-wand-endet  render-exterior.py
cp roof_wings.py.before-versatz-wand-endet       roof_wings.py
cp roof_wings.test.py.before-versatz-wand-endet  roof_wings.test.py
```

Geprueft: der gesicherte Stand laeuft mit 53 Tests gruen (der neue mit 61 --
acht dazu, keiner entfernt, keiner abgeschwaecht).

Keine Datenaenderung, kein Migrationsschritt. Gebaut wurde ausschliesslich
nach Scratch; die zertifizierten Lieferungen auf E: sind unberuehrt.

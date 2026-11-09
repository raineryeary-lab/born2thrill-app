# Objektkarte im Codex-Auftrag

Status: IMPLEMENTED (Rainer, 2026-08-27, "ja")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Der Auftrag nennt Garderobe-, Stuff- und Sanitaerobjekte beim Namen, sagt aber
nirgends, WO sie liegen. Codex muss sie im Render suchen. Beweis aus der
Lieferung `german_catalog_review_bungalow_3_2_3_b_100_1` vom 2026-08-27: die
Garderobe (`garderobe-25`, Bauplan-Position x=4550, y=3246) landete in vier
Bildern an drei verschiedenen Stellen.

Der Auftrag bekommt deshalb eine **Objektkarte**: den Innenraum-Render mit
nummerierten Markern auf jedem genannten Objekt, dazu die passende
Nummernliste in `CODEX-AUFTRAG.md`.

## Current evidence and behavior

- `03-floorplan-warm-modern.png` und `04-floorplan-dark-modern.png`: an der
  Objektstelle nur ein geschlossener Schrank; eine erfundene Garderobenleiste
  an der Dielenwand neben dem Kuehlschrank, wo die `.blend` nichts hat (§2.8).
- `05-floorplan-soft-scandinavian.png` und `06-floorplan-classic.png`:
  Garderobe an der richtigen Stelle, aber sie ersetzt das offene Tuerblatt der
  Haustuer -- die Tuer ist im Bild verschwunden (§1.2).
- Ursache: ein aufgeschlagenes Tuerblatt sieht im Rohrender aus wie ein
  Schrankbrett. Ohne Lageangabe ist das nicht unterscheidbar.

## Repository baselines

Kein Git-Repository (`C:\dev\Floorplan-tools`, is a git repository: false).
Arbeitsstand = Dateisystem. Betroffene Dateien vor der Aenderung gesichert
unter `%TEMP%\claude\...\scratchpad\`.

## Exact scope

1. `scripts/make-codex-job.py`
   - Blender-Abfrage um die Kamera-Projektion erweitern: je genanntem Objekt
     die normierte Bildlage (u, v). Ein Blender-Lauf, nicht zwei.
   - Reine Hilfsfunktionen `_lage_zu_pixel()` und `_marker_liste()`.
   - `objektkarte()` zeichnet die Marker mit Pillow auf den vorhandenen
     `interior-*-baseline.png` und schreibt `OBJEKTKARTE-<stem>.png` in den
     go-baseline-Ordner. Fehlt Pillow oder der Render, wird die Karte
     ausgelassen und der Auftrag bleibt gueltig.
   - `codex-job.json` bekommt `object_map`, `CODEX-AUFTRAG.md` die
     Nummernliste und den Verweis auf die Datei.
2. `docs/CODEX-REGELN-4PLUS2.md`: §2.8 und §2.9 verweisen auf die Objektkarte;
   die Tuerblatt-Falle wird beim Namen genannt.
3. Neu: `scripts/make-codex-job.test.py`.

## Files in scope

- `scripts/make-codex-job.py`
- `scripts/make-codex-job.test.py` (neu)
- `docs/CODEX-REGELN-4PLUS2.md`

## Explicitly out of scope

- Renderer, Bauplan-Erzeugung, Upload, WordPress, Rechte-Gate.
- Neu-Rendern bestehender Haeuser.
- Die bereits gelieferten Bilder von `german_catalog_review_bungalow_3_2_3_b_100_1`.

## API, schema, and data-contract effects

`codex-job.json` (`zf-codex-job-v1`) bekommt das optionale Feld `object_map`.
Additiv; bestehende Leser brechen nicht. `CODEX-AUFTRAG.md` bekommt einen
Abschnitt. Kein Eingriff in Geometrie, Bauplan oder Katalog.

## Acceptance criteria

- Marker-Nummern sind stabil und deckungsgleich mit der Liste im Markdown.
- Die Karte liegt neben der `.blend` im go-baseline-Ordner.
- Ohne Pillow oder ohne Baseline-Render laeuft der Generator unveraendert
  durch und schreibt einen Auftrag ohne Objektkarte.
- Bestehende Auftraege lassen sich neu erzeugen, ohne dass ausser der neuen
  Sektion etwas anderes wird.

## Tests and verification commands

Neu: `python scripts/make-codex-job.test.py`
- `_lage_zu_pixel` spiegelt v korrekt (Blender misst von unten, Bilder von oben).
- `_lage_zu_pixel` klemmt Werte ausserhalb 0..1 nicht heimlich, sondern meldet sie.
- `_marker_liste` nummeriert in derselben Reihenfolge wie die Markdown-Liste.
- `render_markdown` nennt jede Markernummer genau einmal.
- Ohne Lagen entsteht keine `object_map` und der Auftrag bleibt gueltig.

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder umgeschrieben.

## Protected and risky paths

`make-codex-job.py` schreibt in den go-baseline-Ordner. Die Karte bekommt einen
eigenen Namen (`OBJEKTKARTE-*.png`) und darf keine Baseline ueberschreiben.
Der Lieferordner bleibt unberuehrt.

## Rights, provenance, privacy, and security impact

Keine. Die Karte entsteht aus dem eigenen Render des eigenen Bauplans.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder mailen,
ohne zu einer freigegebenen korrigierten Korpusreferenz zu passen?

**Nein.** Der Generator schreibt ausschliesslich Auftragsdateien in den
go-baseline-Ordner. Er ruft weder `publish-renders.py` noch `approve-plan.py`
auf, erzeugt keine Geometrie und keinen Katalogeintrag. Die Objektkarte ist
eine Kopie des bereits vorhandenen Baseline-Renders mit aufgezeichneten
Markern und traegt einen eigenen Dateinamen, den `publish-renders.py` nicht
als Lieferbild aufgreift, weil sie nicht im Lieferordner liegt.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

1. Marker je Netz. Ergebnis: 26 Marker, davon 7 fuer eine Dusche und 5 fuer
   ein Kochfeld -- die Kreise verdeckten einander und liessen das Duschbad
   wichtiger aussehen als die Garderobe. Verworfen zugunsten der Gruppierung
   auf `<stamm>-<nummer>`.
2. Gruppieren auf die ersten zwei Namenssegmente. Ergebnis: `kochfeld-13` und
   `kochfeld-ring` wurden zwei Marker uebereinander, weil die Teilbezeichnung
   dort VOR der Nummer steht. Verworfen zugunsten der Suche nach dem ersten
   rein numerischen Segment.

## Verification

- `python scripts/make-codex-job.test.py` -- 14 Tests, OK.
- Uebrige Python-Tests unveraendert gruen: comfyui-polish-exterior-rule,
  hausdaten (37), rechte, render-furnished-dollhouse, verify_render,
  go (4, mit gesetztem FLOORPLAN_WORKBENCH_DATA_DIR).
- Vorbestehend rot und nicht angefasst: `build-simplifier-render-plan.test.py`
  `test_door_hinge_and_swing_are_normalized_into_the_walls_frame`
  (KUECHENINSEL-DOORTEST-001, wartet auf Rainers Entscheidung).
- Am echten Haus erzeugt: 14 Marker, `OBJEKTKARTE-interior-modern-baseline.png`
  (2000 x 1500), Marker 3 sitzt auf `garderobe-25`.

## Rollback

Sicherungen im Scratchpad zurueckkopieren, `make-codex-job.test.py` loeschen,
Auftrag neu erzeugen.

## Unresolved questions

Keine.

## Approval record

Rainer, 2026-08-27: "ja" auf den Vorschlag "der Render mit nummerierten Markern
auf jedem `garderobe-` und `stuff-`Objekt, und im Auftrag die passende
Nummernliste".

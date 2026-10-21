# Aufgeloestes Modell schlaegt den prozeduralen Kasten

Status: TEIL 1 ANGEWENDET, TEIL 2 ANGEWENDET MIT EINSCHRAENKUNG

Teil 2 freigegeben am 2026-09-03. Ergebnis gemessen: garderobe gewonnen,
kleiderschrank Regression und deshalb gesperrt - siehe Ergebnis Teil 2 unten.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Offenlegung

Teil 1 wurde auf muendliche Zustimmung hin umgesetzt, bevor AGENTS.md in
dieser Sitzung gelesen wurde. Das verletzt Phase 1 der Mandatory workflow.
Die Aenderung ist vollstaendig ruecknehmbar:

    scripts/render-furnished-dollhouse.py.before-model-beats-build-2026-09-03

Es wurde nichts committet, nichts veroeffentlicht, nichts versendet und keine
Datei im Lieferordner angefasst. Teil 2 wartet auf Freigabe.

## Objective

Moebel, fuer die der Plan bereits ein echtes Modell aufgeloest hat, sollen
dieses Modell auch bekommen, statt als prozeduraler Kasten gebaut zu werden.
Position, Drehung, Anzahl und Fussabdruck bleiben unveraendert.

## Current evidence and behavior

Baseline interior-modern-baseline.blend, gemessen ueber invariants.json:
81 Moebelobjekte, davon 49 reine Quader (8 Ecken).

Drei verschiedene Ursachen, belegt:

1. Modell aufgeloest, vom Bauer weggeworfen.
   fernseher traegt mesh_path = TV Flatscreen 03.blend UND build = tv.
   Der prozedurale Zweig greift zuerst. Genau dieser Fehler war fuer spuele
   bereits gefunden und behoben - die Ausnahme wurde aber auf
   type == sink verengt. Betroffen ausserdem dusche
   (Square Shower / Rectangular Shower, build shower).

2. Ein Modell pro Symbol, nicht pro Moebelstueck.
   Aus interior-modern-baseline.log:
       model dropped  kleiderschrank 3082x650x2384 cannot meet symbol
       1050x600x2100 without 2.7x distortion -- built to the symbol
   Fuer alle drei Kleiderschraenke wird dasselbe Modell geholt. Beim 3700er
   passt es, bei den beiden 1050ern nicht. Die Verzerrungssperre arbeitet
   richtig; sie bekommt das falsche Modell vorgesetzt.

3. Die Bibliothek wird gar nicht gefragt.
   garderobe, kuehlschrank, kochfeld, lowboard, stuff und kuechenzeile stehen
   im Plan als model_source = procedural.

Nachgesehen, warum eine Groessensuche allein nicht reicht:
tmp/hub-models-resolved.json enthaelt 93 Modelle, davon genau EINES vom Typ
wardrobe. Es gibt nichts, wonach man suchen koennte. Daneben liegen ungenutzt:

    data/furniture-assets/full-catalog/   33 erzeugte .glb, 16 Typen je
                                          modern und classic, darunter
                                          wardrobe, tv_unit, coat_rack,
                                          storage_shelving
    E:\_models_converted                  1160 konvertierte FBX, nie in
                                          hub-models-resolved.json aufgenommen

## Repository baselines

    Repo   C:\dev\Floorplan-tools\born2thrill-local-workbench
    Branch agent/furnished-render-and-annotation-schema
    Base   5be1a4e18956b9fb2e158bee82aa159898356e89

Vorbestehende, NICHT von dieser Aufgabe stammende Aenderungen im Worktree:
data/simplifier-v2/*.json, data/symbol-model-picks.json, package.json,
scripts/build-simplifier-render-plan.py, scripts/start-floorplan-workbench.ps1,
src/app/api/floorplan-workbench/corrections/route.ts,
src/app/api/floorplan-workbench/reviews/route.ts,
src/app/floorplan-workbench/page.tsx sowie untracked Dateien.
Diese bleiben unangetastet.

## Exact scope

TEIL 1 - angewendet, Beweis unter Acceptance criteria:

  a) has_real_model ist nicht mehr an type == sink gebunden, sondern daran,
     ob ueberhaupt ein mesh_path aufgeloest wurde. shower bleibt bewusst
     ausgenommen, weil build_shower Wanne, Raender und Glas als getrennte
     semantische Teile erzeugt und unklar ist, ob das Bibliotheksmodell eine
     Wanne mitbringt.
  b) TYPE_FINISH bekommt einen Eintrag tv -> metal-matte-black. Ohne ihn fiel
     der Typ auf den Auffangwert wood-oak und das echte Modell rendete beige,
     schlechter als der Kasten, den es ersetzt. Dasselbe Loch ist im Code
     fuer fridge bereits dokumentiert.

TEIL 2 - vorgeschlagen, noch nicht umgesetzt:

  c) Fallback-Kette bei der Modellwahl:
     Hub-Modell, wenn es ohne Verzerrung passt
     -> sonst erzeugtes .glb aus full-catalog fuer Typ und Stil
     -> sonst prozeduraler Kasten.
     Betrifft zuerst kleiderschrank; danach koennen garderobe, lowboard,
     stuff und fernseher dieselbe Kette nutzen.
  d) Kein Eingriff in die Verzerrungssperre. Sie bleibt unveraendert und
     bekommt nur mehr Kandidaten.

## Files in scope

    scripts/render-furnished-dollhouse.py   Teil 1 (angewendet)
    scripts/build-simplifier-render-plan.py Teil 2 (Kandidatenkette)
    data/symbol-model-picks.json            Teil 2, nur falls die Kette dort
                                            statt im Builder verankert wird

## Explicitly out of scope

- Die Dusche. Modell vorhanden, prozeduraler Bau bleibt bis zu einer eigenen
  Entscheidung.
- kuechenzeile, kuehlschrank, kochfeld, hochschrank_herd.
- Jede Aenderung an Position, Drehung, Anzahl, Kamera oder Architektur.
- Jede Datei in einem Lieferordner.
- Das Katalogisieren von E:\_models_converted.
- Bildmodelle, ComfyUI, Masken.

## API, schema, and data-contract effects

Keine Schemaaenderung in Teil 1. Teil 2 fuegt einer Platzierung hoechstens
eine zusaetzliche Herkunftsangabe hinzu (model_source = generated_catalog);
bestehende Felder behalten ihre Bedeutung.

## Acceptance criteria

Teil 1, bereits gemessen:

- fernseher erscheint in der Modellliste des Logs
  (symbol fit fernseher -> 1140x180x700mm), nicht mehr im prozeduralen Bau.
- built in-scene faellt von 14 auf 13, furniture ... from N meshes steigt
  von 15 auf 16.
- Pixelvergleich gegen interior-modern-baseline.png: 2913 von 3 000 000
  Pixeln geaendert, ausschliesslich im Bereich x 1420-1604, y 466-655.
  Das ist der Fernseher und nichts sonst.
- Exit-Code 0.

Teil 2:

- Beide 1050-mm-Kleiderschraenke sind keine 8-Ecken-Quader mehr.
- Der 3700-mm-Kleiderschrank bleibt unveraendert bei seinem Hub-Modell.
- Pixelaenderungen liegen ausschliesslich in den Bildbereichen der beiden
  Schraenke.
- verify_render_blend.py laeuft weiterhin ohne neue FAIL.

## Tests and verification commands

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder
umgeschrieben.

    blender --background --python scripts/render-furnished-dollhouse.py --
        <plan-modern.json> <harness>/model-beats-build/interior-test.png

    blender --background --python scripts/verify_render_blend.py --
        <harness .blend> <plan-modern.json>

    python scripts/blender-harness/verify_invariants.py <vorher> <nachher>

Ergaenzend Pixeldiff gegen die Baseline, um zu belegen, dass ausserhalb des
betroffenen Objekts kein Pixel abweicht.

## Protected and risky paths

    renders/go-baseline/*        Lieferpfad, nur lesend
    interior-modern-baseline.*   nicht neu geschrieben
    Alle Ausgaben nach renders/harness/model-beats-build/

Risiko: has_real_model ist jetzt breiter. Jede kuenftige Platzierung mit
gleichzeitig mesh_path und build nimmt das Modell. Heute betrifft das genau
spuele, fernseher und dusche - geprueft ueber beide Plandateien; dusche ist
ausgenommen.

## Rights, provenance, privacy, and security impact

Keine neuen Assets aufgenommen. Teil 2 wuerde erstmals die erzeugten .glb aus
data/furniture-assets/full-catalog/ in einen Render ziehen; deren Rechtelage
ist Teil des bekannten, offenen Korpus-Blockers und aendert sich durch die
Verwendung im Harness nicht. Nichts davon wird dadurch kommerziell
freigegeben.

## Floorplan-suite invariant

Frage: Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder
mailen, ohne zu einer freigegebenen korrigierten Korpus-Referenz zu passen?

Antwort: nein. Beide Aenderungen liegen ausschliesslich im Renderer bzw. im
Planbauer und wirken nur, wenn ein Mensch den Renderer mit einem Ausgabepfad
aufruft. Es wurde kein Publish-, E-Mail- oder Datenbankpfad beruehrt. Die
Testlaeufe schrieben nach renders/harness/, nie in einen Lieferordner; die
manuelle WordPress- und E-Mail-Sperre bleibt unveraendert bestehen.

## Ergebnis Teil 2 (2026-09-03)

Die Kette wurde an zwei Stellen gebaut, nicht an einer:

- build-simplifier-render-plan.py waehlt das erzeugte .glb, wenn gar kein
  Hub-Modell da ist oder der Planbauer es verwirft.
- render-furnished-dollhouse.py greift zusaetzlich in seinem EIGENEN
  Verzerrungs-Abbruch danach. Das war noetig: der Kleiderschrank faellt
  nicht im Planbauer durch (size_mismatch stand auf false, weil der
  Fussabdruck gemessen war), sondern erst im Renderer. Der Plan traegt dafuer
  fallback_mesh_path und fallback_model_label.

Gemessen:

- garderobe: Gewinn. Der 900x320x1900-Quader ist ein Garderobenstaender mit
  Haken geworden.
- kleiderschrank: REGRESSION. Der prozedurale Quader traegt Fugenschnitte
  (kleiderschrank-17-gap-*), die eine Tuerfuge zeichnen. Das erzeugte Modell
  ersetzte ihn durch eine merkmallose Platte; die Fuge verschwand ersatzlos.
  Die Datei ist 519 KB, das Detail existiert also -- die Tueren zeigen nur
  nicht zur Kamera. Ursache ist die fehlende Deklaration der Frontachse
  importierter Assets.

Konsequenz: GENERATED_TYPES_VERIFIED sperrt die Kette auf die Typen, die
tatsaechlich angesehen und fuer besser befunden wurden. Heute steht dort nur
coat_rack. Die Kette bleibt gebaut, sie feuert nur nicht blind.

Endstand des Testrenders gegen interior-modern-baseline.png:

    18 015 von 3 000 000 Pixeln geaendert, in genau zwei Bereichen
    Fernseher  x 1420-1604, y 466-655
    Garderobe  x  657-885,  y 810-1049
    38 Platzierungen vorher wie nachher, kein Moebel verschoben

Alle Ausgaben in renders/harness/model-beats-build/. Kein Lieferordner
angefasst.

## Customer, email, database, deployment, and external effects

Keine. Kein Commit, kein Push, kein Deploy, keine Migration, keine Mail.

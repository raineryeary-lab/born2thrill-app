## Audit-Ergebnis

Der Ablauf ist noch keine durchgängige Zustandsmaschine. Die `/haus`-Seite zeigt sechs Schritte, aber mindestens vier verschiedene Wahrheiten entscheiden über den Fortschritt:

- Dateiexistenz bzw. `.blend`-Anzahl
- `delivery-manifest.json`
- lokale Corpus-/Rechte-Ledger
- WordPress-Katalogfelder und Bild-Flags

Diese Wahrheiten werden weder zusammengeführt noch überall in derselben Reihenfolge geprüft. Besonders kritisch: Der normale `/haus`-Build verwendet nicht die Korrektur-Revision, auf der der Möbeleditor arbeitet.

## 1. Lückenliste – wichtigstes zuerst

### P0 – Korrektur/Möbel und Build können verschiedene Geometrien verwenden

`/haus` lädt Möbel aus der neuesten Korrektur-Revision, aber „Bauen“ ruft lediglich `go.py <plan>` auf ([pipeline/route.ts](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/api/floorplan-workbench/pipeline/route.ts:131)). `go.py` startet `run_project.py` ohne `--corrected` ([go.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/go.py:191)). Der korrigierte Buildpfad ist nur über das explizite Argument erreichbar ([run_project.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/run_project.py:413)).

Folge: Rainer kann eine Revision prüfen, darauf möblieren und danach aus der ursprünglichen Annotation bauen. Die vorhandene Staleness-Route löst das nicht; sie vergleicht Annotation gegen Revision, steuert aber nicht die Buildquelle.

Erforderlich: Genau eine `active_geometry_revision` pro Haus. Möbel, Build, Zertifikat und Codex-Auftrag müssen dieselbe Revision-ID und denselben `geometry_hash` tragen.

### P0 – Die Hausliste kann veraltete oder unvollständige Häuser als fertig zeigen

Die Zustandsroute prüft nur:

1. Maßstab,
2. ob irgendeine `.blend` existiert,
3. WordPress-Bilder/`approved`.

Bei `catalogue.images > 0 && approved === "ja"` wird sofort `fertig` gesetzt ([state/route.ts](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/api/floorplan-workbench/state/route.ts:163)). Nicht geprüft werden:

- `delivery-manifest.json`
- `built_hash()`
- aktueller Annotation-/Sidecar-Hash
- Möbel-Fingerprint
- Toolchain-Hash
- Artefaktprüfsummen
- Korrektur-Revision
- lokale Corpus-Rechte
- ob wirklich jedes WordPress-Bild freigegeben ist

Damit kann ein nachträglich geändertes, neu möbliertes oder beschädigtes Haus weiterhin `fertig` bleiben.

### P0 – Rechtefreigabe kann an eine alte oder ungeprüfte Lieferung gebunden werden

`approve-plan.py` liest beim Freigeben nur die Existenz des Manifests und dessen deklarierte Artefaktzahl ([approve-plan.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/approve-plan.py:77)). Es verwendet nicht `built_hash()` und prüft nicht, ob Zertifikat, Annotation, Möbel und Toolchain noch zusammenpassen.

Noch problematischer: Ohne Lieferung wird nur ein Hinweis ausgegeben; die Freigabe wird trotzdem gespeichert und erhält `quality_status: not_built` ([approve-plan.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/approve-plan.py:207)). Danach kann die `/haus`-Pipeline unmittelbar `freigeben.py` starten ([pipeline/route.ts](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/api/floorplan-workbench/pipeline/route.ts:143)).

Das Gate muss fail-closed sein: keine Rechte-/Kundenfreigabe ohne frische zertifizierte Lieferung und vollständig geprüften Bildsatz.

### P0 – Codex-Rückgabe ist weder registriert noch validiert

`codex-job.json` beschreibt `required_outputs`, SHA-256 und Zustände, aber es gibt keinen Intake-Schritt, der zurückgegebene Dateien dagegen prüft. `go.py --hochladen` nimmt schlicht den Unterordner mit dem jüngsten Bild ([go.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/go.py:134)).

Dadurch können hochgeladen werden:

- partielle Codex-Ergebnisse
- Dateien eines alten Jobs
- ein beliebiger jüngerer Korrekturordner
- Baselines statt finaler Bilder
- Bilder ohne passendes `catalog.json`
- Bilder mit nicht geprüftem SHA-256 oder `state`

Erforderlich ist ein expliziter „Codex-Rückgabe prüfen“-Schritt, der den Job auf `complete` setzt und einen Bildlieferungs-Manifest erzeugt.

### P1 – Frisch erzeugter Codex-Auftrag bleibt im Tab unsichtbar

Der Auftrag wird nur beim Eintritt in den Codex-Tab geladen ([page.tsx](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/haus/page.tsx:334)). „Auftrag schreiben“ erzeugt die Dateien, lädt `/auftrag` danach aber nicht erneut ([page.tsx](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/haus/page.tsx:351)).

Rainer muss den Tab verlassen und wieder öffnen, bevor Text und `.blend`-Buttons erscheinen.

### P1 – Bilder aktualisieren sich nach Build und Upload nicht

Lokale und Online-Bilder werden nur bei Änderung von `plan` geladen ([page.tsx](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/haus/page.tsx:308)). Nach „Bauen“ oder „Hochladen“ wird zwar die Hausliste neu geladen, aber nicht der Bilderbestand.

Rainer klickt auf „Bilder“ und kann weiterhin den alten React-State sehen, bis er das Haus wechselt oder die Seite neu lädt.

### P1 – Der Bilder-Tab zeigt nicht die lokalen Codex-Finals

Der jüngste Fix listet ausschließlich `renders/go-baseline` ([publish/route.ts](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/api/floorplan-workbench/publish/route.ts:142)). `go.py` lädt dagegen den jüngsten Render-Unterordner hoch, beispielsweise `codex-final-*` ([go.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/go.py:137)).

Damit sind genau die Bilder, die vor dem Upload geprüft werden sollten, im lokalen Bilder-Tab nicht sichtbar.

### P1 – Mehrere sichtbare Zustände sind tote oder unerreichbare Zustände

`korrektur_noetig` und `bilder_hochladen` stehen in der Zustandsliste ([state/route.ts](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/api/floorplan-workbench/state/route.ts:24)), werden aber in keiner Verzweigung gesetzt.

Es fehlen außerdem eigene Zustände für:

- Zeichnung gespeichert, aber keine aktive/approved Revision
- Möbel fehlen
- Möbel auf fremder/veralteter Geometrie
- Build veraltet oder Zertifikat ungültig
- Build fehlgeschlagen
- Codex-Auftrag fehlt/veraltet
- Codex-Rückgabe unvollständig
- Rechte blockiert
- WordPress nicht erreichbar

### P1 – `geometrieFremd` wird berechnet, aber nie angezeigt oder geblockt

Die Staleness-Route erkennt ausdrücklich, dass Möbel ohne Revision auf einer anderen Geometrie stehen können ([staleness/route.ts](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/api/floorplan-workbench/staleness/route.ts:108)). Die Seite typisiert und zeigt aber nur `veraltet`, `moebel` und `grund` ([page.tsx](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/haus/page.tsx:172)).

Der wichtigste Warnfall der Route verschwindet somit vollständig.

### P1 – Erfolgreiches Speichern schaltet Tabs weiter, aber nicht den autoritativen Zustand

Annotator und Möbeleditor setzen lediglich den aktiven Tab ([page.tsx](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/haus/page.tsx:203)). Die Hausliste wird nicht neu berechnet, und es wird kein nächstes Gate geprüft. „Weiter mit Bauen“ erscheint selbst dann, wenn Revision, Maßstab, Dachform oder Möbelgeometrie noch blockieren.

### P2 – Maßstab hat zwei Wahrheiten

Die Hausliste liest nur `annotations.floor_scale` ([state/route.ts](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/api/floorplan-workbench/state/route.ts:137)). Build und Aktualitätsprüfung akzeptieren alternativ `gebaeudemass.json` ([batch-build.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/batch-build.py:78)).

Ein tatsächlich baubares Haus kann deshalb in der Liste als `vermessung_noetig` stehen.

## 2. Regel-Widersprüche

### Zustandsmaschine

- „Fertig“ laut Kommentar: alle Bilder freigegeben und Plan approved.
- „Fertig“ im Code: `catalogue.images > 0 && approved === ja`; einzelne `send`-Flags werden wegen des frühen Rücksprungs nicht geprüft.
- WordPress-Ausfall wird als `warten_auf_codex` bezeichnet ([state/route.ts](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/api/floorplan-workbench/state/route.ts:167)), obwohl die Handlung ausdrücklich „nicht Codex“ lautet.
- Lokales Corpus-Ledger und WordPress-Approval können unabhängig widersprechen; die Hausliste zeigt ausschließlich WordPress.

### Staleness

Drei Definitionen existieren:

- `/staleness`: neueste Revision gegen heutigen `geometry_hash`
- `go.py ist_aktuell`: `annotation_state == built_hash`
- Zertifikat: gespeicherte Annotation-, Sidecar-, Möbel-, Toolchain- und Artefakthashes

Nur `built_hash()` ist annähernd lieferungsbezogen. `/staleness` sagt lediglich etwas über Revision versus Annotation; es beweist nicht, dass die `.blend` aktuell ist. Die Hausliste verwendet keine der beiden Prüfungen.

Zusätzlich nimmt `/staleness` einfach die lexikalisch letzte Revisionsdatei, unabhängig von `draft/approved/rejected` ([staleness/route.ts](C:/dev/Floorplan-tools/born2thrill-local-workbench/src/app/api/floorplan-workbench/staleness/route.ts:40)).

### Vier-Stile-Vertrag gegen `models_locked`

Der Vier-Stile-Vertrag verlangt vier Präsentationsstile pro Interior und erlaubt definierte Material-, Farb-, Licht- und Garderobenänderungen ([four-interior-style-contract-v1.md](C:/dev/Floorplan-tools/born2thrill-local-workbench/plans/four-interior-style-contract-v1.md:7)).

Der reale Generator verlangt nur ein Bild pro `.blend` ([make-codex-job.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/make-codex-job.py:53)) und verbietet jede Material- oder Objektänderung ([make-codex-job.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/make-codex-job.py:150)). Der Plan steht noch auf `PROPOSED`, also ist der Vier-Stile-Vertrag im echten Workflow nicht umgesetzt.

### „Resumable/idempotent“ gegen tatsächliches Codex-Job-Verhalten

Der Docstring behauptet, bestehende passende Jobs blieben unangetastet. Tatsächlich erzeugt jeder Klick erneut:

- `attempt: 1`
- ausschließlich `pending`-Outputs
- eine neue `created_at`
- denselben tagesbasierten `job_id`

und überschreibt beide Jobdateien ([make-codex-job.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/make-codex-job.py:125), [make-codex-job.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/make-codex-job.py:222)). Rückgabestatus geht verloren.

### WordPress-Freigabe gegen Rechte-Gate

- `publish-renders.py --send` prüft das Corpus-Ledger fail-closed.
- Die `/haus`-Pipeline verwendet diesen Pfad nicht für die Freigabe, sondern `approve-plan.py` gefolgt von `freigeben.py`.
- `freigeben.py` selbst prüft kein Ledger.
- `approve-plan.py` prüft Herkunftsrechte, aber nicht die Frische der Lieferung.
- Die Seite bietet keinen expliziten `--rechte-bestaetigt`-Override; bei widersprechendem Provenance-Nachweis endet der Workflow ohne sichtbaren Lösungsweg innerhalb der Seite.

### Korrekturstatus gegen Buildstatus

Der Codex-Auftrag übernimmt `correction_status` lediglich als Metadatum ([make-codex-job.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/make-codex-job.py:131)). Weder Job-Erzeugung noch normaler Build verlangen `approved`; `draft` oder Annotation-Proof können daher bis Codex und WordPress gelangen.

## 3. Ein widerspruchsfreier Workflow

| Schritt | Eingang | Einziges Gate | Ausgang | Sichtbarer Zustand |
|---|---|---|---|---|
| Zeichnen | Vorlage + Annotation | alle Geschosse, Maßstab aus gemeinsamer Loader-Funktion, Dachform, valide Geometrie | unveränderliche Revision mit `geometry_hash`, ausdrücklich approved | `zeichnung_pruefen` / `moebel_bereit` |
| Möbel | exakt die approved Revision | Editor-Geometriehash = aktive Revision; Speichern erfolgreich | Möbelmanifest mit Revision-ID und Fingerprint | `moebel_bearbeiten` / `bau_bereit` |
| Bauen | Revision + Möbelmanifest | beide Hashes aktuell | atomare Lieferung; alle erwarteten `.blend`; beide Verifier; Manifest | `baut`, `bau_fehlgeschlagen` oder `codex_bereit` |
| Bilder prüfen | zertifizierte Lieferung | alle lokalen Baselines sichtbar und menschlich akzeptiert | lokale Reviewentscheidung | `bilder_pruefen` / `codex_bereit` |
| Codex | zertifizierte Lieferung | Job bindet Manifest- und Artefakthashes | Vier-Stile-Job | `warten_auf_codex` |
| Codex-Rückgabe | Dateien + `catalog.json` | exakt alle Outputs, Hashes, Styles, Herkunft und QC vollständig | Bildlieferungsmanifest `complete` | `bilder_final_pruefen` |
| Hochladen | vollständiges Bildlieferungsmanifest | keine Fremd-/Baseline-Auswahl nach mtime | hochgeladener, noch nicht freigegebener Satz | `warten_auf_freigabe` |
| Freigeben | frische Lieferung + Bildsatz | lokale Rechtefreigabe stimmt mit aktuellem Annotation-/Revision-/Lieferhash überein; alle Bilder geprüft | WordPress `send=true`, Plan approved | `fertig` |

Geordnete kleine Baupläne:

1. Eine serverseitige `deriveHouseState(plan)`-Funktion als einzige Wahrheit; UI, Batch und Buttons benutzen sie.
2. `active approved revision` festlegen und `/haus`-Build zwingend mit dieser Revision starten.
3. Manifestprüfung aus `built_hash()` in eine gemeinsam nutzbare Bibliothek ziehen.
4. Codex-Intake mit Vier-Stile-Vertrag, vollständiger Rückgabeprüfung und unveränderlichem Jobstatus bauen.
5. Bilder-Tab auf alle relevanten lokalen Lieferordner erweitern und nach jeder Aktion neu laden.
6. Rechte, Qualitätsfreigabe und WordPress-Release als drei getrennte, sichtbare Gates modellieren.
7. Tote Zustände entfernen; stattdessen ausschließlich Zustände verwenden, die aus den Gates ableitbar sind.

Wegfallen sollten: `.blend`-Anzahl als Fertigkeitsaussage, „jüngster Ordner per mtime“, bloße Zertifikat-Existenz, lexikalisch „neueste“ Revision und getrennte Maßstabsloader.

Keine Dateien wurden geändert und keine externen Aktionen ausgeführt. Der nächste einschlägige Roadmap-Folgepunkt ist gemäß [ROADMAP.md](C:/dev/Floorplan-tools/born2thrill-app-repo/plans/ROADMAP.md:102) Plan 2 der Pose-Vertragsreihe; für den hier festgestellten End-to-End-Workflow und den vorgeschlagenen Vier-Stile-Vertrag existiert dagegen noch kein genehmigter, zusammenführender Implementierungsplan.

---

## In derselben Nacht behobene Instanzen dieser Fehlerklassen

1. **Treppen-Quelle im Moebel-Editor** (P0-1-Instanz, onehalfstorey_029):
   die Ansicht zeigte Raeume aus der Zeichnung, die Treppe aber aus dem
   GENERIERTEN Korrektur-Dokument (andere Groesse, andere Position,
   anders normiertes Gebaeude). Fix: geometry_only() liefert die Treppe
   jetzt aus annotation_stair_core() (dieselbe Quelle wie der Render),
   der Embed zeigt sie statt document.shared_stair_core. Verifiziert im
   gerenderten SVG (Lage identisch zur Zeichnung, U-Pfad).
2. **Schiefe Treppenkontur**: annotation_stair_core() orthogonalisiert
   die Lauflinie (Segmente < 20 Grad neben der Achse werden gerade) und
   offsetiert Ecken per Gehrung statt gemittelter Normale (der alte Weg
   zog jede 90-Grad-Ecke um sqrt(2) ein). Verifiziert: alle 8 Kanten der
   gerenderten Kontur bei 0.0 Grad Achsabweichung.
3. **Shift-Klick im Annotator** (Rainer-Vorschlag): bei gedrueckter
   Shift-Taste rastet der neue Zeichenpunkt exakt waagerecht/senkrecht
   zum vorherigen ein (dominante Achse in Pixeln). annotate.js +
   Cache-Bust 20260822-234500.
4. **Prototyp-Groesse fuer alle Instanzen** (onehalfstorey_029, "Bau
   fehlgeschlagen"): drei Kleiderschraenke mit gemessenen 2400/2000/1900mm
   renderten alle in der Groesse der ERSTEN Platzierung (geteiltes
   proto.data) -- R0 schlug zu Recht an, konnte aber selbst nur EINE
   Erwartung pro Asset ausdruecken (letzte gewinnt). Beide Seiten
   gefixt: Instanz bekommt bei abweichender Zielgroesse eine private,
   passend skalierte Mesh-Kopie (gleiche Loesung wie beim Spiegeln) und
   stempelt symbol_w_mm/symbol_d_mm als Objekt-Property; R0 prueft jede
   Instanz gegen ihren eigenen Stempel. go.py onehalfstorey_029: fertig,
   zertifiziert. Dritte Instanz der Klasse "Asset-weiter Zustand auf
   Instanz-Daten" heute (Spiegel, Groesse; RENDER-SOFA-ROTATION offen).
5. **Balkon-Elemente wurden von NICHTS gelesen** (onehalfstorey_029): der
   Annotator kann type "balcony" zeichnen, kein Skript konsumierte den
   Typ. Jetzt: Plan-Builder reicht floors[n].balconies durch
   (frame-konvertierte Polygone), render-exterior.py baut Platte
   (200mm, Oberkante = Geschossboden) + 900mm-Bruestung auf allen Kanten,
   die nicht binnen 300mm an einer Aussenwand liegen. Render verifiziert
   (Bild an Rainer). Interior-Darstellung des Balkons: Folgearbeit.
6. **Dachform pro Stil war nur per CLI setzbar**: roof_type_modern/
   _classic existieren seit 20.08. (dachform.py -> gebaeudemass.json,
   Builder liest pro Stil). Neu: dachform-Route (GET/POST, schreibt ueber
   dachform.py selbst) + zwei Dropdowns im Bauen-Schritt. Round-trip auf
   onehalfstorey_029 verifiziert.
7. **Geschoss-Massing** (onehalfstorey_029, "no dumbass"): render-exterior
   extrudierte den ERDGESCHOSS-Umriss ueber die volle Haushoehe -- ein
   Obergeschoss, das nur ein Rechteck ueber einem groesseren Erdgeschoss
   ist, wurde als voller Klotz gebaut; die begehbare EG-Dachflaeche
   existierte nicht. Jetzt: jedes Geschoss baut seine eigene Aussenhuelle
   aus SEINEN Waenden (eigene Hoehenlage, eigene Eckpfosten, Union pro
   Geschoss), Geschossdecke deckt Vorspruenge als Flachdach, das Hauptdach
   sitzt auf dem OBERSTEN Umriss, Oeffnungen haengen per Id an der Wand
   ihres eigenen Geschosses (das geometrische Umhaengen entfiel). Der
   Balkon ist jetzt korrekt eine TERRASSE: duenner Belag + Bruestung auf
   der Geschossdecke, keine haengende Platte. Dabei gefundener Klassiker:
   die Oeffnungsschleife ueberschrieb `base_z` der Geschossschleife (jede
   Wand nach einer Fensterwand stand um eine Bruestungshoehe zu hoch --
   "schwebendes Erdgeschoss", per Objekt-Bbox gemessen). Verifiziert:
   029 modern/classic zertifiziert (go: fertig), bungalow_039-Regression
   (eingeschossig) unveraendert korrekt.
8. **bungalow_036 verworfen** (Rainer, 2026-08-23: "delete that house it
   is identical to one we just finished" -- Raumprogramm gegen
   bungalow_039 geprueft: identisches 7-Raum-Bungalow-Layout; online lag
   nichts). Nicht geloescht, sondern nach Suite-Konvention VERSCHOBEN:
   floorplan-simplifier/projects/_verworfen-2026-08-23/bungalow_036 und
   E:\...\corrections\_verworfen-2026-08-23\bungalow_036. Wiederherstellen
   = beide Ordner zurueckschieben. Der WordPress-Katalogeintrag (Zeile im
   Grundriss-Datensatz, ok=offen, keine Bilder) blieb unberuehrt.
9. **Geschosse nicht registriert** (onehalfstorey_029, Rainer 2026-08-23:
   "the floors are not properly aligned"): jedes Geschoss war auf seinem
   eigenen Bild eigen kalibriert (EG 12.686, OG 12.430 m/Einheit, eigener
   Ursprung); gestapelt stand das OG 463mm innerhalb der EG-Ostlinie und
   150-600mm UEBER den anderen Seiten. Fix: RegisteredFrame +
   frame_for_level() im Plan-Builder -- Obergeschosse gehen per Affin-
   Abbildung aus den Annotator-Ausrichtungsmarken (zwei Diagonalecken je
   Geschoss) in den EG-Frame, danach rasten ihre Aussenkanten binnen
   350mm auf die EG-Aussenwandlinien (Ziel = EG-Mittellinie um eine halbe
   Wandstaerke nach innen, weil EG-Raeume bis zur Aussenkante gezeichnet
   sind und OG-Waende nach AUSSEN geschoben werden). Ergebnis gemessen:
   OG-Aussenwand-Mittellinien 2818/11506 x 689/10205 == EG-Hauptkoerper,
   Vorsprung bleibt wie gezeichnet. Gilt fuer Bau, Moebel-Editor
   (geometry_only) und Moebel-Ausdehnung gleichermassen (ein
   frame_for_level). Moebel des OG per scripts/moebel-registrieren.py
   einmalig mitverschoben (Marker floor_registration, Sicherung
   .vor-registrierung). go: fertig, Tests 11/11. Haeuser OHNE Marken
   bleiben unregistriert (Frame wie bisher) -- Marken setzen = fertig.
10. **HARTE REGEL Geschoss-Ausrichtung** (Rainer, 2026-08-23: "make this a
    rule so we cannot go forward without the alignment"): frame_for_level()
    verweigert (SystemExit) jedes Obergeschoss ohne zwei Ausrichtungsmarken
    auf BEIDEN Geschossen -- damit kein Bau, kein Moebel-Editor, keine
    Ausdehnung; go.py meldet es als "Ausrichtung fehlt -- im Annotator ...
    (Floor alignment)" statt "Bau fehlgeschlagen"; state-Route kennt den
    Zustand ausrichtung_noetig. Tests: 3 neue (14/14 gruen). Korpus-Stand:
    98 mehrgeschossige Haeuser, 5 mit Marken (020, 029, 007, 027, 030), 93
    ohne (fast alle auch ohne Massstab). Ergaenzend: workbench_furniture()
    verweigert Obergeschoss-Moebel ohne Registrierungsmarker mit dem
    genauen Befehl (moebel-registrieren.py) -- twostorey_030 scheiterte
    genau daran, nach Migration (15 Moebel) zertifiziert: fertig.

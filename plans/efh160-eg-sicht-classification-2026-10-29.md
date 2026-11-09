# EFH160: strukturelle EG-Sicht-Objekte korrekt klassifizieren

Status: COMPLETE — Nutzerfreigabe am 2026-10-30: Ja, gezielten Fix umsetzen.
Policy: ZF-AGENT-WORKFLOW-v1.0.0

## Objective
Den falschen Möbel-Sichtnachweis für strukturelle Kopien des darunterliegenden Geschosses beseitigen, ohne Bildfehler oder fehlende Möbel zu akzeptieren.

## Current evidence and behavior
make-codex-job.py _stamm() verwendet das erste Namenssegment. EG-Sicht-stair-step-7.001 wird dadurch als Möbeltyp EG statt Architekturtyp stair erkannt. rolle_fuer() schließt stair/floor/ground bereits aus, erreicht diese Klassifikation hier aber nicht. Die aktuelle DG-Karte enthält zehn solche Architekturmarker. Eine 800x600-Erstflächen-Strahlprüfung der frisch geöffneten Blend hat für fünf Stufen null Treffer ergeben; das ist unterstützende Verdeckungsevidenz, kein vollständiger Transparenznachweis. Originalreport: Temp/efh160-dg-visibility.json.

## Repository baselines
born2thrill-local-workbench, branch agent/furnished-render-and-annotation-schema, HEAD 5be1a4e18956b9fb2e158bee82aa159898356e89. 17 vorbestehende geänderte Dateien und weitere unversionierte Dateien bleiben erhalten. make-codex-job.py ist nicht als geändert aufgeführt. Status und Diffstat wurden am 29.10. gelesen.

## Exact scope / files
scripts/make-codex-job.py: EG-Sicht-Präfix ausschließlich für die Typklassifikation abziehen; originale Objektnamen und Meshzählung erhalten. _inventar nutzt dieselbe Klassifikation. Keine pauschale Ausnahme für EG-Sicht-Möbel.
Neue additive Testdatei scripts/make-codex-job-eg-sicht.test.py. Bestehende Tests unverändert ausführen.
Nur für EFH160 Auftrag/Objektkarten/Vertrag aus unveränderten Quellen neu erzeugen; vorher bestehende erzeugte Auftragsdateien sichern. Anschließend reguläre Bildprüfung und bereits autorisierter Upload nach vollständigem Bestehen.

## Out of scope
lieferung-pruefen.py, Publikationsregeln, bestehende Tests, Blender-Geometrie/Kamera, Rechte, E-Mails, andere Hausaufträge.

## Contract effects
Die zehn fälschlichen Architekturmarker entfallen aus Möbelkarte und Möbelinventar. Alle tatsächlichen Möbel und Türen bleiben prüfpflichtig, auch mit EG-Sicht-Präfix. Neuer Vertragshash wird regulär erzeugt, niemals manuell eingesetzt.

## Acceptance and tests
Tests zuerst: EG-Sicht-floor/ground/stair werden wie unpräfigierte Architektur behandelt; EG-Sicht-sofa bleibt Möbel, EG-Sicht-wall-1-door bleibt Tür; normale Namen unverändert; Meshzahl unverändert; Marker entfernen ausschließlich Struktur, keine tatsächlichen Möbel. Bestehende make-codex-job.test.py und lieferung-pruefen.test.py bleiben unverändert und müssen bestehen. Quellenhashes vor/nach Regeneration identisch. Zehn Ausgaben und 710 Innen-Meshes bleiben unverändert.

## Risks / invariant / external effects
Kein geänderter Pfad erzeugt oder veröffentlicht ungeprüfte Geometrie. Renderer und Upload-Gates unverändert. Regressionstests sichern echte Möbel/Türen ab. Keine Rechteänderung, keine Kundensendung, kein Commit. Bildfehler bleiben separate offene Arbeit.

## Failed hypotheses
Nur Ursache Namenspräfix untersucht und im Code bestätigt. Kein Prüfer-Bypass vorgeschlagen.

## Rollback
Nur eigenen Patch rückgängig machen und gesicherte erzeugte Auftragsdateien wiederherstellen; keine fremden Änderungen überschreiben.

## Approval record
Explizit freigegeben am 2026-10-30. Tests zuerst: erwartete Fehler vor Fix. Danach 5 neue, 169 Generator- und 101 Lieferprüfer-Tests bestanden. Präfix auch bei Bauteilgruppierung bewahrt; echte Möbel behalten ihre Identität.


## Completion evidence 2026-10-30
275 tests passed. Normal EFH160 job regeneration and preflight passed; ten structural markers removed only; EG42/DG41 and 710 interior meshes; four unchanged source hashes. New contract83e6143d13485b234b94894143604d8f0f3f2966343bffc4f569976b20200839. Ten images accepted and uploaded IDs1333–1342, all remote SHA256 match and send=false. Workspace evidence: efh160-completion. No commits or pushes.

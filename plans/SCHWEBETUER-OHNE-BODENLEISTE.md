# Begehbarer Schrank: Schwebetüren ohne Bodenleiste

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-01: "on our begehbaren schrank, please dont add the leiste on the floor thses would be schwebetüren". Regel 32 in `REGELN.md`.

## Exact scope

- `scripts/render-furnished-dollhouse.py`: `schiene-unten` und das untere Flügelprofil raus, das Glas reicht bis zur Fuge über dem Boden.
- `scripts/make-codex-job.py`: nur der eine Satz in Regel 6, auf Rainers Wort.
- `docs/CODEX-REGELN-4PLUS2.md` 13.3, `REGELN.md`, Tests.

## Explicitly out of scope

Gespeicherte Häuser, fertige Bilder, Codex-Aufträge in Hausordnern, Upload.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Answer: no. Nur die Darstellung eines Möbels, kein Weg zu Veröffentlichung oder E-Mail.

## Rollback

Die `.before-schwebetuer`-Dateien zurückkopieren, Regel 32 entfernen.

## Approval record

Rainers Anweisung vom 2026-11-01 im Chat.

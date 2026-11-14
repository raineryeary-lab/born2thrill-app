# Anzeigename je Haus (die Projekt-ID bleibt)

Status: DONE 2026-11-07 (Annotator server restarted with Start-Alles.ps1; saving checked live)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "can i reedit the names as well like bungalow_007 is actually 2 story BAH". After explanation (the ID carries the build folders, the ledger and the catalogue images): "Yes, add it".

## Implementation

- **app.py:** `anzeigename_setzen()` writes ONLY `projects/<id>/anzeigename.json`.
  - At most 80 characters; whitespace collapsed; an empty name deletes the file.
  - annotations.json and data.json stay untouched, so no build goes stale.
  - New POST `/api/anzeigename`. Reading goes through the existing `/projects/<id>/anzeigename.json`.
  - Backup `app.py.before-anzeigename`.
- **static/anzeigename.js** + annotate.html: field „Anzeigename“ at the top of the Dach tab. It saves on Enter or when leaving the field.
- **Workbench:** state route `anzeigename`; /haus shows "ID · Name" in the list and the name next to the heading.
- **Tests first, red before and green after:**
  - tests/test_anzeigename.py 3;
  - static/anzeigename.test.mjs 2;
  - scripts/anzeigename-haus.test.mjs 1.
  - static 459/459; simplifier tests/ OK.
- **Live:**
  - bungalow_007 = „2-Geschosser am Hang (BAH)“ (Rainer's example), set through the same function;
  - /haus shows it in the list and the header;
  - the Annotator field loads it.
  - Saving from the Annotator only works once the Annotator server is restarted: it still runs the old app.py, and Start-Alles.ps1 skips running servers.

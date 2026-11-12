# Raumtyp „Haustechnikraum“ (Mehrfamilienhäuser)

Status: DONE 2026-11-07 (window rule takes effect at the next Annotator restart)

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-07: "we also need a haustechnikraum for thr mehrfamilienhäuser".

## Implementation (same pattern as raumtyp-treppenhaus-v1)

- **app.py:** `ROOM_CHECKLIST` += („haustechnik“, „Haustechnikraum“); `no_window_required_ids` += haustechnik.
- **annotate.js:** room list += Haustechnikraum (after Treppenhaus). annotate/zoom-pan/geometry-tools v=20261107-5.
- **Build:** „technik“ → service (ROOM_KINDS). **Matrix:** „technik“ in KEIN_ZIMMER, so not a Zimmer (checked: `ist_zimmer` False). The area counts like HWR.
- **Test first:** tests/test_raumtyp_haustechnik.py 3, red before, green after. tests/ OK, static 459/459.
- Backups `.before-haustechnik`.
- **Live:** in the room list after F5 (checked). The no-window rule applies after the next Annotator restart.

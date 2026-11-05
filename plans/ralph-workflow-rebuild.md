# Ralph loop: one coherent /haus workflow (Codex audit, 7 plans)

Approved by Rainer, 2026-08-23: "do it then" — all 7 items as a batch.
Source: plans/workflow-audit-2026-08-22.md (Codex audit) and its agreed
build order. Each item below is ONE loop iteration: write
plans/<item>-v1.md (TEMPLATE.md sections), tests first, implement, verify
on real houses (bungalow_039, onehalfstorey_029, twostorey_030), record a
completion record, tick the box here, note anything learned for the
next item. Stop the loop and ask Rainer whenever an item needs a design
decision — never guess. Never touch WordPress/publishing/external systems
in this loop. Keep every existing test green.

## Task list

- [x] 1. `deriveHouseState(plan)` — one server-side function, the only
      source of the house list state; replaces the ad-hoc branches in
      state/route.ts; uses built_hash()/manifest, revision status, marks,
      Maßstab, Dachform, Codex job, catalogue. UI, batch and buttons read it.
- [x] 2. Active approved revision — Möbel editor AND Bauen use the same
      revision id + geometry_hash; /haus build refuses when the furniture
      was placed on a different geometry than the one being built.
- [ ] 3. Shared freshness library — built_hash()/annotation_state() from
      batch-build.py become an importable module used by go.py,
      /staleness, state derivation and approve-plan.py (one definition
      of "veraltet"; /staleness stops taking the lexically last revision).
- [ ] 4. Codex intake — a "Codex-Rückgabe prüfen" step validating returned
      files against codex-job.json (required outputs, sha256, styles,
      catalog.json), four-style contract in make-codex-job.py, job status
      immutable across re-runs; upload only from a validated image
      delivery manifest, never "newest folder by mtime".
- [ ] 5. Page reloads — Bilder reload after Bauen/Hochladen/Freigeben,
      Auftrag reload after "Auftrag schreiben", staleness re-check after
      annotator/Möbel saves.
- [ ] 6. Three visible gates — rights (ledger), quality (fresh certified
      delivery + validated images) and WordPress release modelled
      separately and fail-closed; approve-plan.py refuses without a fresh
      certified delivery.
- [ ] 7. Dead code — remove unreachable states (korrektur_noetig,
      bilder_hochladen if still unreachable after item 1), the dead
      cut_features/sliced_features rail in render-furnished-dollhouse.py,
      and any superseded branch the earlier items made obsolete.

## Log

(one line per iteration: date, item, outcome, follow-ups)

- 2026-08-23 · Item 1 deriveHouseState · DONE. Pure derivation + 7 tests;
  freshness from the one Python oracle via haus-zustand.py; route reduced to
  fact-gathering. Live over 232 houses; bungalow_039 correctly fell to
  bau_veraltet despite WordPress approval, back to fertig after rebuild.
  Found+fixed a tuple/string contract bug in the new bridge. Follow-up for
  item 3: haus-zustand.py should become a thin caller of the shared freshness
  module. Follow-up for item 7: `korrektur_noetig` and the old
  `warten_auf_codex`-on-WordPress-timeout branch are now unreachable.
- 2026-08-23 · Item 2 furniture/geometry binding · DONE. Audit premise
  re-checked first: editor and build already share one geometry, so the
  remaining hole was furniture not recording WHICH drawing it was placed on.
  Now stamped on save, refused on mismatch (legacy unstamped still builds),
  geometrieFremd surfaced in /haus. Found+fixed: the normalizer silently
  erased the floor_registration marker on every editor save. Follow-up for
  item 6: the --corrected path still has no such binding.

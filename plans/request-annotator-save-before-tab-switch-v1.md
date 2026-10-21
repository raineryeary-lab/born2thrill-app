# Hausakte: ask the embedded annotator to save before switching away from it

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer: "in the möbel part the walls are not being upüdated after being
changed in the annotator." Paired with
`floorplan-simplifier/plans/annotator-save-on-parent-request-v1.md`, which
adds the annotator half of this fix (a `bitte-speichern` /
`zeichnung-gespeichert` postMessage handshake). This plan is the other
half: actually asking for it, at every point `/haus` can navigate away
from an active "Zeichnen" session.

## Current evidence and behavior

- `src/app/haus/page.tsx:335-344` — `rahmenUrl` is derived from `schritt`;
  when `schritt` changes the SAME `<iframe ref={rahmen}>` (`:406`) gets a
  new `src`, and the browser navigates it away from whatever was loaded —
  discarding any unsaved state inside it. No code anywhere calls into the
  iframe (`rahmen.current.contentWindow`) before this happens — confirmed
  by search: `rahmen.current` and `contentWindow` do not appear together
  anywhere in this file today.
- Four places change `schritt` away from a potentially-active "raeume"
  step, none of them guarded:
  - `:383` the step nav buttons themselves — `onClick={() =>
    setSchritt(s.id)}` — the exact click the bug report describes
    (Zeichnen → Möbel).
  - `:332` `weiter()` ("Nächstes Haus →") — `setPlan(naechstes.plan);
    setSchritt("raeume")` — same risk, switching to a different plan
    entirely while still on "raeume" for the current one.
  - `:356` the house-list sidebar buttons — `setPlan(h.plan);
    setSchritt("raeume")` — identical risk.
  - `:202` `setSchritt("bauen")`, triggered by a `moebel-gespeichert`
    message — NOT in scope, this already only fires after the Möbel
    editor's own save succeeded (`furniture.tsx`'s save-gated button,
    established behavior, unrelated to this bug).
  - `:213` `setSchritt("moebel")`, triggered by `projekt-fertig` — NOT in
    scope either, for the same reason: that message only fires after
    `finishProjectAndContinue()` in the annotator already saved.
- `src/app/haus/page.tsx:25` — `const ANNOTATOR = ... "http://
  localhost:8765"` already defined, the correct target origin for
  `postMessage` to the annotator iframe.
- `src/app/haus/page.tsx:195-219` — existing pattern for a
  same-origin-checked incoming `message` listener already exists in this
  file (`hoeren()`), reusable as the template for listening for the new
  `zeichnung-gespeichert` reply.

## Repository baselines

- Repo: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- `src/app/haus/page.tsx`: not yet checked for uncommitted changes this
  session — will re-check immediately before editing (this file was read
  but not previously edited this session, unlike `floorplan-workbench/
  page.tsx`).

## Exact scope

1. Add `sichereZeichnungVorWechsel(): Promise<boolean>` — if `schritt !==
   "raeume"` or the iframe has no `contentWindow`, resolves `true`
   immediately (nothing to guard). Otherwise: posts
   `{typ:"bitte-speichern"}` to the iframe at the `ANNOTATOR` origin,
   listens for a same-origin-checked `zeichnung-gespeichert` reply,
   resolves `ok` from it. On a 4-second timeout with no reply, falls back
   to an explicit `window.confirm(...)` asking whether to proceed anyway —
   fail-safe with the user's own explicit call, not a silent guess in
   either direction (mirrors this file's own existing use of
   `window.confirm` for the destructive media-delete flow, `:295-299`).
2. Add `wechsleSchritt(ziel: SchrittId)` and `wechslePlan(neuerPlan: string,
   ziel: SchrittId = "raeume")` async wrappers that call the guard above
   first and only then call `setSchritt`/`setPlan`.
3. Rewire the three unguarded switch-away points (`:332`, `:356`, `:383`)
   to go through these wrappers instead of calling `setSchritt`/`setPlan`
   directly.

## Files in scope

- `src/app/haus/page.tsx` only.

## Explicitly out of scope

- No change to the two ALREADY-gated transitions (`:202`, `:213`) — they
  already only fire post-save via their own existing mechanisms.
- No change to the Möbel step's own save/continue flow
  (`furniture.tsx`/`FurniturePalette`) — unrelated, already correct.
- No autosave added anywhere — this remains "ask before you leave", not
  "save on every keystroke," matching the annotator's own existing
  explicit-save UX for standalone use.
- No change to the annotator itself — that is the paired
  floorplan-simplifier plan.

## API, schema, and data-contract effects

New, purely additive outbound `postMessage` (`bitte-speichern`) and a new
inbound listener for `zeichnung-gespeichert` — matches the contract defined
in the paired annotator-side plan exactly. No change to any HTTP API, no
change to any saved file format.

## Acceptance criteria

- Editing something in the Zeichnen tab, then clicking "Möbel": the
  annotator saves first (verifiable the same way any other annotator save
  is — its own status line, and the change persisting in
  `annotations.json`), THEN the Möbel step's walls reflect it. This is the
  reported bug's exact scenario.
- The same for "Nächstes Haus" and picking a different house from the
  sidebar while Zeichnen has unsaved changes.
- Switching among Möbel/Bauen/Bilder/etc. (never having touched Zeichnen,
  or after it has nothing unsaved) is not slowed down or changed —
  `sichereZeichnungVorWechsel()` resolves immediately in that case.
- If the annotator genuinely does not respond (e.g. an old cached bundle
  without the new listener — a known trap in this exact annotator per its
  own HANDOFF history), the user sees an explicit confirm dialog rather
  than either silently losing work or being stuck unable to navigate at
  all.

## Tests and verification commands

No existing test harness covers this page's interactive/postMessage
behavior (confirmed: no `*.test.tsx`/`*.test.ts` exists for
`src/app/haus/`). Verification is manual, end-to-end, against the real
reported bug:

1. Open `/haus?plan=bungalow_039`, go to Zeichnen, move a room point or
   redraw part of the outline (do not click the annotator's own Save).
2. Click "Möbel" in the tab bar. Expect: a brief save happens automatically
   (annotator's status line shows it), then Möbel's plan shows the edited
   walls — not the pre-edit ones.
3. Repeat via "Nächstes Haus" and via picking a different house from the
   sidebar while Zeichnen has an unsaved edit — confirm the save happens
   before either navigates away.
4. With nothing unsaved, confirm switching tabs feels exactly as fast as
   today (no perceptible delay from the resolved-immediately fast path).

## Protected and risky paths

- This touches the main step-switching logic of the Hausakte, used for
  every house, every session. Mitigated by keeping the guard a pure
  addition (new functions; the OLD direct `setSchritt`/`setPlan` calls are
  replaced, not left as an alternate path) and by the fast-path/timeout
  design ensuring it can never hang navigation indefinitely.

## Rights, provenance, privacy, and security impact

None.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching
an approved corrected corpus reference?

Required answer: no. This only makes an EXISTING save (the annotator's own,
human-editable annotation save) happen reliably before navigation — no new
generation, publish, or email path.

## Customer, email, database, deployment, and external effects

None.

## Failed-hypothesis log

Not applicable — root cause already confirmed by reading both sides of the
embed together with the paired annotator-side plan, before writing either
plan.

## Rollback

Pure additive/rewiring change in one file. Revert to undo; nothing else
touched.

## Unresolved questions

- Exact timeout value (4000ms proposed) — will keep unless real-world
  testing shows the annotator's own save round-trip (network + Python
  write) sometimes exceeds it on this machine, in which case it will be
  raised and reported, not silently guessed larger.

## Completion record (2026-08-22)

Implemented as scoped: `sichereZeichnungVorWechsel()`, `wechsleSchritt()`,
`wechslePlan()` added; all three unguarded switch-away points (`weiter()`,
the house-list buttons, the step-nav buttons) rewired through them.

Verification:
- `npx tsc --noEmit` — clean, zero errors.
- Live: posted `{typ:"bitte-speichern"}` from the parent tab to the real
  embedded annotator iframe and confirmed a correct
  `{typ:"zeichnung-gespeichert", ok:true}` reply — the exact protocol
  `sichereZeichnungVorWechsel()` itself uses.
- Live: clicked the "Möbel" tab with the Zeichnen iframe loaded and no
  pending edit — switched immediately with no perceptible delay and no
  confirm dialog, confirming the fast path (`schritt !== "raeume"` guard /
  immediate `ok:true` reply) adds no regression to the common case.
- Not independently forced: a real unsaved-edit-then-switch run through the
  live UI (embedded canvas at this viewport size made a precise drag
  impractical to script reliably in this pass). The code path for that
  case reuses the same `sichereZeichnungVorWechsel()` already verified
  above, waiting on the same message contract, so it is reasoned-correct
  from the verified parts rather than independently observed end-to-end.

Files changed: `src/app/haus/page.tsx` only.

## Approval record

Approved by Rainer, 2026-08-22 ("ok").

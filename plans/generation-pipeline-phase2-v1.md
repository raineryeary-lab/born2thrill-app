# Generation pipeline Phase 2 (variant generation, scoring, façade, rendering, catalogue enrichment)

Status: PROPOSED — NOT APPROVED. Do not implement from this plan yet.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Capture the six-step "durable end-to-end target workflow" from the 2026-08-02
Codex handoff (rule-based variant generation → automatic validation/scoring →
Schokoladenseite façade + camera selection → geometry lock → exterior
rendering API → human-approved catalogue enrichment) as a scoped plan, so it
is ready for review and approval rather than started ad hoc. This is Phase 2,
deliberately separate from and after the already-completed Phase 1
(`workbench-catalog-search-ui-v1.md`).

This plan intentionally does NOT get implemented on this pass. It exists
because the user asked for autonomous progress while away, and writing a
careful plan — without touching any of the higher-risk pieces below — is the
responsible way to make progress on Phase 2 without a green light on its
riskiest decisions.

## Current evidence and behavior (verified this session, not assumed)

- Steps "façade scoring" and "geometry lock" already have narrower, APPROVED,
  apparently-working implementations: `plans/blender-facade-view-wiring.md`
  and `plans/geometry-lock-prototype.md`. The Workbench's Gartenseite/
  Straßenseite/Ostseite/Westseite view switcher and "Same approved geometry ·
  <hash>" massing guide are live today. A broader, monolithic
  `plans/canonical-generator-blender-v1.md` exists but only ever reached
  PROPOSED — never approved. Reuse the two approved, working pieces; do not
  restart from the monolithic proposal.
- Steps 1 and 2 (rule-based variant generation, automatic validation/scoring
  of variants) have no plan file and no code anywhere in either repo. This is
  genuinely unbuilt, not just unwired.
- An external "rendering API" for photorealistic exteriors (step 5) is
  mentioned only in prose. No provider, endpoint, credential, or cost model
  exists anywhere in the repos. This is a real, unresolved product/business
  decision, not an engineering detail — see Unresolved questions.
- Step 6 ("approved asset records written back to the catalogue") is *not*
  starting from zero. `C:\dev\born2thrill-app-repo\src\lib\generator\
  approved-floorplan-catalog.ts` and `scripts\import-approved-floorplan-
  package.mjs` (schema `dmh-floorplan-approved-package-v3`) already exist and
  already work: they read a package of `canonical-plan.json`, `floorplan.jpg`,
  `geometry-guide.png`, `massing.json` + `manifest.json` (with `rights` and
  `wordpress_eligible` fields) and expose it via `selectApprovedFloorplan()`.
  The Workbench's existing "Export approved package" button
  (`corrections/route.ts`, `exportApproved()`) already writes files in
  exactly this format to a local `exports/revision-XXXX/` directory. The only
  missing piece is running the existing `import:approved-floorplan` script
  against each new export — that is a process/workflow gap, not a missing
  feature.
- `src/lib/generator/fixtures/approved/catalog.generated.mjs` currently
  contains exactly **one** record (`plan-caaccb688174a403`,
  `wordpress_eligible: true`). This lines up exactly with the earlier
  finding that only one specific questionnaire combination currently
  produces a floorplan end to end on the live site — strong evidence that
  growing this one-record catalogue, not building the six-step pipeline, is
  the fastest lever on "more real combinations work for customers."
- `scripts/approved-floorplan-package.test.mjs` could not be run in this
  sandbox (`Cannot find package 'sharp'`) — confirmed as a sandbox-only
  platform issue: the installed native binary is `@img+sharp-win32-x64`
  (Windows-only), unusable from this Linux sandbox. Not a Codex-caused
  regression; unverified here, not contradicted.
- All other reproducible claims from the 2026-08-02 handoff's "Verified"
  section were reproduced exactly this session: 24+7=31 workbench focused
  tests, 24+4+7+7=42 main-app tests (across the four sandbox-runnable
  scripts), and the v2 corpus totals (310/497/3072/7205) via
  `current-corpus-handoff.test.mjs`.

## Repository baseline

- `C:\dev\born2thrill-local-workbench`, branch `agent/zuhausefinder-generator`,
  base SHA `0c3255fa3f4d4d9c53dd5a5735078dc07e89c633`.
- `C:\dev\born2thrill-app-repo`, branch `fix/customer-floorplan-output`,
  base SHA `cbd4be4480aafc775ea390e3b1991eede9672fef`.
- Both worktrees remain heavily dirty; every pre-existing file preserved.

## Recommended sequencing (for user decision, not yet approved)

1. **Fastest, lowest-risk win, not part of Codex's six steps:** batch through
   the Workbench's existing filter UI (Phase 1) approving more of the 310
   already-annotated reference plans, export each, and run the existing
   `import:approved-floorplan` script to grow
   `catalog.generated.mjs` past its current single record. Zero new code.
   Directly grows real questionnaire coverage. Could plausibly be scripted
   into a small batch-promotion helper as its own tiny plan if there turn out
   to be many approvals to process.
2. Steps 1–2 (rule-based variant generation + automatic scoring) as their own
   scoped plan, once the exact allowed mutation rules (room swap limits,
   niche rules, dimension-adjustment bounds) are written down precisely
   enough to be testable — the handoff describes them only in prose today.
3. Step 5 (external rendering API) only after Unresolved Questions below are
   answered by the user — this is the one piece with real external cost and
   a new third-party dependency.
4. Steps 3–4 (façade scoring, geometry lock) are largely reusable from the
   already-approved `blender-facade-view-wiring.md` /
   `geometry-lock-prototype.md` work — extend, don't rebuild.

## Files in scope (once approved — none touched yet)

To be finalized per sub-plan above. Likely: new
`scripts/generate-floorplan-variants.mjs` + tests (step 1–2),
`src/lib/generator/facade-scoring.ts` extensions (step 3, extending existing
Blender façade wiring), a new `src/app/api/floorplan-workbench/exterior-render`
route (step 5, only after provider decision), and extensions to
`import-approved-floorplan-package.mjs` / the Workbench export flow (step 6).

## Explicitly out of scope (for this plan and for any autonomous work today)

- Any actual implementation of steps 1, 2, or 5.
- Any external API credential creation, external network call, or spend.
- Any change to WordPress, live site, email, or the master
  `customer_delivery_enabled` switch.
- Any change to rights, approval, or quality status of any existing record.
- Deployment of any kind.

## API, schema, database, and artifact-contract effects

None yet — this plan only records scope and evidence. Schema/contract effects
will be added per sub-plan once each is separately approved.

## Acceptance criteria

Not applicable until a sub-plan is approved and scoped with its own criteria.

## Tests and verification commands

Not applicable yet.

## Protected and risky paths

The external rendering API (step 5) is the single highest-risk piece: real
cost, a new third-party dependency, and a new place customer-adjacent data
could leave the local environment. Nothing here authorizes building or
calling it.

## Rights, provenance, privacy, and security impact

Step 5 in particular needs an explicit answer on what data leaves the local
environment (geometry, style prompt, materials) and to which provider, before
any implementation starts.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

Not evaluated yet — no code from this plan has been written. Every sub-plan
above must answer this independently before its own approval.

## Customer, email, database, deployment, and external effects

None from this plan itself. Any future sub-plan touching WordPress or
customer delivery requires its own explicit approval, same as the earlier
`fix-smoke-test-delivery-gate.md` work.

## Failed-hypothesis log

None yet.

## Rollback

This plan file can be deleted with no code effect; nothing has been built
from it yet.

## Addendum 2026-08-02: gap-driven scope for the "tweak, don't invent" ask

The user's framing (after the fast-win catalogue growth) was specifically:
figure out what's still missing, then generate the missing combinations, then
some new ones, and — the actual priority — let a customer's answers tweak a
*generic* approved base plan toward their optimum, rather than inventing
open-ended new floorplans. A read-only coverage pass over the 295
quality-passed references (`docs/approved-catalog-review-queue.md`) grounds
this precisely instead of leaving "generate what we still need" abstract:

- `garage` exists in only 3 bungalow / 1 one-and-a-half-storey / 2 two-storey
  passed references (out of 295). `balcony` exists in 0 bungalow / 4
  one-and-a-half-storey / 1 two-storey. No bungalow or one-and-a-half-storey
  reference has `roof_terrace`. A one-and-a-half-storey office + guest_wc +
  utility_room + garage combination has zero matches at all.
- These specific gaps — not a general "more variety everywhere" — are what
  "generate the types we still need" should mean concretely: adding a garage
  or a balcony/terrace to an otherwise-good, already-approved generic base,
  for the house types where the corpus itself never had that combination.

Proposed narrow rule set for a first "tweak" implementation (still requires
approval; nothing here is built):

1. **Add-garage tweak.** Input: an approved plan with no garage, house type
   bungalow or one-and-a-half-storey (both currently under-covered). Rule:
   append a garage volume adjacent to the existing entrance-side footprint
   within a fixed width/depth range (e.g., 3000–3600 mm × 5500–6000 mm,
   values to be confirmed against the Bastian/rulebook conventions already
   used for stairs), with its own exterior door and no window-area
   requirement (non-habitable). Reject if the resulting footprint would
   overlap an existing room or exceed a maximum lot-width assumption.
2. **Add-balcony/terrace tweak.** Input: an approved plan with an upper-floor
   bedroom or living room on an exterior wall and no existing balcony/
   roof_terrace tag. Rule: attach a balcony slab (fixed depth, e.g.
   1200–1800 mm) to that wall span, replacing a window with a glazed terrace
   door per the existing door-width rulebook constants
   (`FLOORPLAN_RULES.doors`), only where the wall is a habitable room's
   exterior wall.
3. **Explicitly excluded from this first tweak set:** room swaps, boundary/
   dimension adjustments to existing rooms, and anything to the shared stair
   core — these need their own bounds defined before they're testable, per
   Unresolved question 2 below.
4. Every tweak output must: (a) remain `internal_reference_only` by default,
   never auto-set `wordpress_eligible`; (b) carry a new geometry hash derived
   from the parent's hash plus the tweak parameters, so it's traceable to its
   generic base; (c) pass the same `validateCorrectionDocument` checks
   (closed walls, wall-linked openings, room containment) as any manually
   corrected plan; (d) still require the same human approval + rights
   attestation in the Workbench before it could ever become customer-facing
   — tweaks do not get a shortcut around that gate.

This addendum narrows Unresolved question 2 for garage/balcony specifically;
room swaps and dimension adjustments remain open.

## Unresolved questions (blocking approval)

1. **Rendering provider for step 5.** Which service actually generates the
   photorealistic exterior (OpenAI images, a different provider, something
   self-hosted)? What's the per-render cost and expected volume? Is this the
   same API key/account already used elsewhere in the WordPress snippet, or
   a new one?
2. **Exact variant-generation rules for steps 1–2.** "Room swaps, niches,
   dimension adjustments within defined limits" needs concrete, testable
   bounds (e.g., which rooms may swap with which, maximum dimension delta in
   mm) before any code can validate against them.
3. **Priority vs. the faster win.** Should effort go to steps 1–2/5 first, or
   to batch-promoting more of the existing 310 already-annotated plans into
   the approved-package catalogue first (recommended — see Recommended
   sequencing above), since that alone would multiply working questionnaire
   combinations without any new pipeline?
4. **Scoring criteria weights for façade/variant ranking** — the handoff
   lists criteria (garden access, symmetry, window arrangement, etc.) but not
   relative weights or thresholds for "explainable" scoring.

## Approval record

Not approved. Written proactively while the user was away, per their
instruction to make safe autonomous progress; explicitly does not authorize
any implementation of steps 1, 2, or 5, any external API use, or any
WordPress/customer-facing change.

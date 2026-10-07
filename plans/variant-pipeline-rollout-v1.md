# Multi-variant render pipeline — rollout plan

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

The handoff's deliverable is 6 images per home (modern x2 finishes, classic
x2 finishes, 2 exteriors) at scale (100 plans = 600 renders), plus a ComfyUI
polish pass. Nothing about that shape is being changed. This plan is the
ORDER to build it in, so that a bug found tonight — hours to isolate in a
single variant — doesn't ship six times per home before anyone catches it.

Codex could not complete a review of the FULL pipeline tonight (two attempts
at that broader question timed out mid-investigation, no verdict). A third,
narrowly-scoped review — this plan document only, no repo exploration — did
complete, run directly by Rainer. Its answer reordered the stages and
supplied real SDXL parameters in place of this session's untested guesses;
both are incorporated below and marked as Codex's, not this session's.

## Current evidence and behavior

What's actually built right now: one interior cutaway path
(`render-furnished-dollhouse.py`), producing a single colour PNG, no depth
pass, no edge pass, no finish-variant switching, no exterior path, no
ComfyUI wiring. Confirmed by reading the render tail (`bpy.ops.render.render`
called once, one `scene.render.filepath`, no compositor node setup for
additional passes).

Tonight's furniture-orientation check needed: 3 Codex reviews, ~30
individually-inspected image crops, 2 real code bugs found and fixed (corner
sofa mirror; the catalog shell-filter). That was for ONE variant's furniture,
already-placed, not yet varying finish, model, or camera. This is the
concrete basis for staging variants rather than building all 6 in parallel.

## Exact scope, staged

Order per Codex's review (2026-08-09, plan-only pass, run by Rainer):
**1 → 5 → small Stage-6 pilot → 2 → 3 → 4 → full Stage 6 → 7.** Rationale in
its own words: "Generate depth/edge passes once the first geometry is
correct, then prove the polish pipeline before multiplying variants."
Superseded this session's earlier 1-2-3-4-5-6-7 ordering, which put the
ComfyUI pass last instead of piloting it early.

**Stage 1 — one variant, fully correct.** Interior cutaway, modern, one
finish set. This is what tonight's work was actually on. Gate: every
placement checked against the drawing (14/14 real-model pieces done
tonight), the remaining defects list
(`plans/remaining-render-defects-v1.md`) cleared or explicitly deferred with
your sign-off per item.

**Stage 5 — depth and edge passes**, moved up. Add to the SAME render call
as the colour pass (Blender can write multiple passes in one render via the
compositor/view layer — no separate render needed, confirmed cheap per the
handoff). Land once Stage 1's geometry is trusted, so the depth pass
measures something correct.

**Small Stage-6 pilot.** Prove the ComfyUI polish pass on Stage 1's images
BEFORE multiplying into finish or model variants — if the polish pipeline
needs rework, better to find out against one variant than six. Starting
parameters, per Codex, all explicitly empirical and to be locked during
tuning (seed, sampler, model, resolution, preprocessors held fixed while
these are adjusted):

- Denoise: 0.25-0.35 for strong geometry preservation; test 0.40 only if
  results stay stable there.
- Canny ControlNet weight: 0.70-0.85, active roughly the first 0-85% of
  sampling.
- Depth ControlNet weight: 0.35-0.55, active roughly the first 0-75% of
  sampling.
- Canny should dominate structural edges; depth reinforces massing without
  fighting it.

**Stage 2 — finish variant only**, same layout/positions/furniture, second
material palette (floor, wall tone, upholstery, joinery). Low risk by
construction: no geometry changes, only material swaps on objects Stage 1
already proved correct. Verify with a side-by-side render, not a fresh
per-piece check.

**Stage 3 — classic model swap.** Different models per
`data/symbol-model-picks.json`'s `classic` entries. This DOES need the same
per-piece verification as Stage 1 — new geometry, different real models,
possibly different `MODEL_FACING_DEG`/`MODEL_MIRROR_Y` needs (the classic
corner sofa entry is a completely different model file from the modern one
and hasn't been checked at all tonight). Then Stage 2's finish-variant
repeated for classic.

**Stage 4 — exteriors.** Needs new geometry the handoff says doesn't exist
yet: roof, facade material, front door placement via `role: main_entrance`,
exterior window rendering. Codex's review flagged this explicitly:
"Exterior rendering needs its own geometry/control-pass specification" —
scope as its own plan once Stage 1-3 are stable, not folded into this one.

**Full Stage 6 — ComfyUI at scale**, once the pilot's parameters hold across
Stage 2-4's variants, not just Stage 1.

**Stage 7 — budget lock-in.** Only after Stage 6 needs zero manual
per-image intervention on a batch of ~30-60 test images. Measure actual
per-image wall-clock time (Blender pass + ComfyUI pass) from that batch,
then set the 100-plan production budget from measurement, not the handoff's
placeholder 5-30 minute range.

## Also flagged, not urgent

Window pane count (`panes`, currently unrendered) and fine material detail
on real-model furniture are both borderline-visible at final dollhouse-
cutaway render distance and resolution (2000x1500). Lower priority than
anything above; the kitchen-parts redirect tonight (materials on procedural
shapes, not extracted geometry) is the same judgment applied already.

## Files in scope

`render-furnished-dollhouse.py` (stages 5-6 need compositor/pass changes),
new ComfyUI workflow files (stage 6, not yet created), a new exteriors plan
(stage 4, out of scope here beyond noting it's needed).

## Explicitly out of scope

Building stage 4 (exteriors) or stage 6 (ComfyUI) now — both need their own
plans once their prerequisite stages are done.

## Acceptance criteria

Per stage, the gate stated above. No stage starts before the previous one's
gate is met and shown, not claimed.

## Tests and verification commands

Stage-appropriate: Stage 1/3 use the per-piece drawing-vs-render comparison
method from tonight; Stage 2 uses a side-by-side finish comparison; Stage 5
onward need their own verification once built.

## Protected and risky paths

Stage 3 (classic models) is the next place a corner-sofa-style chirality or
facing bug is most likely to reappear — different model files, same class
of risk. Budget real verification time for it, not a rubber stamp because
Stage 1's modern models are already trusted.

## Floorplan-suite invariant

No change from prior plans tonight — `bungalow_040_66` stays
`not_for_delivery`. Nothing here touches promotion, export, or email.

## Rollback

Each stage is additive; no stage depends on deleting or replacing a prior
stage's output.

## Unresolved questions

Per Codex's review, this plan cannot be executed cold without Rainer
deciding each of these — none has a right answer this session can invent:

1. Exact six-output matrix, filenames, and metadata per image.
2. Fixed model/checkpoint, VAE, sampler, scheduler, resolution, and seed
   policy for the ComfyUI pass.
3. Canny edge-detection thresholds and depth-map normalisation.
4. An objective geometry-drift tolerance and how to measure it (the plan
   above says "compare furniture bounding boxes or eyeball a sample" — not
   a real tolerance number).
5. ComfyUI version, required custom nodes/models, and where they live.
6. Prompt and negative-prompt templates, and which fields are allowed to
   vary between images.
7. Failure/retry/resume behaviour for a 600-render batch — what happens
   when render 340 of 600 fails.
8. Exterior geometry inputs and camera-selection contract (Stage 4).
9. Measurable pass/fail thresholds per stage, not just "looks right."
10. A concrete definition of "zero manual intervention" (Stage 7's gate)
    and the actual production budget ceiling once Stage 7's measurement
    exists.

## Approval record

Not approved. This session is already partway into Stage 1 work (furniture
orientation checked, catalog fixed, kitchen materials in progress). Proposal
is to finish Stage 1's remaining items
(`plans/remaining-render-defects-v1.md`) before Stage 5 (depth/edge passes)
starts, per the reordered sequence above.

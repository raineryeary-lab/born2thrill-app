# Approved-catalogue review queue

Generated 2026-08-02 from `data/simplifier-v2/search-catalog.json` (295
quality-passed of 310 total references). Purpose: the customer-facing
approved catalogue (`born2thrill-app-repo/src/lib/generator/
approved-floorplan-catalog.ts`) currently has exactly **one**
`wordpress_eligible: true` record. This list is a prioritized shortlist of
which references to review and approve first in the Workbench
(`http://127.0.0.1:3020/floorplan-workbench`) to get the broadest real
coverage for the fewest reviews — not an instruction to approve all 295.

**This queue does not grant any approval.** Reviewing geometry quality and
attesting commercial rights for each plan is a human decision in the
Workbench UI (`Rights and approval gate` section → usage scope, decision,
and — for reconstruction-only sources — the explicit attestation checkbox).
Nothing in this repo or this session auto-approves anything; the batch
import script (`batch-import:approved-floorplans`) only ever ingests
packages that were already marked commercially cleared by a human.

## Suggested workflow per plan

1. Use the Workbench's catalogue search panel (Phase 1) or open
   `?reference=<project_id>` directly.
2. Review the corrected geometry, run **Validate + re-render**.
3. If it looks right, set the rights fields and click **Approve locally**,
   then **Export approved package**.
4. Once you've exported a batch, run `pnpm batch-import:approved-floorplans`
   from `born2thrill-app-repo` to pull every already-cleared export into the
   customer-facing catalogue in one pass.

## Coverage gaps found (why these plans specifically)

Across the 295 passed references: `garage` appears in only 3 bungalow, 1
one-and-a-half-storey, and 2 two-storey plans. `balcony` appears in 0
bungalow, 4 one-and-a-half-storey, and 1 two-storey plans. No
one-and-a-half-storey or bungalow plan has `roof_terrace`. A one-and-a-half-
storey home office + guest WC + utility room + garage combination has **zero**
matches anywhere in the corpus — that specific combination cannot be offered
to a customer today no matter how many other plans get approved; it would
need a rule-based tweak (see `generation-pipeline-phase2-v1.md`) or a new
annotation, not just review.

## Bungalow — 10 picks (of 133 passed)

| project_id | floors | tags |
|---|---|---|
| bungalow_016 | 1 | dressing, garage, guest_wc, office, utility_room |
| bungalow_033 | 1 | child_rooms, dressing, garage, guest_wc, utility_room |
| bungalow_008 | 1 | dressing, office, utility_room |
| bungalow_012 | 1 | dressing, guest_wc, office, utility_room |
| bungalow_017 | 1 | child_rooms, dressing, guest_wc, utility_room |
| bungalow_032 | 1 | garage, guest_wc, office, utility_room |
| bungalow_034 | 2 | child_rooms, dressing, guest_wc, office, utility_room |
| bungalow_040_15 | 1 | child_rooms, dressing, guest_wc, utility_room |
| bungalow_040_29 | 1 | child_rooms, dressing, utility_room |
| bungalow_040_40 | 1 | dressing, guest_wc, utility_room |

## One-and-a-half-storey — 10 picks (of 87 passed)

| project_id | floors | tags |
|---|---|---|
| german_catalog_review_onehalfstorey_1_6_2_efh_190 | 2 | child_rooms, dressing, garage, guest_wc, utility_room |
| onehalfstorey_043 | 2 | balcony, child_rooms, dressing, guest_wc, office, utility_room |
| german_catalog_review_onehalfstorey_1_6_1_efh_190 | 2 | child_rooms, dressing, guest_wc, office, utility_room |
| onehalfstorey_008 | 2 | child_rooms, dressing, guest_wc, utility_room |
| onehalfstorey_014 | 2 | child_rooms, dressing, guest_wc, office, utility_room |
| onehalfstorey_021 | 2 | child_rooms, dressing, guest_wc, utility_room |
| onehalfstorey_029 | 2 | balcony, child_rooms, guest_wc, office, utility_room |
| onehalfstorey_033 | 2 | balcony, child_rooms, guest_wc, utility_room |
| onehalfstorey_038 | 2 | balcony, child_rooms, guest_wc, office, utility_room |
| onehalfstorey_queue_1_2_3_efh_140_1 | 2 | child_rooms, dressing, guest_wc |

## Two-storey — 10 picks (of 87 passed)

| project_id | floors | tags |
|---|---|---|
| twostorey_054 | 1 | balcony, child_rooms, dressing, garage, guest_wc, office, utility_room |
| german_catalog_review_twostorey_5_1_1_sv_130 | 2 | child_rooms, dressing, guest_wc, utility_room |
| german_catalog_review_twostorey_5_3_6_sv_145 | 2 | child_rooms, dressing, guest_wc, office, utility_room |
| measured_twostorey_bach_001 | 2 | child_rooms, dressing, guest_wc, utility_room |
| twostorey_030 | 2 | child_rooms, garage, guest_wc, utility_room |
| twostorey_038 | 2 | child_rooms, dressing, guest_wc, office, utility_room |
| twostorey_051 | 2 | child_rooms, dressing, guest_wc, utility_room |
| twostorey_052 | 2 | dressing, guest_wc, office, utility_room |
| twostorey_queue_5_1_4_sv_130 | 2 | child_rooms, guest_wc, roof_terrace, utility_room |
| twostorey_queue_5_3_4_sv_145 | 2 | child_rooms, guest_wc, roof_terrace, utility_room |

These 30 were chosen by a greedy pass that prioritizes rare tags first
(garage, balcony, roof_terrace, dressing) then general room-program
diversity, so they cover 30 distinct (house type, bedroom-count bucket,
program tag set) signatures rather than 30 near-duplicates.

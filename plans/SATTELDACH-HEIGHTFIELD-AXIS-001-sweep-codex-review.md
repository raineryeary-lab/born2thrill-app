# Review request: sweep for other missing `along_x` forwarding in the two-wing roof code

## Context

`born2thrill-local-workbench/scripts/render-exterior.py` and
`born2thrill-local-workbench/scripts/roof_profile.py` build two-wing
(L-shaped) `satteldach`/`pultdach`/`doppelpultdach` roofs. When a plan sets
`roof_axis_override` ("x"/"y"), that forced ridge axis must be threaded
through to EVERY per-wing geometry call as `along_x=...` -- otherwise a call
that omits it falls back to auto-detecting each wing's own ridge axis
independently (whichever side of that wing's own rectangle is longer),
which can silently disagree with the forced axis for one wing while
agreeing (by coincidence) for the other.

This exact bug class has now caused two separate, real defects:

1. Documented in `roof_profile.py`'s `wing_height_at()` docstring
   (lines 226-256): an earlier caller passed no `along_x`, one wing's height
   was silently sampled across the wrong axis/span. Already fixed at that
   call site.
2. Found today (2026-09-26, via a Codex read-only review, brief and output
   saved at `plans/SATTELDACH-HEIGHTFIELD-AXIS-001-codex-review.md`):
   `render-exterior.py`'s call to `roof_profile.heightfield_roof_mesh()`
   (around line 1764) omitted `along_x=_u_along_x` even though every other
   call in the same branch (profile scaling, the gable-cap loop,
   `wall_extension()`) already passes it. Root cause of a real open hole in
   the roof (a gable end exposing the attic underside) plus torn roof-sheet
   facets on house `german_catalog_review_bungalow_4_3_1_wb_125` built as
   satteldach. Just fixed: added `along_x=_u_along_x` to that call, verified
   via a real rebuild (`go.py`) -- the hole and torn facets are gone, the
   sibling doppelpultdach build (a different code branch, unaffected)
   remains clean.

The person I'm working for just said, in effect: "this illogical stuff is
holding up going to production, help me fix this properly" -- i.e. they
want this CLASS of bug found and closed everywhere it exists, not fixed
one instance at a time as it happens to surface in a render.

## What I need from this review

A systematic sweep, not a general lecture on the pattern:

1. Every function in `roof_profile.py` that accepts an `along_x` parameter
   (`_axes`, `wing_height_at`, `combined_height_at`, `gable_cap_polygon`,
   `gable_cap_prism`, `heightfield_roof_mesh`, `wall_extension`, and any
   others you find) -- list them, with their signature line number.
2. Every CALL SITE of each of those functions in BOTH
   `render-exterior.py` and `roof_profile.py` itself (functions can call
   each other) -- for each call site, state:
   - file:line
   - whether it passes `along_x` explicitly
   - if it does NOT pass it, whether that is actually safe (e.g. it is
     legitimately in a code path that never has a forced axis to honour --
     state which one and why) or whether it is the SAME latent bug as the
     two already found (a forced-axis context where this call still falls
     back to auto-detect).
3. For any newly-found instance of the bug: same output shape as before --
   confidence, file:line, root cause, and what the fix should be (matching
   the pattern of the fix just applied: forward the already-computed
   resolved axis variable already in scope at that call site, do not invent
   a new default).
4. Separately: is there a way to make this bug class structurally
   impossible instead of finding each instance by hand -- e.g. should
   `along_x` stop being an optional/defaulted parameter on these functions
   in this two-wing code path (make it required wherever a wing-aware
   caller exists, so a forgotten forward is a loud `TypeError` at call time
   instead of a silent wrong-axis fallback)? Is that safe given the
   functions are also used from the single-rectangle path where there is
   no per-wing ambiguity to begin with (would need a real default there,
   just not a silent one in the two-wing path)?

## Out of scope

- Do not re-litigate or re-verify the two ALREADY-fixed instances (Solidify
  Fill Rim's real behaviour, the specific WB_125 measurements) -- already
  established, cited above for context only.
- Do not review other bug classes (asset scaling/catalogue-size mismatches
  are a SEPARATE, already-tracked plan, `HUB-ASSET-FIT-CONTRACT-001`) --
  stay focused on `along_x` forwarding only.
- Style/formatting nits.

## Output format

Section 1: table of `along_x`-accepting functions.
Section 2: table of call sites, one row each, with the safe/unsafe verdict.
Section 3: any newly-confirmed bug instances, same format as before
(confidence | file:line | root cause | fix).
Section 4: your answer to the "make it structurally required" question,
a few sentences, with a recommendation.

---

## Codex output

**No additional missing `along_x` forwarding found:** 11 accepting functions, 27 call sites, one intentional omission.

Reviewed the current working files on branch `agent/furnished-render-and-annotation-schema`, HEAD `5be1a4e18956b9fb2e158bee82aa159898356e89`. Both reviewed files are untracked, so these findings describe their working-tree contents.

**Section 1: Functions accepting `along_x`**

All definitions are in [scripts/roof_profile.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/roof_profile.py). Lines identify the start of each signature.

| Function | Signature line | `along_x` contract |
|---|---:|---|
| `wing_height_at` | 226 | Keyword-only, defaults to `None` |
| `combined_height_at` | 259 | Keyword-only, defaults to `None` |
| `gable_cap_polygon` | 273 | Keyword-only, defaults to `None` |
| `gable_cap_prism` | 304 | Keyword-only, defaults to `None` |
| `heightfield_roof_mesh` | 349 | Keyword-only, defaults to `None` |
| `_axes` | 481 | Keyword-only, defaults to `None` |
| `profile_mesh` | 500 | Keyword-only, defaults to `None` |
| `_prism` | 544 | Required positional-or-keyword |
| `_long_wall` | 578 | Required positional-or-keyword |
| `wall_extension` | 601 | Keyword-only, defaults to `None` |
| `end_wall_and_soffit` | 694 | Keyword-only, defaults to `None` |

**Section 2: Every call site**

Below, **RE** means [scripts/render-exterior.py](C:/dev/Floorplan-tools/born2thrill-local-workbench/scripts/render-exterior.py), and **RP** means `scripts/roof_profile.py`. Positional arguments count as explicit forwarding.

| File:line | Called function | Explicit `along_x` | Verdict |
|---|---|---|---|
| RE:1378 | `_axes` | **No** | **Safe:** computes only the whole-building automatic fallback. Its span/origin results are discarded; line 1379 applies the override before geometry calculations. |
| RE:1380 | `_axes` | `_u_along_x` | Safe: computes design span using the resolved building axis. |
| RE:1643 | `_axes` | `_u_along_x` | Safe: per-wing profile scaling uses the building axis. |
| RE:1663 | `_axes` | `_u_along_x` | Safe: profile softening uses the same axis/span. |
| RE:1784 | `heightfield_roof_mesh` | `_u_along_x` | Safe: forwards the building axis into height sampling. |
| RE:1831 | `_axes` | `_u_along_x` | Safe: resolves the cap’s wing axis consistently. |
| RE:1833 | `gable_cap_prism` | `_w_along_x` | Safe: forwards the immediately resolved cap axis. |
| RE:1848 | `_axes` | `_u_along_x` | Safe: resolves the wall’s wing axis consistently. |
| RE:1849 | `wall_extension` | `_w_along_x` | Safe: forwards the immediately resolved wall axis. |
| RE:1886 | `_axes` | `_forced_along_x` | Safe: single-rectangle resolution boundary; `None` intentionally selects automatic orientation when no override exists. |
| RE:1891 | `profile_mesh` | `_along_x` | Safe: uses the resolved single-rectangle axis. |
| RE:1896 | `wall_extension` | `_along_x` | Safe: uses the same axis as the rectangle’s sheet. |
| RP:253 | `_axes` | `along_x` | Safe: `wing_height_at` forwards its input. |
| RP:268 | `wing_height_at` | `along_x` | Safe: `combined_height_at` forwards to every wing. |
| RP:294 | `_axes` | `along_x` | Safe: `gable_cap_polygon` forwards its input. |
| RP:342 | `_axes` | `along_x` | Safe: `gable_cap_prism` forwards its input. |
| RP:346 | `_prism` | `along_x`, positional | Safe: passes the boolean resolved at line 342. |
| RP:410 | `combined_height_at` | `along_x` | Safe: heightfield forwards into combined sampling. |
| RP:514 | `_axes` | `along_x` | Safe: `profile_mesh` forwards its input. |
| RP:640 | `_axes` | `along_x` | Safe: `wall_extension` forwards its input. |
| RP:658 | `_prism` | `along_x`, positional | Safe: end wall uses the resolved axis. |
| RP:680 | `_prism` | `along_x`, positional | Safe: soffit uses the resolved axis. |
| RP:689 | `_long_wall` | `along_x`, positional | Safe: longitudinal wall uses the resolved axis. |
| RP:714 | `_axes` | `along_x` | Safe: `end_wall_and_soffit` forwards its input. |
| RP:730 | `_prism` | `along_x`, positional | Safe: end wall uses the resolved axis. |
| RP:736 | `_prism` | `along_x`, positional | Safe: soffit uses the resolved axis. |

`gable_cap_polygon` and `end_wall_and_soffit` have **no callers in either reviewed file**; their internal calls are nevertheless included above.

**Section 3: Newly confirmed bug instances**

| Confidence | File:line | Root cause | Fix |
|---|---|---|---|
| — | — | No additional missing-forwarding instances found. | No forwarding patch needed. |

This conclusion comes from an AST inventory cross-checked against textual references and axis-variable assignments. It is specific to forwarding in these two files, not a general certification of roof geometry. No rebuild or re-verification of the two established defects was performed.

**Section 4: Make forwarding structurally required**

**Recommendation: require keyword-only `along_x` on geometry functions and reject `None`; allow automatic selection only at an explicit axis-resolution boundary.** Removing the default makes omission raise `TypeError`, while rejecting `None` also prevents callers from accidentally restoring silent auto-detection. `_prism` and `_long_wall` already require the argument.

This fits both current renderer paths: the two-wing branch resolves `_u_along_x` once at lines 1378–1379, and the single-rectangle branch resolves `_along_x` at line 1886; both already pass booleans downstream. Single-rectangle geometry therefore needs no implicit default—only its resolver needs automatic mode. This is an API migration, however: existing tests intentionally exercise omitted arguments and automatic behavior, so preserve that coverage through explicit resolver calls or a clearly named automatic wrapper, with separately approved test changes.

Add contract tests for omitted/`None` arguments and forced `True`/`False` across oppositely proportioned wings. Also correct the forwarding-related docstrings at RP:244–248 and RP:384–390: their claim that the renderer intentionally permits per-wing automatic orientation no longer matches the current implementation.

No files changed; rollback is unnecessary. Git status remains 16 modified tracked files and 505 untracked entries. **Next proposed follow-up: the required-axis API contract and regression tests.** Recording it in the [canonical roadmap](C:/dev/Floorplan-tools/born2thrill-app-repo/plans/ROADMAP.md) is blocked by this session’s read-only filesystem, so that required tracking step remains outstanding.
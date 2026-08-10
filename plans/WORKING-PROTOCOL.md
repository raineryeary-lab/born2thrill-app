# Working protocol — furnished render pipeline

Written by Codex on 2026-08-09 after a day in which I repeatedly used heuristics
where authoritative data already existed, and repeatedly claimed fixes without
verifying them. Rainer asked for this. It governs work on this pipeline.

## Evidence-first protocol

### 1. Before writing code: data or rule?

For every output-affecting value, create a source table:

| Value | Explicit user data? | Canonical source | Allowed fallback |
|---|---:|---|---|
| Door swing | Yes | `swing_side`, `hinge_side` | None |
| Symbol orientation | Yes | annotation + source SVG | None |
| Furniture footprint | Yes | dragged footprint | None |
| Model dimensions | Yes | verified-dimensions file | None |

Apply this precedence:

1. Explicit user-set value.
2. Canonical source record.
3. Directly measured source/model property.
4. Documented deterministic default.
5. Heuristic—only with explicit user approval.

If levels 1–3 exist, using level 4 or 5 is a bug.

Before inventing any heuristic, run searches for the concept and its synonyms across schemas, fixtures, generated files, catalogues, and model inventories. Open representative assets. A catalogue entry is not evidence that you inspected its contents.

No fallback may silently replace valid explicit data. Missing or invalid required data should produce a visible error containing the object ID and missing field.

### 2. Minimum proof before saying “fixed”

You may say “fixed” only after all four gates pass:

1. **Input proof:** Log the exact source values and object IDs used.
2. **Path proof:** Show that execution reached the changed branch.
3. **State proof:** Inspect the resulting scene/object measurements, transforms, model selection, and relevant metadata.
4. **Output proof:** Produce a fresh render and compare it with the prior render and an expected reference.

Also run regression checks on at least:

- the reported failing case;
- one ordinary case;
- one case likely to be harmed by the fix.

Report “implemented, not yet verified” until all gates pass.

### 3. If output does not change

Stop immediately.

Do not interpret the image or propose another visual hypothesis. Check, in order:

1. Was the correct code executed?
2. Was the correct input and object ID loaded?
3. Did the changed branch run?
4. Did intermediate state change?
5. Was the output regenerated rather than reused or cached?
6. Are old and new outputs actually byte-identical?

Byte-identical output means the change had no effect on that artifact. Revert or retain it only after explaining why it is still independently correct.

### 4. Root-cause discipline

Never state a cause without a discriminating measurement.

Use this format:

- **Observation:** directly measured fact.
- **Hypothesis:** one proposed explanation.
- **Prediction:** what must be observed if it is true.
- **Test:** command or instrumentation used.
- **Result:** actual output.
- **Conclusion:** supported, rejected, or unresolved.

Instrument from input to output: source fields → selected asset → raw bounds → scale calculation → transform → final scene bounds → render.

After three distinct failed hypotheses, stop. Record them and reassess the data path from the beginning. Do not produce a fourth narrative.

### 5. When the user already told you the answer

Treat the user’s statement as the primary hypothesis and test it first, literally.

If told “compare the symbols to the models”:

1. Open the symbols.
2. Open the models, including collection/set files.
3. Record orientation, handedness, dimensions, origin, and axes.
4. Compare them directly.
5. Only then inspect proxies such as names, bounding-box ratios, or catalogue metadata.

You may disagree only with measured evidence. Never silently reinterpret a direct instruction into an easier proxy task.

## Hard prohibitions

- No heuristic may override explicit annotation data.
- No model may be called “missing” until all indexed files and nested objects have been searched and inspected.
- No size/orientation correction may be based solely on bounding-box aspect ratio.
- No destructive import filter may be added without logging every removed object and testing known valid large objects.
- No rejection gate may replace a user-measured asset with a fallback silently.
- No “fixed,” “working,” or “resolved” without a fresh verified artifact.

The governing rule is simple: **read explicit facts, measure intermediate state, and make every fallback loud.**
tokens used
8,714
You substituted inference for inspection, then substituted explanation for verification. Use this protocol mechanically.

## Evidence-first protocol

### 1. Before writing code: data or rule?

For every output-affecting value, create a source table:

| Value | Explicit user data? | Canonical source | Allowed fallback |
|---|---:|---|---|
| Door swing | Yes | `swing_side`, `hinge_side` | None |
| Symbol orientation | Yes | annotation + source SVG | None |
| Furniture footprint | Yes | dragged footprint | None |
| Model dimensions | Yes | verified-dimensions file | None |

Apply this precedence:

1. Explicit user-set value.
2. Canonical source record.
3. Directly measured source/model property.
4. Documented deterministic default.
5. Heuristic—only with explicit user approval.

If levels 1–3 exist, using level 4 or 5 is a bug.

Before inventing any heuristic, run searches for the concept and its synonyms across schemas, fixtures, generated files, catalogues, and model inventories. Open representative assets. A catalogue entry is not evidence that you inspected its contents.

No fallback may silently replace valid explicit data. Missing or invalid required data should produce a visible error containing the object ID and missing field.

### 2. Minimum proof before saying “fixed”

You may say “fixed” only after all four gates pass:

1. **Input proof:** Log the exact source values and object IDs used.
2. **Path proof:** Show that execution reached the changed branch.
3. **State proof:** Inspect the resulting scene/object measurements, transforms, model selection, and relevant metadata.
4. **Output proof:** Produce a fresh render and compare it with the prior render and an expected reference.

Also run regression checks on at least:

- the reported failing case;
- one ordinary case;
- one case likely to be harmed by the fix.

Report “implemented, not yet verified” until all gates pass.

### 3. If output does not change

Stop immediately.

Do not interpret the image or propose another visual hypothesis. Check, in order:

1. Was the correct code executed?
2. Was the correct input and object ID loaded?
3. Did the changed branch run?
4. Did intermediate state change?
5. Was the output regenerated rather than reused or cached?
6. Are old and new outputs actually byte-identical?

Byte-identical output means the change had no effect on that artifact. Revert or retain it only after explaining why it is still independently correct.

### 4. Root-cause discipline

Never state a cause without a discriminating measurement.

Use this format:

- **Observation:** directly measured fact.
- **Hypothesis:** one proposed explanation.
- **Prediction:** what must be observed if it is true.
- **Test:** command or instrumentation used.
- **Result:** actual output.
- **Conclusion:** supported, rejected, or unresolved.

Instrument from input to output: source fields → selected asset → raw bounds → scale calculation → transform → final scene bounds → render.

After three distinct failed hypotheses, stop. Record them and reassess the data path from the beginning. Do not produce a fourth narrative.

### 5. When the user already told you the answer

Treat the user’s statement as the primary hypothesis and test it first, literally.

If told “compare the symbols to the models”:

1. Open the symbols.
2. Open the models, including collection/set files.
3. Record orientation, handedness, dimensions, origin, and axes.
4. Compare them directly.
5. Only then inspect proxies such as names, bounding-box ratios, or catalogue metadata.

You may disagree only with measured evidence. Never silently reinterpret a direct instruction into an easier proxy task.

## Hard prohibitions

- No heuristic may override explicit annotation data.
- No model may be called “missing” until all indexed files and nested objects have been searched and inspected.
- No size/orientation correction may be based solely on bounding-box aspect ratio.
- No destructive import filter may be added without logging every removed object and testing known valid large objects.
- No rejection gate may replace a user-measured asset with a fallback silently.
- No “fixed,” “working,” or “resolved” without a fresh verified artifact.

The governing rule is simple: **read explicit facts, measure intermediate state, and make every fallback loud.**

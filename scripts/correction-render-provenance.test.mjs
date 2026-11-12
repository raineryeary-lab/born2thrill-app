import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

test("correction render plans carry source annotation provenance", () => {
  const script = fs.readFileSync(
    new URL("./build-simplifier-render-plan.py", import.meta.url),
    "utf8",
  );
  const correctionPlan = script.slice(
    script.indexOf("def correction_plan("),
    script.indexOf("\ndef main():"),
  );

  assert.match(
    correctionPlan,
    /"source_provenance":\s*source_provenance\(reference\)/,
  );
});

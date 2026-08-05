import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

test("main generator is connected to the current validated v2 corpus", async () => {
  const source = await readFile(new URL("../src/lib/training/simplifier-reference.ts", import.meta.url), "utf8");
  assert.match(source, /data\/simplifier-v2\/dataset\.json/);
  assert.match(source, /project\.qualityStatus === "passed"/);
  assert.match(source, /project\.packageStatus === "training_ready"/);
  assert.match(source, /packageStatus: project\.package_status/);
  assert.match(source, /qualityStatus: project\.quality_status/);
  const dataset = JSON.parse(await readFile(new URL("../data/simplifier-v2/dataset.json", import.meta.url), "utf8"));
  const manifest = JSON.parse(await readFile(new URL("../data/simplifier-v2/manifest.json", import.meta.url), "utf8"));
  assert.equal(dataset.projects.length, manifest.project_count);
  const passed = dataset.projects.filter((project) => project.quality_status === "passed" && project.package_status === "training_ready");
  assert.ok(passed.length >= 295);
  for (const houseType of ["bungalow", "onehalfstorey", "twostorey"]) {
    assert.ok(passed.some((project) => project.house_type === houseType), houseType);
  }
  assert.ok(dataset.projects.filter((project) => project.quality_status !== "passed").every((project) => project.commercial_generator_eligible === false));
});
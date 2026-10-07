import assert from "node:assert/strict";
import test from "node:test";

import {
  countDataset,
  validateCorpusLedger,
  validateDataset,
  validateReconstructionDataset,
} from "./import-simplifier-handoff.mjs";

function project(index, floorLevel = "groundfloor") {
  return {
    project_id: `project_${index}`,
    house_type: index % 2 ? "twostorey" : "bungalow",
    source_kind: "real_annotated",
    approval_status: "annotated_reference",
    usage_scope: "internal_reference_only",
    quality_status: "review_required",
    annotation_sha256: String(index).padStart(64, "0"),
    floors: [{
      floor_level: floorLevel,
      rooms: [{ id: `room_${index}`, polygon: [[0, 0], [1, 0], [1, 1]] }],
      elements: [{ id: `door_${index}`, type: "door", points: [[0, 0], [0, 1]] }],
    }],
  };
}

function ledgerFor(projects) {
  return {
    schema_version: "floorplan-corpus-ledger-v1",
    policy: {
      unchanged_annotations_are_not_reprocessed_until_hash_changes: true,
      commercial_approval_requires_explicit_rights_and_quality: true,
      generated_candidates_require_human_approval: true,
    },
    counts: {
      annotated_reference: projects.filter((item) => item.approval_status === "annotated_reference").length,
      approved_real: projects.filter((item) => item.approval_status === "approved_real").length,
    },
    projects: projects.map((item) => ({
      project_id: item.project_id,
      corpus_status: item.approval_status,
      annotation_sha256: item.annotation_sha256,
      internal_reference_eligible: true,
      commercial_generator_eligible: item.approval_status === "approved_real",
    })),
  };
}

test("requires a ledger bound to every dataset project and annotation hash", () => {
  const value = fixture(Array.from({ length: 2 }, (_, index) => project(index)));
  const ledger = ledgerFor(value.dataset.projects);
  assert.doesNotThrow(() => validateCorpusLedger(ledger, value.counts, value.dataset));
  ledger.projects[0].annotation_sha256 = "f".repeat(64);
  assert.throws(
    () => validateCorpusLedger(ledger, value.counts, value.dataset),
    /hash mismatch/,
  );
});

function fixture(projects = [project(1)]) {
  const dataset = {
    dataset_version: "floorplan-generator-simplifier-v1",
    source_schema: "simplifier-annotations-v1",
    privacy: {
      local_only: true,
      contains_raw_floorplans: false,
      contains_customer_names_or_addresses: false,
    },
    projects,
  };
  const counts = countDataset(dataset);
  const manifest = {
    dataset_version: dataset.dataset_version,
    ...counts,
  };
  const knowledge = {
    knowledge_version: "simplifier-knowledge-v1",
    basis: counts,
    element_counts: { door: counts.element_count, window: 0, stairs: 0 },
  };
  return { dataset, manifest, knowledge, counts };
}
test("restricted references are accepted only by the reconstruction dataset contract", () => {
  const restricted = project(9);
  restricted.source_rights_status = "restricted_reference";
  restricted.reconstruction_only = true;
  restricted.commercial_generator_eligible = false;
  const dataset = {
    dataset_version: "floorplan-reconstruction-reference-v1",
    source_schema: "simplifier-annotations-v1",
    privacy: {
      local_only: true,
      contains_raw_floorplans: false,
      contains_customer_names_or_addresses: false,
    },
    policy: {
      source_assets_excluded: true,
      reconstruction_only: true,
      commercial_output_requires_separate_geometry_and_rights_approval: true,
    },
    projects: [restricted],
  };

  assert.equal(validateReconstructionDataset(dataset).project_count, 1);
  restricted.commercial_generator_eligible = true;
  assert.throws(
    () => validateReconstructionDataset(dataset),
    /commercial_generator_eligible/,
  );
});


test("accepts a future larger dataset without fixed counts", () => {
  const value = fixture(Array.from({ length: 200 }, (_, index) => project(index)));
  assert.deepEqual(validateDataset(value.dataset, value.manifest, value.knowledge), value.counts);
});

test("rejects a manifest count mismatch", () => {
  const value = fixture();
  value.manifest.project_count += 1;
  assert.throws(
    () => validateDataset(value.dataset, value.manifest, value.knowledge),
    /manifest\.project_count mismatch/,
  );
});

for (const [field, invalid] of [
  ["local_only", undefined],
  ["contains_raw_floorplans", true],
  ["contains_customer_names_or_addresses", undefined],
]) {
  test(`rejects invalid or missing privacy flag ${field}`, () => {
    const value = fixture();
    if (invalid === undefined) delete value.dataset.privacy[field];
    else value.dataset.privacy[field] = invalid;
    assert.throws(() => validateDataset(value.dataset, value.manifest, value.knowledge), /privacy\./);
  });
}

test("rejects unsupported dataset and annotation schema versions", () => {
  const datasetVersion = fixture();
  datasetVersion.dataset.dataset_version = "floorplan-generator-simplifier-v2";
  assert.throws(
    () => validateDataset(datasetVersion.dataset, datasetVersion.manifest, datasetVersion.knowledge),
    /dataset_version mismatch/,
  );

  const sourceSchema = fixture();
  sourceSchema.dataset.source_schema = "simplifier-annotations-v2";
  assert.throws(
    () => validateDataset(sourceSchema.dataset, sourceSchema.manifest, sourceSchema.knowledge),
    /source_schema mismatch/,
  );
});

test("recognizes basement floors only through the typed floor_level field", () => {
  const value = fixture([project(1, "basement"), project(2, "groundfloor")]);
  const counts = validateDataset(value.dataset, value.manifest, value.knowledge);
  assert.equal(counts.floor_levels.basement, 1);
  assert.equal(counts.floor_levels.groundfloor, 1);
});

test("keeps incomplete floors countable but prevents room references on them", () => {
  const value = fixture();
  value.dataset.projects[0].floors.push({
    floor_level: "upperfloor",
    rooms: [],
    elements: [{ id: "stairs_only", type: "stairs", points: [[0, 0], [0, 1]] }],
  });
  const counts = countDataset(value.dataset);
  value.manifest = { dataset_version: value.dataset.dataset_version, ...counts };
  value.knowledge.basis = counts;
  value.knowledge.element_counts = { door: 1, stairs: 1, window: 0 };

  assert.equal(validateDataset(value.dataset, value.manifest, value.knowledge).floor_count, 2);

  value.dataset.projects[0].floors[1].elements[0].room_id = "missing_room";
  assert.throws(
    () => validateDataset(value.dataset, value.manifest, value.knowledge),
    /cannot reference rooms on an incomplete floor/,
  );
});

test("rejects floors with only degenerate room polygons", () => {
  const value = fixture();
  value.dataset.projects[0].floors[0].rooms[0].polygon = [[0, 0], [1, 1], [2, 2]];
  assert.throws(
    () => validateDataset(value.dataset, value.manifest, value.knowledge),
    /must contain at least one valid room polygon/,
  );
});

test("rejects malformed knowledge element counts", () => {
  const value = fixture();
  value.knowledge.element_counts.window = "many";
  assert.throws(
    () => validateDataset(value.dataset, value.manifest, value.knowledge),
    /knowledge\.element_counts\.window must be a non-negative integer/,
  );
});

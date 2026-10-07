import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";
import {
  buildSearchCatalog,
  filterCatalogRecords,
  stableJson,
} from "./build-floorplan-search-catalog.mjs";

const dataset = JSON.parse(await readFile(new URL("../data/simplifier-v2/dataset.json", import.meta.url), "utf8"));
const manifest = JSON.parse(await readFile(new URL("../data/simplifier-v2/manifest.json", import.meta.url), "utf8"));

test("catalog reconciles every exported project, floor, room, and element", () => {
  const catalog = buildSearchCatalog(dataset, manifest);
  assert.equal(catalog.schema, "zf-floorplan-search-catalog-v1");
  assert.equal(catalog.records.length, 310);
  assert.deepEqual(catalog.totals, {
    projects: manifest.project_count,
    floors: manifest.floor_count,
    rooms: manifest.room_count,
    elements: manifest.element_count,
  });
  assert.equal(catalog.records.reduce((sum, record) => sum + record.floor_count, 0), manifest.floor_count);
  assert.equal(catalog.records.reduce((sum, record) => sum + record.room_polygon_count, 0), manifest.room_count);
  assert.equal(catalog.records.reduce((sum, record) => sum + record.element_count, 0), manifest.element_count);
});

test("catalog exposes useful room-program counts without inventing square metres", () => {
  const catalog = buildSearchCatalog(dataset, manifest);
  const bungalow = catalog.records.find((record) => record.project_id === "bungalow_001");
  assert.ok(bungalow);
  assert.equal(bungalow.house_type, "bungalow");
  assert.equal(bungalow.floor_count, 1);
  assert.equal(bungalow.room_counts.eltern, 1);
  assert.equal(bungalow.room_counts.hwr_htr, 1);
  assert.equal(bungalow.room_counts.bad, 1);
  assert.ok(bungalow.program_tags.includes("utility_room"));
  assert.ok(bungalow.program_tags.includes("bathroom"));
  assert.equal(bungalow.metric_area.status, "unavailable");
  assert.equal("area_m2" in bungalow, false);
  assert.equal(JSON.stringify(catalog).includes('"area_m2"'), false);
});

test("combined rooms expand semantic tags without duplicating room polygons", () => {
  const catalog = buildSearchCatalog(dataset, manifest);
  const bungalow = catalog.records.find((record) => record.project_id === "bungalow_001");
  assert.ok(bungalow.room_counts.wohnen >= 1);
  assert.ok(bungalow.room_counts.essen >= 1);
  assert.ok(bungalow.room_counts.kueche >= 1);
  assert.equal(bungalow.room_polygon_count, bungalow.floors.reduce((sum, floor) => sum + floor.room_polygon_count, 0));
});

test("rights metadata is copied and restricted records cannot pass the commercial filter", () => {
  const catalog = buildSearchCatalog(dataset, manifest);
  const source = dataset.projects.find((project) => project.project_id === "bungalow_001");
  const record = catalog.records.find((candidate) => candidate.project_id === source.project_id);
  assert.equal(record.source_rights_status, source.source_rights_status);
  assert.equal(record.usage_scope, source.usage_scope);
  assert.equal(record.commercial_generator_eligible, source.commercial_generator_eligible);
  const restricted = {
    ...record,
    usage_scope: "commercial_generator",
    source_rights_status: "restricted_reference",
    reconstruction_only: true,
    commercial_generator_eligible: true,
  };
  assert.deepEqual(filterCatalogRecords([restricted], { usage_scope: "commercial_generator" }), []);
  const commercial = filterCatalogRecords(catalog.records, { usage_scope: "commercial_generator" });
  assert.equal(commercial.length, 0);
});

test("filters combine storeys, room minima, tags, and quality", () => {
  const catalog = buildSearchCatalog(dataset, manifest);
  const matches = filterCatalogRecords(catalog.records, {
    house_type: "onehalfstorey",
    habitable_floor_count: 2,
    quality_status: "passed",
    required_tags: ["utility_room", "office"],
    minimum_room_counts: { eltern: 1, kind: 2, bad: 1 },
  });
  assert.ok(matches.length > 0);
  assert.ok(matches.every((record) =>
    record.house_type === "onehalfstorey"
    && record.habitable_floor_count === 2
    && record.quality_status === "passed"
    && record.program_tags.includes("utility_room")
    && record.program_tags.includes("office")
    && record.room_counts.kind >= 2
  ));
});

test("catalog output is byte-stable for unchanged source data", () => {
  assert.equal(stableJson(buildSearchCatalog(dataset, manifest)), stableJson(buildSearchCatalog(dataset, manifest)));
});

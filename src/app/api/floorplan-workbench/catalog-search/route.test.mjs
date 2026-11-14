import assert from "node:assert/strict";
import test from "node:test";

const origin = process.env.FLOORPLAN_WORKBENCH_ORIGIN || "http://127.0.0.1:3020";

async function search(query = "") {
  const response = await fetch(`${origin}/api/floorplan-workbench/catalog-search${query ? `?${query}` : ""}`);
  return { status: response.status, body: await response.json() };
}

test("empty filters return the full catalogue, capped at the default limit", async () => {
  const { status, body } = await search();
  assert.equal(status, 200);
  assert.equal(body.schema, "zf-floorplan-workbench-catalog-search-v1");
  assert.equal(body.total_catalogue_projects, 310);
  assert.equal(body.matched_count, 310);
  assert.equal(body.returned_count, 60);
  assert.equal(body.truncated, true);
});

test("houseType narrows results to only that house type", async () => {
  const { status, body } = await search("houseType=bungalow&limit=200");
  assert.equal(status, 200);
  assert.ok(body.matched_count > 0);
  assert.ok(body.results.every((result) => result.house_type === "bungalow"));
});

test("combined houseType and requiredTags intersect", async () => {
  const { body } = await search("houseType=onehalfstorey&requiredTags=office,guest_wc,utility_room&limit=200");
  assert.ok(body.matched_count > 0);
  assert.ok(body.results.every((result) =>
    result.house_type === "onehalfstorey"
    && ["office", "guest_wc", "utility_room"].every((tag) => result.program_tags.includes(tag))
  ));
});

test("the three demo presets each return at least one match", async () => {
  const presets = [
    "houseType=onehalfstorey&requiredTags=office,guest_wc,utility_room",
    "houseType=bungalow&requiredTags=office,guest_wc,child_rooms",
    "houseType=twostorey&requiredTags=garage",
  ];
  for (const query of presets) {
    const { body } = await search(query);
    assert.ok(body.matched_count > 0, `preset "${query}" returned no matches`);
  }
});

test("unknown house type or tag returns an empty result, not an error", async () => {
  const { status, body } = await search("houseType=not-a-real-type");
  assert.equal(status, 200);
  assert.equal(body.matched_count, 0);
  assert.deepEqual(body.results, []);
});

test("minRoom filters by minimum room count", async () => {
  const { body: unfiltered } = await search("houseType=bungalow&limit=200");
  const { body: filtered } = await search("houseType=bungalow&minRoom=kind:2&limit=200");
  assert.ok(filtered.matched_count <= unfiltered.matched_count);
  assert.ok(filtered.results.every((result) => (result.room_counts.kind ?? 0) >= 2));
});

test("response never leaks the full catalogue payload shape", async () => {
  const { body } = await search("limit=1");
  const [result] = body.results;
  assert.ok(result);
  assert.equal(Object.prototype.hasOwnProperty.call(result, "derived_counts"), false);
  assert.equal(Object.prototype.hasOwnProperty.call(result, "element_counts"), false);
  assert.equal(Object.prototype.hasOwnProperty.call(result, "annotation_sha256"), false);
});

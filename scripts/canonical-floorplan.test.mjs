import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

import {
  CANONICAL_FLOORPLAN_SCHEMA_VERSION,
  CanonicalFloorplanValidationError,
  canonicalFloorplanGeometrySha256,
  loadCanonicalFloorplan,
  validateCanonicalFloorplan,
  withCanonicalGeometryHash,
} from "../src/lib/generator/canonical-floorplan.mjs";

const rect = (x, y, width, height) => [
  [x, y],
  [x + width, y],
  [x + width, y + height],
  [x, y + height],
];

function makeStorey(prefix, levelIndex, elevationMm) {
  const livingId = `${prefix}-living`;
  const hallId = `${prefix}-hall`;
  const wallIds = {
    northLiving: `${prefix}-wall-north-living`,
    northHall: `${prefix}-wall-north-hall`,
    southLiving: `${prefix}-wall-south-living`,
    southHall: `${prefix}-wall-south-hall`,
    west: `${prefix}-wall-west`,
    east: `${prefix}-wall-east`,
    divider: `${prefix}-wall-divider`,
  };
  const walls = [
    {
      id: wallIds.northLiving,
      wall_type: "exterior",
      start_mm: [0, 0],
      end_mm: [6000, 0],
      thickness_mm: 350,
      separates: ["outside", livingId],
    },
    {
      id: wallIds.northHall,
      wall_type: "exterior",
      start_mm: [6000, 0],
      end_mm: [10000, 0],
      thickness_mm: 350,
      separates: ["outside", hallId],
    },
    {
      id: wallIds.southLiving,
      wall_type: "exterior",
      start_mm: [0, 8000],
      end_mm: [6000, 8000],
      thickness_mm: 350,
      separates: ["outside", livingId],
    },
    {
      id: wallIds.southHall,
      wall_type: "exterior",
      start_mm: [6000, 8000],
      end_mm: [10000, 8000],
      thickness_mm: 350,
      separates: ["outside", hallId],
    },
    {
      id: wallIds.west,
      wall_type: "exterior",
      start_mm: [0, 0],
      end_mm: [0, 8000],
      thickness_mm: 350,
      separates: ["outside", livingId],
    },
    {
      id: wallIds.east,
      wall_type: "exterior",
      start_mm: [10000, 0],
      end_mm: [10000, 8000],
      thickness_mm: 350,
      separates: ["outside", hallId],
    },
    {
      id: wallIds.divider,
      wall_type: "partition",
      start_mm: [6000, 0],
      end_mm: [6000, 8000],
      thickness_mm: 100,
      separates: [livingId, hallId],
    },
  ];
  const openings = [
    {
      id: `${prefix}-door-living`,
      opening_type: "door",
      wall_id: wallIds.divider,
      offset_mm: 1800,
      width_mm: 900,
      connects: [livingId, hallId],
      traversable: true,
    },
    {
      id: `${prefix}-window-living`,
      opening_type: "window",
      wall_id: wallIds.northLiving,
      offset_mm: 1500,
      width_mm: 1800,
      connects: ["outside", livingId],
      traversable: false,
      sill_height_mm: 900,
      height_mm: 1350,
    },
  ];
  if (levelIndex === 0) {
    openings.push({
      id: "door-entry",
      opening_type: "door",
      wall_id: wallIds.east,
      offset_mm: 3200,
      width_mm: 1000,
      connects: ["outside", hallId],
      traversable: true,
    });
  }
  return {
    id: prefix,
    level_index: levelIndex,
    elevation_mm: elevationMm,
    planning_boundary_mm: rect(0, 0, 10000, 8000),
    rooms: [
      {
        id: livingId,
        name: levelIndex === 0 ? "Wohnen" : "Schlafen",
        room_type: levelIndex === 0 ? "living" : "bedroom",
        access_required: true,
        habitable: true,
        polygon_mm: rect(0, 0, 6000, 8000),
      },
      {
        id: hallId,
        name: levelIndex === 0 ? "Diele" : "Flur",
        room_type: "circulation",
        access_required: true,
        habitable: false,
        polygon_mm: rect(6000, 0, 4000, 8000),
      },
    ],
    walls,
    openings,
    slab_openings: levelIndex === 1
      ? [{
          id: "upper-stair-opening",
          opening_type: "stairs",
          polygon_mm: rect(7500, 2500, 2000, 3000),
        }]
      : [],
  };
}

function makeValidPlan() {
  const plan = {
    schema_version: CANONICAL_FLOORPLAN_SCHEMA_VERSION,
    plan_id: "synthetic-two-storey-valid",
    units: "mm",
    coordinate_system: {
      origin: "northwest",
      x_positive: "east",
      y_positive: "south",
      integer_precision_mm: 1,
      north_rotation_degrees: null,
      wall_reference: "centerline",
    },
    building: {
      storey_type: "2_storey",
    },
    footprint: {
      boundary_reference: "exterior_wall_centerline",
      boundary_polygon_mm: rect(0, 0, 10000, 8000),
    },
    storeys: [
      makeStorey("groundfloor", 0, 0),
      makeStorey("upperfloor", 1, 2800),
    ],
    entrance: {
      storey_id: "groundfloor",
      opening_id: "door-entry",
      enters_room_id: "groundfloor-hall",
    },
    stairs: [{
      id: "stair-main",
      stair_type: "half_turn",
      from_storey_id: "groundfloor",
      to_storey_id: "upperfloor",
      clear_width_mm: 900,
      direction: "up",
      path_mm: [
        [8500, 5200],
        [8500, 2800],
      ],
      interfaces: [
        {
          storey_id: "groundfloor",
          footprint_polygon_mm: rect(7500, 2500, 2000, 3000),
          arrival_room_id: "groundfloor-hall",
          slab_opening_id: null,
        },
        {
          storey_id: "upperfloor",
          footprint_polygon_mm: rect(7500, 2500, 2000, 3000),
          arrival_room_id: "upperfloor-hall",
          slab_opening_id: "upper-stair-opening",
        },
      ],
    }],
    provenance: {
      source_kind: "synthetic_test",
      source_project_id: "synthetic-two-storey-valid",
      source_schema_version: "synthetic-test-v1",
      source_annotation_sha256: null,
      conversion_method: "hand-authored-test-fixture",
      scale_anchor: {
        status: "not_applicable_synthetic",
        kind: null,
        source_segment_normalized: null,
        length_mm: null,
      },
    },
    geometry_hash: {
      algorithm: "sha256",
      canonicalization: "dmh-canonical-geometry-v1",
      value: "0".repeat(64),
    },
    approval: {
      state: "internal_reference",
      quality_status: "passed",
      rights_status: "not_explicitly_recorded",
      usage_scope: "internal_reference_only",
      approved_by: null,
      approved_at: null,
      rights_evidence_reference: null,
    },
  };
  return withCanonicalGeometryHash(plan);
}

function mutatedPlan(mutate, { rehash = true } = {}) {
  let plan = structuredClone(makeValidPlan());
  mutate(plan);
  if (rehash) plan = withCanonicalGeometryHash(plan);
  return plan;
}

function assertHasError(plan, code) {
  const report = validateCanonicalFloorplan(plan);
  assert.equal(report.passed, false, `expected ${code}, got no errors`);
  assert.ok(
    report.errors.some((error) => error === code || error.startsWith(`${code}:`)),
    `expected ${code}, got ${report.errors.join(", ")}`,
  );
}

test("machine-readable schema is valid JSON and names the runtime version", async () => {
  const schema = JSON.parse(await readFile(
    new URL("../src/lib/generator/canonical-floorplan.schema.json", import.meta.url),
    "utf8",
  ));
  assert.equal(schema.properties.schema_version.const, CANONICAL_FLOORPLAN_SCHEMA_VERSION);
  assert.equal(schema.additionalProperties, false);
});

test("loads a valid deterministic two-storey canonical plan", () => {
  const plan = makeValidPlan();
  const report = validateCanonicalFloorplan(plan);
  assert.equal(report.passed, true, report.errors.join(", "));
  assert.deepEqual(report.errors, []);
  assert.equal(report.stats.storeyCount, 2);
  assert.equal(report.stats.roomCount, 4);
  assert.equal(report.stats.stairCount, 1);
  assert.equal(loadCanonicalFloorplan(JSON.stringify(plan)).plan_id, plan.plan_id);
});

test("geometry hash is stable and excludes approval metadata", () => {
  const plan = makeValidPlan();
  const changedApproval = structuredClone(plan);
  changedApproval.approval.approved_by = "Internal reviewer";
  assert.equal(
    canonicalFloorplanGeometrySha256(changedApproval),
    canonicalFloorplanGeometrySha256(plan),
  );
});

test("loader rejects malformed JSON with a structured validation error", () => {
  assert.throws(
    () => loadCanonicalFloorplan("{not-json"),
    (error) => error instanceof CanonicalFloorplanValidationError
      && error.report.errors.includes("invalid_json"),
  );
});

test("rejects unsupported versions and unknown properties", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.schema_version = "dmh-canonical-floorplan-v2";
  }), "unsupported_schema_version");
  assertHasError(mutatedPlan((plan) => {
    plan.free_generation_hint = true;
  }), "unknown_property");
});

test("rejects non-finite or non-integer millimetre geometry", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].rooms[0].polygon_mm[0][0] = "NaN";
  }), "invalid_integer_mm");
});

test("rejects degenerate and self-intersecting room polygons", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].rooms[0].polygon_mm[1] = [0, 0];
  }), "polygon_zero_length_edge");
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].rooms[0].polygon_mm = [
      [0, 0],
      [6000, 0],
      [6000, 6000],
      [1000, 6000],
      [1000, 2000],
      [5000, 2000],
      [5000, 8000],
      [0, 8000],
    ];
  }), "polygon_self_intersection");
});

test("rejects diagonal V1 geometry", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].walls.find((wall) => wall.id === "groundfloor-wall-divider").end_mm = [6100, 8000];
  }), "wall_not_rectilinear");
});

test("rejects walls outside the planning boundary", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].walls[0].start_mm = [-100, 0];
  }), "wall_outside_planning_boundary");
});

test("rejects rooms outside the planning boundary", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].rooms[0].polygon_mm = rect(-100, 0, 6100, 8000);
  }), "room_outside_planning_boundary");
});

test("rejects room overlaps and coverage gaps", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].rooms[1].polygon_mm = rect(5900, 0, 4100, 8000);
  }), "room_overlap");
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].rooms[0].polygon_mm = rect(0, 0, 5900, 8000);
  }), "room_coverage_gap");
});

test("rejects walls that do not cover a room boundary", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].walls = plan.storeys[0].walls.filter(
      (wall) => wall.id !== "groundfloor-wall-west",
    );
  }), "room_boundary_without_wall");
});

test("rejects openings on unknown walls or beyond wall length", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].openings[0].wall_id = "wall-missing";
  }), "opening_references_unknown_wall");
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].openings[0].offset_mm = 7600;
    plan.storeys[0].openings[0].width_mm = 900;
  }), "opening_outside_wall");
});

test("rejects opening connections that disagree with wall topology", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].openings[0].connects = ["outside", "groundfloor-living"];
  }), "opening_connections_mismatch_wall");
});

test("rejects overlapping openings on one wall", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].openings.push({
      id: "groundfloor-window-overlap",
      opening_type: "window",
      wall_id: "groundfloor-wall-north-living",
      offset_mm: 2000,
      width_mm: 1800,
      connects: ["outside", "groundfloor-living"],
      traversable: false,
      sill_height_mm: 900,
      height_mm: 1350,
    });
  }), "openings_overlap");
});

test("rejects an entrance that is not an exterior door", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.entrance.opening_id = "groundfloor-door-living";
    plan.entrance.enters_room_id = "groundfloor-living";
  }), "entrance_connections_invalid");
});

test("rejects any access-required room unreachable from the entrance", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[1].openings = plan.storeys[1].openings.filter(
      (opening) => opening.id !== "upperfloor-door-living",
    );
  }), "room_unreachable_from_entrance");
});

test("rejects stair interfaces shifted beyond the five millimetre tolerance", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.stairs[0].interfaces[1].footprint_polygon_mm =
      plan.stairs[0].interfaces[1].footprint_polygon_mm
        .map(([x, y]) => [x + 10, y]);
  }), "stair_interfaces_not_aligned");
});

test("rejects missing or misaligned upper stair slab openings", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[1].slab_openings = [];
  }), "upper_stair_slab_opening_invalid");
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[1].slab_openings[0].polygon_mm =
      plan.storeys[1].slab_openings[0].polygon_mm.map(([x, y]) => [x + 10, y]);
  }), "stair_slab_opening_not_aligned");
});

test("rejects geometry mutations when the stored hash is stale", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.storeys[0].rooms[0].name = "Changed geometry label";
  }, { rehash: false }), "geometry_hash_mismatch");
});

test("rejects commercial use without recorded rights and approval evidence", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.approval.state = "commercial_approved";
    plan.approval.usage_scope = "commercial_generator";
  }), "commercial_rights_not_confirmed");
});

test("rejects synthetic plans even when commercial approval fields are populated", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.approval = {
      state: "commercial_approved",
      quality_status: "passed",
      rights_status: "confirmed_owned",
      usage_scope: "commercial_generator",
      approved_by: "reviewer-1",
      approved_at: "2026-07-30T12:00:00.000Z",
      rights_evidence_reference: "rights-record-1",
    };
  }), "synthetic_source_cannot_be_commercial");
});

test("requires a verified physical scale for real annotated sources", () => {
  assertHasError(mutatedPlan((plan) => {
    plan.provenance.source_kind = "real_annotated";
    plan.provenance.source_annotation_sha256 = "a".repeat(64);
  }), "real_source_requires_verified_scale");
});

test("accepts commercial approval only with a verified real source and evidence", () => {
  const plan = mutatedPlan((candidate) => {
    candidate.provenance = {
      source_kind: "real_annotated",
      source_project_id: "owned-reference-1",
      source_schema_version: "simplifier-annotations-v1",
      source_annotation_sha256: "a".repeat(64),
      conversion_method: "verified-overall-width",
      scale_anchor: {
        status: "verified",
        kind: "overall_width",
        source_segment_normalized: [[0.1, 0.2], [0.9, 0.2]],
        length_mm: 10000,
      },
    };
    candidate.approval = {
      state: "commercial_approved",
      quality_status: "passed",
      rights_status: "confirmed_owned",
      usage_scope: "commercial_generator",
      approved_by: "reviewer-1",
      approved_at: "2026-07-30T12:00:00.000Z",
      rights_evidence_reference: "rights-record-1",
    };
  });
  const report = validateCanonicalFloorplan(plan);
  assert.equal(report.passed, true, report.errors.join(", "));
});

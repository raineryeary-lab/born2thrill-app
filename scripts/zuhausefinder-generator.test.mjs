import assert from "node:assert/strict";
import test from "node:test";
import {
  classifyZuhausefinderFloorplan,
  mapZuhausefinderBrief,
  validateZuhausefinderBrief,
} from "../src/lib/generator/zuhausefinder-brief.mjs";
import {
  assertSafeGeneratedSvg,
  customerFacingQualityPassed,
  floorplanQuality,
  renderFloorplanSvg,
  selectQualityVariant,
} from "../src/lib/generator/floorplan-svg.mjs";
import {
  buildZuhausefinderVisualizationContext,
  geometrySha256,
  planGeometryGuideModel,
} from "../src/lib/generator/zuhausefinder-visualization.mjs";

const input = {
  schema: "dmh-floorplan-brief-v1",
  request_id: "ZF-TEST-1234",
  design_fingerprint: "a".repeat(64),
  generation_attempt: 2,
  household: { description: "Zwei Erwachsene und zwei Kinder" },
  site: { description: "Grundstück vorhanden, Garten nach Süden" },
  area: { target_living_area_m2: 145 },
  ranked_storey_candidates: [{ type: "one_and_half_storeys", score: 1 }],
  room_program: {
    description: "Drei Schlafzimmer, Büro, Gäste-WC, Bad und HWR",
  },
  zoning_strategy: {
    public_zone: "Kochen, Essen und Wohnen offen zum Garten",
    private_zone: "Ruhige Schlafräume",
    service_zone: "HWR und Gäste-WC kompakt",
  },
  access_and_future: { description: "Später altersgerecht nutzbar" },
  exterior_preferences: {
    description: "Warm, ruhig und mit natürlichen Materialien",
    roof_answer: "Satteldach – vertraut und flexibel",
  },
  normalized_preference_scores: {
    openness: 0.85,
    garden_connection: 0.85,
    accessibility: 0.75,
  },
  reference_search: {
    search_tags: [
      "house_type:onehalfstorey",
      "floors:1.5",
      "kitchen:semi-open",
      "garden:private",
      "stair:separable",
      "office:separate",
      "zoning:day_down_flexible_up",
      "service_core:compact",
      "flexible_rooms:yes",
      "unsafe:<script>",
    ],
  },
  generation_policy: {
    reference_first: true,
    invent_from_personality: false,
  },
  output_requirements: {
    mandatory_label: "Schematischer Konzeptvorschlag – keine Architekturplanung.",
  },
};

test("maps a complete ZuhauseFinder brief without contact data", () => {
  const validated = validateZuhausefinderBrief(input);
  assert.equal(validated.selected_storey.type, "one_and_half_storeys");
  const brief = mapZuhausefinderBrief(input);
  assert.equal(brief.area, 145);
  assert.equal(brief.floors, 2);
  assert.equal(brief.storeyType, "1_5_storey");
  assert.equal(brief.children, 2);
  assert.equal(brief.bedrooms, 3);
  assert.equal(brief.office, true);
  assert.equal(brief.guestWc, true);
  assert.equal(brief.utilityRoom, true);
  assert.equal(brief.kitchen, "semi-open");
  assert.equal(brief.gardenConnection, "private");
  assert.equal(brief.stairPreference, "separable");
  assert.equal(brief.generationAttempt, 2);
  assert.equal(brief.streetDirection, "unbekannt");
  assert.equal(brief.gardenDirection, "unbekannt");
  assert.equal(brief.roof, "Satteldach – vertraut und flexibel");
  assert.ok(brief.priorities.includes("service_core:compact"));
  assert.equal(brief.priorities.some((priority) => priority.includes("<script>")), false);
  assert.equal("email" in brief, false);
  assert.match(brief.critiqueNotes, /90 cm/);
});

test("rejects personality-only or incomplete requests", () => {
  assert.throws(
    () => validateZuhausefinderBrief({
      ...input,
      area: { target_living_area_m2: null },
    }),
    /Wohnfläche/,
  );
  assert.throws(
    () => validateZuhausefinderBrief({
      ...input,
      generation_policy: {
        reference_first: false,
        invent_from_personality: true,
      },
    }),
    /referenzbasiert/,
  );
  assert.throws(
    () => validateZuhausefinderBrief({
      ...input,
      design_fingerprint: "not-a-fingerprint",
    }),
    /Fingerprint/,
  );
  assert.throws(
    () => validateZuhausefinderBrief({
      ...input,
      generation_attempt: 21,
    }),
    /Generierungsversuch/,
  );
});

test("builds deterministic visualization facts without invented orientation or roof confidence", () => {
  const brief = mapZuhausefinderBrief(input);
  const variant = {
    storeyType: "1_5_storey",
    floors: [
      {
        floor: 0,
        name: "Erdgeschoss",
        referenceLayoutId: "onehalfstorey_005",
        referenceFootprint: { x: 0, y: 0, width: 500, height: 400 },
        rooms: [
          {
            id: "living",
            kind: "living",
            x: 0,
            y: 0,
            width: 300,
            height: 400,
          },
          {
            id: "service",
            kind: "service",
            x: 300,
            y: 0,
            width: 200,
            height: 400,
          },
        ],
        stair: null,
      },
      {
        floor: 1,
        name: "Dachgeschoss",
        referenceLayoutId: "onehalfstorey_005",
        referenceFootprint: { x: 0, y: 0, width: 500, height: 400 },
        rooms: [
          {
            id: "sleeping",
            kind: "sleeping",
            x: 0,
            y: 0,
            width: 500,
            height: 400,
          },
        ],
        stair: null,
      },
    ],
    metrics: {
      footprintWidthM: 10,
      footprintDepthM: 8,
      referenceLayoutId: "onehalfstorey_005",
    },
  };
  const context = buildZuhausefinderVisualizationContext(input, brief, variant);
  assert.equal(context.geometry_sha256, geometrySha256(variant));
  assert.deepEqual(context.orientation, {
    street: null,
    garden: null,
    confidence: "unverified",
  });
  assert.equal(context.roof.form, "satteldach");
  assert.equal(context.roof.confidence, "verified");
  assert.ok(context.must_match.includes("Dachform: satteldach"));
  assert.equal(context.footprint.aspect_ratio, 1.25);

  const inferredInput = {
    ...input,
    exterior_preferences: {
      description: "Modern und klar",
      roof_answer: "",
    },
  };
  const inferredBrief = mapZuhausefinderBrief(inferredInput);
  const inferred = buildZuhausefinderVisualizationContext(
    inferredInput,
    inferredBrief,
    variant,
  );
  assert.equal(inferred.roof.confidence, "inferred");
  assert.equal(inferred.must_match.some((entry) => entry.startsWith("Dachform:")), false);
  assert.ok(inferred.unresolved.includes("exact_roof_form"));

  const guideModel = planGeometryGuideModel(variant);
  assert.equal(guideModel.floors.length, 2);
  assert.equal("name" in guideModel.floors[0], false);
  assert.equal(geometrySha256(variant), geometrySha256(structuredClone(variant)));
  assert.notEqual(
    geometrySha256(variant),
    geometrySha256({
      ...variant,
      metrics: { ...variant.metrics, footprintDepthM: 8.5 },
    }),
  );
});

test("renders a self-contained safe floorplan SVG", () => {
  const variant = {
    floors: [{
      name: "Erdgeschoss",
      rooms: [
        {
          name: "Wohnen & Essen",
          kind: "living",
          area: 42,
          x: 40,
          y: 40,
          width: 300,
          height: 210,
          polygon: [
            { x: 40, y: 40 },
            { x: 340, y: 40 },
            { x: 340, y: 250 },
            { x: 40, y: 250 },
          ],
        },
        {
          name: "HWR / HTR",
          kind: "service",
          area: 10,
          x: 340,
          y: 40,
          width: 160,
          height: 210,
        },
      ],
      referenceFootprint: { x: 40, y: 40, width: 460, height: 210 },
      referenceElements: [{
        type: "window",
        points: [{ x: 120, y: 40 }, { x: 200, y: 40 }],
      }],
      stairPath: [],
    }],
    metrics: { referenceLayoutId: "reference-house-1" },
  };
  const svg = renderFloorplanSvg(variant, {
    requestId: "ZF-TEST-1234",
    mandatoryLabel: input.output_requirements.mandatory_label,
  });
  assert.equal(assertSafeGeneratedSvg(svg), svg);
  assert.match(svg, /Wohnen &amp; Essen/);
  assert.match(svg, /HWR \/ HTR/);
  assert.match(svg, /reference-house-1/);
  assert.doesNotMatch(
    svg.replace('xmlns="http://www.w3.org/2000/svg"', ""),
    /<script|https?:\/\//i,
  );
  assert.throws(
    () => assertSafeGeneratedSvg(`${svg}<script>alert(1)</script>`),
    /nicht erlaubte/,
  );
  assert.throws(
    () => assertSafeGeneratedSvg(svg.replace("<rect", '<rect onclick="alert(1)"')),
    /nicht erlaubte/,
  );
  assert.throws(
    () => assertSafeGeneratedSvg(svg.replace("</svg>", '<image href="data:image/svg+xml,x"/></svg>')),
    /nicht erlaubte/,
  );
});

test("prefers variants without critical geometry failures", () => {
  const weak = {
    score: 99,
    checks: [
      { label: "Interne Kollisionsprüfung: Treppe liegt frei", passed: false },
    ],
  };
  const safe = {
    score: 88,
    checks: [
      { label: "Interne Kollisionsprüfung: Treppe liegt frei", passed: true },
      { label: "Fluranteil im Zielbereich", passed: false },
    ],
  };
  assert.equal(selectQualityVariant([weak, safe]), safe);
  assert.equal(floorplanQuality(weak).criticalFailures.length, 1);
  assert.equal(floorplanQuality(safe).criticalFailures.length, 0);
  assert.equal(customerFacingQualityPassed(floorplanQuality(weak)), false);
  assert.equal(customerFacingQualityPassed(floorplanQuality(safe)), true);
});

test("classifies output without making it automatically training eligible", () => {
  const brief = mapZuhausefinderBrief(input);
  const variant = {
    floors: [{ name: "Erdgeschoss" }, { name: "Dachgeschoss" }],
    metrics: { referenceLayoutId: "onehalfstorey_005" },
  };
  const classification = classifyZuhausefinderFloorplan(
    input,
    brief,
    variant,
    {
      failedChecks: ["Interne Kollisionsprüfung: Treppe liegt frei"],
      criticalFailures: ["Interne Kollisionsprüfung: Treppe liegt frei"],
    },
  );
  assert.deepEqual(classification, {
    schema: "dmh-floorplan-classification-v1",
    house_type: "one_and_half_storeys",
    storeys: 1.5,
    floor_count: 2,
    living_area_m2: 145,
    area_band: "family",
    household_size: 4,
    bedroom_count: 3,
    bathroom_count: 1,
    room_program_tags: [
      "office",
      "guest_wc",
      "utility_room",
      "accessible",
    ],
    reference_search_tags: [
      "house_type:onehalfstorey",
      "floors:1.5",
      "kitchen:semi-open",
      "garden:private",
      "stair:separable",
      "office:separate",
      "zoning:day_down_flexible_up",
      "service_core:compact",
      "flexible_rooms:yes",
    ],
    reference_layout_id: "onehalfstorey_005",
    reference_source: "annotated_floorplan_corpus",
    geometry_quality: "review_required",
    data_origin: "structured_brief",
    storey_model: {
      type: "1_5_storey",
      shared_stair_core: false,
    },
    training_status: "reference_generated",
    training_eligible: false,
  });
});

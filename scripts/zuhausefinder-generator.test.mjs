import assert from "node:assert/strict";
import test from "node:test";
import {
  classifyZuhausefinderFloorplan,
  mapZuhausefinderBrief,
  validateZuhausefinderBrief,
} from "../src/lib/generator/zuhausefinder-brief.mjs";
import {
  assertSafeGeneratedSvg,
  floorplanQuality,
  renderFloorplanSvg,
  selectQualityVariant,
} from "../src/lib/generator/floorplan-svg.mjs";

const input = {
  schema: "dmh-floorplan-brief-v1",
  request_id: "ZF-TEST-1234",
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
  normalized_preference_scores: {
    openness: 0.85,
    garden_connection: 0.85,
    accessibility: 0.75,
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
  assert.equal(brief.children, 2);
  assert.equal(brief.bedrooms, 3);
  assert.equal(brief.office, true);
  assert.equal(brief.guestWc, true);
  assert.equal(brief.utilityRoom, true);
  assert.equal(brief.kitchen, "open");
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
      "open_kitchen",
    ],
    reference_layout_id: "onehalfstorey_005",
    reference_source: "annotated_floorplan_corpus",
    geometry_quality: "review_required",
    data_origin: "structured_brief",
    training_status: "reference_generated",
    training_eligible: false,
  });
});

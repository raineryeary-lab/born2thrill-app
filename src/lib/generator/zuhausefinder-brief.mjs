const NUMBER_WORDS = new Map([
  ["ein", 1],
  ["eine", 1],
  ["einen", 1],
  ["eins", 1],
  ["zwei", 2],
  ["drei", 3],
  ["vier", 4],
  ["fünf", 5],
  ["funf", 5],
  ["fuenf", 5],
  ["sechs", 6],
  ["sieben", 7],
  ["acht", 8],
]);

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function text(value) {
  return typeof value === "string" ? value.trim() : "";
}

function normalize(value) {
  return text(value)
    .toLocaleLowerCase("de-DE")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}

function countBeforeTerm(value, terms, fallback) {
  const source = normalize(value);
  for (const term of terms) {
    const match = source.match(new RegExp(`(?:^|\\s)(\\d+|${[...NUMBER_WORDS.keys()].join("|")})\\s+${term}\\b`, "i"));
    if (!match) continue;
    const numeric = Number(match[1]);
    if (Number.isFinite(numeric)) return numeric;
    return NUMBER_WORDS.get(match[1]) ?? fallback;
  }
  return fallback;
}

function includesAny(value, terms) {
  const source = normalize(value);
  return terms.some((term) => source.includes(normalize(term)));
}

function requiredRecord(value, name) {
  if (!isRecord(value)) throw new Error(`${name} fehlt.`);
  return value;
}

const REFERENCE_TAG_VALUES = {
  house_type: new Set(["bungalow", "onehalfstorey", "twostorey"]),
  floors: new Set(["1", "1.5", "2"]),
  kitchen: new Set(["open", "semi-open"]),
  garden: new Set(["generous", "private"]),
  stair: new Set(["undecided", "feature", "separable"]),
  office: new Set(["separate", "integrated-flexible"]),
  zoning: new Set([
    "day_down_private_up",
    "day_private_wings",
    "day_down_flexible_up",
  ]),
  service_core: new Set(["compact", "balanced"]),
  flexible_rooms: new Set(["yes", "optional"]),
};

function referenceSearchFor(value) {
  if (!isRecord(value)) {
    return {
      search_tags: [],
      tags: new Map(),
    };
  }
  const searchTags = [];
  const tags = new Map();
  for (const entry of Array.isArray(value.search_tags) ? value.search_tags : []) {
    const candidate = text(entry).toLowerCase();
    const match = candidate.match(/^([a-z_]+):([a-z0-9._-]+)$/);
    if (!match || !REFERENCE_TAG_VALUES[match[1]]?.has(match[2])) continue;
    searchTags.push(`${match[1]}:${match[2]}`);
    tags.set(match[1], match[2]);
  }
  return {
    ...value,
    search_tags: [...new Set(searchTags)],
    tags,
  };
}

export function validateZuhausefinderBrief(input) {
  const brief = requiredRecord(input, "Planungsbriefing");
  if (brief.schema !== "dmh-floorplan-brief-v1") {
    throw new Error("Das Grundriss-Briefing hat eine unbekannte Version.");
  }
  if (!/^[A-Z0-9-]{6,64}$/i.test(text(brief.request_id))) {
    throw new Error("Die Anfragekennung ist ungültig.");
  }
  const designFingerprint = text(brief.design_fingerprint).toLowerCase();
  if (!/^[a-f0-9]{64}$/.test(designFingerprint)) {
    throw new Error("Der Plan-Fingerprint ist ungültig.");
  }
  const generationAttempt = Number(brief.generation_attempt ?? 0);
  if (
    !Number.isInteger(generationAttempt) ||
    generationAttempt < 0 ||
    generationAttempt > 20
  ) {
    throw new Error("Der Generierungsversuch ist ungültig.");
  }

  const household = requiredRecord(brief.household, "Haushalt");
  const area = requiredRecord(brief.area, "Wohnfläche");
  const roomProgram = requiredRecord(brief.room_program, "Raumprogramm");
  const zoning = requiredRecord(brief.zoning_strategy, "Zonierung");
  const policy = requiredRecord(brief.generation_policy, "Generierungsregeln");
  const targetArea = Number(area.target_living_area_m2);
  if (!Number.isFinite(targetArea) || targetArea < 70 || targetArea > 400) {
    throw new Error("Die Wohnfläche muss zwischen 70 und 400 m² liegen.");
  }
  if (text(household.description).length < 3) {
    throw new Error("Die Haushaltsbeschreibung fehlt.");
  }
  if (text(roomProgram.description).length < 3) {
    throw new Error("Das Raumprogramm fehlt.");
  }
  if (text(zoning.public_zone).length < 3) {
    throw new Error("Die Beschreibung des Wohnbereichs fehlt.");
  }
  if (policy.reference_first !== true || policy.invent_from_personality !== false) {
    throw new Error("Der Generator darf nur referenzbasiert arbeiten.");
  }

  const candidates = Array.isArray(brief.ranked_storey_candidates)
    ? brief.ranked_storey_candidates.filter(isRecord)
    : [];
  const storey = candidates.find((candidate) =>
    ["bungalow", "one_and_half_storeys", "two_storeys"].includes(text(candidate.type))
  );
  if (!storey) {
    throw new Error("Eine eindeutige Geschossigkeit fehlt.");
  }
  return {
    ...brief,
    request_id: text(brief.request_id),
    design_fingerprint: designFingerprint,
    generation_attempt: generationAttempt,
    household,
    area: { ...area, target_living_area_m2: targetArea },
    room_program: roomProgram,
    zoning_strategy: zoning,
    generation_policy: policy,
    reference_search: referenceSearchFor(brief.reference_search),
    selected_storey: storey,
  };
}

export function mapZuhausefinderBrief(input) {
  const source = validateZuhausefinderBrief(input);
  const household = text(source.household.description);
  const roomProgram = text(source.room_program.description);
  const living = text(source.zoning_strategy.public_zone);
  const privateZone = text(source.zoning_strategy.private_zone);
  const site = isRecord(source.site) ? text(source.site.description) : "";
  const future = isRecord(source.access_and_future)
    ? text(source.access_and_future.description)
    : "";
  const exterior = isRecord(source.exterior_preferences)
    ? text(source.exterior_preferences.description)
    : "";
  const roofAnswer = isRecord(source.exterior_preferences)
    ? text(source.exterior_preferences.roof_answer)
    : "";
  const scores = isRecord(source.normalized_preference_scores)
    ? source.normalized_preference_scores
    : {};
  const referenceTags = source.reference_search.tags;
  const storeyType = text(source.selected_storey.type);
  const floors = storeyType === "bungalow" ? 1 : 2;
  const canonicalStoreyType = storeyType === "bungalow"
    ? "1_storey"
    : storeyType === "one_and_half_storeys"
      ? "1_5_storey"
      : "2_storey";
  const roof = includesAny(roofAnswer, [
    "satteldach",
    "walmdach",
    "flachdach",
    "pultdach",
  ])
    ? roofAnswer
    : storeyType === "one_and_half_storeys"
      ? "Satteldach"
      : includesAny(exterior, ["flachdach", "walmdach", "pultdach"])
        ? exterior
        : "zeitgemäßes, ruhig proportioniertes Dach";
  const adults = Math.min(8, countBeforeTerm(household, ["erwachsene", "personen"], 2));
  const children = Math.min(8, countBeforeTerm(household, ["kinder", "kind"], 0));
  const bedroomFallback = Math.max(1, children + 1);
  const bedrooms = Math.min(
    8,
    countBeforeTerm(roomProgram, ["schlafzimmer", "zimmer"], bedroomFallback),
  );
  const bathrooms = Math.min(
    4,
    countBeforeTerm(
      roomProgram,
      ["bader", "badezimmer", "bad"],
      includesAny(roomProgram, ["elternbad", "kinderbad", "zweites bad"]) ? 2 : 1,
    ),
  );
  const openness = Number(scores.openness);
  const gardenConnection = Number(scores.garden_connection);
  const accessibility = Number(scores.accessibility);
  const kitchen = referenceTags.get("kitchen") === "open"
    ? "open"
    : referenceTags.get("kitchen") === "semi-open"
      ? "semi-open"
      : includesAny(living, ["getrennt", "separate küche"])
    ? "separate"
    : includesAny(living, ["offen", "verbunden", "gemeinsam"]) || openness >= 0.7
      ? "open"
      : "semi-open";
  const gardenPreference = referenceTags.get("garden");
  const stairPreference = referenceTags.get("stair");
  const officePreference = referenceTags.get("office");

  return {
    projectName: source.request_id,
    area: source.area.target_living_area_m2,
    floors,
    storeyType: canonicalStoreyType,
    adults,
    children,
    bedrooms,
    bathrooms,
    office: Boolean(officePreference) ||
      includesAny(roomProgram, ["büro", "arbeitszimmer", "homeoffice"]),
    guestWc: includesAny(roomProgram, ["gäste-wc", "gaste-wc", "wc"]),
    utilityRoom: includesAny(roomProgram, ["hwr", "htr", "technik", "hauswirtschaft"]),
    groundFloorSleeping: includesAny(roomProgram + " " + future, [
      "schlafen im erdgeschoss",
      "schlafzimmer im erdgeschoss",
      "ebenerdig schlafen",
    ]),
    accessibility: accessibility >= 0.7 || includesAny(future, [
      "barriere",
      "altersgerecht",
      "ebenerdig",
      "rollstuhl",
    ]),
    kitchen,
    gardenConnection: gardenPreference === "generous" || gardenPreference === "private"
      ? gardenPreference
      : gardenConnection >= 0.7
      ? "generous"
      : gardenConnection <= 0.35
        ? "private"
        : "balanced",
    stairPreference: floors > 1 &&
      ["undecided", "feature", "separable"].includes(stairPreference)
      ? stairPreference
      : floors > 1
        ? "undecided"
        : "central",
    basement: includesAny(roomProgram + " " + site, ["keller", "unterkellert"]) ? "full" : "none",
    roof,
    style: exterior || "zeitlos-modern",
    streetDirection: "unbekannt",
    gardenDirection: "unbekannt",
    priorities: [
      living,
      privateZone,
      text(source.zoning_strategy.service_zone),
      future,
      ...source.reference_search.search_tags,
    ].filter(Boolean),
    generationAttempt: source.generation_attempt,
    critiqueNotes: [
      "Referenzgrundriss nur in kleinen kontrollierten Schritten verändern.",
      "Treppenlauf 90 cm breit, an einer Wand und auf beiden Etagen deckungsgleich.",
      "HWR/HTR möglichst etwa 10 m², WC mindestens 2 m².",
      "Keine unbrauchbaren Restflächen zwischen Treppe, Bad, HWR oder Flur.",
    ].join(" "),
  };
}

export function classifyZuhausefinderFloorplan(input, brief, variant, quality) {
  const source = validateZuhausefinderBrief(input);
  const targetArea = Number(source.area.target_living_area_m2);
  const failedChecks = Array.isArray(quality?.failedChecks) ? quality.failedChecks : [];
  const criticalFailures = Array.isArray(quality?.criticalFailures)
    ? quality.criticalFailures
    : [];
  const roomProgramTags = [
    brief.office && "office",
    brief.guestWc && "guest_wc",
    brief.utilityRoom && "utility_room",
    brief.groundFloorSleeping && "ground_floor_sleeping",
    brief.accessibility && "accessible",
    brief.kitchen === "open" && "open_kitchen",
  ].filter(Boolean);

  return {
    schema: "dmh-floorplan-classification-v1",
    house_type: source.selected_storey.type,
    storeys: source.selected_storey.type === "bungalow"
      ? 1
      : source.selected_storey.type === "one_and_half_storeys"
        ? 1.5
        : 2,
    floor_count: Array.isArray(variant?.floors) ? variant.floors.length : brief.floors,
    living_area_m2: targetArea,
    area_band: targetArea < 120 ? "compact" : targetArea < 170 ? "family" : "generous",
    household_size: Number(brief.adults || 0) + Number(brief.children || 0),
    bedroom_count: brief.bedrooms,
    bathroom_count: brief.bathrooms,
    room_program_tags: roomProgramTags,
    reference_search_tags: source.reference_search.search_tags,
    reference_layout_id: variant?.metrics?.referenceLayoutId || null,
    reference_source: text(source.generation_policy.reference_source)
      || "annotated_floorplan_corpus",
    geometry_quality: criticalFailures.length
      ? "review_required"
      : failedChecks.length
        ? "check_recommended"
        : "passed",
    data_origin: "structured_brief",
    storey_model: {
      type: brief.storeyType,
      shared_stair_core: brief.floors === 1 || Boolean(variant?.stairCore),
    },
    training_status: "reference_generated",
    training_eligible: false,
  };
}

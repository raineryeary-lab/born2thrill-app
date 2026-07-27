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

export function validateZuhausefinderBrief(input) {
  const brief = requiredRecord(input, "Planungsbriefing");
  if (brief.schema !== "dmh-floorplan-brief-v1") {
    throw new Error("Das Grundriss-Briefing hat eine unbekannte Version.");
  }
  if (!/^[A-Z0-9-]{6,64}$/i.test(text(brief.request_id))) {
    throw new Error("Die Anfragekennung ist ungültig.");
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
    household,
    area: { ...area, target_living_area_m2: targetArea },
    room_program: roomProgram,
    zoning_strategy: zoning,
    generation_policy: policy,
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
  const scores = isRecord(source.normalized_preference_scores)
    ? source.normalized_preference_scores
    : {};
  const storeyType = text(source.selected_storey.type);
  const floors = storeyType === "bungalow" ? 1 : 2;
  const roof = storeyType === "one_and_half_storeys"
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
  const kitchen = includesAny(living, ["getrennt", "separate küche"])
    ? "separate"
    : includesAny(living, ["offen", "verbunden", "gemeinsam"]) || openness >= 0.7
      ? "open"
      : "semi-open";

  return {
    projectName: source.request_id,
    area: source.area.target_living_area_m2,
    floors,
    adults,
    children,
    bedrooms,
    bathrooms,
    office: includesAny(roomProgram, ["büro", "arbeitszimmer", "homeoffice"]),
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
    gardenConnection: gardenConnection >= 0.7
      ? "generous"
      : gardenConnection <= 0.35
        ? "private"
        : "balanced",
    stairPreference: floors > 1 ? "undecided" : "central",
    basement: includesAny(roomProgram + " " + site, ["keller", "unterkellert"]) ? "full" : "none",
    roof,
    style: exterior || "zeitlos-modern",
    streetDirection: "Nord",
    gardenDirection: includesAny(site, ["süden", "süd", "sued"]) ? "Süd" : "unbekannt",
    priorities: [living, privateZone, text(source.zoning_strategy.service_zone), future].filter(Boolean),
    generationAttempt: 0,
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
    reference_layout_id: variant?.metrics?.referenceLayoutId || null,
    reference_source: text(source.generation_policy.reference_source)
      || "annotated_floorplan_corpus",
    geometry_quality: criticalFailures.length
      ? "review_required"
      : failedChecks.length
        ? "check_recommended"
        : "passed",
    data_origin: "structured_brief",
    training_status: "reference_generated",
    training_eligible: false,
  };
}

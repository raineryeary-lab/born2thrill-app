// Ausstattung symbol catalogue.
//
// Vocabulary for the furnishing layer, per plans/symbol-library-v1.md in
// born2thrill-local-workbench. Keys are German and match Rainer's drawings.
//
// A symbol records WHAT and WHERE. It never names a 3D model or a material —
// a style pack resolves key -> model + finish at render time, so one
// annotation renders modern, classic, or any style added later without
// re-annotating anything.
//
// Footprints are measured from Möbel3svg.svg at 33.5 mm per SVG unit,
// calibrated against the one dimension confirmed directly (Doppelbett
// 1800 x 2000) and cross-checked against Badewanne (1710 x 760 measured vs
// 1700 x 750 standard) and Vorwandinstallation (190 measured vs 150 stated).
//
// placement:
//   "stamp"  click to place; carries rotation and mirror
//   "path"   drawn along walls like the stairs tool; fixed depth, 90 corners
//   "rect"   dragged out; both dimensions chosen by the annotator
//
// footprint_mode:
//   "fixed"       real dimensions that must be respected (a WC is 360 wide)
//   "indicative"  a placeholder; the style pack decides the real size
//
// height:
//   "floor"    base on the floor (default)
//   "wall"     mounted at mount_height_mm, which is the item's CENTRE
//   "surface"  sits on a Küchenzeile or Insel worktop

// --- wall behaviour --------------------------------------------------------
// Three behaviours, not two. Most fitted things go tight against the wall, but
// upholstery cannot be jammed into plaster, and anything that sits on a
// worktop or in the middle of a room must never be pulled to a wall at all —
// the Küchenspüle belongs in the Küchenzeile, not against the plaster behind
// it.
//
// "gap" values are the real clearance a fitter would leave.
const WALL_FLUSH = new Set([
  "vorwandinstallation", "wand_wc", "waschtisch", "doppelwaschtisch",
  "handwaschbecken", "badewanne", "eckbadewanne", "dusche_klein", "dusche",
  "dusche_gross",
  "badheizkoerper", "kuechenzeile", "kuehlschrank", "hochschrank_herd",
  "kleiderschrank", "schrank_40", "schrank_60", "abstellschrank", "garderobe",
  "lowboard", "sideboard", "fernseher", "waschmaschine", "trockner",
]);

const WALL_GAP_MM = {
  doppelbett: 50, einzelbett: 50,
  ecksofa: 100, sofa_3sitzer: 100, sofa_2sitzer: 100, sofa_1sitzer: 100,
  schreibtisch: 50, schreibtisch_kind: 50,
};

function wallBehaviour(key) {
  if (WALL_FLUSH.has(key)) return { mode: "flush", gap_mm: 0 };
  if (key in WALL_GAP_MM) return { mode: "gap", gap_mm: WALL_GAP_MM[key] };
  return { mode: "free", gap_mm: 0 };
}

const SYMBOL_CATALOG = Object.freeze([
  // ---------------------------------------------------------------- Sanitär
  s("vorwandinstallation", "Vorwandinstallation", "sanitaer", {
    placement: "path", depth_mm: 150, height_mm: 1500,
    note: "WC und Waschtisch werden daran montiert",
  }),
  s("wand_wc", "Wand-WC", "sanitaer", {
    w: 360, d: 540, height: "wall", mount_height_mm: 200,
  }),
  s("waschtisch", "Waschtisch", "sanitaer", {
    w: 600, d: 550, height: "wall", mount_height_mm: 850,
  }),
  s("handwaschbecken", "Handwaschbecken", "sanitaer", {
    w: 450, d: 340, height: "wall", mount_height_mm: 850,
  }),
  s("doppelwaschtisch", "Doppelwaschtisch", "sanitaer", {
    w: 1200, d: 450, height: "wall", mount_height_mm: 850,
  }),
  s("badewanne", "Badewanne", "sanitaer", { w: 1700, d: 750 }),
  s("eckbadewanne", "Eckbadewanne", "sanitaer", { w: 1500, d: 1500, mirrorable: true }),
  // The square tray a Dusch-WC gets when there is no room for anything longer.
  s("dusche_klein", "Dusche 80x80", "sanitaer", { w: 800, d: 800, mirrorable: true }),
  s("dusche", "Dusche", "sanitaer", { w: 930, d: 1360, mirrorable: true }),
  s("dusche_gross", "Dusche gross", "sanitaer", { w: 990, d: 1200, mirrorable: true }),
  s("badheizkoerper", "Badheizkörper", "sanitaer", {
    w: 550, d: 100, height: "wall", mount_height_mm: 900,
  }),

  // ----------------------------------------------------------------- Küche
  s("kuechenzeile", "Küchenzeile", "kueche", {
    placement: "path", depth_mm: 600, height_mm: 900,
    note: "Gerade, L- oder U-Form; 90-Grad-Ecken",
  }),
  s("kuecheninsel", "Kücheninsel", "kueche", {
    placement: "rect", height_mm: 900,
  }),
  s("kochfeld", "Kochfeld", "kueche", { w: 600, d: 520, height: "surface" }),
  s("spuele", "Spüle", "kueche", { w: 600, d: 600, height: "surface" }),
  s("hochschrank_herd", "Hochschrank / Herd", "kueche", { w: 600, d: 600 }),
  s("kuehlschrank", "Kühlschrank", "kueche", { w: 600, d: 600 }),

  // ---------------------------------------------------------------- Wohnen
  s("ecksofa", "Ecksofa", "wohnen", { w: 2800, d: 1800, mode: "indicative", mirrorable: true }),
  s("sofa_3sitzer", "3-Sitzer", "wohnen", { w: 2270, d: 900, mode: "indicative" }),
  s("sofa_2sitzer", "2-Sitzer", "wohnen", { w: 1600, d: 900, mode: "indicative" }),
  s("sofa_1sitzer", "1-Sitzer", "wohnen", { w: 1010, d: 1030, mode: "indicative" }),
  s("hocker", "Hocker", "wohnen", { w: 500, d: 500, mode: "indicative" }),
  s("couchtisch", "Couchtisch", "wohnen", { w: 1100, d: 600, mode: "indicative" }),
  s("pflanze", "Pflanze (groß)", "wohnen", { w: 450, d: 450, mode: "indicative" }),
  s("lowboard", "Lowboard", "wohnen", { w: 2110, d: 320, mode: "indicative" }),
  s("fernseher", "Fernseher", "wohnen", {
    w: 1140, d: 180, mode: "indicative", height: "wall", mount_height_mm: 1100,
  }),
  s("sideboard", "Sideboard", "wohnen", { w: 1880, d: 320, mode: "indicative" }),
  s("playstation_gruppe", "Playstation-Gruppe", "wohnen", {
    w: 1230, d: 1700, mode: "indicative", assembly: true,
  }),

  // -------------------------------------------------- Schlafen und Stauraum
  s("doppelbett", "Doppelbett", "schlafen", { w: 1800, d: 2000 }),
  s("einzelbett", "Einzelbett", "schlafen", { w: 900, d: 2000 }),
  s("kleiderschrank", "Kleiderschrank", "schlafen", { w: 1050, d: 600, mode: "indicative" }),
  s("schrank_40", "Schrank 40 tief", "schlafen", { w: 1070, d: 400 }),
  s("schrank_60", "Schrank 60 tief", "schlafen", { w: 1070, d: 600 }),
  s("abstellschrank", "Abstellschrank", "schlafen", { placement: "rect", height_mm: 2000 }),
  s("garderobe", "Garderobe", "schlafen", { w: 900, d: 320, mode: "indicative" }),

  // --------------------------------------------- Essen, Büro, Hauswirtschaft
  s("essgruppe_6", "Essgruppe 6 Personen", "essen", {
    w: 1710, d: 1600, mode: "indicative", assembly: true,
  }),
  // Measured off the drawing these came out 970x1140 and 660x1140, which is
  // the size they were drawn at, not the size a desk is. Real-world figures
  // per Rainer: an adult desk is 1600x800, a child's 1200x600.
  s("schreibtisch", "Schreibtisch", "essen", { w: 1600, d: 800, mode: "indicative", mirrorable: true }),
  s("schreibtisch_kind", "Schreibtisch Kind", "essen", { w: 1200, d: 600, mode: "indicative", mirrorable: true }),
  s("schreibtischstuhl", "Schreibtischstuhl", "essen", { w: 610, d: 610, mode: "indicative" }),
  s("waschmaschine", "Waschmaschine", "essen", { w: 600, d: 600 }),
  s("trockner", "Trockner", "essen", { w: 600, d: 600 }),
]);

function s(key, label, category, options) {
  const placement = options.placement || "stamp";
  return Object.freeze({
    key,
    label,
    category,
    placement,
    // stamp only
    footprint_mm: placement === "stamp"
      ? Object.freeze({ width_mm: options.w, depth_mm: options.d })
      : null,
    footprint_mode: placement === "stamp" ? (options.mode || "fixed") : null,
    mirrorable: options.mirrorable === true,
    assembly: options.assembly === true,
    // path only
    depth_mm: options.depth_mm ?? null,
    // vertical placement
    height: options.height || "floor",
    mount_height_mm: options.mount_height_mm ?? null,
    height_mm: options.height_mm ?? null,
    note: options.note || null,
    wall: wallBehaviour(key),
  });
}

const SYMBOL_CATEGORIES = Object.freeze([
  { key: "sanitaer", label: "Sanitär" },
  { key: "kueche", label: "Küche" },
  { key: "wohnen", label: "Wohnen" },
  { key: "schlafen", label: "Schlafen / Stauraum" },
  { key: "essen", label: "Essen / Büro / HWR" },
]);

const SYMBOLS_BY_KEY = new Map(SYMBOL_CATALOG.map((item) => [item.key, item]));

function getSymbol(key) {
  return SYMBOLS_BY_KEY.get(key) || null;
}

function symbolsInCategory(category) {
  return SYMBOL_CATALOG.filter((item) => item.category === category);
}


// --- room -> plausible symbols ---------------------------------------------
// Once the room is known, so is most of what belongs in it. Used to filter the
// palette, and mirrored by ROOM_SYMBOLS in symbol_detection.py, which uses the
// same knowledge to decide what to look for.
//
// DUPLICATION: this table exists twice, here and in the detector. Same problem
// as the footprints, which exist three times. Worth collapsing to one source
// served from Python before it drifts.

const ROOM_SYMBOL_SETS = Object.freeze({
  bad: ["badewanne", "eckbadewanne", "dusche_klein", "dusche", "dusche_gross", "wand_wc",
        "waschtisch", "doppelwaschtisch", "handwaschbecken", "badheizkoerper",
        "vorwandinstallation"],
  wc: ["wand_wc", "handwaschbecken", "waschtisch", "vorwandinstallation"],
  kueche: ["kuechenzeile", "kuecheninsel", "kuehlschrank", "hochschrank_herd",
           "kochfeld", "spuele"],
  wohnen: ["ecksofa", "sofa_3sitzer", "sofa_2sitzer", "sofa_1sitzer", "hocker",
           "couchtisch", "pflanze", "lowboard", "fernseher", "sideboard", "essgruppe_6",
           "playstation_gruppe"],
  schlafen: ["doppelbett", "einzelbett", "kleiderschrank", "schrank_40",
             "schrank_60", "schreibtisch", "schreibtisch_kind",
             "schreibtischstuhl", "garderobe"],
  diele: ["garderobe", "schrank_40", "sideboard", "kleiderschrank"],
  hwr: ["waschmaschine", "trockner", "abstellschrank", "schrank_60"],
  buero: ["schreibtisch", "schreibtisch_kind", "schreibtischstuhl",
          "sofa_2sitzer", "sideboard"],
});

// Order matters and is deliberate, not alphabetical or by length. A room name
// can contain two clues — "Elternbad" holds both "eltern" and "bad" — and the
// wet-room clue must win, otherwise a parents' bathroom is classed as a
// bedroom and offered wardrobes. Sorting by length got this wrong, because
// "eltern" is longer than "bad".
//
// Wet rooms first, then the rest.
const ROOM_LABEL_BUCKETS = [
  // wet rooms, including every compound that ends in -bad
  ["duschbad", "bad"], ["kinderbad", "bad"], ["elternbad", "bad"], ["gästebad", "bad"],
  ["gaestebad", "bad"], ["tageslichtbad", "bad"], ["badezimmer", "bad"],
  ["du-wc", "bad"], ["dusch", "bad"], ["bad", "bad"],
  ["gäste-wc", "wc"], ["gaeste-wc", "wc"], ["gäste wc", "wc"], ["wc", "wc"],
  // then the rest
  ["küche", "kueche"], ["kueche", "kueche"], ["kochen", "kueche"],
  ["wohnzimmer", "wohnen"], ["wohnen", "wohnen"], ["essen", "wohnen"],
  ["schlafen", "schlafen"], ["eltern", "schlafen"], ["kinderzimmer", "schlafen"],
  ["kind", "schlafen"], ["gast", "schlafen"], ["ankleide", "schlafen"],
  ["garderobe", "diele"], ["diele", "diele"], ["flur", "diele"],
  ["hauswirtschaft", "hwr"], ["hwr", "hwr"], ["htr", "hwr"], ["abstell", "hwr"],
  ["büro", "buero"], ["buero", "buero"], ["arbeit", "buero"],
];

function bucketForRoomLabel(label) {
  const text = `${label || ""}`.toLocaleLowerCase("de-DE");
  // First match in declared order — see the note above.
  for (const [needle, bucket] of ROOM_LABEL_BUCKETS) {
    if (text.includes(needle)) return bucket;
  }
  return null;
}

function symbolsForRoomLabel(label) {
  const bucket = bucketForRoomLabel(label);
  if (!bucket) return null;
  return ROOM_SYMBOL_SETS[bucket] || null;
}


// --- key -> the group Rainer drew ------------------------------------------
// static/moebel-symbols.svg is his Möbel3svg.svg, copied in unchanged. These
// are the group ids inside it, so the palette and the plan show his own
// linework rather than a generic box.
const SYMBOL_SOURCE_GROUP = Object.freeze({
  badewanne: "Badewanne", eckbadewanne: "Badewanne_Eckig",
  dusche_klein: "Dusche", dusche: "Dusche", dusche_gross: "Dusche_112",
  wand_wc: "WC", waschtisch: "einzelwaschbecken",
  doppelwaschtisch: "doppelwachtisch", handwaschbecken: "waschbecken_klein",
  badheizkoerper: "Badheizkörper", vorwandinstallation: "Abseitenbereich",
  kuechenzeile: "theke", kuecheninsel: "insel", kochfeld: "herd",
  spuele: "sink", hochschrank_herd: "Hochherd", kuehlschrank: "Kühlschrank",
  ecksofa: "L-couch", sofa_3sitzer: "_x33_-sitzer", sofa_2sitzer: "_x32_-sitzer",
  sofa_1sitzer: "_x31__sitzer", hocker: "sessel", couchtisch: "coffeetable",
  lowboard: "lowboard", fernseher: "TV", sideboard: "sideboard1",
  playstation_gruppe: "Playstation_gruppe",
  doppelbett: "Doppelbett", einzelbett: "Einzelbett", kleiderschrank: "schrank",
  schrank_40: "schrank_40", schrank_60: "Schrank_60",
  abstellschrank: "abstellschränke", garderobe: "garderobe",
  essgruppe_6: "dning_6", schreibtisch: "schreibtisch",
  schreibtisch_kind: "schreibtisch1", schreibtischstuhl: "Schreibtischstuhl",
  waschmaschine: "washer", trockner: "dryer",
});

// Ausstattung layer — the furnishing symbols.
//
// Loaded after annotate.js, whose top-level let/const bindings live in the
// shared global lexical scope and are therefore reachable from here.
//
// A symbol records WHAT and WHERE, never a 3D model or a material. A style
// pack resolves key -> model + finish at render time, so one annotation can be
// rendered modern, classic, or in a style invented later, without touching the
// annotation again.
//
// Symbols are presentation data and must never affect geometry_hash. Hence a
// separate array, a separate tab, and a separate save key.

let symbols = [];
let activeSymbolKey = null;
let activeLayer = "architektur";

const layerTabButtons = document.querySelectorAll(".layer-tab");
const layerArchitektur = document.querySelector("#layerArchitektur");
const layerAusstattung = document.querySelector("#layerAusstattung");
const layerExterior = document.querySelector("#layerExterior");
const symbolPaletteEl = document.querySelector("#symbolPalette");
const symbolListEl = document.querySelector("#symbolList");
const symbolPlacementControls = document.querySelector("#symbolPlacementControls");
const symbolRotationSelect = document.querySelector("#symbolRotation");
const symbolMirrorLabel = document.querySelector("#symbolMirrorLabel");
const symbolMirrorCheckbox = document.querySelector("#symbolMirror");
const symbolHintEl = document.querySelector("#symbolHint");
const symbolRoomFilter = document.querySelector("#symbolRoomFilter");

// --- scale -----------------------------------------------------------------
// The Simplifier stores normalized 0-1 coordinates and has no millimetre scale
// of its own, but a symbol cannot be drawn without one: a bathtub has to look
// like a bathtub-sized thing in this room, or there is no way to see whether
// it fits.
//
// Two sources, explicit preferred:
//
//   1. A stated drawing scale (1:100). Exact, when the preview's real-world
//      page size is known.
//   2. Derived from room areas. Comparing a room's stated m2 against its
//      normalized polygon area gives metres per normalized unit. Approximate,
//      but needs nothing beyond what is already annotated.

let statedFloorScale = {};        // floor_level -> metres per normalized unit
let calibrating = false;
let calibrationPoints = [];

const scaleStatusEl = document.querySelector("#scaleStatus");
const calibrateScaleButton = document.querySelector("#calibrateScaleButton");

// Calibration: click two points, state the real distance between them.
//
// Measured in practice on twostorey_044: rooms carry area_ratio but no
// area_m2 at all, so deriving scale from areas silently yields nothing. Page
// size does not work either, because the preview preserves the uploaded crop
// and is not a whole page. Two points and a known distance works regardless of
// crop, drawing scale, or how the preview was produced.
function beginCalibration() {
  calibrating = true;
  calibrationPoints = [];
  updateScaleStatus();
  setStatus("Maßstab: zwei Punkte mit bekanntem Abstand anklicken.");
  draw();
}

function handleCalibrationClick(point) {
  calibrationPoints.push(point);
  if (calibrationPoints.length < 2) {
    setStatus("Zweiten Punkt anklicken.");
    draw();
    return;
  }
  const [a, b] = calibrationPoints;
  // Normalized coordinates are relative to a non-square image, so the pixel
  // aspect has to come back in before measuring a distance.
  const dx = (b.x - a.x) * canvas.width;
  const dy = (b.y - a.y) * canvas.height;
  const pixels = Math.hypot(dx, dy);
  const unitDistance = pixels / canvas.width;   // in normalized-x units

  const answer = window.prompt(
    "Abstand zwischen den beiden Punkten in Metern:", "5");
  calibrating = false;
  calibrationPoints = [];

  const metres = Number((answer || "").replace(",", "."));
  if (!(metres > 0)) {
    setStatus("Maßstab nicht gesetzt.", true);
    draw();
    return;
  }
  if (!(unitDistance > 0.000001)) {
    setStatus("Punkte zu dicht beieinander.", true);
    draw();
    return;
  }
  statedFloorScale[activeFloor] = metres / unitDistance;
  updateScaleStatus();
  draw();
  markDirty(`Maßstab für ${activeFloor} gesetzt. Zum Speichern auf Save klicken.`);
}

function updateScaleStatus() {
  const stated = statedFloorScale[activeFloor];
  const derived = stated ? null : scaleFromRoomAreas();
  if (stated) {
    const width = (stated).toFixed(2);
    scaleStatusEl.textContent = `Gesetzt: Bildbreite entspricht ${width} m.`;
  } else if (derived) {
    scaleStatusEl.textContent =
      `Aus Raumflächen geschätzt: Bildbreite ≈ ${derived.toFixed(2)} m. Besser festlegen.`;
  } else if (calibrating) {
    scaleStatusEl.textContent = "Zwei Punkte anklicken …";
  } else {
    scaleStatusEl.textContent =
      "Kein Maßstab. Ohne ihn lassen sich Symbole nicht maßstäblich zeichnen.";
  }
}

calibrateScaleButton.addEventListener("click", beginCalibration);

function scaleFromRoomAreas() {
  const samples = [];
  for (const room of annotations) {
    if (room.floor_level !== activeFloor) continue;
    const area = Number(room.area_m2 || room.manual_area_m2);
    if (!(area > 0) || !Array.isArray(room.points) || room.points.length < 3) continue;
    const normalized = Math.abs(polygonArea(room.points));
    // Normalized area is x-units x y-units, and a y-unit is not a metre-for-
    // metre match for an x-unit on a non-square plan.
    if (normalized > 0.000001) {
      samples.push(Math.sqrt((area / normalized) * (canvas.width / canvas.height)));
    }
  }
  if (!samples.length) return null;
  samples.sort((a, b) => a - b);
  return samples[Math.floor(samples.length / 2)];   // median resists one bad room
}

function floorScaleMetresPerUnit() {
  return statedFloorScale[activeFloor] || scaleFromRoomAreas();
}

// The scale is metres across the image WIDTH, so a metre converts to
// normalized-x units by dividing by it. Depth is drawn against canvas.height,
// which is a different unit on a non-square plan: on this 820 x 668 canvas a
// y-unit is only 81% of an x-unit, so every stamp came out that much too
// shallow. The aspect factor puts the depth back into real metres.
//
// Every consumer (drawing, hit-testing, wall snapping) multiplies w by
// canvas.width and h by canvas.height, so correcting it here corrects them
// all. The path tool never had the problem: it multiplies its depth by
// canvas.width already.
function symbolFootprintInUnits(symbol, placed) {
  const scale = floorScaleMetresPerUnit();
  // A footprint dragged onto the plan is a measurement off the actual drawing;
  // the catalogue value is a nominal size for furniture in general. The
  // measurement wins.
  if (placed && placed.footprint_mm && placed.footprint_mm.width_mm) {
    symbol = { ...symbol, footprint_mm: placed.footprint_mm };
  }
  if (!symbol.footprint_mm || !scale) return null;
  const aspect = canvas.width / canvas.height;
  return {
    w: (symbol.footprint_mm.width_mm / 1000) / scale,
    h: ((symbol.footprint_mm.depth_mm / 1000) / scale) * aspect,
  };
}

// --- palette ---------------------------------------------------------------

function renderSymbolPalette() {
  symbolPaletteEl.replaceChildren();
  // Once the room is known so is most of what belongs in it, so scrolling 39
  // symbols to find a WC while annotating a bathroom is wasted effort.
  const allowed = symbolRoomFilter && symbolRoomFilter.value
    ? symbolsForRoomLabel(symbolRoomFilter.value)
    : null;
  for (const category of SYMBOL_CATEGORIES) {
    const items = symbolsInCategory(category.key)
      .filter((item) => !allowed || allowed.includes(item.key));
    if (!items.length) continue;
    const label = document.createElement("p");
    label.className = "symbol-group-label";
    label.textContent = category.label;
    const row = document.createElement("div");
    row.className = "symbol-buttons";
    for (const item of items) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = item.label;
      button.dataset.symbol = item.key;
      button.dataset.placement = item.placement;
      if (item.placement === "path") {
        button.title = `Pfad-Werkzeug, ${item.depth_mm} mm tief`;
      } else if (item.placement === "rect") {
        button.title = "Rechteck aufziehen";
      } else {
        button.title = `${item.footprint_mm.width_mm} × ${item.footprint_mm.depth_mm} mm`;
      }
      button.addEventListener("click", () => selectSymbol(item.key));
      row.append(button);
    }
    symbolPaletteEl.append(label, row);
  }
  if (typeof decorateSymbolPalette === "function") decorateSymbolPalette();
}

function selectSymbol(key) {
  const symbol = getSymbol(key);
  if (!symbol) return;

  // An open path used to vanish when another symbol was picked, because the
  // draft was cleared further down. Finish it instead — those points were
  // drawn deliberately. Must happen BEFORE activeSymbolKey is reassigned:
  // finishDrawnSymbol reads it to decide what is being drawn.
  if (symbolDraft.length >= 2 && activeSymbolKey && activeSymbolKey !== key) {
    finishDrawnSymbol();
  }

  activeSymbolKey = key;
  for (const button of symbolPaletteEl.querySelectorAll("button")) {
    button.classList.toggle("active", button.dataset.symbol === key);
  }
  symbolPlacementControls.hidden = false;
  symbolMirrorLabel.hidden = !symbol.mirrorable;
  if (!symbol.mirrorable) symbolMirrorCheckbox.checked = false;

  symbolDraft = [];
  updateDrawingActions();
  if (symbol.placement === "path") {
    symbolHintEl.textContent =
      `${symbol.label}: Punkte klicken, 90°-Ecken, ${symbol.depth_mm} mm tief. Doppelklick oder Enter beendet, Esc bricht ab.`;
  } else if (symbol.placement === "rect") {
    symbolHintEl.textContent = `${symbol.label}: zwei gegenüberliegende Ecken anklicken. Esc bricht ab.`;
  } else if (!floorScaleMetresPerUnit()) {
    symbolHintEl.textContent =
      "Kein Maßstab bekannt. Mindestens ein Raum mit Flächenangabe annotieren.";
  } else {
    const wall = symbol.wall || { mode: "free" };
    symbolHintEl.textContent = wall.mode === "flush"
      ? `${symbol.label} platzieren: klicken. Rastet an der Wand ein.`
      : wall.mode === "gap"
        ? `${symbol.label} platzieren: klicken. Rastet mit ${wall.gap_mm} mm Abstand an der Wand ein.`
        : `${symbol.label} platzieren: in den Plan klicken.`;
  }
  draw();
}

// --- placement -------------------------------------------------------------

// Pull a stamp onto the nearest wall, respecting its clearance.
//
// The symbol goes against the wall with its BACK, not its centre, so the
// offset is half its depth plus whatever gap the piece needs. Its rotation
// comes from the wall too — a bath on a north wall and the same bath on an
// east wall are one object turned 90 degrees, and making the annotator set
// that by hand every time is busywork.
//
// The search radius is generous, unlike the path tool's tight 14 px: someone
// placing a bath clicks roughly where it should sit, which is half a bath
// away from the wall. One depth's reach means "you clicked near this wall",
// while anything further out stays where it was put.
function snapStampToWall(symbol, point) {
  const behaviour = symbol.wall;
  if (!behaviour || behaviour.mode === "free") return null;
  const scale = floorScaleMetresPerUnit();
  const size = symbolFootprintInUnits(symbol);
  if (!scale || !size) return null;

  // Everything below is in canvas pixels, matching how symbols are drawn.
  const depthPx = size.h * canvas.height;
  const gapPx = ((behaviour.gap_mm / 1000) / scale) * canvas.width;
  const hit = snapToWall(point, depthPx * 1.5 + gapPx);
  if (!hit) return null;

  const [a, b] = hit.edge;
  const angle = Math.atan2((b.y - a.y) * canvas.height, (b.x - a.x) * canvas.width);

  // Normal pointing away from the wall, towards wherever the click came from,
  // so the piece lands inside the room rather than through the plaster.
  let nx = -Math.sin(angle);
  let ny = Math.cos(angle);
  const towardsClick = (point.x - hit.point.x) * canvas.width * nx
                     + (point.y - hit.point.y) * canvas.height * ny;
  if (towardsClick < 0) { nx = -nx; ny = -ny; }

  const offset = depthPx / 2 + gapPx;
  return {
    position: {
      x: clamp01((hit.point.x * canvas.width + nx * offset) / canvas.width),
      y: clamp01((hit.point.y * canvas.height + ny * offset) / canvas.height),
    },
    rotation_deg: Math.round((((angle * 180) / Math.PI) + 360) % 360),
  };
}

function placeSymbolAt(point) {
  // A drag finishes with a click event. Without this, moving a symbol would
  // also place a new one on top of it.
  if (symbolDragMoved) {
    symbolDragMoved = false;
    return false;
  }
  if (calibrating) {
    handleCalibrationClick(point);
    return true;
  }
  const symbol = getSymbol(activeSymbolKey);
  if (!symbol) return false;
  if (symbol.placement !== "stamp") {
    if (!floorScaleMetresPerUnit()) {
      setStatus("Ohne Maßstab kann nicht maßstäblich gezeichnet werden.", true);
      return false;
    }
    return handleDrawingClick(point);
  }
  if (!floorScaleMetresPerUnit()) {
    setStatus("Ohne Maßstab kann die Symbolgröße nicht berechnet werden.", true);
    return false;
  }
  if (symbolAtPoint(point)) return false;   // that click selected something

  const snapped = snapStampToWall(symbol, point);
  symbols.push({
    id: `${Date.now()}_${Math.random().toString(16).slice(2)}`,
    floor_level: activeFloor,
    symbol: symbol.key,
    position: snapped ? snapped.position : { x: point.x, y: point.y },
    // A wall-snapped piece takes the wall's angle; anything else keeps what
    // the annotator chose.
    rotation_deg: snapped ? snapped.rotation_deg : (Number(symbolRotationSelect.value) || 0),
    mirrored: symbol.mirrorable && symbolMirrorCheckbox.checked,
    ...(snapped ? { wall_snapped: true } : {}),
  });
  renderSymbolList();
  draw();
  markDirty(`${symbol.label} platziert. Zum Speichern auf Save klicken.`);
  return true;
}

function drawSymbol(placed) {
  const symbol = getSymbol(placed.symbol);
  if (!symbol) return;
  const drawnSelected = placed.id === selectedSymbolId;
  if (placed.points && placed.points.length >= 2) {
    if (symbol.placement === "path") drawPathSymbol(placed, symbol, drawnSelected);
    else drawRectSymbol(placed, symbol, drawnSelected);
    return;
  }
  const size = symbolFootprintInUnits(symbol, placed);
  if (!size) return;

  const cx = placed.position.x * canvas.width;
  const cy = placed.position.y * canvas.height;
  const w = size.w * canvas.width;
  const h = size.h * canvas.height;

  ctx.save();
  ctx.translate(cx, cy);
  ctx.rotate(((placed.rotation_deg || 0) * Math.PI) / 180);
  if (placed.mirrored) ctx.scale(-1, 1);
  const isSelected = placed.id === selectedSymbolId;
  const hasArt = drawSymbolArt(placed.symbol, w, h);
  if (!hasArt) {
    // Box only while the artwork is still being sliced out of the sheet.
    ctx.fillStyle = isSelected ? "#f59e0b33" : "#2563eb22";
    ctx.strokeStyle = isSelected ? "#b45309" : "#2563eb";
    ctx.lineWidth = isSelected ? 3 : 1.5;
    ctx.fillRect(-w / 2, -h / 2, w, h);
    ctx.strokeRect(-w / 2, -h / 2, w, h);
  } else if (isSelected) {
    // Selection outline sits around the drawing, not instead of it.
    ctx.strokeStyle = "#b45309";
    ctx.lineWidth = 2.5;
    ctx.strokeRect(-w / 2, -h / 2, w, h);
  }
  // Tick on the front edge, so rotation and mirroring read at a glance
  // instead of having to be inferred.
  ctx.beginPath();
  ctx.moveTo(0, -h / 2);
  ctx.lineTo(0, -h / 2 + Math.min(h * 0.25, 14));
  ctx.stroke();
  ctx.restore();

  if (isSelected) {
    ctx.fillStyle = "#7c2d12";
    ctx.font = "11px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(symbol.label, cx, cy + 4);
    ctx.textAlign = "start";
  }
}

function drawSymbolsForActiveFloor() {
  for (const placed of symbols) {
    if (placed.floor_level === activeFloor) drawSymbol(placed);
  }
  drawSymbolSuggestions();
  drawSymbolDraft();
  if (calibrating && calibrationPoints.length) {
    ctx.save();
    ctx.strokeStyle = "#d12f6a";
    ctx.fillStyle = "#d12f6a";
    ctx.lineWidth = 2;
    for (const point of calibrationPoints) {
      ctx.beginPath();
      ctx.arc(point.x * canvas.width, point.y * canvas.height, 4, 0, Math.PI * 2);
      ctx.fill();
    }
    ctx.restore();
  }
}

function renderSymbolList() {
  symbolListEl.replaceChildren();
  const visible = symbols.filter((item) => item.floor_level === activeFloor);
  if (!visible.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = "Noch keine Symbole platziert.";
    symbolListEl.append(empty);
    return;
  }
  for (const placed of visible) {
    const symbol = getSymbol(placed.symbol);
    const row = document.createElement("div");
    row.className = "annotation-item";
    const label = document.createElement("span");
    const bits = [symbol ? symbol.label : placed.symbol];
    if (placed.points) bits.push(`${placed.points.length} Punkte`);
    if (placed.rotation_deg) bits.push(`${placed.rotation_deg}°`);
    if (placed.mirrored) bits.push("gespiegelt");
    label.textContent = bits.join(" · ");
    const remove = document.createElement("button");
    remove.type = "button";
    remove.textContent = "Remove";
    remove.addEventListener("click", () => {
      symbols = symbols.filter((item) => item.id !== placed.id);
      renderSymbolList();
      draw();
      markDirty("Symbol entfernt. Zum Speichern auf Save klicken.");
    });
    row.append(label, remove);
    symbolListEl.append(row);
  }
}

// --- layer switching -------------------------------------------------------

function setActiveLayer(layer) {
  // Commit any open path before leaving the furnishing tab, for the same
  // reason as switching symbols: those points were drawn deliberately and
  // should not evaporate.
  if (activeLayer === "ausstattung" && layer !== "ausstattung" && symbolDraft.length >= 2) {
    finishDrawnSymbol();
  }
  activeLayer = layer;
  for (const button of layerTabButtons) {
    button.classList.toggle("active", button.dataset.layer === layer);
  }
  layerArchitektur.hidden = layer !== "architektur";
  layerAusstattung.hidden = layer !== "ausstattung";
  if (layerExterior) layerExterior.hidden = layer !== "exterior";
  if (layer === "ausstattung") {
    draft = [];
    refreshSymbolRoomFilter();
    if (typeof refreshRoomNav === "function") refreshRoomNav();
    renderSymbolPalette();
    renderSymbolList();
    updateScaleStatus();
  } else {
    activeSymbolKey = null;
    symbolPlacementControls.hidden = true;
    for (const button of symbolPaletteEl.querySelectorAll("button")) {
      button.classList.remove("active");
    }
  }
  if (layer === "exterior") {
    draft = [];
    if (typeof renderExteriorAreaList === "function") renderExteriorAreaList();
  }
  draw();
}

for (const button of layerTabButtons) {
  button.addEventListener("click", () => setActiveLayer(button.dataset.layer));
}

renderSymbolPalette();
renderSymbolList();
updateScaleStatus();

// --- automatic detection ---------------------------------------------------
// Reads the furniture symbols already drawn on the plan and proposes matches.
// Detection only: every hit needs approving, exactly like area suggestions.
// Nothing enters `symbols` until the annotator says so.

let symbolSuggestions = [];

const detectSymbolsButton = document.querySelector("#detectSymbolsButton");
const symbolSuggestionListEl = document.querySelector("#symbolSuggestionList");

async function detectSymbols() {
  const scale = floorScaleMetresPerUnit();
  if (!scale) {
    setStatus("Erst den Maßstab festlegen — ohne ihn ist keine Größenmessung möglich.", true);
    return;
  }
  detectSymbolsButton.disabled = true;
  setStatus("Suche Möbelsymbole im Plan …");
  try {
    const url = `/api/symbol-suggestions?project=${encodeURIComponent(projectId)}`
      + `&floor=${encodeURIComponent(activeFloor)}&scale=${encodeURIComponent(scale)}`;
    const response = await fetch(url);
    const payload = await response.json();
    if (!response.ok || !payload.ok) throw new Error(payload.error || "Erkennung fehlgeschlagen.");
    symbolSuggestions = payload.suggestions || [];
    renderSymbolSuggestions();
    draw();
    setStatus(symbolSuggestions.length
      ? `${symbolSuggestions.length} Vorschläge. Jeden prüfen und übernehmen.`
      : "Keine Symbole erkannt. Maßstab prüfen.");
  } catch (error) {
    setStatus(error.message, true);
  } finally {
    detectSymbolsButton.disabled = false;
  }
}

function renderSymbolSuggestions() {
  symbolSuggestionListEl.replaceChildren();
  if (!symbolSuggestions.length) return;
  for (const [index, item] of symbolSuggestions.entries()) {
    const row = document.createElement("div");
    row.className = "annotation-item";

    // The measured size leads, not a guessed name. Detection reliably finds
    // WHERE something is; at 600x600 a fridge, dishwasher, oven housing and
    // washing machine are indistinguishable by size, so asserting one would
    // be a coin toss dressed as a result.
    const label = document.createElement("span");
    label.textContent = `${item.measured_mm[0]}×${item.measured_mm[1]} mm · ${item.room_label || ""}`;

    // The best match is preselected, the equally-plausible alternatives sit
    // next to it. One click when the guess is right, one dropdown when not.
    const choice = document.createElement("select");
    const options = [item.symbol, ...(item.ambiguous_with || [])];
    for (const key of options) {
      const symbol = getSymbol(key);
      const option = document.createElement("option");
      option.value = key;
      option.textContent = symbol ? symbol.label : key;
      choice.append(option);
    }
    choice.value = item.symbol;
    choice.addEventListener("change", () => {
      item.symbol = choice.value;
      draw();
    });

    const use = document.createElement("button");
    use.type = "button";
    use.textContent = "Übernehmen";
    use.className = "edit";
    use.addEventListener("click", () => {
      symbols.push({
        id: `${Date.now()}_${Math.random().toString(16).slice(2)}`,
        floor_level: activeFloor,
        symbol: choice.value,
        position: { x: item.position.x, y: item.position.y },
        rotation_deg: item.rotation_deg || 0,
        mirrored: false,
        source: "detected",
      });
      symbolSuggestions.splice(index, 1);
      renderSymbolSuggestions();
      renderSymbolList();
      draw();
      markDirty("Symbol übernommen. Zum Speichern auf Save klicken.");
    });

    const drop = document.createElement("button");
    drop.type = "button";
    drop.textContent = "Verwerfen";
    drop.addEventListener("click", () => {
      symbolSuggestions.splice(index, 1);
      renderSymbolSuggestions();
      draw();
    });

    row.append(label, choice, use, drop);
    symbolSuggestionListEl.append(row);
  }
}

function drawSymbolSuggestions() {
  for (const item of symbolSuggestions) {
    const symbol = getSymbol(item.symbol);
    if (!symbol) continue;
    const size = symbolFootprintInUnits(symbol, placed);
    if (!size) continue;
    const cx = item.position.x * canvas.width;
    const cy = item.position.y * canvas.height;
    const w = size.w * canvas.width;
    const h = size.h * canvas.height;
    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(((item.rotation_deg || 0) * Math.PI) / 180);
    // Dashed and unfilled: an unapproved proposal must not look like a
    // placed symbol.
    ctx.setLineDash([6, 4]);
    ctx.strokeStyle = "#c026d3";
    ctx.lineWidth = 2;
    ctx.strokeRect(-w / 2, -h / 2, w, h);
    ctx.restore();
    ctx.fillStyle = "#86198f";
    ctx.font = "11px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(`${item.measured_mm[0]}×${item.measured_mm[1]}`, cx, cy + 4);
    ctx.textAlign = "start";
  }
}

detectSymbolsButton.addEventListener("click", detectSymbols);

// --- select and move -------------------------------------------------------
// Placed symbols can be picked up and dragged. Auto-placement and detection
// both get things roughly right and roughly right is not good enough, so the
// annotator needs to be able to nudge anything by hand.

let selectedSymbolId = null;
let symbolDrag = null;          // { id, offsetX, offsetY } in normalized units
let symbolDragMoved = false;    // suppresses the click that ends a drag

function symbolAtPoint(point) {
  // Topmost first, so the most recently placed wins an overlap.
  for (let index = symbols.length - 1; index >= 0; index -= 1) {
    const placed = symbols[index];
    if (placed.floor_level !== activeFloor) continue;
    const symbol = getSymbol(placed.symbol);
    if (!symbol) continue;
    const size = symbolFootprintInUnits(symbol, placed);
    if (!size) continue;

    // Into the symbol's own frame, so rotation is handled rather than
    // approximated by an axis-aligned box.
    const dx = (point.x - placed.position.x) * canvas.width;
    const dy = (point.y - placed.position.y) * canvas.height;
    const angle = -((placed.rotation_deg || 0) * Math.PI) / 180;
    const localX = dx * Math.cos(angle) - dy * Math.sin(angle);
    const localY = dx * Math.sin(angle) + dy * Math.cos(angle);
    if (Math.abs(localX) <= (size.w * canvas.width) / 2 &&
        Math.abs(localY) <= (size.h * canvas.height) / 2) {
      return placed;
    }
  }
  return null;
}

canvas.addEventListener("pointerdown", (event) => {
  if (!ausstattungActive() || event.button !== 0) return;
  const point = normalizedPoint(event);
  const hit = symbolAtPoint(point);
  if (!hit) {
    if (selectedSymbolId) { selectedSymbolId = null; draw(); }
    return;
  }
  // Shift starts a copy rather than moving the original, the way Illustrator
  // does it. The drag then runs on the clone, so the original stays put.
  let dragTarget = hit;
  if (event.shiftKey) {
    dragTarget = {
      ...structuredClone(hit),
      id: `${Date.now()}_${Math.random().toString(16).slice(2)}`,
      source: "cloned",
    };
    symbols.push(dragTarget);
    renderSymbolList();
  }
  selectedSymbolId = dragTarget.id;
  syncControlsToSelection();
  symbolDrag = {
    id: dragTarget.id,
    offsetX: point.x - dragTarget.position.x,
    offsetY: point.y - dragTarget.position.y,
    // Start point, so the drag can be locked to whichever axis the mouse is
    // actually pushing along.
    startX: point.x,
    startY: point.y,
    cloned: event.shiftKey,
  };
  symbolDragMoved = false;
  canvas.setPointerCapture(event.pointerId);
  draw();
});

canvas.addEventListener("pointermove", (event) => {
  if (!ausstattungActive() || !symbolDrag) return;
  const placed = symbols.find((item) => item.id === symbolDrag.id);
  if (!placed) return;
  let point = normalizedPoint(event);
  // Holding shift constrains to the dominant axis, so a copy can be dropped
  // exactly in line with its original. Compared in canvas pixels, otherwise a
  // non-square image biases the choice.
  if (event.shiftKey) {
    const dx = Math.abs(point.x - symbolDrag.startX) * canvas.width;
    const dy = Math.abs(point.y - symbolDrag.startY) * canvas.height;
    point = dx >= dy
      ? { x: point.x, y: symbolDrag.startY }
      : { x: symbolDrag.startX, y: point.y };
  }
  placed.position = {
    x: clamp01(point.x - symbolDrag.offsetX),
    y: clamp01(point.y - symbolDrag.offsetY),
  };
  symbolDragMoved = true;
  draw();
});

canvas.addEventListener("pointerup", (event) => {
  if (!ausstattungActive() || !symbolDrag) return;
  const placed = symbols.find((item) => item.id === symbolDrag.id);
  const wasCloned = symbolDrag.cloned;
  symbolDrag = null;
  if (placed && symbolDragMoved) {
    const symbol = getSymbol(placed.symbol);
    const label = symbol ? symbol.label : "Symbol";
    renderSymbolList();
    markDirty(`${label} ${wasCloned ? "kopiert" : "verschoben"}. Zum Speichern auf Save klicken.`);
  } else if (placed && wasCloned) {
    // Shift-clicked without moving: an unwanted duplicate on top of the
    // original. Drop it rather than leaving two stacked invisibly.
    symbols = symbols.filter((item) => item.id !== placed.id);
    selectedSymbolId = null;
    renderSymbolList();
    draw();
  }
  draw();
});

// Rotate and mirror the selection from the keyboard; Delete removes it.
window.addEventListener("keydown", (event) => {
  if (!ausstattungActive() || !selectedSymbolId) return;
  if (event.target && /input|select|textarea/i.test(event.target.tagName)) return;
  const placed = symbols.find((item) => item.id === selectedSymbolId);
  if (!placed) return;
  const symbol = getSymbol(placed.symbol);

  if (event.key === "r" || event.key === "R") {
    const step = event.shiftKey ? -SYMBOL_ROTATION_STEP : SYMBOL_ROTATION_STEP;
    placed.rotation_deg = (((placed.rotation_deg || 0) + step) % 360 + 360) % 360;
    symbolRotationSelect.value = String(placed.rotation_deg);
  } else if (event.key === "m" || event.key === "M") {
    if (!symbol || !symbol.mirrorable) {
      setStatus(`${symbol ? symbol.label : "Dieses Symbol"} ist nicht spiegelbar.`, true);
      return;
    }
    placed.mirrored = !placed.mirrored;
    symbolMirrorCheckbox.checked = placed.mirrored;
  } else if (event.key === "Delete" || event.key === "Backspace") {
    symbols = symbols.filter((item) => item.id !== selectedSymbolId);
    selectedSymbolId = null;
  } else {
    return;
  }
  event.preventDefault();
  renderSymbolList();
  draw();
  markDirty("Symbol geändert. Zum Speichern auf Save klicken.");
});


// The Drehung dropdown and the Gespiegelt box set defaults for the NEXT
// placement. Once something is selected they should act on it instead —
// otherwise selecting a symbol and changing the rotation appears to do
// nothing, which is exactly how it read.
function applyControlsToSelection() {
  if (!selectedSymbolId) return false;
  const placed = symbols.find((item) => item.id === selectedSymbolId);
  if (!placed) return false;
  const symbol = getSymbol(placed.symbol);
  placed.rotation_deg = Number(symbolRotationSelect.value) || 0;
  placed.mirrored = Boolean(symbol && symbol.mirrorable && symbolMirrorCheckbox.checked);
  renderSymbolList();
  draw();
  markDirty("Symbol geändert. Zum Speichern auf Save klicken.");
  return true;
}

symbolRotationSelect.addEventListener("change", applyControlsToSelection);
symbolMirrorCheckbox.addEventListener("change", applyControlsToSelection);

// Selecting something loads its current values into the controls, so the
// dropdown always shows the truth about what is selected.
function syncControlsToSelection() {
  const placed = symbols.find((item) => item.id === selectedSymbolId);
  if (!placed) return;
  const symbol = getSymbol(placed.symbol);
  symbolRotationSelect.value = String(placed.rotation_deg || 0);
  symbolMirrorCheckbox.checked = Boolean(placed.mirrored);
  symbolPlacementControls.hidden = false;
  symbolMirrorLabel.hidden = !(symbol && symbol.mirrorable);
  symbolHintEl.textContent = `${symbol ? symbol.label : "Symbol"} ausgewählt · Drehung/Spiegelung ändern, R dreht, M spiegelt, Entf löscht.`;
}


// Rooms already annotated on this floor drive the filter, so it always offers
// the real rooms rather than a generic list.
function refreshSymbolRoomFilter() {
  if (!symbolRoomFilter) return;
  const current = symbolRoomFilter.value;
  const labels = [...new Set(
    annotations
      .filter((item) => item.floor_level === activeFloor && item.label)
      .map((item) => item.label)
  )].sort();
  symbolRoomFilter.replaceChildren();
  const all = document.createElement("option");
  all.value = "";
  all.textContent = "Alle Symbole";
  symbolRoomFilter.append(all);
  for (const label of labels) {
    const option = document.createElement("option");
    option.value = label;
    // A room with no mapping still appears, so it is obvious the room exists
    // and simply has no symbol set yet.
    option.textContent = symbolsForRoomLabel(label) ? label : `${label} (kein Set)`;
    symbolRoomFilter.append(option);
  }
  if (labels.includes(current)) symbolRoomFilter.value = current;
}

symbolRoomFilter.addEventListener("change", () => {
  renderSymbolPalette();
  const allowed = symbolRoomFilter.value ? symbolsForRoomLabel(symbolRoomFilter.value) : null;
  if (symbolRoomFilter.value && !allowed) {
    setStatus(`Für "${symbolRoomFilter.value}" ist kein Symbolsatz hinterlegt — alle Symbole werden gezeigt.`, true);
  }
});

// --- path and rectangle tools ----------------------------------------------
// A Küchenzeile follows the walls and a Vorwandinstallation runs along one, so
// neither is a stamp: they are drawn, at a depth fixed by the catalogue, with
// square corners. A Kücheninsel is free-standing but sized to its room, so it
// is dragged out instead.
//
// The stairs tool already stores a path plus a width; this is the same idea
// with the depth taken from the catalogue rather than chosen by the user.

let symbolDraft = [];

function activeSymbolPlacement() {
  const symbol = getSymbol(activeSymbolKey);
  return symbol ? symbol.placement : null;
}

// --- wall snapping ---------------------------------------------------------
// A Vorwandinstallation is a wall lining and a Küchenzeile runs along the
// units against a wall, so neither should ever float mid-room. Room polygon
// edges are the wall lines available here, so a click near one is pulled onto
// it.
//
// Snapping also fixes the run's direction for free: once the first point is on
// a wall, the rest of the path follows that wall rather than needing a
// right-angle guess.

const WALL_SNAP_PX = 14;

function roomEdgesOnFloor() {
  const edges = [];
  for (const room of annotations) {
    if (room.floor_level !== activeFloor) continue;
    const pts = room.points;
    if (!Array.isArray(pts) || pts.length < 3) continue;
    for (let i = 0; i < pts.length; i += 1) {
      edges.push([pts[i], pts[(i + 1) % pts.length]]);
    }
  }
  return edges;
}

// Perpendicular projection of a point onto a segment, clamped to its ends.
function projectOntoEdge(point, a, b) {
  const ax = a.x * canvas.width, ay = a.y * canvas.height;
  const bx = b.x * canvas.width, by = b.y * canvas.height;
  const px = point.x * canvas.width, py = point.y * canvas.height;
  const dx = bx - ax, dy = by - ay;
  const lengthSquared = dx * dx + dy * dy;
  if (!lengthSquared) return null;
  let t = ((px - ax) * dx + (py - ay) * dy) / lengthSquared;
  t = Math.max(0, Math.min(1, t));
  const cx = ax + t * dx, cy = ay + t * dy;
  return { point: { x: cx / canvas.width, y: cy / canvas.height },
           distance: Math.hypot(px - cx, py - cy),
           edge: [a, b] };
}

function snapToWall(point, radiusPx = WALL_SNAP_PX) {
  let best = null;
  for (const [a, b] of roomEdgesOnFloor()) {
    const hit = projectOntoEdge(point, a, b);
    if (hit && hit.distance <= radiusPx && (!best || hit.distance < best.distance)) best = hit;
  }
  return best;
}

// Square corners: each new point is pulled onto the horizontal or vertical of
// the previous one, whichever it already sits closer to. A kitchen run three
// degrees off looks like a mistake and measures wrong.
function snapToRightAngle(previous, point) {
  const dx = (point.x - previous.x) * canvas.width;
  const dy = (point.y - previous.y) * canvas.height;
  return Math.abs(dx) >= Math.abs(dy)
    ? { x: point.x, y: previous.y }
    : { x: previous.x, y: point.y };
}

function updateDrawingActions() {
  const bar = document.querySelector("#symbolDrawActions");
  if (!bar) return;
  const drawing = symbolDraft.length > 0;
  bar.hidden = !drawing;
  const count = document.querySelector("#symbolDraftCount");
  if (count) count.textContent = drawing ? `${symbolDraft.length} Punkte` : "";
}

function handleDrawingClick(point) {
  const placement = activeSymbolPlacement();
  if (placement === "path") {
    // Prefer a wall. Only fall back to the right-angle rule when the click is
    // nowhere near one, so a free-standing run is still possible.
    const snapped = snapToWall(point);
    let next;
    if (snapped) {
      next = snapped.point;
      if (symbolDraft.length) {
        // Keep the run on the same wall line as the previous point where the
        // click is close to it, instead of stair-stepping off the wall.
        const previous = symbolDraft[symbolDraft.length - 1];
        const along = projectOntoEdge(previous, snapped.edge[0], snapped.edge[1]);
        if (along && along.distance <= WALL_SNAP_PX) next = snapped.point;
        else next = snapToRightAngle(previous, snapped.point);
      }
    } else {
      next = symbolDraft.length ? snapToRightAngle(symbolDraft[symbolDraft.length - 1], point) : point;
    }
    symbolDraft.push(next);
    updateDrawingActions();
    setStatus(symbolDraft.length < 2
      ? "Zweiten Punkt setzen. Doppelklick oder Enter beendet den Zug."
      : "Weitere Punkte setzen, Doppelklick oder Enter beendet.");
    draw();
    updateDrawingActions();
    return true;
  }
  if (placement === "rect") {
    // Click-click still works, but dragging is the natural gesture and matches
    // how room areas are drawn.
    symbolDraft.push(point);
    updateDrawingActions();
    if (symbolDraft.length < 2) {
      setStatus("Gegenüberliegende Ecke anklicken, oder aufziehen.");
      draw();
      return true;
    }
    finishDrawnSymbol();
    return true;
  }
  return false;
}

// --- rectangle by dragging -------------------------------------------------
// An island is sized to its room, so it has to be pulled out rather than
// stamped. Same gesture as drawing a room area.

let rectDrag = null;

canvas.addEventListener("pointerdown", (event) => {
  if (!ausstattungActive() || event.button !== 0) return;
  if (activeSymbolPlacement() !== "rect") return;
  if (symbolAtPoint(normalizedPoint(event))) return;   // that grabs an existing symbol
  if (!floorScaleMetresPerUnit()) return;
  event.preventDefault();
  event.stopPropagation();
  rectDrag = { start: normalizedPoint(event), moved: false };
  canvas.setPointerCapture(event.pointerId);
}, true);

canvas.addEventListener("pointermove", (event) => {
  if (!rectDrag) return;
  const now = normalizedPoint(event);
  const dx = Math.abs(now.x - rectDrag.start.x) * canvas.width;
  const dy = Math.abs(now.y - rectDrag.start.y) * canvas.height;
  if (dx > 3 || dy > 3) rectDrag.moved = true;
  symbolDraft = [rectDrag.start, now];
  draw();
}, true);

canvas.addEventListener("pointerup", (event) => {
  if (!rectDrag) return;
  const end = normalizedPoint(event);
  const dragged = rectDrag.moved;
  rectDrag = null;
  if (!dragged) { symbolDraft = []; draw(); return; }   // a click, not a drag
  symbolDraft = [symbolDraft[0], end];
  finishDrawnSymbol();
  updateDrawingActions();
}, true);

function finishDrawnSymbol() {
  const symbol = getSymbol(activeSymbolKey);
  if (!symbol) return;
  if (symbolDraft.length < 2) {
    if (symbol.placement === "path") setStatus("Ein Zug braucht mindestens zwei Punkte.", true);
    return;
  }

  const points = symbol.placement === "rect"
    ? (() => {
        const [a, b] = symbolDraft;
        return [
          { x: a.x, y: a.y }, { x: b.x, y: a.y },
          { x: b.x, y: b.y }, { x: a.x, y: b.y },
        ];
      })()
    : symbolDraft.slice();

  symbols.push({
    id: `${Date.now()}_${Math.random().toString(16).slice(2)}`,
    floor_level: activeFloor,
    symbol: symbol.key,
    points,
    rotation_deg: 0,
    mirrored: false,
  });
  symbolDraft = [];
  updateDrawingActions();
  renderSymbolList();
  draw();
  markDirty(`${symbol.label} gezeichnet. Zum Speichern auf Save klicken.`);
}

function cancelDrawnSymbol() {
  if (!symbolDraft.length) return false;
  symbolDraft = [];
  updateDrawingActions();
  draw();
  setStatus("Zeichnung abgebrochen.");
  return true;
}

// Depth in normalized-x units, from the catalogue rather than from the mouse.
function pathDepthUnits(symbol) {
  const scale = floorScaleMetresPerUnit();
  if (!scale || !symbol.depth_mm) return null;
  return (symbol.depth_mm / 1000) / scale;
}

function drawPathSymbol(placed, symbol, selected) {
  const depth = pathDepthUnits(symbol);
  const widthPx = depth ? depth * canvas.width : 8;
  ctx.save();
  ctx.lineJoin = "miter";
  ctx.lineCap = "butt";
  ctx.strokeStyle = selected ? "#b45309" : "#2563eb";
  const trace = () => {
    ctx.beginPath();
    placed.points.forEach((point, index) => {
      const x = point.x * canvas.width;
      const y = point.y * canvas.height;
      if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
  };
  ctx.globalAlpha = 0.35;
  ctx.lineWidth = widthPx;
  trace();
  ctx.stroke();
  ctx.globalAlpha = 1;
  ctx.lineWidth = selected ? 3 : 1.5;
  trace();
  ctx.stroke();
  ctx.restore();
}

function drawRectSymbol(placed, symbol, selected) {
  ctx.save();
  ctx.fillStyle = selected ? "#f59e0b33" : "#2563eb22";
  ctx.strokeStyle = selected ? "#b45309" : "#2563eb";
  ctx.lineWidth = selected ? 3 : 1.5;
  ctx.beginPath();
  placed.points.forEach((point, index) => {
    const x = point.x * canvas.width;
    const y = point.y * canvas.height;
    if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  });
  ctx.closePath();
  ctx.fill();
  ctx.stroke();
  ctx.restore();
}

let snapPreview = null;

canvas.addEventListener("pointermove", (event) => {
  if (!ausstattungActive()) return;
  const active = getSymbol(activeSymbolKey);
  const seeksWall = activeSymbolPlacement() === "path"
    || (active && active.wall && active.wall.mode !== "free");
  if (!seeksWall) { if (snapPreview) { snapPreview = null; draw(); } return; }
  const point = normalizedPoint(event);
  let radius = WALL_SNAP_PX;
  if (activeSymbolPlacement() !== "path") {
    const size = symbolFootprintInUnits(active);
    if (size) radius = size.h * canvas.height * 1.5;
  }
  const hit = snapToWall(point, radius);
  const changed = Boolean(hit) !== Boolean(snapPreview);
  snapPreview = hit;
  if (changed || hit) draw();
});

function drawSymbolDraft() {
  // Highlight the wall a click would land on, so snapping is visible before
  // it happens rather than being a surprise afterwards.
  if (snapPreview) {
    ctx.save();
    ctx.strokeStyle = "#0ea5e9";
    ctx.lineWidth = 3;
    ctx.globalAlpha = 0.8;
    ctx.beginPath();
    ctx.moveTo(snapPreview.edge[0].x * canvas.width, snapPreview.edge[0].y * canvas.height);
    ctx.lineTo(snapPreview.edge[1].x * canvas.width, snapPreview.edge[1].y * canvas.height);
    ctx.stroke();
    ctx.restore();
  }
  if (!symbolDraft.length) return;
  const symbol = getSymbol(activeSymbolKey);

  // Show the draft at its real width, not as a hairline. A Küchenzeile is a
  // 600mm band; drawing the centreline only made a finished run and an
  // unfinished one look the same, and gave no sense of whether it fits.
  if (symbol && symbol.placement === "path" && symbolDraft.length >= 2) {
    const depth = pathDepthUnits(symbol);
    if (depth) {
      ctx.save();
      ctx.strokeStyle = "#c026d3";
      ctx.globalAlpha = 0.25;
      ctx.lineWidth = depth * canvas.width;
      ctx.lineJoin = "miter";
      ctx.lineCap = "butt";
      ctx.beginPath();
      symbolDraft.forEach((point, index) => {
        const x = point.x * canvas.width;
        const y = point.y * canvas.height;
        if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
      });
      ctx.stroke();
      ctx.restore();
    }
  }

  ctx.save();
  ctx.setLineDash([6, 4]);
  ctx.strokeStyle = "#c026d3";
  ctx.lineWidth = 2;
  if (symbol && symbol.placement === "rect" && symbolDraft.length === 2) {
    const [a, b] = symbolDraft;
    const x = Math.min(a.x, b.x) * canvas.width;
    const y = Math.min(a.y, b.y) * canvas.height;
    ctx.fillStyle = "#c026d322";
    ctx.fillRect(x, y, Math.abs(b.x - a.x) * canvas.width, Math.abs(b.y - a.y) * canvas.height);
    ctx.strokeRect(x, y, Math.abs(b.x - a.x) * canvas.width, Math.abs(b.y - a.y) * canvas.height);
  } else {
    ctx.beginPath();
    symbolDraft.forEach((point, index) => {
      const x = point.x * canvas.width;
      const y = point.y * canvas.height;
      if (index === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }
  ctx.setLineDash([]);
  for (const point of symbolDraft) {
    ctx.beginPath();
    ctx.arc(point.x * canvas.width, point.y * canvas.height, 4, 0, Math.PI * 2);
    ctx.fillStyle = "#c026d3";
    ctx.fill();
  }
  ctx.restore();
}

canvas.addEventListener("dblclick", (event) => {
  if (!ausstattungActive()) return;
  if (activeSymbolPlacement() !== "path") return;
  event.preventDefault();
  finishDrawnSymbol();
});

window.addEventListener("keydown", (event) => {
  if (!ausstattungActive()) return;
  if (event.key === "Escape" && cancelDrawnSymbol()) {
    event.preventDefault();
    return;
  }
  if (event.key === "Enter" && activeSymbolPlacement() === "path") {
    event.preventDefault();
    finishDrawnSymbol();
  }
});

// --- real symbol artwork ---------------------------------------------------
// Draw Rainer's own drawings rather than a bounding box. A rectangle labelled
// "Ecksofa" says almost nothing on a plan; the drawn shape shows which way the
// chaise faces and whether it fits the corner.
//
// Each symbol is its own file in static/symbols/, split out of his
// Möbel3svg.svg. One file per symbol means any single symbol can be redrawn or
// replaced without touching the others, and the browser caches them normally.

const symbolArt = new Map();      // key -> HTMLImageElement | "pending" | "failed"

function symbolImage(key) {
  const cached = symbolArt.get(key);
  if (cached instanceof HTMLImageElement) return cached;
  if (cached === "pending" || cached === "failed") return null;

  symbolArt.set(key, "pending");
  const image = new Image();
  image.onload = () => { symbolArt.set(key, image); draw(); };
  image.onerror = () => { symbolArt.set(key, "failed"); };
  image.src = `/symbols/${encodeURIComponent(key)}.png`;
  return null;
}

// Draw the artwork if it is ready; otherwise request it and let the caller
// fall back to a box for this frame. Never blocks a repaint.
//
// Several symbols are drawn on the sheet at 90 degrees to their catalogue
// footprint — a 2-Sitzer is drawn portrait (820x1600) against a landscape
// footprint (1600x900), and the same goes for the lowboard and the
// Eckbadewanne. Painting the drawing straight into the footprint box squashed
// it and left it facing the wrong way, on top of whatever rotation the user
// set.
//
// Rather than maintain a per-symbol "is drawn rotated" flag that would go
// stale the moment a symbol is redrawn, compare the drawing's own proportions
// with the footprint's and turn it a quarter-turn when they are transposed.
// Self-correcting: redraw a symbol in the other orientation and this follows.
function drawSymbolArt(key, w, h) {
  const cached = symbolArt.get(key);
  if (!(cached instanceof HTMLImageElement)) {
    if (cached === undefined) symbolImage(key);
    return false;
  }

  const artW = cached.naturalWidth;
  const artH = cached.naturalHeight;
  if (!artW || !artH) return false;

  const artLandscape = artW >= artH;
  const boxLandscape = w >= h;
  if (artLandscape === boxLandscape) {
    ctx.drawImage(cached, -w / 2, -h / 2, w, h);
    return true;
  }

  // Transposed: rotate a quarter-turn and swap the box, so the drawing keeps
  // its proportions instead of being stretched to fit.
  ctx.save();
  ctx.rotate(Math.PI / 2);
  ctx.drawImage(cached, -h / 2, -w / 2, h, w);
  ctx.restore();
  return true;
}

// Palette thumbnails, so a button shows the drawing rather than only a word.
function decorateSymbolPalette() {
  for (const button of symbolPaletteEl.querySelectorAll("button[data-symbol]")) {
    if (button.querySelector("img")) continue;
    const thumb = document.createElement("img");
    thumb.src = `/symbols/${encodeURIComponent(button.dataset.symbol)}.png`;
    thumb.alt = "";
    thumb.className = "symbol-thumb";
    thumb.onerror = () => thumb.remove();
    button.prepend(thumb);
  }
}

// --- right-click to rotate -------------------------------------------------
// Rotating was a dropdown in the sidebar or a keyboard shortcut, so adjusting
// a symbol meant leaving the plan. Right-click turns the thing under the
// cursor.

// Right-click on a symbol opens a menu rather than acting immediately. An
// instant rotate meant a mis-aimed click silently changed the plan, and there
// was nowhere to offer mirroring or deleting.
canvas.addEventListener("contextmenu", (event) => {
  if (!ausstattungActive()) return;
  const hit = symbolAtPoint(normalizedPoint(event));
  if (!hit) { closeSymbolMenu(); return; }
  event.preventDefault();
  selectedSymbolId = hit.id;
  syncControlsToSelection();
  draw();
  openSymbolMenu(hit, event.clientX, event.clientY);
});

const symbolMenu = document.querySelector("#symbolMenu");

function closeSymbolMenu() {
  symbolMenu.hidden = true;
  symbolMenu.replaceChildren();
}

// 45-degree steps, not 90. Furniture sits at an angle often enough — a corner
// desk, a bed turned into a room — and 90 only was too coarse.
const SYMBOL_ROTATION_STEP = 45;

function openSymbolMenu(placed, clientX, clientY) {
  const symbol = getSymbol(placed.symbol);
  symbolMenu.replaceChildren();

  const commit = (message) => {
    closeSymbolMenu();
    renderSymbolList();
    draw();
    markDirty(`${symbol ? symbol.label : "Symbol"} ${message}. Zum Speichern auf Save klicken.`);
  };

  const turn = (delta) => {
    placed.rotation_deg = (((placed.rotation_deg || 0) + delta) % 360 + 360) % 360;
    symbolRotationSelect.value = String(placed.rotation_deg);
    commit(`auf ${placed.rotation_deg}° gedreht`);
  };

  const items = [
    [`↻  45° drehen`, () => turn(SYMBOL_ROTATION_STEP)],
    [`↺  45° zurück`, () => turn(-SYMBOL_ROTATION_STEP)],
    [`↻  90° drehen`, () => turn(90)],
    ["separator"],
  ];

  if (symbol && symbol.mirrorable) {
    items.push([placed.mirrored ? "● Gespiegelt" : "   Spiegeln", () => {
      placed.mirrored = !placed.mirrored;
      symbolMirrorCheckbox.checked = placed.mirrored;
      commit(placed.mirrored ? "gespiegelt" : "Spiegelung aufgehoben");
    }]);
    items.push(["separator"]);
  }

  items.push([`Ausrichtung zurücksetzen (0°)`, () => {
    placed.rotation_deg = 0;
    placed.mirrored = false;
    symbolRotationSelect.value = "0";
    symbolMirrorCheckbox.checked = false;
    commit("zurückgesetzt");
  }]);
  items.push(["separator"]);
  items.push(["Löschen", () => {
    symbols = symbols.filter((item) => item.id !== placed.id);
    selectedSymbolId = null;
    commit("gelöscht");
  }]);

  for (const [label, action] of items) {
    if (label === "separator") { symbolMenu.append(document.createElement("hr")); continue; }
    const button = document.createElement("button");
    button.type = "button";
    button.textContent = label;
    if (label === "Löschen") button.className = "danger";
    button.addEventListener("click", () => {
      if (!contextMenuReady(symbolMenu)) return;
      action();
    });
    symbolMenu.append(button);
  }

  placeContextMenu(symbolMenu, clientX, clientY);
}

window.addEventListener("pointerdown", (event) => {
  if (!symbolMenu.hidden && !symbolMenu.contains(event.target)) closeSymbolMenu();
});

// --- room navigator --------------------------------------------------------
// Zoomed in, finding a room means scrolling and hunting. This jumps straight
// to one: pick it and the view frames it.

const roomNavSelect = document.querySelector("#roomNavSelect");
const roomNavPanel = document.querySelector("#roomNavPanel");

function roomBoundsNormalized(room) {
  const xs = room.points.map((p) => p.x);
  const ys = room.points.map((p) => p.y);
  return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
}

function zoomToRoom(label) {
  const room = annotations.find((item) => item.floor_level === activeFloor && item.label === label
                                          && Array.isArray(item.points) && item.points.length >= 3);
  if (!room) return;
  const b = roomBoundsNormalized(room);
  const pane = canvasWrap.getBoundingClientRect();
  if (!imageEl.naturalWidth || !pane.width) return;

  // Room size as a fraction of the whole image, then the zoom that makes it
  // fill the pane with a margin so the walls are not flush to the edge.
  const margin = 0.82;
  const roomW = Math.max(b.x1 - b.x0, 0.02);
  const roomH = Math.max(b.y1 - b.y0, 0.02);
  const zoomForWidth = (pane.width * margin) / (imageEl.naturalWidth * roomW);
  const zoomForHeight = (pane.height * margin) / (imageEl.naturalHeight * roomH);
  applyZoom(Math.min(zoomForWidth, zoomForHeight));

  // Centre it. Scroll is in the zoomed image's pixels.
  const centreX = ((b.x0 + b.x1) / 2) * imageEl.naturalWidth * viewZoom;
  const centreY = ((b.y0 + b.y1) / 2) * imageEl.naturalHeight * viewZoom;
  canvasWrap.scrollLeft = Math.max(0, centreX - pane.width / 2);
  canvasWrap.scrollTop = Math.max(0, centreY - pane.height / 2);

  setStatus(`${label} im Blick.`);
}

function refreshRoomNav() {
  if (!roomNavSelect) return;
  const current = roomNavSelect.value;
  const labels = [...new Set(
    annotations.filter((item) => item.floor_level === activeFloor && item.label)
               .map((item) => item.label))].sort();
  roomNavSelect.replaceChildren();
  const none = document.createElement("option");
  none.value = "";
  none.textContent = labels.length ? "Raum wählen …" : "Keine Räume annotiert";
  roomNavSelect.append(none);
  for (const label of labels) {
    const option = document.createElement("option");
    option.value = label;
    option.textContent = label;
    roomNavSelect.append(option);
  }
  if (labels.includes(current)) roomNavSelect.value = current;
  roomNavPanel.hidden = false;
}

roomNavSelect.addEventListener("change", () => {
  if (!roomNavSelect.value) return;
  zoomToRoom(roomNavSelect.value);
  // Filtering the palette to the room being worked on saves a second lookup.
  if (symbolRoomFilter && [...symbolRoomFilter.options].some((o) => o.value === roomNavSelect.value)) {
    symbolRoomFilter.value = roomNavSelect.value;
    renderSymbolPalette();
  }
});

document.querySelector("#roomNavWhole").addEventListener("click", () => {
  roomNavSelect.value = "";
  zoomToFit();
  setStatus("Ganzer Grundriss.");
});

// The panel is draggable, because the room it frames may sit underneath it.
(() => {
  let drag = null;
  const handle = document.querySelector("#roomNavHandle");
  handle.addEventListener("pointerdown", (event) => {
    const r = roomNavPanel.getBoundingClientRect();
    drag = { dx: event.clientX - r.left, dy: event.clientY - r.top };
    handle.setPointerCapture(event.pointerId);
    event.preventDefault();
  });
  handle.addEventListener("pointermove", (event) => {
    if (!drag) return;
    roomNavPanel.style.left = `${event.clientX - drag.dx}px`;
    roomNavPanel.style.top = `${event.clientY - drag.dy}px`;
    roomNavPanel.style.right = "auto";
  });
  handle.addEventListener("pointerup", () => { drag = null; });
})();

refreshRoomNav();


// Save from the Ausstattung tab. The Save button lives in the Architektur
// panel, which is hidden here, so furnishing work meant switching tabs to
// save it.
document.querySelector("#saveAusstattung").addEventListener("click", () => {
  document.querySelector("#saveAnnotations").click();
});


document.querySelector("#symbolDrawFinish").addEventListener("click", () => {
  finishDrawnSymbol();
  updateDrawingActions();
});
document.querySelector("#symbolDrawCancel").addEventListener("click", () => {
  cancelDrawnSymbol();
});


// Changing floor with a path half-drawn would strand it on the old floor or
// lose it. Commit first.
(() => {
  const floorSelect = document.querySelector("#floorSelect") || document.querySelector("select[name='floor']");
  if (!floorSelect) return;
  floorSelect.addEventListener("mousedown", () => {
    if (ausstattungActive() && symbolDraft.length >= 2) finishDrawnSymbol();
  });
})();

// --- resize handles -------------------------------------------------------
//
// Symbols took their size from the catalogue, which is a nominal figure for
// furniture in general. Every plan is different, and the 3D render was coming
// out systematically undersized because a real 2200 mm dining set was being
// squeezed into an 1800 mm nominal footprint.
//
// Dragging a corner records what is actually drawn on THIS plan, which is a
// measurement rather than an assumption — and it is the annotator, looking at
// the drawing, who is best placed to take it.
//
// Dragging scales each axis freely, so a symbol can be matched to whatever is
// drawn. Hold Shift to keep the proportions.

const HANDLE_PX = 7;
let resizeDrag = null;

function selectedSymbolRecord() {
  if (!selectedSymbolId) return null;
  return symbols.find((item) => item.id === selectedSymbolId) || null;
}

// The four corners of a placed symbol, in canvas pixels, in its own rotated
// frame so the handles stay on the corners when the piece is turned.
function symbolHandles(placed) {
  const symbol = getSymbol(placed.symbol);
  if (!symbol) return [];
  const size = symbolFootprintInUnits(symbol, placed);
  if (!size) return [];
  const cx = placed.position.x * canvas.width;
  const cy = placed.position.y * canvas.height;
  const w = size.w * canvas.width;
  const h = size.h * canvas.height;
  const angle = ((placed.rotation_deg || 0) * Math.PI) / 180;
  return [[-1, -1], [1, -1], [1, 1], [-1, 1]].map(([sx, sy]) => {
    const lx = (sx * w) / 2;
    const ly = (sy * h) / 2;
    return {
      x: cx + lx * Math.cos(angle) - ly * Math.sin(angle),
      y: cy + lx * Math.sin(angle) + ly * Math.cos(angle),
      sx, sy,
    };
  });
}

function handleAtPoint(point) {
  const placed = selectedSymbolRecord();
  if (!placed || !placed.position) return null;
  const px = point.x * canvas.width;
  const py = point.y * canvas.height;
  for (const handle of symbolHandles(placed)) {
    if (Math.hypot(px - handle.x, py - handle.y) <= HANDLE_PX + 3) {
      return { placed, handle };
    }
  }
  return null;
}

function drawSymbolHandles() {
  const placed = selectedSymbolRecord();
  if (!placed || !placed.position) return;
  ctx.save();
  ctx.fillStyle = "#fff";
  ctx.strokeStyle = "#b45309";
  ctx.lineWidth = 2;
  for (const handle of symbolHandles(placed)) {
    ctx.beginPath();
    ctx.rect(handle.x - HANDLE_PX / 2, handle.y - HANDLE_PX / 2, HANDLE_PX, HANDLE_PX);
    ctx.fill();
    ctx.stroke();
  }
  ctx.restore();
}

canvas.addEventListener("pointerdown", (event) => {
  if (!ausstattungActive() || event.button !== 0) return;
  const hit = handleAtPoint(normalizedPoint(event));
  if (!hit) return;
  // Beat the move-drag and the placement click to the event.
  event.preventDefault();
  event.stopPropagation();

  const symbol = getSymbol(hit.placed.symbol);
  const current = (hit.placed.footprint_mm && hit.placed.footprint_mm.width_mm)
    ? hit.placed.footprint_mm
    : symbol.footprint_mm;
  resizeDrag = {
    placed: hit.placed,
    handle: hit.handle,
    start: normalizedPoint(event),
    from: { width_mm: current.width_mm, depth_mm: current.depth_mm },
  };
  canvas.setPointerCapture(event.pointerId);
}, true);

canvas.addEventListener("pointermove", (event) => {
  if (!resizeDrag) return;
  event.preventDefault();
  event.stopPropagation();

  const point = normalizedPoint(event);
  const scale = floorScaleMetresPerUnit();
  if (!scale) return;

  // Movement in the symbol's own frame, so dragging a corner of a rotated
  // piece still grows it along its own width and depth.
  const angle = -((resizeDrag.placed.rotation_deg || 0) * Math.PI) / 180;
  const dx = (point.x - resizeDrag.start.x) * canvas.width;
  const dy = (point.y - resizeDrag.start.y) * canvas.height;
  const localX = dx * Math.cos(angle) - dy * Math.sin(angle);
  const localY = dx * Math.sin(angle) + dy * Math.cos(angle);

  // Pixels per millimetre, isotropic: the scale is metres across the image
  // WIDTH, so both axes convert through canvas.width.
  const pxPerMm = canvas.width / (scale * 1000);
  let width = resizeDrag.from.width_mm + (resizeDrag.handle.sx * 2 * localX) / pxPerMm;
  let depth = resizeDrag.from.depth_mm + (resizeDrag.handle.sy * 2 * localY) / pxPerMm;

  if (event.shiftKey) {
    // Free by default, uniform on Shift. Measuring off a drawing means matching
    // what is actually drawn, and drawn furniture is rarely at catalogue
    // proportions — a Kuechenzeile in particular lengthens along its wall
    // without getting deeper. Shift is there for when the shape should hold.
    const ratio = resizeDrag.from.depth_mm / resizeDrag.from.width_mm;
    if (Math.abs(width - resizeDrag.from.width_mm) > Math.abs(depth - resizeDrag.from.depth_mm)) {
      depth = width * ratio;
    } else {
      width = depth / ratio;
    }
  }

  resizeDrag.placed.footprint_mm = {
    width_mm: Math.max(50, Math.round(width)),
    depth_mm: Math.max(50, Math.round(depth)),
  };
  draw();
}, true);

canvas.addEventListener("pointerup", () => {
  if (!resizeDrag) return;
  const { placed } = resizeDrag;
  resizeDrag = null;
  const size = placed.footprint_mm;
  const symbol = getSymbol(placed.symbol);
  renderSymbolList();
  draw();
  markDirty(`${symbol ? symbol.label : "Symbol"} auf ${size.width_mm} x ${size.depth_mm} mm `
            + "gemessen. Zum Speichern auf Save klicken.");
}, true);

// Paint the handles on top of everything the base draw() produced.
const _drawWithHandles = draw;
draw = function patchedDraw() {
  _drawWithHandles();
  if (ausstattungActive()) drawSymbolHandles();
};

// --- Wände: Overlay + Ecken fixieren ---------------------------------------
//
// The overlay draws the SAME walls the 3D renderer derives (walls.py is a
// port of the workbench's build_walls), so furniture placement stops being
// a guessing game about where the plaster will end up. "Ecken fixieren"
// snaps near-touching corners of neighbouring rooms onto one point — the
// exact annotation flaw that produced phantom 240mm walls downstream —
// and only changes the in-memory state: Rainer reviews and saves.

const WALL_EXCLUDED_ROOMS = ["carport", "garage", "terrasse", "balkon", "loggia"];
let wallOverlay = null;        // walls for the floor they were fetched for
let wallOverlayFloor = null;
let wallOverlayOn = false;

function wallRoomsPayload() {
  return annotations
    .filter((item) => item.floor_level === activeFloor)
    .filter((item) => {
      const label = (item.label || "").toLowerCase();
      return !WALL_EXCLUDED_ROOMS.some((needle) => label.includes(needle));
    })
    .map((item) => ({ id: item.id, points: item.points }));
}

async function fetchWallOverlay() {
  const scale = floorScaleMetresPerUnit();
  if (!scale) {
    setStatus("Erst Maßstab festlegen — ohne ihn gibt es keine Wandstärken.", true);
    return false;
  }
  const response = await fetch("/api/walls", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      rooms: wallRoomsPayload(),
      scale,
      aspect: canvas.height / canvas.width,
    }),
  });
  const payload = await response.json();
  if (!payload.ok) {
    setStatus(payload.error || "Wände konnten nicht abgeleitet werden.", true);
    return false;
  }
  wallOverlay = payload.walls;
  wallOverlayFloor = activeFloor;
  return true;
}

function drawWallOverlay() {
  if (!wallOverlayOn || !wallOverlay) return;
  if (wallOverlayFloor !== activeFloor) return;
  ctx.save();
  for (const wall of wallOverlay) {
    const ax = wall.a.x * canvas.width;
    const ay = wall.a.y * canvas.height;
    const bx = wall.b.x * canvas.width;
    const by = wall.b.y * canvas.height;
    // thickness_rel is in x-units; stroke width in canvas px.
    const px = Math.max(2, wall.thickness_rel * canvas.width);
    ctx.beginPath();
    ctx.moveTo(ax, ay);
    ctx.lineTo(bx, by);
    ctx.lineWidth = px;
    ctx.lineCap = "butt";
    ctx.strokeStyle = wall.wall_type === "exterior" ? "#334155cc" : "#64748bbb";
    ctx.stroke();
  }
  ctx.restore();
}

const toggleWallsButton = document.getElementById("toggleWallsButton");
if (toggleWallsButton) {
  toggleWallsButton.addEventListener("click", async () => {
    if (wallOverlayOn) {
      wallOverlayOn = false;
      toggleWallsButton.textContent = "Wände anzeigen";
      draw();
      return;
    }
    if (await fetchWallOverlay()) {
      wallOverlayOn = true;
      toggleWallsButton.textContent = "Wände ausblenden";
      setStatus(`${wallOverlay.length} Wände abgeleitet.`);
      draw();
    }
  });
}

const fixCornersButton = document.getElementById("fixCornersButton");
if (fixCornersButton) {
  fixCornersButton.addEventListener("click", async () => {
    const scale = floorScaleMetresPerUnit();
    if (!scale) {
      setStatus("Erst Maßstab festlegen.", true);
      return;
    }
    const rooms = annotations
      .filter((item) => item.floor_level === activeFloor)
      .map((item) => ({ id: item.id, points: item.points }));
    const response = await fetch("/api/fix-corners", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rooms, scale, aspect: canvas.height / canvas.width }),
    });
    const payload = await response.json();
    if (!payload.ok) {
      setStatus(payload.error || "Ecken konnten nicht fixiert werden.", true);
      return;
    }
    if (!payload.merged) {
      setStatus("Keine fast-berührenden Ecken gefunden — nichts geändert.");
      return;
    }
    const fixedById = new Map(payload.rooms.map((room) => [room.id, room.points]));
    for (const item of annotations) {
      if (item.floor_level !== activeFloor) continue;
      const points = fixedById.get(item.id);
      if (points) item.points = points;
    }
    if (wallOverlayOn) await fetchWallOverlay();
    draw();
    markDirty(`${payload.merged} Eckpunkt-Gruppen zusammengeführt. Zum Speichern auf Save klicken.`);
  });
}

// Drawing order: annotate.js's draw() calls drawWallOverlay() between the
// architecture and the symbols, so walls sit under the furniture.

/**
 * deriveHouseState -- the ONE place that says what state a house is in.
 *
 * Before (state/route.ts, until 2026-08-23): four independent truths -- file
 * existence, delivery manifest, local ledger, WordPress -- consulted in
 * ad-hoc branches, and "fertig" came from WordPress alone: a house whose
 * annotation, furniture or toolchain had changed since its delivery stayed
 * "fertig" forever (Codex audit, plans/workflow-audit-2026-08-22.md, P0).
 *
 * Now: the route GATHERS facts (including delivery freshness from the same
 * Python oracle go.py uses), this function DERIVES. Pure, no I/O, fully
 * table-tested. Gates run in order; the first one that fails names the state,
 * the blocker, and the one action that clears it.
 *
 * facts = {
 *   raster, rooms, levels, scale, gebaeudemass, alignmentComplete,
 *   zertifikat, aktuell, aktuellGrund, blends, finalsLokal,
 *   wordpress: { erreichbar, hochgeladen, freigegeben } | null,
 *   catalogue: { images, approved } | null,
 * }
 */

export const STATES = Object.freeze([
  "fertig",
  "fertig_update",
  "veroeffentlicht_build_alt",
  "warten_auf_freigabe",
  "bilder_freigeben",
  "bilder_hochladen",
  "warten_auf_codex",
  "wordpress_unerreichbar",
  "bau_veraltet",
  "baubereit",
  "ausrichtung_noetig",
  "vermessung_noetig",
  "keine_vorlage",
  "unbegonnen",
]);

/**
 * Die Zustaende, bei denen nichts mehr zu tun ist.
 *
 * Rainer, 2026-08-30, in der Hausakte: "the logic here is confusing me, i
 * really can't tell which one i still have to fix, can we make the ones green
 * that are accepted and uploaded?"
 *
 * Die Seite zaehlte als offen, was nicht GENAU "fertig" war. Damit standen die
 * elf veroeffentlichten Haeuser mit auf der Liste, obwohl ihre eigene
 * naechste Handlung "nichts noetig" lautet: `veroeffentlicht_build_alt` heisst,
 * die Bilder stehen beim Kunden und nur unser Renderer hat sich seither
 * bewegt. Das ist eine Notiz, kein Blocker -- so steht es unten in
 * `deriveHouseState` auch schon im Kommentar.
 *
 * Die Liste steht HIER und nicht in der Seite: der Zaehler im Kopf und die
 * gruene Farbe in der Zeile muessen dasselbe meinen, sonst steht "11 offen"
 * neben elf gruenen Zeilen.
 */
export const ERLEDIGT = new Set(["fertig", "fertig_update", "veroeffentlicht_build_alt"]);

/** Unbekanntes gilt als OFFEN -- lieber ein Haus zu viel auf der Liste. */
export function istErledigt(state) {
  return ERLEDIGT.has(state);
}

/**
 * Die Stufe davor: gebaut, zertifiziert, Bilder da -- es fehlt nur noch die
 * Lieferstrecke, und jeder dieser Schritte ist EIN Knopf.
 *
 * Rainer, 2026-08-30: "how about yellow for things that are almost finished
 * like Bilder Freigeben?"
 *
 * `warten_auf_codex` gehoert ausdruecklich NICHT dazu: da liegt die Arbeit bei
 * Codex, und wie viele Runden das kostet, hat der 2026-08-30 gezeigt --
 * german_catalog_review_bungalow_3_3_2_b_100_2 brauchte drei und war danach
 * immer noch falsch. `wordpress_unerreichbar` auch nicht: dort ist der Stand
 * UNBEKANNT, und unbekannt ist nicht fast fertig.
 *
 * Die drei stehen in STATES direkt hinter den erledigten. Das ist kein Zufall
 * und muss so bleiben: STATES sortiert auch die Hausliste, und nur so stehen
 * gruen und gelb beieinander und die Farbe bleibt ein Fortschrittsbalken.
 */
export const FAST_FERTIG = new Set([
  "warten_auf_freigabe",
  "bilder_freigeben",
  "bilder_hochladen",
]);

export function istFastFertig(state) {
  return FAST_FERTIG.has(state);
}

function result(state, blocker = "", action = "") {
  return { state, blocker, action };
}

/**
 * FERTIG-BLEIBT-FERTIG-001, 2026-10-07. Rainer: "when we say a set is finished
 * it stays finished, maybe in a different color with update, but it still
 * stays finished ... finished 1,0 or 1,1 depending on newer versions".
 *
 * The state route keeps a ledger (fertig-ledger.json) of every house that ever
 * reached "fertig". A ledgered house that would now derive anything else --
 * renderer newer, new images not yet released, WordPress unreachable -- is
 * `fertig_update`: still done, shown in its own colour, with the reason.
 * Real faults (no template, no scale, no alignment) still win.
 */
const ECHTE_FEHLER = new Set(["unbegonnen", "keine_vorlage", "vermessung_noetig", "ausrichtung_noetig"]);

const UPDATE_GRUND = {
  veroeffentlicht_build_alt: "Renderer neuer",
  bau_veraltet: "Renderer neuer",
  baubereit: "neu bauen",
  warten_auf_codex: "neuer Bau, Bilder fehlen noch",
  bilder_hochladen: "neue Bilder noch nicht hochgeladen",
  bilder_freigeben: "neue Bilder nicht freigegeben",
  warten_auf_freigabe: "Plan im Katalog nicht auf ja",
  wordpress_unerreichbar: "WordPress nicht erreichbar",
};

/** Version after this house is fertig on `build`: 1.0 the first time, the
 *  minor goes up each time it is fertig on a different build. */
export function naechsteFertigVersion(eintrag, build) {
  if (!eintrag) return { version: "1.0", build };
  if (!build || eintrag.build === build) return { version: eintrag.version, build: eintrag.build };
  const [major, minor] = String(eintrag.version || "1.0").split(".").map((n) => Number(n) || 0);
  return { version: `${major || 1}.${minor + 1}`, build };
}

export function deriveHouseState(facts, plan = "") {
  const basis = deriveBasis(facts, plan);
  const eintrag = facts?.fertigLedger;
  if (!eintrag) return basis;
  if (basis.state === "fertig") return { ...basis, version: eintrag.version };
  if (ECHTE_FEHLER.has(basis.state)) return basis;
  // FERTIG-IST-FERTIG, Rainer 2026-10-18: "no fertig ist fertig!!!" Ein
  // fertiges Haus, an dem sich NICHTS geaendert hat ausser unserem Renderer,
  // bleibt schlicht fertig -- gruen, keine Update-Meldung. Erst wenn
  // Zeichnung, Mass oder Moebel des Hauses selbst sich aendern, heisst es
  // fertig_update.
  if (facts?.nurRenderer && (basis.state === "bau_veraltet" || basis.state === "veroeffentlicht_build_alt")) {
    return { state: "fertig", blocker: `Fertig v${eintrag.version}`, action: "", version: eintrag.version };
  }
  const grund = UPDATE_GRUND[basis.state] || basis.blocker || basis.state;
  return {
    state: "fertig_update",
    blocker: `Fertig v${eintrag.version} · Update verfügbar (${grund})`,
    action: basis.action ? `optional: ${basis.action}` : "",
    version: eintrag.version,
  };
}

function deriveBasis(facts, plan = "") {
  const f = facts || {};
  const levels = Array.isArray(f.levels) ? f.levels : [];
  const ground = levels.includes("groundfloor") ? "groundfloor" : levels[0];
  const scale = f.scale || {};

  if (!f.raster && !(f.rooms > 0)) {
    return result("unbegonnen", "leerer Projektordner", "verwerfen oder Vorlage liefern");
  }
  if (!f.raster) {
    return result("keine_vorlage",
      "kein Bild im Ordner - ohne Bild ist kein Massstab messbar",
      "Vorlage neu beschaffen oder Gebaeudemass von Hand eintragen");
  }
  // Maßstab has two legitimate sources (annotation floor_scale OR
  // gebaeudemass.json beside it) -- the build accepts either, so the list
  // must not call a buildable house "vermessung_noetig".
  if (!levels.length || (!scale[ground] && !f.gebaeudemass)) {
    return result("vermessung_noetig",
      `kein Massstab fuer ${ground || "das Erdgeschoss"}`,
      "im Annotator: Gebaeudemass (setzt alle Geschosse)");
  }
  // HARD RULE (Rainer, 2026-08-23): no upper storey without alignment marks
  // on both floors -- it would stack misregistered by hundreds of mm.
  if (levels.length > 1 && !f.alignmentComplete) {
    return result("ausrichtung_noetig",
      "Geschosse nicht zueinander ausgerichtet",
      "im Annotator: auf beiden Geschossen die zwei diagonalen Aussenecken markieren (Floor alignment)");
  }
  // A certificate is the delivery manifest, not a pile of .blend files.
  if (!f.zertifikat) {
    return result("baubereit",
      f.blends > 0 ? `${f.blends} .blend ohne Zertifikat` : "noch nicht gebaut",
      "Bauen");
  }
  // Ein VEROEFFENTLICHTES Haus wird nicht dadurch unfertig, dass unser
  // Renderer sich weiterbewegt hat. Die Bilder stehen beim Kunden; der
  // aeltere Build ist eine Notiz, kein Blocker (Rainer, 2026-08-23:
  // "bungalow_039 is already finished and uploaded", dasselbe fuer
  // bungalow_040_66 -- beide standen als "bau_veraltet" in der Liste).
  const veroeffentlicht = f.catalogue && f.catalogue.approved === "ja"
    && (f.catalogue.images || 0) > 0;
  if (!f.aktuell && veroeffentlicht) {
    return result("veroeffentlicht_build_alt",
      "veröffentlicht — Build älter als der Renderer",
      "nichts nötig; Bauen nur, wenn die Bilder die neue Geometrie zeigen sollen");
  }
  // INVARIANT: eine NICHT veroeffentlichte Lieferung, die nicht mehr passt,
  // ist niemals fertig -- egal was sonst danebensteht.
  if (!f.aktuell) {
    return result("bau_veraltet",
      `Lieferung veraltet${f.aktuellGrund ? ` (${f.aktuellGrund})` : ""}`,
      "Bauen (baut neu und zertifiziert)");
  }
  const wp = f.wordpress;
  const online = wp && wp.erreichbar ? wp : null;
  if (wp && wp.erreichbar === false) {
    return result("wordpress_unerreichbar",
      "WordPress nicht erreichbar -- Bilderstand unbekannt",
      "spaeter neu laden; NICHT neu hochladen");
  }
  const hochgeladen = online ? online.hochgeladen : 0;
  const freigegeben = online ? online.freigegeben : 0;
  if (hochgeladen === 0 && !(f.finalsLokal > 0)) {
    return result("warten_auf_codex",
      `${f.blends} .blend zertifiziert, noch keine fertigen Bilder`,
      "An Codex: Auftrag schreiben, Bilder in den Lieferordner aus dem Auftrag, "
      + "dann `lieferung-pruefen.py --annehmen`");
  }
  if (hochgeladen === 0) {
    return result("bilder_hochladen",
      `${f.finalsLokal} fertige Bilder lokal, online noch keine`,
      "Hochladen");
  }
  if (freigegeben < hochgeladen) {
    return result("bilder_freigeben",
      `${hochgeladen} Bilder hochgeladen, ${freigegeben} angehakt`,
      "Freigeben");
  }
  const approved = f.catalogue && f.catalogue.approved === "ja";
  if (!approved) {
    return result("warten_auf_freigabe",
      `${freigegeben} Bilder freigegeben, Plan noch nicht`,
      "Freigeben (setzt den Plan im Katalog auf ja)");
  }
  return result("fertig");
}

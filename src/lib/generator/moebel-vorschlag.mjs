// Bereich einrichten: ein Moebel-VORSCHLAG fuer einen markierten Bereich.
// MOEBEL-BEREICH-EINRICHTEN-001, plans/moebel-bereich-einrichten-v1.md.
//
// Rainer, 2026-10-09: "i click on a room or mark an area and you
// automatically furnish this area, if something is wrong i can grab it and
// move it or rotate". Antworten: Nachttisch = Stuff-Kasten, Dusche vor Wanne,
// bei schon vorhandenen Moebeln vorher fragen (das macht der Aufrufer).
//
// Reine Rechnung, kein React, kein DOM. Ergebnis sind gewoehnliche
// Palettenmoebel (dieselbe Form wie von Hand gesetzte), damit danach alles
// greift, was der Editor schon kann. Gespeichert wird hier nichts.
//
// Konventionen des Editors:
//  - Millimeter, y nach unten.
//  - Vorn ist lokales +y (Vorderseitenpfeil). rotation_deg dreht wie SVG
//    rotate(): 0 -> vorn zeigt nach +y, 90 -> nach -x, 180 -> -y, 270 -> +x.
//  - "stuff" ist ein Rechteck-Moebel: points_mm = zwei Gegenecken.
//
// Was NICHT passt, wird weggelassen und gemeldet -- nie gequetscht.

import { getSymbol, wallBehaviour } from "./symbol-catalog.mjs";

export const TUER_FREIRAUM_MM = 900;
export const FENSTER_FREIRAUM_MM = 600;
const SCHRITT_MM = 50;
const TOLERANZ_MM = 5;

/** Die drei Raumtypen des Prototyps (Rainer: erst fuehlen, dann alle elf). */
// Reihenfolge wie Rainers Liste (2026-10-09): "wohnzimmer esszimmer küche
// diele hwr kinderzimmer gast schlafzimmer du/bad wc bad".
export const RAUMTYPEN = Object.freeze([
  { key: "wohnzimmer", label: "Wohnzimmer" },
  { key: "esszimmer", label: "Esszimmer" },
  { key: "kueche", label: "Küche" },
  { key: "diele", label: "Diele" },
  { key: "hwr", label: "HWR" },
  { key: "kinderzimmer", label: "Kinderzimmer" },
  { key: "gast", label: "Gast" },
  // Rainer, 2026-10-09: "büro fehlt".
  { key: "buero", label: "Büro" },
  { key: "schlafzimmer", label: "Schlafzimmer" },
  { key: "duschbad", label: "Du/Bad" },
  { key: "wc", label: "WC" },
  { key: "bad", label: "Bad" },
]);

// In alten Daten heisst der Raum auch "K\ufffdche".
const KOCHEN = /k(ü|ue|\ufffd)che|kochen/i;

/** Raumname -> Raumtyp, wenn er eindeutig einer der drei ist. */
export function raumtypAusName(name) {
  const text = `${name || ""}`.toLocaleLowerCase("de-DE");
  // Rainer, 2026-10-30: "when there is a DuWC why is hter no shower added".
  // Der Annotator nennt den Raum "DU-WC"; das fiel bisher auf die WC-Regel.
  if (/dusch|du\/bad|du-bad|(^|[^a-zäöüß])du[-\/ ]?wc\b/.test(text)) return "duschbad";
  if (/bad/.test(text)) return "bad";
  if (/(^|[^a-z])wc\b/.test(text)) return "wc";
  if (/schlaf|eltern/.test(text)) return "schlafzimmer";
  if (/kind/.test(text)) return "kinderzimmer";
  if (/gast|gäste|gaeste/.test(text)) return "gast";
  if (/diele|flur|garderobe/.test(text)) return "diele";
  if (/hwr|htr|hauswirtschaft|technik/.test(text)) return "hwr";
  if (/büro|buero|arbeit|office/.test(text)) return "buero";
  // Ein kombinierter Raum ("Wohnen / Essen / Kochen") hat KEINEN eindeutigen
  // Typ -- dort zeichnet Rainer die Bereiche selbst (2026-10-09: "this
  // bereich can be wohnzimmer and esszimmer and kitchen").
  const teile = [/wohn/, /ess(en|zimmer)/, KOCHEN].filter((re) => re.test(text)).length;
  if (teile > 1) return null;
  if (/wohn/.test(text)) return "wohnzimmer";
  if (/ess(en|zimmer)/.test(text)) return "esszimmer";
  if (KOCHEN.test(text)) return "kueche";
  return null;
}

// --- Geometrie -------------------------------------------------------------

export function punktImPolygon(x, y, poly) {
  let drin = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if ((yi > y) !== (yj > y)
        && x < ((xj - xi) * (y - yi)) / ((yj - yi) || 1e-9) + xi) drin = !drin;
  }
  return drin;
}

function abstandZurStrecke(x, y, a, b) {
  const dx = b[0] - a[0];
  const dy = b[1] - a[1];
  const l2 = dx * dx + dy * dy;
  let t = l2 ? ((x - a[0]) * dx + (y - a[1]) * dy) / l2 : 0;
  t = Math.max(0, Math.min(1, t));
  return Math.hypot(x - (a[0] + dx * t), y - (a[1] + dy * t));
}

/** Drinnen oder auf dem Rand (Moebel stehen buendig an der Wand). */
function imOderAufPolygon(x, y, poly) {
  if (punktImPolygon(x, y, poly)) return true;
  for (let i = 0; i < poly.length; i += 1) {
    if (abstandZurStrecke(x, y, poly[i], poly[(i + 1) % poly.length]) <= TOLERANZ_MM) return true;
  }
  return false;
}

/** Achsparalleles Rechteck {x0,y0,x1,y1} liegt ganz im Polygon. */
function rechteckImPolygon(r, poly) {
  const ecken = [[r.x0, r.y0], [r.x1, r.y0], [r.x1, r.y1], [r.x0, r.y1],
                 [(r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2]];
  if (!ecken.every(([x, y]) => imOderAufPolygon(x, y, poly))) return false;
  // Eine einspringende Ecke des Raums darf nicht im Rechteck stecken (L-Raum).
  return !poly.some(([x, y]) => x > r.x0 + TOLERANZ_MM && x < r.x1 - TOLERANZ_MM
                             && y > r.y0 + TOLERANZ_MM && y < r.y1 - TOLERANZ_MM);
}

function ueberlappen(a, b) {
  return a.x0 < b.x1 - TOLERANZ_MM && b.x0 < a.x1 - TOLERANZ_MM
      && a.y0 < b.y1 - TOLERANZ_MM && b.y0 < a.y1 - TOLERANZ_MM;
}

function rechteckAusPunkten(punkte) {
  const xs = punkte.map((p) => p[0]);
  const ys = punkte.map((p) => p[1]);
  return { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
}

/** Kanten des Bereichs, jede mit Laenge, Richtung und Normale nach innen. */
export function kantenNachInnen(poly) {
  const kanten = [];
  for (let i = 0; i < poly.length; i += 1) {
    const a = poly[i];
    const b = poly[(i + 1) % poly.length];
    const laenge = Math.hypot(b[0] - a[0], b[1] - a[1]);
    if (laenge < 300) continue;
    const u = [(b[0] - a[0]) / laenge, (b[1] - a[1]) / laenge];
    // Nur achsparallele Kanten: alle Moebel stehen in 90-Grad-Schritten.
    if (Math.abs(u[0]) > 0.02 && Math.abs(u[1]) > 0.02) continue;
    const mitte = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
    let n = [-u[1], u[0]];
    if (!punktImPolygon(mitte[0] + n[0] * 50, mitte[1] + n[1] * 50, poly)) n = [u[1], -u[0]];
    if (!punktImPolygon(mitte[0] + n[0] * 50, mitte[1] + n[1] * 50, poly)) continue;
    kanten.push({ a, b, u, n: [Math.round(n[0]), Math.round(n[1])], laenge, index: i });
  }
  return kanten;
}

function drehungFuerNormale(n) {
  if (n[1] === 1) return 0;
  if (n[0] === -1) return 90;
  if (n[1] === -1) return 180;
  return 270;
}

/**
 * Freiraum vor einer Oeffnung, als Rechteck. Liegt die Oeffnung auf dem
 * Bereichsrand, nur nach innen; sonst (gezogenes Rechteck neben einer Tuer)
 * nach beiden Seiten -- lieber zu vorsichtig.
 */
function freiraumVor(oeffnung, poly, tiefe) {
  const [a, b] = [oeffnung.a, oeffnung.b];
  const laenge = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
  const u = [(b[0] - a[0]) / laenge, (b[1] - a[1]) / laenge];
  const mitte = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const normalen = [[-u[1], u[0]], [u[1], -u[0]]];
  const nachInnen = normalen.filter((n) => punktImPolygon(mitte[0] + n[0] * 150, mitte[1] + n[1] * 150, poly));
  const richtungen = nachInnen.length === 1 ? nachInnen : normalen;
  // 300 mm HINTER der Oeffnung beginnen: in den Daten sitzt die Oeffnung auf
  // der Wandmitte, die Raumkante auf der Innenseite -- mal davor, mal dahinter
  // (onehalfstorey_020 Buero: Fenster 120 mm INNERHALB der Raumkante, die
  // Fensterwand galt deshalb als fensterlos).
  const R = 300;
  return richtungen.map((n) => rechteckAusPunkten([
    [a[0] - n[0] * R, a[1] - n[1] * R], [b[0] - n[0] * R, b[1] - n[1] * R],
    [a[0] + n[0] * tiefe, a[1] + n[1] * tiefe], [b[0] + n[0] * tiefe, b[1] + n[1] * tiefe],
  ]));
}

// --- Platzieren ------------------------------------------------------------

/** Hohe Moebel duerfen nicht vor ein Fenster. */
const HOCH = new Set(["kleiderschrank", "schrank_40", "schrank_60", "hochschrank_herd",
  "kuehlschrank", "abstellschrank"]);

/** Ueber dem Lowboard haengt der Fernseher -- er darf es ueberlappen. */
const DARF_UEBERLAPPEN = {
  fernseher: ["lowboard"], spuele: ["kuechenzeile"], kochfeld: ["kuechenzeile"],
  // Der Stuhl schiebt sich ein Stueck unter die Platte.
  schreibtischstuhl: ["schreibtisch", "schreibtisch_kind"],
  // Der Rahmen des Ecksofas ist neben der Liege leer -- dort steht der Tisch.
  couchtisch: ["ecksofa"],
};

function masse(key) {
  const s = getSymbol(key);
  return { w: s?.footprint_mm?.width_mm || 0, d: s?.footprint_mm?.depth_mm || 0 };
}

/**
 * Ein Moebel an Kante `kante`, Mitte bei Laufposition t (mm ab kante.a).
 * Liefert das Weltrechteck und das PlacedSymbol, ohne zu pruefen.
 */
function anKante(key, kante, t, abstand = null) {
  const { w, d } = masse(key);
  const gap = abstand ?? (wallBehaviour(key).gap_mm || 0);
  const mx = kante.a[0] + kante.u[0] * t + kante.n[0] * (gap + d / 2);
  const my = kante.a[1] + kante.u[1] * t + kante.n[1] * (gap + d / 2);
  const quer = Math.abs(kante.u[0]) > 0.5; // Kante laeuft in x
  const halbX = quer ? w / 2 : d / 2;
  const halbY = quer ? d / 2 : w / 2;
  return {
    rechteck: { x0: mx - halbX, y0: my - halbY, x1: mx + halbX, y1: my + halbY },
    moebel: {
      symbol: key,
      position_mm: [Math.round(mx), Math.round(my)],
      rotation_deg: drehungFuerNormale(kante.n),
      mirrored: false,
      footprint_mm: { width_mm: w, depth_mm: d },
    },
  };
}

/** Liegt die Kante auf einer echten Wand (Raumkante des Geschosses)? */
function kanteAnWand(kante, raumKanten) {
  if (!raumKanten?.length) return true; // ohne Angabe: jede Kante ist Wand
  const proben = [0.25, 0.5, 0.75].map((f) => [kante.a[0] + (kante.b[0] - kante.a[0]) * f,
                                              kante.a[1] + (kante.b[1] - kante.a[1]) * f]);
  return proben.every(([x, y]) => raumKanten.some(([a, b]) => abstandZurStrecke(x, y, a, b) <= 150));
}

/**
 * Schon stehende Moebel als Hindernisse. Eine gezeichnete Kuechenzeile behaelt
 * ihren Schluessel, damit Spuele und Kochfeld auf sie duerfen, und sperrt nur
 * ihre Schenkel: das Huellrechteck einer L-Zeile waere die halbe Kueche.
 */
function belegtVon(r) {
  if (r.symbol !== "kuechenzeile" || !(r.points_mm?.length >= 2)) return [{ ...r, key: "vorhanden" }];
  return schenkelVon(r.points_mm).map((s, i, alle) => {
    const vor = i > 0 ? ZEILE_HALB_MM : 0;
    const nach = i < alle.length - 1 ? ZEILE_HALB_MM : 0;
    const a = [s.a[0] - s.u[0] * vor, s.a[1] - s.u[1] * vor];
    const b = [s.b[0] + s.u[0] * nach, s.b[1] + s.u[1] * nach];
    const quer = [Math.abs(s.u[1]) * ZEILE_HALB_MM, Math.abs(s.u[0]) * ZEILE_HALB_MM];
    return { ...r, key: "kuechenzeile",
             x0: Math.min(a[0], b[0]) - quer[0], x1: Math.max(a[0], b[0]) + quer[0],
             y0: Math.min(a[1], b[1]) - quer[1], y1: Math.max(a[1], b[1]) + quer[1] };
  });
}

function erzeugeKontext(bereich) {
  const { polygon, oeffnungen = [], vorhandene = [], raumKanten = [] } = bereich;
  const poly = polygon;
  const tuerZonen = oeffnungen
    .filter((o) => o.typ === "door" || o.typ === "passage")
    .flatMap((o) => freiraumVor(o, poly, TUER_FREIRAUM_MM));
  const fensterZonen = oeffnungen
    .filter((o) => o.typ === "window")
    .flatMap((o) => freiraumVor(o, poly, FENSTER_FREIRAUM_MM));
  return {
    eingabe: bereich,
    poly,
    kanten: kantenNachInnen(poly).map((k) => ({ ...k, anWand: kanteAnWand(k, raumKanten) })),
    tuerZonen,
    fensterZonen,
    vorhanden: vorhandene,
    belegt: vorhandene.flatMap(belegtVon),
    gesetzt: [],
    weggelassen: [],
  };
}

function frei(ctx, key, rechteck) {
  if (!rechteckImPolygon(rechteck, ctx.poly)) return false;
  if (ctx.tuerZonen.some((z) => ueberlappen(z, rechteck))) return false;
  if (HOCH.has(key) && ctx.fensterZonen.some((z) => ueberlappen(z, rechteck))) return false;
  return !ctx.belegt.some((r) => ueberlappen(r, rechteck) && !(DARF_UEBERLAPPEN[key] || []).includes(r.key));
}

/** Wieviel einer Kante von Tueren beruehrt wird -- weniger ist besser. */
function tuerAnKante(ctx, kante) {
  const streifen = rechteckAusPunkten([kante.a, kante.b,
    [kante.a[0] + kante.n[0] * 100, kante.a[1] + kante.n[1] * 100]]);
  return ctx.tuerZonen.some((z) => ueberlappen(z, streifen)) ? 1 : 0;
}

function fensterAnKante(ctx, kante) {
  const streifen = rechteckAusPunkten([kante.a, kante.b,
    [kante.a[0] + kante.n[0] * 100, kante.a[1] + kante.n[1] * 100]]);
  return ctx.fensterZonen.some((z) => ueberlappen(z, streifen)) ? 1 : 0;
}

/**
 * Laufpositionen auf einer Kante, sortiert nach Naehe zum Wunsch.
 * wunsch: "mitte" | "ecke" | Zahl (t in mm).
 */
function positionen(kante, w, wunsch) {
  const min = w / 2;
  const max = kante.laenge - w / 2;
  if (max < min - TOLERANZ_MM) return [];
  const alle = [];
  for (let t = min; t <= max + 1e-6; t += SCHRITT_MM) alle.push(t);
  if (!alle.length || Math.abs(alle[alle.length - 1] - max) > 1) alle.push(max);
  if (wunsch === "ecke") {
    return alle.sort((p, q) => Math.min(p - min, max - p) - Math.min(q - min, max - q));
  }
  const ziel = typeof wunsch === "number" ? wunsch : kante.laenge / 2;
  return alle.sort((p, q) => Math.abs(p - ziel) - Math.abs(q - ziel));
}

/**
 * Setzt `key` an die erste passende Stelle. kanten: Reihenfolge der Wahl.
 * Gibt das gesetzte Ergebnis (mit Kante) zurueck oder null.
 */
function setze(ctx, key, kanten, wunsch = "mitte", abstand = null) {
  const { w } = masse(key);
  for (const kante of kanten) {
    const wunschHier = typeof wunsch === "function" ? wunsch(kante) : wunsch;
    for (const t of positionen(kante, w, wunschHier)) {
      const versuch = anKante(key, kante, t, abstand);
      if (!frei(ctx, key, versuch.rechteck)) continue;
      ctx.belegt.push({ ...versuch.rechteck, key });
      ctx.gesetzt.push(versuch.moebel);
      return { ...versuch, kante, t };
    }
  }
  return null;
}

/** Ein freistehendes Moebel mit festem Mittelpunkt (Couchtisch). */
function setzeFrei(ctx, key, mitte, drehung) {
  const { w, d } = masse(key);
  const quer = drehung % 180 === 0;
  const hx = (quer ? w : d) / 2;
  const hy = (quer ? d : w) / 2;
  const rechteck = { x0: mitte[0] - hx, y0: mitte[1] - hy, x1: mitte[0] + hx, y1: mitte[1] + hy };
  if (!frei(ctx, key, rechteck)) return null;
  ctx.belegt.push({ ...rechteck, key });
  const moebel = {
    symbol: key, position_mm: [Math.round(mitte[0]), Math.round(mitte[1])],
    rotation_deg: drehung, mirrored: false, footprint_mm: { width_mm: w, depth_mm: d },
  };
  ctx.gesetzt.push(moebel);
  return { rechteck, moebel };
}

/** Rechteck-Moebel "stuff" (Nachttisch-Platzhalter) an festem Ort. */
function setzeKasten(ctx, rechteck) {
  if (!frei(ctx, "stuff", rechteck)) return false;
  ctx.belegt.push({ ...rechteck, key: "stuff" });
  ctx.gesetzt.push({
    symbol: "stuff",
    points_mm: [[Math.round(rechteck.x0), Math.round(rechteck.y0)],
                [Math.round(rechteck.x1), Math.round(rechteck.y1)]],
    rotation_deg: 0, mirrored: false,
  });
  return true;
}

function weg(ctx, label) { ctx.weggelassen.push(label); }

// Kanten-Reihenfolgen.
const laengsteZuerst = (kanten) => [...kanten].sort((a, b) =>
  (Number(b.anWand) - Number(a.anWand)) || (b.laenge - a.laenge));
function ruhigsteZuerst(ctx) {
  // Echte Wand vor offener Bereichsgrenze: ein selbst gezeichneter Bereich
  // in einem grossen Raum hat Kanten, die nur Luft sind.
  return [...ctx.kanten].sort((a, b) =>
    (Number(b.anWand) - Number(a.anWand))
    || (tuerAnKante(ctx, a) - tuerAnKante(ctx, b))
    || (fensterAnKante(ctx, a) - fensterAnKante(ctx, b))
    || (b.laenge - a.laenge));
}
const gegenueber = (kante) => (k) => k.n[0] === -kante.n[0] && k.n[1] === -kante.n[1];

// --- Regeln je Raumtyp -----------------------------------------------------

const NACHTTISCH_B = 450;
const NACHTTISCH_T = 400;

function schlafzimmer(ctx) {
  const bett = setze(ctx, "doppelbett", ruhigsteZuerst(ctx), "mitte")
    || setze(ctx, "einzelbett", ruhigsteZuerst(ctx), "mitte");
  if (!bett) weg(ctx, "Bett");
  if (bett) {
    // Nachttische links und rechts am Kopfteil (Rainer: Stuff-Kasten nehmen).
    const { kante, t } = bett;
    const { w } = masse(bett.moebel.symbol);
    let gesetzt = 0;
    for (const seite of [-1, 1]) {
      const tMitte = t + seite * (w / 2 + 30 + NACHTTISCH_B / 2);
      const p = (lauf, tief) => [kante.a[0] + kante.u[0] * lauf + kante.n[0] * tief,
                                 kante.a[1] + kante.u[1] * lauf + kante.n[1] * tief];
      const r = rechteckAusPunkten([p(tMitte - NACHTTISCH_B / 2, 0), p(tMitte + NACHTTISCH_B / 2, NACHTTISCH_T)]);
      if (setzeKasten(ctx, r)) gesetzt += 1;
    }
    if (gesetzt < 2) weg(ctx, gesetzt ? "ein Nachttisch" : "Nachttische");
    const andere = ruhigsteZuerst(ctx).filter((k) => k !== kante);
    if (!setze(ctx, "kleiderschrank", [...andere, kante], "ecke")) weg(ctx, "Kleiderschrank");
  }
}

function dusche(ctx) {
  const dusche = setze(ctx, "dusche", laengsteZuerst(ctx.kanten), "ecke")
    || setze(ctx, "dusche_gross", laengsteZuerst(ctx.kanten), "ecke")
    || setze(ctx, "dusche_klein", laengsteZuerst(ctx.kanten), "ecke");
  if (!dusche) weg(ctx, "Dusche");
  return dusche;
}

function waschtischUndWc(ctx) {
  if (!setze(ctx, "waschtisch", ruhigsteZuerst(ctx), "mitte")
      && !setze(ctx, "handwaschbecken", ruhigsteZuerst(ctx), "mitte")) weg(ctx, "Waschtisch");
  if (!setze(ctx, "wand_wc", ruhigsteZuerst(ctx), "mitte")) weg(ctx, "WC");
}

function bad(ctx) {
  // Rainer, 2026-10-09: "the bathroom was missing the badewanne". Ein Bad
  // bekommt Dusche UND Wanne; die Dusche zuerst (seine Antwort "2 Dusche"),
  // die Wanne in eine andere Ecke, wenn sie noch passt -- sonst gemeldet.
  dusche(ctx);
  waschtischUndWc(ctx);
  if (!setze(ctx, "badewanne", laengsteZuerst(ctx.kanten), "ecke")) weg(ctx, "Badewanne");
}

function duschbad(ctx) {
  dusche(ctx);
  waschtischUndWc(ctx);
}

function wc(ctx) {
  if (!setze(ctx, "wand_wc", ruhigsteZuerst(ctx), "mitte")) weg(ctx, "WC");
  if (!setze(ctx, "handwaschbecken", ruhigsteZuerst(ctx), "mitte")) weg(ctx, "Handwaschbecken");
}

/** Zwei Moebel nebeneinander an derselben Wand (Waschmaschine + Trockner). */
function setzeDaneben(ctx, key, neben) {
  const { w } = masse(key);
  const { w: wNeben } = masse(neben.moebel.symbol);
  for (const seite of [1, -1]) {
    const t = neben.t + seite * (wNeben / 2 + w / 2);
    const versuch = anKante(key, neben.kante, t, 0);
    if (t - w / 2 < -TOLERANZ_MM || t + w / 2 > neben.kante.laenge + TOLERANZ_MM) continue;
    if (!frei(ctx, key, versuch.rechteck)) continue;
    ctx.belegt.push({ ...versuch.rechteck, key });
    ctx.gesetzt.push(versuch.moebel);
    return { ...versuch, kante: neben.kante, t };
  }
  return null;
}

function diele(ctx) {
  // Nur an die Wand -- die Mitte bleibt Laufweg.
  const garderobe = setze(ctx, "garderobe", ruhigsteZuerst(ctx), "mitte");
  if (!garderobe) weg(ctx, "Garderobe");
  const schrank = (garderobe && setzeDaneben(ctx, "schrank_40", garderobe))
    || setze(ctx, "schrank_40", ruhigsteZuerst(ctx), "ecke");
  if (!schrank) weg(ctx, "Schrank");
}

function hwr(ctx) {
  const wm = setze(ctx, "waschmaschine", ruhigsteZuerst(ctx), "ecke");
  if (!wm) weg(ctx, "Waschmaschine");
  if (!(wm && setzeDaneben(ctx, "trockner", wm)) && !setze(ctx, "trockner", ruhigsteZuerst(ctx), "ecke")) {
    weg(ctx, "Trockner");
  }
  if (!setze(ctx, "schrank_60", ruhigsteZuerst(ctx), "ecke")) weg(ctx, "Regal/Schrank");
}

/** Fensterkanten zuerst (Schreibtisch unters Fenster), sonst wie ruhigsteZuerst. */
function fensterZuerst(ctx) {
  return [...ctx.kanten].sort((a, b) =>
    (Number(b.anWand) - Number(a.anWand))
    || (fensterAnKante(ctx, b) - fensterAnKante(ctx, a))
    || (tuerAnKante(ctx, a) - tuerAnKante(ctx, b))
    || (b.laenge - a.laenge));
}

function kinderzimmer(ctx) {
  // Einzelbett in eine Ecke, Kopfteil an die Wand; ein Nachttisch daneben.
  const bett = setze(ctx, "einzelbett", ruhigsteZuerst(ctx), "ecke");
  if (!bett) weg(ctx, "Bett");
  if (bett) {
    const { kante, t } = bett;
    const { w } = masse("einzelbett");
    const p = (lauf, tief) => [kante.a[0] + kante.u[0] * lauf + kante.n[0] * tief,
                               kante.a[1] + kante.u[1] * lauf + kante.n[1] * tief];
    // Auf die Seite, die NICHT an der Nachbarwand liegt.
    const seite = t < kante.laenge / 2 ? 1 : -1;
    const tMitte = t + seite * (w / 2 + 30 + NACHTTISCH_B / 2);
    const r = rechteckAusPunkten([p(tMitte - NACHTTISCH_B / 2, 0), p(tMitte + NACHTTISCH_B / 2, NACHTTISCH_T)]);
    if (!setzeKasten(ctx, r)) weg(ctx, "Nachttisch");
  }
  if (!setze(ctx, "schreibtisch_kind", fensterZuerst(ctx), "mitte")) weg(ctx, "Schreibtisch");
  if (!setze(ctx, "kleiderschrank", ruhigsteZuerst(ctx), "ecke")) weg(ctx, "Kleiderschrank");
  // Rainer, 2026-11-01: "put the playstation gruppe to the kidsroom and not the living room".
  if (!setze(ctx, "playstation_gruppe", ruhigsteZuerst(ctx), "mitte")) weg(ctx, "Playstation-Gruppe");
}

// Ecksofa: im Symbol (ecksofa.png) sitzt die Liege links, also bei lokal -x.
// Breite der Liege und Tiefe des Sitzteils, aus dem Symbol abgegriffen.
const ECKSOFA_LIEGE_B = 700;
const ECKSOFA_SITZ_T = 950;

function wohnzimmer(ctx) {
  // Rainer, 2026-10-09: "please use the eckcouch for wohnzimmer". Das
  // Ecksofa kommt in eine Ecke, Ruecken an die Wand, die Liege zur Ecke --
  // so umarmt das L die Ecke. Passt es nicht, wie bisher 3- oder 2-Sitzer.
  let sofa = setze(ctx, "ecksofa", ruhigsteZuerst(ctx), "ecke");
  let tSitz = sofa?.t;
  let sitzTiefe = sofa ? ECKSOFA_SITZ_T : 0;
  if (sofa) {
    const { kante, t } = sofa;
    const { w } = masse("ecksofa");
    // Das Ecksofa-Symbol ist andersherum gezeichnet als alle anderen: seine
    // Vorderseite ist lokal -y. Rainer setzt es von Hand entsprechend --
    // onehalfstorey_020 EG: an der Oberwand mit 180 Grad (+ gespiegelt),
    // Lowboard, Bett, Schreibtisch dort mit der ueblichen Drehung. Also hier
    // um 180 Grad weiter drehen, sonst schaut die Lehne in den Raum.
    sofa.moebel.rotation_deg = (sofa.moebel.rotation_deg + 180) % 360;
    // Zur naeheren Ecke zeigt -u (Anfang der Kante) oder +u (Ende).
    const zurEcke = t < kante.laenge / 2 ? -1 : 1;
    const winkel = (sofa.moebel.rotation_deg * Math.PI) / 180;
    const lokalX = [Math.round(Math.cos(winkel)), Math.round(Math.sin(winkel))];
    const xEntlangU = lokalX[0] * kante.u[0] + lokalX[1] * kante.u[1]; // +1 oder -1
    // Ungespiegelt liegt die Liege bei lokal -x, also bei -xEntlangU entlang u.
    sofa.moebel.mirrored = -xEntlangU !== zurEcke;
    // Sitzteil = der Teil neben der Liege; dorthin zielen Tisch und Fernseher.
    tSitz = t - zurEcke * (ECKSOFA_LIEGE_B / 2);
    void w;
  }
  if (!sofa) {
    sofa = setze(ctx, "sofa_3sitzer", ruhigsteZuerst(ctx), "mitte")
      || setze(ctx, "sofa_2sitzer", ruhigsteZuerst(ctx), "mitte");
    tSitz = sofa?.t;
    sitzTiefe = sofa ? masse(sofa.moebel.symbol).d : 0;
  }
  if (!sofa) { weg(ctx, "Sofa"); return; }
  // Lowboard + Fernseher gegenueber, auf Hoehe des Sitzteils.
  const mitteSofa = [sofa.kante.a[0] + sofa.kante.u[0] * tSitz, sofa.kante.a[1] + sofa.kante.u[1] * tSitz];
  const gegen = ctx.kanten.filter(gegenueber(sofa.kante));
  const aufHoehe = (k) => (mitteSofa[0] - k.a[0]) * k.u[0] + (mitteSofa[1] - k.a[1]) * k.u[1];
  const board = setze(ctx, "lowboard", gegen, aufHoehe);
  if (!board) weg(ctx, "Lowboard + Fernseher");
  if (board && !setze(ctx, "fernseher", [board.kante], board.t)) weg(ctx, "Fernseher");
  // Couchtisch: 400 mm vor dem Sitzteil, quer wie das Sofa.
  const tisch = masse("couchtisch");
  const vor = (wallBehaviour(sofa.moebel.symbol).gap_mm || 0) + sitzTiefe + 400 + tisch.d / 2;
  const mitte = [sofa.kante.a[0] + sofa.kante.u[0] * tSitz + sofa.kante.n[0] * vor,
                 sofa.kante.a[1] + sofa.kante.u[1] * tSitz + sofa.kante.n[1] * vor];
  if (!setzeFrei(ctx, "couchtisch", mitte, sofa.moebel.rotation_deg)) weg(ctx, "Couchtisch");
}

/** Freistehend nahe einem Zielpunkt suchen (Tisch mitten im Bereich). */
function setzeFreiNahe(ctx, key, ziel, drehungen) {
  const xs = ctx.poly.map((p) => p[0]);
  const ys = ctx.poly.map((p) => p[1]);
  const kandidaten = [];
  for (let x = Math.min(...xs); x <= Math.max(...xs); x += 100) {
    for (let y = Math.min(...ys); y <= Math.max(...ys); y += 100) kandidaten.push([x, y]);
  }
  kandidaten.sort((p, q) => Math.hypot(p[0] - ziel[0], p[1] - ziel[1]) - Math.hypot(q[0] - ziel[0], q[1] - ziel[1]));
  for (const mitte of [ziel, ...kandidaten]) {
    for (const drehung of drehungen) {
      const r = setzeFrei(ctx, key, mitte, drehung);
      if (r) return r;
    }
  }
  return null;
}

function bereichsMitte(poly) {
  const xs = poly.map((p) => p[0]);
  const ys = poly.map((p) => p[1]);
  return { mitte: [(Math.min(...xs) + Math.max(...xs)) / 2, (Math.min(...ys) + Math.max(...ys)) / 2],
           breit: Math.max(...xs) - Math.min(...xs) >= Math.max(...ys) - Math.min(...ys) };
}

function esszimmer(ctx) {
  // Der Tisch steht frei in der Mitte, die lange Seite laengs des Bereichs.
  const { mitte, breit } = bereichsMitte(ctx.poly);
  const quer = breit ? [0, 90] : [90, 0];
  if (setzeFreiNahe(ctx, "essgruppe_6", mitte, quer)) return;
  const tisch = setzeFreiNahe(ctx, "esstisch", mitte, quer);
  if (!tisch) { weg(ctx, "Esstisch"); return; }
  // Kleiner Bereich: Tisch einzeln, Stuehle an die langen Seiten, so viele passen.
  const r = tisch.rechteck;
  const stuhl = masse("esszimmerstuhl");
  const laengsX = r.x1 - r.x0 >= r.y1 - r.y0;
  let stuehle = 0;
  for (const f of [0.25, 0.75]) {
    for (const seite of [-1, 1]) {
      const mitteStuhl = laengsX
        ? [r.x0 + (r.x1 - r.x0) * f, seite < 0 ? r.y0 - stuhl.d / 2 + 100 : r.y1 + stuhl.d / 2 - 100]
        : [seite < 0 ? r.x0 - stuhl.d / 2 + 100 : r.x1 + stuhl.d / 2 - 100, r.y0 + (r.y1 - r.y0) * f];
      // Vorn (+y lokal) zeigt zum Tisch.
      const drehung = laengsX ? (seite < 0 ? 0 : 180) : (seite < 0 ? 270 : 90);
      if (setzeFrei(ctx, "esszimmerstuhl", mitteStuhl, drehung)) stuehle += 1;
    }
  }
  if (stuehle < 4) weg(ctx, `${4 - stuehle} Stühle`);
}

// --- Kueche ------------------------------------------------------------------
// Rainer, 2026-10-30: "küche bracuht kücheninsel kochfeld spüle hohschrank
// fridge" und "please dont do the küchenzeile": die Zeile zeichnet er selbst,
// hier kommt nur dazu, was auf und an sie gehoert.

const ZEILE_HALB_MM = 300;
// Gemessen an 81 von Rainer gezeichneten Kuechen: Gang im Median 1100 mm, im
// unteren Viertel 800; Inseln meist 2000 oder 1600 lang und 1000 tief. In
// jeder zweiten stehen sie quer oder hinter dem Zeilenende. Deshalb erst der
// Wunschgang, dann enger, bevor "zu wenig Platz" gemeldet wird.
const INSEL_GAENGE_MM = [1100, 900, 800];
const INSEL_WAND_MM = 800;
const INSEL_SUCHE_MM = 100;
const INSEL_MASSE = [[2000, 1000], [1600, 1000], [1200, 900]];

/**
 * Gerade Schenkel einer gezeichneten Zeile. Von Hand gezeichnet liegen Punkte
 * auch mal 50 mm schief oder mitten auf der Strecke; beides wird glattgezogen.
 */
function schenkelVon(punkte) {
  const roh = [];
  for (let i = 0; i + 1 < punkte.length; i += 1) {
    const [a, b] = [punkte[i], punkte[i + 1]];
    const inX = Math.abs(b[0] - a[0]) >= Math.abs(b[1] - a[1]);
    const richtung = Math.sign(inX ? b[0] - a[0] : b[1] - a[1]);
    if (!richtung) continue;
    const letzter = roh[roh.length - 1];
    if (letzter && letzter.inX === inX && letzter.richtung === richtung) letzter.b = b;
    else roh.push({ a, b, inX, richtung });
  }
  return roh.map(({ a, b, inX, richtung }) => {
    const quer = inX ? (a[1] + b[1]) / 2 : (a[0] + b[0]) / 2;
    const pa = inX ? [a[0], quer] : [quer, a[1]];
    const pb = inX ? [b[0], quer] : [quer, b[1]];
    return { a: pa, b: pb, u: inX ? [richtung, 0] : [0, richtung],
             laenge: Math.abs(inX ? pb[0] - pa[0] : pb[1] - pa[1]) };
  });
}

const mitteVon = (s) => [(s.a[0] + s.b[0]) / 2, (s.a[1] + s.b[1]) / 2];
const laengsterZuerst = (schenkel) => [...schenkel].sort((p, q) => q.laenge - p.laenge);

/** Abstand vom Punkt bis zum Bereichsrand, in Richtung n. */
function randAbstand(poly, p, n) {
  let d = 0;
  while (d < 30000 && punktImPolygon(p[0] + n[0] * (d + SCHRITT_MM), p[1] + n[1] * (d + SCHRITT_MM), poly)) {
    d += SCHRITT_MM;
  }
  return d;
}

function zeilenImBereich(ctx) {
  const drin = (p) => punktImPolygon(p[0], p[1], ctx.poly) || ctx.poly.some((a, i) =>
    abstandZurStrecke(p[0], p[1], a, ctx.poly[(i + 1) % ctx.poly.length]) <= 150);
  return ctx.vorhanden
    .filter((r) => r.symbol === "kuechenzeile" && r.points_mm?.length >= 2)
    .map((r) => schenkelVon(r.points_mm))
    .filter((schenkel) => schenkel.length && drin(mitteVon(laengsterZuerst(schenkel)[0])))
    .sort((p, q) => q.reduce((n, s) => n + s.laenge, 0) - p.reduce((n, s) => n + s.laenge, 0));
}

/**
 * Wo die Zeile ihre Front hat. Bei L und U zur Innenseite der Kurve, bei einer
 * geraden Zeile weg von der naechsten Wand.
 */
function frontVon(ctx, schenkel, i) {
  const s = schenkel[i];
  const normalen = [[-s.u[1] || 0, s.u[0] || 0], [s.u[1] || 0, -s.u[0] || 0]];
  const nachbar = schenkel[i + 1] || schenkel[i - 1];
  if (nachbar) {
    const weg = schenkel[i + 1] ? nachbar.u : [-nachbar.u[0], -nachbar.u[1]];
    return normalen.find((n) => n[0] * weg[0] + n[1] * weg[1] > 0);
  }
  const mitte = mitteVon(s);
  const [erste, zweite] = normalen.map((n) => randAbstand(ctx.poly, mitte, n));
  return erste <= zweite ? normalen[1] : normalen[0];
}

/**
 * Die Schenkel als Kanten, wie sie setze() versteht: Hinterkante der Zeile,
 * Front nach vorn, ohne die Ecken der Kurve. Reicht der Bereich nicht bis
 * dorthin (Zeile dicht an der Raumkante gezeichnet), rueckt die Hinterkante
 * an den Rand.
 */
function zeilenKanten(ctx, schenkel) {
  return schenkel.map((s, i) => {
    const n = frontVon(ctx, schenkel, i);
    const hinten = Math.min(ZEILE_HALB_MM, randAbstand(ctx.poly, mitteVon(s), [-n[0], -n[1]]));
    const vor = i > 0 ? ZEILE_HALB_MM : 0;
    const nach = i < schenkel.length - 1 ? ZEILE_HALB_MM : 0;
    const a = [s.a[0] + s.u[0] * vor - n[0] * hinten, s.a[1] + s.u[1] * vor - n[1] * hinten];
    const laenge = s.laenge - vor - nach;
    return { a, b: [a[0] + s.u[0] * laenge, a[1] + s.u[1] * laenge], u: s.u, n, laenge, schenkel: s,
             ende: [s.b[0] - n[0] * hinten, s.b[1] - n[1] * hinten],
             anfang: [s.a[0] - n[0] * hinten, s.a[1] - n[1] * hinten] };
  });
}

/** Platz i (0 = direkt an der Zeile) hinter einem freien Zeilenende. */
function platzAmEnde(ende, i) {
  const a = [ende.von[0] + ende.raus[0] * 600 * i, ende.von[1] + ende.raus[1] * 600 * i];
  return { a, b: [a[0] + ende.raus[0] * 600, a[1] + ende.raus[1] * 600], u: ende.raus, n: ende.n, laenge: 600 };
}

function hoheGeraete(ctx, kanten) {
  const erste = kanten[0];
  const letzte = kanten[kanten.length - 1];
  const enden = [
    { von: letzte.ende, raus: letzte.u, n: letzte.n },
    { von: erste.anfang, raus: [-erste.u[0], -erste.u[1]], n: erste.n },
  ];
  // Hochschrank an die Zeile, der Kuehlschrank ganz aussen.
  const reihe = ["hochschrank_herd", "kuehlschrank"].filter((key) => !steht(ctx, key));
  const passt = (ende) => reihe.every((key, i) => frei(ctx, key, anKante(key, platzAmEnde(ende, i), 300, 0).rechteck));
  const ziel = enden.find(passt);
  if (ziel) {
    reihe.forEach((key, i) => setze(ctx, key, [platzAmEnde(ziel, i)], 300, 0));
    return;
  }
  // Steht am Ende eine Wand (Zeile von Wand zu Wand), bleibt nur eine freie Wand:
  // die naechste, nicht irgendeine quer durch den Raum, und beide Geraete beisammen.
  const waende = ctx.kanten.filter((k) => k.anWand);
  let nah = mitteVon(kanten[0]);
  const entfernung = (k) => abstandZurStrecke(nah[0], nah[1], k.a, k.b);
  const lauf = (k) => (nah[0] - k.a[0]) * k.u[0] + (nah[1] - k.a[1]) * k.u[1];
  for (const key of reihe) {
    const stehtDa = setze(ctx, key, enden.map((ende) => platzAmEnde(ende, 0)), 300, 0)
      || setze(ctx, key, [...waende].sort((p, q) => entfernung(p) - entfernung(q)), lauf, 0);
    if (!stehtDa) { weg(ctx, getSymbol(key)?.label || key); continue; }
    const r = stehtDa.rechteck;
    nah = [(r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2];
  }
}

/** Kleinster Abstand zweier Rechtecke; 0, wenn sie sich beruehren. */
function lueckeZwischen(a, b) {
  return Math.max(a.x0 - b.x1, b.x0 - a.x1, a.y0 - b.y1, b.y0 - a.y1, 0);
}

function kuecheninsel(ctx, kanten) {
  const sperren = ctx.belegt.filter((r) => r.key === "kuechenzeile" || HOCH.has(r.key) || HOCH.has(r.symbol));
  const waende = ctx.kanten.filter((k) => k.anWand).map((k) => rechteckAusPunkten([k.a, k.b]));
  const passt = (r, gang) => frei(ctx, "kuecheninsel", r)
    && sperren.every((z) => lueckeZwischen(r, z) >= gang - TOLERANZ_MM)
    && waende.every((w) => lueckeZwischen(r, w) >= INSEL_WAND_MM - TOLERANZ_MM);
  const reihenfolge = [...kanten].sort((p, q) => q.schenkel.laenge - p.schenkel.laenge);
  for (const gang of INSEL_GAENGE_MM) {
    for (const [lang, tief] of INSEL_MASSE) {
      // Parallel zur Zeile zuerst, quer nur, wenn das nicht geht.
      for (const [entlang, davor] of [[lang, tief], [tief, lang]]) {
        for (const { schenkel, n, u } of reihenfolge) {
          const mitte = mitteVon(schenkel);
          const halb = [Math.abs(u[0]) * entlang / 2 + Math.abs(n[0]) * davor / 2,
                        Math.abs(u[1]) * entlang / 2 + Math.abs(n[1]) * davor / 2];
          const versatz = [0];
          for (let d = INSEL_SUCHE_MM; d <= schenkel.laenge; d += INSEL_SUCHE_MM) versatz.push(d, -d);
          for (let weiter = 0; weiter <= 1500; weiter += INSEL_SUCHE_MM) {
            const vor = ZEILE_HALB_MM + gang + weiter + davor / 2;
            for (const d of versatz) {
              const x = mitte[0] + u[0] * d + n[0] * vor;
              const y = mitte[1] + u[1] * d + n[1] * vor;
              const r = { x0: x - halb[0], y0: y - halb[1], x1: x + halb[0], y1: y + halb[1] };
              if (!passt(r, gang)) continue;
              ctx.belegt.push({ ...r, key: "kuecheninsel" });
              ctx.gesetzt.push({
                symbol: "kuecheninsel",
                points_mm: [[Math.round(r.x0), Math.round(r.y0)], [Math.round(r.x1), Math.round(r.y1)]],
                rotation_deg: 0, mirrored: false,
              });
              return;
            }
          }
        }
      }
    }
  }
  weg(ctx, "Kücheninsel (zu wenig Platz)");
}

/** Steht dieses Moebel schon im Bereich? Dann nicht doppelt setzen. */
function steht(ctx, key) {
  return ctx.vorhanden.some((r) => r.symbol === key
    && punktImPolygon((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, ctx.poly));
}

/**
 * Der Raum, in dem der Bereich liegt -- wenn dort eine Zeile steht. Rainer zieht
 * den Bereich oft nur neben die Zeile (2026-10-30: "Kitchen einrichtung delivers
 * nothing any more"); die Zeile gehoert trotzdem dazu.
 */
function raumMitZeile(ctx) {
  const mitte = [0, 1].map((i) => ctx.poly.reduce((n, p) => n + p[i], 0) / ctx.poly.length);
  return (ctx.eingabe.raumPolygone || []).find((poly) => poly.length >= 3
    && punktImPolygon(mitte[0], mitte[1], poly)
    && zeilenImBereich({ poly, vorhanden: ctx.vorhanden }).length);
}

function freieAbschnitte(ctx, kante, tiefe, sperren = []) {
  const p = (lauf, tief) => [kante.a[0] + kante.u[0] * lauf + kante.n[0] * tief,
                             kante.a[1] + kante.u[1] * lauf + kante.n[1] * tief];
  const abschnitte = [];
  let start = null;
  for (let t = 0; t < kante.laenge - 1; t += SCHRITT_MM) {
    const ende = Math.min(t + SCHRITT_MM, kante.laenge);
    const stueck = rechteckAusPunkten([p(t, 0), p(ende, tiefe)]);
    const ok = rechteckImPolygon(stueck, ctx.poly)
      && !ctx.tuerZonen.some((z) => ueberlappen(z, stueck))
      && !sperren.some((z) => ueberlappen(z, stueck))
      && !ctx.belegt.some((r) => ueberlappen(r, stueck));
    if (ok && start === null) start = t;
    if (!ok && start !== null) { abschnitte.push([start, t]); start = null; }
    if (ok && ende >= kante.laenge - 1) { abschnitte.push([start, kante.laenge]); start = null; }
  }
  return abschnitte;
}

const PLATTE_MIN_MM = 1800;
const HOHE_GERAETE_MM = 1200;
const GEDACHTE_ZEILE_MAX_MM = 4000;

/**
 * Wo die Zeile staende, wenn Rainer noch keine gezeichnet hat. Sie wird NICHT
 * gesetzt, an ihr richten sich nur die Geraete aus. Rainer, 2026-10-30: "i want
 * to have kochfeld spuele hochschrank herd refridgerator and the kuecheninsel
 * please dont do the kuechenzeile".
 */
function gedachteZeile(ctx) {
  const laengster = (sperren) => {
    let best = null;
    for (const kante of ctx.kanten) {
      for (const [a, b] of freieAbschnitte(ctx, kante, ZEILE_HALB_MM * 2, sperren)) {
        const wert = (kante.anWand ? 1e6 : 0) + (b - a);
        if (!best || wert > best.wert) best = { kante, a, b, wert };
      }
    }
    return best;
  };
  // Eine Wand ohne Fenster zuerst: dort haben auch die hohen Geraete Platz.
  const ohneFenster = laengster(ctx.fensterZonen);
  const best = ohneFenster && ohneFenster.b - ohneFenster.a >= PLATTE_MIN_MM + HOHE_GERAETE_MM
    ? ohneFenster : laengster([]);
  if (!best || best.b - best.a < HOHE_GERAETE_MM) return null;
  const { kante, a, b } = best;
  const platz = b - a >= PLATTE_MIN_MM + HOHE_GERAETE_MM ? b - a - HOHE_GERAETE_MM : b - a;
  const p = (lauf) => [kante.a[0] + kante.u[0] * lauf + kante.n[0] * ZEILE_HALB_MM,
                       kante.a[1] + kante.u[1] * lauf + kante.n[1] * ZEILE_HALB_MM];
  return [p(a), p(a + Math.min(platz, GEDACHTE_ZEILE_MAX_MM))];
}

function kueche(ctx) {
  if (!zeilenImBereich(ctx).length) {
    const raum = raumMitZeile(ctx);
    if (raum) Object.assign(ctx, erzeugeKontext({ ...ctx.eingabe, polygon: raum }));
  }
  let zeile = zeilenImBereich(ctx)[0];
  if (!zeile) {
    const punkte = gedachteZeile(ctx);
    if (!punkte) { weg(ctx, "Küche (kein freier Wandplatz)"); return; }
    const gedacht = { ...rechteckVon({ symbol: "kuechenzeile", points_mm: punkte }), symbol: "kuechenzeile", points_mm: punkte };
    ctx.belegt.push(...belegtVon(gedacht));
    zeile = schenkelVon(punkte);
  }
  const kanten = zeilenKanten(ctx, zeile);
  const plattenKanten = [...kanten].filter((k) => k.laenge >= 600).sort((p, q) => q.laenge - p.laenge);
  // Mit Abstand, wenn er da ist; auf kurzer Platte an die beiden Enden.
  const spuele = (k) => (k.laenge >= PLATTE_MIN_MM ? k.laenge * 0.3 : 300);
  const kochfeld = (k) => (k.laenge >= PLATTE_MIN_MM ? k.laenge * 0.75 : k.laenge - 300);
  if (!steht(ctx, "spuele") && !setze(ctx, "spuele", plattenKanten, spuele, 0)) weg(ctx, "Spüle");
  if (!steht(ctx, "kochfeld") && !setze(ctx, "kochfeld", plattenKanten, kochfeld, 0)) weg(ctx, "Kochfeld");
  hoheGeraete(ctx, kanten);
  if (!steht(ctx, "kuecheninsel")) kuecheninsel(ctx, kanten);
}

function buero(ctx) {
  // Schreibtisch an die Fensterwand (Licht von vorn), Stuhl davor mit dem
  // Gesicht zum Tisch, ein Sideboard (oder schmaler Schrank) an eine andere Wand.
  const tisch = setze(ctx, "schreibtisch", fensterZuerst(ctx), "mitte")
    || setze(ctx, "schreibtisch_kind", fensterZuerst(ctx), "mitte");
  if (!tisch) weg(ctx, "Schreibtisch");
  if (tisch) {
    const { kante, t } = tisch;
    const { d } = masse(tisch.moebel.symbol);
    const stuhl = masse("schreibtischstuhl");
    const gap = wallBehaviour(tisch.moebel.symbol).gap_mm || 0;
    // Der Stuhl schiebt sich ein Stueck unter die Platte.
    const vor = gap + d + stuhl.d / 2 - 150;
    const mitte = [kante.a[0] + kante.u[0] * t + kante.n[0] * vor,
                   kante.a[1] + kante.u[1] * t + kante.n[1] * vor];
    const zumTisch = (tisch.moebel.rotation_deg + 180) % 360;
    const gesetzt = setzeFrei(ctx, "schreibtischstuhl", mitte, zumTisch);
    if (!gesetzt) weg(ctx, "Schreibtischstuhl");
  }
  if (!setze(ctx, "sideboard", ruhigsteZuerst(ctx), "mitte")
      && !setze(ctx, "schrank_40", ruhigsteZuerst(ctx), "ecke")) weg(ctx, "Sideboard/Schrank");
  // Rainer, 2026-10-16: "if an office is above 10m2 then please add a
  // 2-seater couch". An eine ruhige Wand; passt es nicht, wird es gemeldet.
  if (polygonFlaecheM2(ctx.poly) > BUERO_SOFA_AB_M2
      && !setze(ctx, "sofa_2sitzer", ruhigsteZuerst(ctx), "mitte")) weg(ctx, "2-Sitzer");
}

const BUERO_SOFA_AB_M2 = 10;

function polygonFlaecheM2(poly) {
  let summe = 0;
  for (let i = 0; i < poly.length; i += 1) {
    const [x0, y0] = poly[i];
    const [x1, y1] = poly[(i + 1) % poly.length];
    summe += x0 * y1 - x1 * y0;
  }
  return Math.abs(summe) / 2 / 1e6;
}

const REGELN = {
  wohnzimmer, esszimmer, kueche, diele, hwr, kinderzimmer,
  gast: schlafzimmer, buero, schlafzimmer, duschbad, wc, bad,
};

/**
 * @param bereich { polygon: [x,y][], oeffnungen?: {a,b,typ}[],
 *                  vorhandene?: {x0,y0,x1,y1,symbol?,points_mm?}[] }
 * @param raumtyp "schlafzimmer" | "bad" | "wohnzimmer"
 * @returns { moebel: PlacedSymbol-artig ohne id, weggelassen: string[] }
 */
export function richteBereichEin(bereich, raumtyp) {
  const regel = REGELN[raumtyp];
  if (!regel) return { moebel: [], weggelassen: [`Raumtyp ${raumtyp} gibt es noch nicht`] };
  if (!bereich?.polygon || bereich.polygon.length < 3) return { moebel: [], weggelassen: ["Bereich fehlt"] };
  const ctx = erzeugeKontext(bereich);
  regel(ctx);
  return { moebel: ctx.gesetzt, weggelassen: ctx.weggelassen };
}

/** Weltrechteck eines gesetzten Moebels -- fuer Tests und Hindernisse. */
export function rechteckVon(moebel) {
  if (moebel.points_mm) {
    const r = rechteckAusPunkten(moebel.points_mm);
    // Ein Lauf (Kuechenzeile) ist eine Mittellinie mit Tiefe.
    const symbol = getSymbol(moebel.symbol);
    const tief = symbol?.placement === "path" ? (symbol.depth_mm || 600) / 2 : 0;
    // Gerader Lauf: nur quer zur Laufrichtung dicker, nicht an den Enden.
    const tx = r.x1 - r.x0 < 1 || r.y1 - r.y0 >= 1 ? tief : 0;
    const ty = r.y1 - r.y0 < 1 || r.x1 - r.x0 >= 1 ? tief : 0;
    return { x0: r.x0 - tx, y0: r.y0 - ty, x1: r.x1 + tx, y1: r.y1 + ty };
  }
  const { width_mm: w, depth_mm: d } = moebel.footprint_mm || masse(moebel.symbol);
  const quer = (moebel.rotation_deg || 0) % 180 === 0;
  const hx = (quer ? w : d) / 2;
  const hy = (quer ? d : w) / 2;
  const [x, y] = moebel.position_mm;
  return { x0: x - hx, y0: y - hy, x1: x + hx, y1: y + hy };
}

const KUECHEN_TEILE = ["spuele", "kochfeld", "hochschrank_herd", "kuehlschrank", "kuecheninsel"];
const KOMBI_FERTIG = {
  kueche: (hat) => KUECHEN_TEILE.every(hat),
  esszimmer: (hat) => ["essgruppe_6", "esstisch"].some(hat),
};

const TISCH_GANG_MM = 900;

/**
 * Was ein Kombiraum bekommt. Rainer, 2026-11-01: "do anything with kochen like
 * wohnen essen koschen or essen kochen add all of our kichten stuff" und "the
 * same with essen jsut add the table". Erst die Kueche, der Tisch nimmt, was
 * frei bleibt.
 */
function kombiTeile(name) {
  return [[KOCHEN, "kueche"], [/ess(en|zimmer)/i, "esszimmer"]]
    .filter(([re]) => re.test(name)).map(([, typ]) => typ);
}

/**
 * Alle Raeume eines Geschosses nach ihrem Namen einrichten
 * (moebel-alles-einrichten-v1). Rainer, 2026-10-23: "the room names are
 * there why not just populate automatically?"
 *
 * Jeder Raum mit eindeutigem Typ (raumtypAusName) wird wie mit "Bereich
 * einrichten" eingerichtet -- der Bereich ist der ganze Raum. Ein Kombiraum
 * bekommt die Teile aus kombiTeile. Ausgelassen und mit Grund gemeldet:
 * Raeume ohne Typ, Raeume, in denen schon Moebel stehen, und Nicht-Raeume
 * (Luftraum, Treppenoeffnung, Terrasse, Balkon, Treppe). Was in einem Raum
 * gesetzt wird, gilt fuer die folgenden als vorhanden.
 *
 * @param raeume [{id, name, kind, polygon_mm|polygon}]
 * @returns { moebel, eingerichtet: string[], uebersprungen: {name, grund}[], weggelassen: string[] }
 */
export function richteAlleRaeumeEin({ raeume = [], oeffnungen = [], vorhandene = [], raumKanten = [],
                                      hindernisse = [] } = {}) {
  const moebel = [];
  const eingerichtet = [];
  const uebersprungen = [];
  const weggelassen = [];
  // Hindernisse (die Treppe) belegen Platz, zaehlen aber nicht als "schon
  // eingerichtet" -- sonst bliebe jede Diele mit Treppe leer.
  const belegt = [...vorhandene, ...hindernisse];
  for (const raum of raeume) {
    const name = raum.name || raum.label || "Raum";
    const poly = raum.polygon_mm || raum.polygon || [];
    if (poly.length < 3) continue;
    if (["luftraum", "treppenoeffnung"].includes(raum.kind)
        || /luftraum|treppe|terrasse|balkon|loggia/i.test(name)) {
      uebersprungen.push({ name, grund: "kein Wohnraum" });
      continue;
    }
    const typ = raumtypAusName(name);
    const kombi = typ ? [] : kombiTeile(name);
    if (!typ && !kombi.length) {
      uebersprungen.push({ name, grund: "kein eindeutiger Raumtyp -- mit „Bereich einrichten“ von Hand" });
      continue;
    }
    const drin = (r) => punktImPolygon((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2, poly);
    const hat = (key) => vorhandene.some((r) => r.symbol === key && drin(r));
    // Die Kuechenzeile zeichnet Rainer selbst: sie allein heisst nicht "eingerichtet".
    const schonDa = typ && vorhandene.some((r) => drin(r) && !(typ === "kueche" && r.symbol === "kuechenzeile"));
    const offen = typ ? [typ] : kombi.filter((teil) => !KOMBI_FERTIG[teil](hat));
    if (schonDa || !offen.length) {
      uebersprungen.push({ name, grund: "schon eingerichtet" });
      continue;
    }
    let gesetzt = 0;
    for (const teil of offen) {
      const bereich = { polygon: poly, oeffnungen, vorhandene: belegt, raumKanten };
      // Der Tisch haelt einen Gang zur Kueche; geht das nicht, steht er dichter.
      const gang = kombi.length && teil === "esszimmer"
        ? belegt.filter((r) => drin(r) && [...KUECHEN_TEILE, "kuechenzeile"].includes(r.symbol))
          .map((r) => ({ x0: r.x0 - TISCH_GANG_MM, y0: r.y0 - TISCH_GANG_MM,
                         x1: r.x1 + TISCH_GANG_MM, y1: r.y1 + TISCH_GANG_MM }))
        : [];
      const mitGang = gang.length ? richteBereichEin({ ...bereich, vorhandene: [...belegt, ...gang] }, teil) : null;
      const ergebnis = mitGang?.moebel.length ? mitGang : richteBereichEin(bereich, teil);
      gesetzt += ergebnis.moebel.length;
      moebel.push(...ergebnis.moebel);
      belegt.push(...ergebnis.moebel.map((m) => ({ ...rechteckVon(m), symbol: m.symbol })));
      weggelassen.push(...ergebnis.weggelassen.map((w) => `${name}: ${w}`));
    }
    if (gesetzt) eingerichtet.push(name);
    else uebersprungen.push({ name, grund: "nichts untergebracht" });
  }
  return { moebel, eingerichtet, uebersprungen, weggelassen };
}

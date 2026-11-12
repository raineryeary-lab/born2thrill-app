/**
 * Moebel ausserhalb jedes Raums finden -- die, die man nicht anklicken kann.
 *
 * Rainer, 2026-08-28: "the one you are reffering to i cant see and not
 * delete". In onehalfstorey_020 lag ein `stuff`-Rechteck bei y 11400..12050,
 * waehrend der Grundriss bei rund 11000 endet: unterhalb der Zeichenflaeche.
 * Der Bau brach daran ab (R6_furniture_inside: "stuff steht bei 7900,364
 * ausserhalb jedes Raums"), und im Editor gab es keinen Weg, es loszuwerden.
 *
 * Die Zahlen unten sind die echten aus jenem Haus.
 *
 * Dieselbe Logik wie in furniture.tsx. Bewusst hier wiederholt: die Datei ist
 * eine React-Komponente, und ein Test dafuer braeuchte ein DOM. Geprueft wird
 * die Entscheidung, nicht die Darstellung.
 */
import { test } from "node:test";
import assert from "node:assert/strict";

const AUSSERHALB_TOLERANZ_MM = 300;

function punktInPolygon(x, y, poly) {
  let drin = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if ((yi > y) !== (yj > y)
        && x < ((xj - xi) * (y - yi)) / ((yj - yi) || 1e-9) + xi) drin = !drin;
  }
  return drin;
}

function abstandZumPolygon(x, y, poly) {
  let kuerzester = Infinity;
  for (let i = 0; i < poly.length; i += 1) {
    const [ax, ay] = poly[i];
    const [bx, by] = poly[(i + 1) % poly.length];
    const dx = bx - ax;
    const dy = by - ay;
    const laenge = dx * dx + dy * dy;
    const t = laenge === 0 ? 0 : Math.max(0, Math.min(1, ((x - ax) * dx + (y - ay) * dy) / laenge));
    kuerzester = Math.min(kuerzester, Math.hypot(x - (ax + t * dx), y - (ay + t * dy)));
  }
  return kuerzester;
}

function mitteVon(item) {
  if (item?.position_mm) return [item.position_mm[0], item.position_mm[1]];
  const punkte = item?.points_mm;
  if (!punkte?.length) return null;
  return [punkte.reduce((s, p) => s + p[0], 0) / punkte.length,
          punkte.reduce((s, p) => s + p[1], 0) / punkte.length];
}

function verlorene(symbols, rooms) {
  const polygone = (rooms || [])
    .map((raum) => raum.polygon || raum.polygon_mm)
    .filter((poly) => poly && poly.length >= 3);
  if (!polygone.length) return [];
  return (symbols || []).filter((item) => {
    const mitte = mitteVon(item);
    if (!mitte) return false;
    const [x, y] = mitte;
    return !polygone.some((poly) =>
      punktInPolygon(x, y, poly) || abstandZumPolygon(x, y, poly) <= AUSSERHALB_TOLERANZ_MM);
  });
}

/** Das Kinderzimmer im Obergeschoss von onehalfstorey_020. */
const KIND = { name: "Kind", polygon: [[7147, 1285], [10666, 1285],
                                       [10666, 5058], [7147, 5058]] };

test("das Rechteck unter dem Bildrand wird gefunden", () => {
  // Der echte Fall: 921 mm vor der Suedfassade, im Editor unerreichbar.
  const verirrt = { id: "1b7ce8", symbol: "stuff",
                    points_mm: [[7200, 39], [8600, 689]] };
  const gefunden = verlorene([verirrt], [KIND]);
  assert.equal(gefunden.length, 1);
  assert.equal(gefunden[0].id, "1b7ce8");
});

test("ein Moebel mitten im Raum gilt nicht als verloren", () => {
  const drin = { id: "a", symbol: "einzelbett", position_mm: [8500, 3000] };
  assert.equal(verlorene([drin], [KIND]).length, 0);
});

test("eine an die Wand geschobene Kommode gilt nicht als verloren", () => {
  // 300 mm Toleranz, dieselbe wie im Verifier: Wandstaerke plus Anschnitt.
  const anDerWand = { id: "b", symbol: "lowboard", position_mm: [8500, 1100] };
  assert.equal(verlorene([anDerWand], [KIND]).length, 0);
});

test("knapp jenseits der Toleranz gilt als verloren", () => {
  const knapp = { id: "c", symbol: "stuff", position_mm: [8500, 900] };
  assert.equal(verlorene([knapp], [KIND]).length, 1);
});

test("ohne Raumpolygone wird nichts als verloren gemeldet", () => {
  // Sonst stuende beim ersten Laden, bevor die Geometrie da ist, jedes
  // Moebelstueck in der roten Liste.
  const irgendwo = { id: "d", symbol: "stuff", position_mm: [1, 1] };
  assert.equal(verlorene([irgendwo], []).length, 0);
});

test("ein Symbol ohne Koordinaten wird uebergangen", () => {
  assert.equal(verlorene([{ id: "e", symbol: "stuff" }], [KIND]).length, 0);
});

test("die Mitte eines gezeichneten Laufs ist der Schwerpunkt seiner Punkte", () => {
  assert.deepEqual(mitteVon({ points_mm: [[0, 0], [100, 200]] }), [50, 100]);
});

test("position_mm hat Vorrang vor points_mm", () => {
  assert.deepEqual(mitteVon({ position_mm: [7, 9], points_mm: [[0, 0]] }), [7, 9]);
});

/**
 * Gegen WELCHE Raeume wird gemessen?
 *
 * Rainer, 2026-08-29: "can you fix anything while im away."
 *
 * Das Panel meldete fuer `german_catalog_review_bungalow_3_2_5_b_100_1`
 * "11 Möbel außerhalb der Räume" -- bei einem Haus, das gebaut, angenommen
 * und hochgeladen ist. Im Browser nachgemessen: alle 11 liegen INNERHALB
 * eines gezeichneten Raumpolygons.
 *
 * Die Ursache stand in zwei Zeilen derselben Datei:
 *
 *     Zeile  303   const floor = overrideFloor || document.floors[floorIndex]
 *     Zeile 1279   rooms={document.floors?.[floorIndex]?.rooms || []}
 *
 * Die Zeichenflaeche nimmt `overrideFloor` -- das Geschoss, das auch gerendert
 * wird, im Bauplan-Rahmen (x bis 15234). Das Panel nahm `document.floors[i]`,
 * das Korrekturdokument (x bis 10600). Zwei Rahmen, und alles rechts von
 * 10600 sah nach "ausserhalb" aus.
 *
 * Ein Waechter, der bei einem fertigen Haus elf Fehlalarme schlaegt, wird nach
 * dem zweiten Mal ueberblaettert -- genau das, was bei der Kasten-Warnung
 * vermieden werden sollte.
 */

test("dieselben Raeume wie die Zeichenflaeche, nicht ein anderes Geschoss", () => {
  // Genau die Konstellation: das gezeichnete Geschoss reicht bis x 15234,
  // das Korrekturdokument nur bis 10600.
  const gezeichnet = { rooms: [{ polygon: [[11000, 3000], [15000, 3000],
                                           [15000, 6000], [11000, 6000]] }] };
  const korrektur  = { rooms: [{ polygon: [[0, 0], [10600, 0],
                                           [10600, 9149], [0, 9149]] }] };
  const bett = { id: "a", symbol: "doppelbett", position_mm: [14150, 3950] };

  // So war es: gegen das Korrekturdokument gemessen -> Fehlalarm.
  assert.equal(verlorene([bett], korrektur.rooms).length, 1);
  // So ist es richtig: gegen das gezeichnete Geschoss.
  assert.equal(verlorene([bett], gezeichnet.rooms).length, 0);
});

test("welches Geschoss gilt: das ueberschriebene, sonst das aus dem Index", () => {
  // Dieselbe Wahl wie in Zeile 303, damit Panel und Zeichenflaeche nie wieder
  // auseinanderlaufen.
  const wahl = (overrideFloor, doc, i) => overrideFloor || doc.floors?.[i];
  const doc = { floors: [{ id: "korrektur" }] };
  assert.equal(wahl({ id: "render" }, doc, 0).id, "render");
  assert.equal(wahl(null, doc, 0).id, "korrektur");
  assert.equal(wahl(null, { floors: [] }, 0), undefined);
});

/**
 * Wo ist vorn? Ein Pfeil auf den Symbolen, bei denen man es nicht sieht.
 *
 * Rainer, 2026-08-28: "there are some symbols where it is hard to see where
 * the front is -- like kuehlschrank, hochschrank herd, waschbecken, wandwc.
 * could you add like an arrow on top, back to front?"
 *
 * Ein Kuehlschrank ist im Grundriss ein Rechteck von 600 x 600 mm. Ob seine
 * Tuer zum Raum oder zur Wand zeigt, steht nur in `rotation_deg` -- und das
 * sieht man dem Quadrat nicht an.
 *
 * Gemessen an den 62 platzierten Stuecken dieser Art in den zwoelf
 * Moebeldateien vom 2026-08-28: die Vorderseite zeigt 36-mal in den Raum und
 * 26-mal in die Wand. Es gibt also heute KEINE verlaessliche Ausrichtung, und
 * der Pfeil behauptet auch keine -- er zeigt, wie das Stueck steht, damit die
 * falsch stehenden auffallen und gedreht werden koennen.
 *
 * Die Konvention ist die aus `snapStampToWalls`: die Rueckseite liegt an der
 * Wand, also ist lokales +y die Vorderseite. Breite laeuft entlang x, Tiefe
 * entlang y, und `rotation_deg` dreht beides.
 */
import { test } from "node:test";
import assert from "node:assert/strict";

// Dieselbe Liste und Rechnung wie in furniture.tsx.
//
// Umgedreht am 2026-09-03. Vorher zaehlte die Liste die neun Stuecke auf, die
// einen Pfeil bekamen. Rainer: "mach doch die Pfeile bei allen Moebeln immer
// von der Wand weg ausser Esstisch und Couchtisch." Jetzt zaehlt sie die
// Ausnahmen. Ein Tisch steht frei und wird von allen Seiten benutzt; alles,
// was mit dem Ruecken an einer Wand steht, hat eine Vorderseite -- auch ein
// Kleiderschrank, der vorher keinen Pfeil hatte und dessen Drehung genauso
// falsch sein kann.
const OHNE_VORDERSEITE = new Set([
  "esstisch", "couchtisch", "essgruppe_6", "essgruppe_4", "essgruppe_8",
]);

function zeigtVorderseite(symbolKey) {
  return !OHNE_VORDERSEITE.has(symbolKey);
}

/**
 * Die Drehung, die snapStampToWalls aus der Wandnormalen bildet.
 *
 * `n` ist die Normale, die IN DEN RAUM zeigt. Gesucht ist die Drehung, nach
 * der die lokale Vorderseite +y auf n faellt.
 */
function drehungAusNormale(nx, ny) {
  return Math.round(((Math.atan2(-nx, ny) * 180) / Math.PI + 360) % 360);
}

/** Wohin die lokale +y-Richtung nach `deg` Grad zeigt. */
function vorderseiteNach(deg) {
  const r = (deg * Math.PI) / 180;
  return [-Math.sin(r), Math.cos(r)];
}

/**
 * Der Pfeil im LOKALEN Rahmen des Symbols: von der Rueckseite zur
 * Vorderseite, also entlang +y. Gedreht wird er vom `transform` des Symbols,
 * genau wie das Rechteck -- deshalb steht hier keine Winkelrechnung.
 */
function pfeilLokal(width, depth) {
  const laenge = Math.min(depth * 0.55, 420);
  const spitzeY = depth / 2;
  const fussY = spitzeY - laenge;
  const breite = Math.min(width * 0.30, 220);
  return {
    schaft: [[0, fussY], [0, spitzeY - breite * 0.8]],
    spitze: [[0, spitzeY], [-breite / 2, spitzeY - breite * 0.9], [breite / 2, spitzeY - breite * 0.9]],
  };
}

test("nur die Stuecke mit einer echten Vorderseite bekommen einen Pfeil", () => {
  for (const key of ["kuehlschrank", "hochschrank_herd", "wand_wc",
                     "handwaschbecken", "doppelwaschtisch", "waschtisch",
                     "spuele", "waschmaschine", "trockner"]) {
    assert.equal(zeigtVorderseite(key), true, key);
  }
});

test("ein Tisch bekommt keinen Pfeil", () => {
  // Ein Esstisch und ein Couchtisch stehen frei und werden von allen Seiten
  // benutzt. Ein Pfeil darauf waere eine Behauptung.
  for (const key of ["esstisch", "couchtisch", "essgruppe_6"]) {
    assert.equal(zeigtVorderseite(key), false, key);
  }
});

test("alles was an einer Wand steht bekommt einen -- auch die Schraenke", () => {
  // Diese sechs hatten vor dem 2026-09-03 keinen Pfeil, obwohl ihre Drehung
  // genauso falsch sein kann wie die eines Kuehlschranks.
  for (const key of ["kleiderschrank", "garderobe", "lowboard",
                     "badewanne", "dusche_gross", "essgruppe_stuhl"]) {
    assert.equal(zeigtVorderseite(key), true, key);
  }
});

test("die Drehung kommt aus der Normalen, nicht aus der Wandrichtung", () => {
  // Der eigentliche Fehler: snapStampToWalls bestimmte das Vorzeichen der
  // Normalen richtig, gab dann aber die Wandrichtung als Drehung zurueck.
  // Zwei Raeume links und rechts derselben Wand bekamen dieselbe Drehung.
  // Gemessen am 2026-08-28: von 62 Stuecken zeigten 26 in die Wand.
  //
  // Fuer jede der vier Achsenrichtungen muss die gedrehte Vorderseite auf die
  // Normale fallen.
  for (const [nx, ny] of [[0, 1], [0, -1], [1, 0], [-1, 0]]) {
    const [fx, fy] = vorderseiteNach(drehungAusNormale(nx, ny));
    assert.ok(Math.abs(fx - nx) < 1e-9 && Math.abs(fy - ny) < 1e-9,
      `Normale ${nx},${ny} ergab Vorderseite ${fx.toFixed(3)},${fy.toFixed(3)}`);
  }
});

test("dieselbe Wand von beiden Seiten ergibt entgegengesetzte Drehungen", () => {
  // Eine waagerechte Wand: der Raum liegt einmal darueber, einmal darunter.
  const oben = drehungAusNormale(0, 1);
  const unten = drehungAusNormale(0, -1);
  assert.equal(Math.abs(oben - unten), 180,
    `oben ${oben}, unten ${unten} -- das war der Fehler: beide gleich`);
});

test("die Spitze sitzt auf der Vorderkante", () => {
  // 600 mm tief: die Vorderkante liegt bei +300.
  const { spitze } = pfeilLokal(600, 600);
  assert.equal(spitze[0][1], 300);
});

test("der Schaft beginnt hinten und zeigt nach vorn", () => {
  const { schaft } = pfeilLokal(600, 600);
  assert.ok(schaft[0][1] < schaft[1][1], "der Schaft muss nach +y laufen");
});

test("bei einem flachen Stueck wird der Pfeil nicht laenger als das Stueck", () => {
  // Ein Handwaschbecken ist 350 mm tief; ein 420er Pfeil ragte hinten heraus.
  const { schaft, spitze } = pfeilLokal(400, 350);
  assert.ok(schaft[0][1] >= -175, `Fuss bei ${schaft[0][1]} liegt hinter der Rueckkante`);
  assert.equal(spitze[0][1], 175);
});

test("bei einem schmalen Stueck wird die Spitze nicht breiter als das Stueck", () => {
  // Ein Badheizkoerper ist 100 mm tief und 550 breit -- die Spitze darf nicht
  // ueber die Seitenkanten stehen.
  const { spitze } = pfeilLokal(300, 600);
  const halbeBreite = Math.max(...spitze.map((p) => Math.abs(p[0])));
  assert.ok(halbeBreite <= 150, `Spitze ${halbeBreite} ragt ueber die halbe Breite 150`);
});

test("ein tiefes Stueck bekommt keinen endlos langen Pfeil", () => {
  // Sonst zoege eine 1500 mm tiefe Eckbadewanne einen Pfeil quer durchs Bad.
  const { schaft, spitze } = pfeilLokal(1500, 1500);
  assert.equal(spitze[0][1] - schaft[0][1], 420);
});

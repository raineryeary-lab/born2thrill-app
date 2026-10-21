/**
 * Einzelne Punkte an Kuechenzeile und Vorwandinstallation -- die Rechnung dahinter.
 *
 * Rainer, 2026-08-28: "can we also edit the Kuechenzeile and
 * vorwandinstallation, make the points selectable and moveable? its almost
 * impossible to get them right on the first try -- you know, select point,
 * align and nudge?"
 *
 * Bis hierher hatten nur Rechtecke (Kuecheninsel, Abstellschrank) Griffe an
 * den Ecken. Ein gezeichneter Lauf liess sich nur als Ganzes verschieben --
 * ein einzelner Knick war nicht zu erreichen, und ein Lauf, der nicht beim
 * ersten Zeichnen sass, musste neu gezeichnet werden.
 *
 * Gerechnet wird in Millimetern, wie ueberall im Moebel-Editor. Die
 * Zahlen unten sind die echte Kuechenzeile aus
 * `german_catalog_review_bungalow_3_2_5_b_100_1`.
 *
 * Dieselbe Logik wie in furniture.tsx. Bewusst hier wiederholt: die Datei ist
 * eine React-Komponente, und ein Test dafuer braeuchte ein DOM. Geprueft wird
 * die Entscheidung, nicht die Darstellung.
 */
import { test } from "node:test";
import assert from "node:assert/strict";

const GRIFF_RADIUS_MM = 260;
const SCHRITT_MM = 10;
const SCHRITT_FEIN_MM = 1;
const SCHRITT_GROB_MM = 100;

function schrittWeiteMm(event) {
  if (event.shiftKey) return SCHRITT_GROB_MM;
  if (event.altKey) return SCHRITT_FEIN_MM;
  return SCHRITT_MM;
}

function medianVon(werte) {
  if (!werte.length) return 0;
  const sortiert = [...werte].sort((a, b) => a - b);
  const mitte = Math.floor(sortiert.length / 2);
  return sortiert.length % 2
    ? sortiert[mitte]
    : (sortiert[mitte - 1] + sortiert[mitte]) / 2;
}

/** Welcher Punkt liegt unter dem Zeiger? Der naechste innerhalb des Radius. */
function punktUnterZeiger(punkte, ziel, radius = GRIFF_RADIUS_MM) {
  let beste = null;
  punkte.forEach(([x, y], index) => {
    const abstand = Math.hypot(x - ziel[0], y - ziel[1]);
    if (abstand <= radius && (!beste || abstand < beste.abstand)) {
      beste = { index, abstand };
    }
  });
  return beste ? beste.index : null;
}

/** Die gewaehlten Punkte um dx/dy verschieben. */
function schiebePunkte(punkte, indices, dx, dy) {
  const gewaehlt = new Set(indices);
  return punkte.map(([x, y], index) =>
    gewaehlt.has(index) ? [Math.round(x + dx), Math.round(y + dy)] : [x, y]);
}

/** Die gewaehlten Punkte auf eine Linie bringen. achse 0 = x, 1 = y. */
function richtePunkteAus(punkte, indices, achse) {
  if (indices.length < 2) return punkte;
  const ziel = Math.round(medianVon(indices.map((i) => punkte[i][achse])));
  const gewaehlt = new Set(indices);
  return punkte.map((punkt, index) => {
    if (!gewaehlt.has(index)) return punkt;
    const neu = [...punkt];
    neu[achse] = ziel;
    return neu;
  });
}

/** Die Kuechenzeile: an der Wand entlang, mit einem Knick, der 40 mm daneben liegt. */
function kuechenzeile() {
  return [[1200, 800], [4300, 840], [4300, 3100]];
}

test("ein Klick auf den Knick findet genau diesen Punkt", () => {
  assert.equal(punktUnterZeiger(kuechenzeile(), [4320, 860]), 1);
});

test("ein Klick daneben findet nichts", () => {
  // Sonst faengt jeder Klick auf den Lauf einen Punkt und man kann ihn nicht
  // mehr als Ganzes verschieben.
  assert.equal(punktUnterZeiger(kuechenzeile(), [2800, 820]), null);
});

test("liegen zwei Punkte dicht beieinander, gewinnt der naehere", () => {
  const eng = [[1000, 1000], [1200, 1000]];
  assert.equal(punktUnterZeiger(eng, [1180, 1000]), 1);
  assert.equal(punktUnterZeiger(eng, [1020, 1000]), 0);
});

test("ein Punkt laesst sich einzeln schieben", () => {
  const neu = schiebePunkte(kuechenzeile(), [1], 0, -SCHRITT_MM);
  assert.deepEqual(neu[1], [4300, 830]);
  assert.deepEqual(neu[0], [1200, 800]);   // nicht gewaehlt, bleibt
  assert.deepEqual(neu[2], [4300, 3100]);
});

test("mehrere gewaehlte Punkte wandern gemeinsam", () => {
  const neu = schiebePunkte(kuechenzeile(), [0, 1], SCHRITT_MM, 0);
  assert.deepEqual(neu[0], [1210, 800]);
  assert.deepEqual(neu[1], [4310, 840]);
  assert.deepEqual(neu[2], [4300, 3100]);
});

test("Shift schiebt grob, Alt fein", () => {
  assert.equal(schrittWeiteMm({ shiftKey: true }), 100);
  assert.equal(schrittWeiteMm({ altKey: true }), 1);
  assert.equal(schrittWeiteMm({}), 10);
});

test("waagerecht ausrichten zieht die y-Werte auf den Median", () => {
  // Der echte Fall: die Zeile sitzt an der Wand, der Knick liegt 40 mm daneben.
  const neu = richtePunkteAus(kuechenzeile(), [0, 1], 1);
  assert.equal(neu[0][1], 820);
  assert.equal(neu[1][1], 820);
  assert.equal(neu[2][1], 3100);           // nicht gewaehlt
});

test("senkrecht ausrichten laesst y in Ruhe", () => {
  const neu = richtePunkteAus(kuechenzeile(), [1, 2], 0);
  assert.deepEqual(neu.map((p) => p[0]), [1200, 4300, 4300]);
  assert.deepEqual(neu.map((p) => p[1]), [800, 840, 3100]);
});

test("der Median gewinnt, nicht der Mittelwert", () => {
  // Drei Punkte auf 800, einer auf 1600. Ein Mittelwert zoege alle vier auf
  // 1000 -- also die drei, die stimmten, mit daneben.
  const lauf = [[0, 800], [1000, 800], [2000, 800], [3000, 1600]];
  const neu = richtePunkteAus(lauf, [0, 1, 2, 3], 1);
  assert.deepEqual(neu.map((p) => p[1]), [800, 800, 800, 800]);
});

test("ein einzelner Punkt laesst sich nicht ausrichten", () => {
  const lauf = kuechenzeile();
  assert.deepEqual(richtePunkteAus(lauf, [1], 1), lauf);
});

test("Millimeter bleiben ganze Zahlen", () => {
  // Die Datei speichert gerundet; ein Punkt mit Nachkommastellen waere ein
  // Unterschied, den niemand gezeichnet hat.
  const neu = schiebePunkte([[100.4, 200.6]], [0], 0.3, 0.3);
  assert.deepEqual(neu[0], [101, 201]);
});

/**
 * Der Rueckweg -- dasselbe Argument wie im Zeichner.
 *
 * Rainer, 2026-08-28: "if i align them accidentally waagrecht instead of
 * senkrecht then its over."
 */

/** Ein Abzug der Symbolliste, wie er vor jeder Aenderung weggelegt wird. */
function abzug(symbols) {
  return symbols.map((item) => ({
    ...item,
    points_mm: item.points_mm ? item.points_mm.map(([x, y]) => [x, y]) : undefined,
  }));
}

test("ein falsches Ausrichten laesst sich zuruecknehmen", () => {
  const symbols = [{ id: "a", symbol: "kuechenzeile", points_mm: kuechenzeile() }];
  const gemerkt = abzug(symbols);
  symbols[0].points_mm = richtePunkteAus(symbols[0].points_mm, [0, 1], 1);
  assert.equal(symbols[0].points_mm[1][1], 820);
  assert.deepEqual(gemerkt[0].points_mm, [[1200, 800], [4300, 840], [4300, 3100]]);
});

test("der Abzug haelt Zahlen fest, keine Verweise", () => {
  // Sonst zeigte er auf dieselben Reihen, die gerade veraendert werden.
  const symbols = [{ id: "a", points_mm: kuechenzeile() }];
  const gemerkt = abzug(symbols);
  symbols[0].points_mm[0][0] = 9999;
  assert.equal(gemerkt[0].points_mm[0][0], 1200);
});

test("ein Symbol ohne Punkte uebersteht den Abzug", () => {
  const symbols = [{ id: "b", symbol: "kuehlschrank", position_mm: [1, 2] }];
  assert.deepEqual(abzug(symbols)[0].position_mm, [1, 2]);
  assert.equal(abzug(symbols)[0].points_mm, undefined);
});

test("je Aenderung genau ein Eintrag im Stapel", () => {
  // Der erste Anlauf legte den Abzug INNERHALB des setDocument-Updaters weg.
  // React ruft den im Entwicklungsmodus zweimal auf, also stand jede
  // Aenderung doppelt im Stapel und ein Strg+Z bewegte nichts -- gemessen am
  // 2026-08-28: sechs Eintraege fuer drei Aenderungen. Der Abzug entsteht
  // seither VOR dem Aufruf.
  const stapel = [];
  let symbols = [{ id: "a", points_mm: kuechenzeile() }];
  function aendern(fn) {
    stapel.push(abzug(symbols));          // vorher, genau einmal
    symbols = fn(symbols);
  }
  aendern((liste) => liste.map((i) => ({ ...i, points_mm: richtePunkteAus(i.points_mm, [0, 1], 1) })));
  aendern((liste) => liste.map((i) => ({ ...i, points_mm: schiebePunkte(i.points_mm, [0], 10, 0) })));
  assert.equal(stapel.length, 2);
  symbols = stapel.pop();
  assert.equal(symbols[0].points_mm[0][1], 820);   // nach dem Ausrichten
  symbols = stapel.pop();
  assert.deepEqual(symbols[0].points_mm, kuechenzeile());
});

/**
 * Der doppelte Punkt am Ende, und wie man einen einzelnen loswird.
 *
 * Rainer, 2026-08-28: "when i doubleclick to end the creation many times
 * there are 2 points created at the end."
 *
 * Die Ursache steht im Ereignis selbst: ein Doppelklick feuert erst ZWEI
 * click-Ereignisse -- jedes haengt einen Punkt an den Entwurf -- und erst
 * danach `dblclick`, das den Lauf abschliesst. Der letzte Punkt ist also
 * zweimal drin, an derselben Stelle.
 */

const DOPPELT_MM = 60;

/** Aufeinanderfolgende Punkte, die praktisch aufeinander liegen, zusammenziehen. */
function entdoppelt(punkte) {
  const raus = [];
  for (const punkt of punkte) {
    const letzter = raus[raus.length - 1];
    if (letzter && Math.hypot(punkt[0] - letzter[0], punkt[1] - letzter[1]) <= DOPPELT_MM) continue;
    raus.push(punkt);
  }
  return raus;
}

/** Einen Punkt entfernen. Unter zwei Punkten ist es kein Lauf mehr. */
function loeschePunkt(punkte, index) {
  if (punkte.length <= 2) return punkte;
  if (index < 0 || index >= punkte.length) return punkte;
  return punkte.filter((_, i) => i !== index);
}

test("der doppelte Punkt am Ende faellt beim Anlegen weg", () => {
  // Genau das, was der Doppelklick erzeugt.
  const ausDemDoppelklick = [[1200, 800], [4300, 840], [4300, 3100], [4300, 3100]];
  assert.deepEqual(entdoppelt(ausDemDoppelklick), kuechenzeile());
});

test("ein um wenige Millimeter versetzter Doppelpunkt faellt auch weg", () => {
  // Zwei Klicks derselben Hand treffen nicht exakt denselben Millimeter.
  const wackelig = [[1200, 800], [4300, 840], [4300, 3100], [4318, 3122]];
  assert.equal(entdoppelt(wackelig).length, 3);
});

test("zwei echte Punkte in derselben Ecke bleiben beide", () => {
  // 200 mm sind eine bewusst gesetzte kurze Strecke, kein Zittern.
  const kurz = [[0, 0], [200, 0], [200, 900]];
  assert.equal(entdoppelt(kurz).length, 3);
});

test("ein sauber gezeichneter Lauf bleibt unveraendert", () => {
  assert.deepEqual(entdoppelt(kuechenzeile()), kuechenzeile());
});

test("ein einzelner Punkt laesst sich loeschen", () => {
  assert.deepEqual(loeschePunkt(kuechenzeile(), 1), [[1200, 800], [4300, 3100]]);
});

test("der letzte verbliebene Strich wird nicht auch noch geloescht", () => {
  // Unter zwei Punkten ist es kein Lauf mehr, sondern ein Punkt im Nichts.
  const zwei = [[0, 0], [1000, 0]];
  assert.deepEqual(loeschePunkt(zwei, 0), zwei);
});

test("ein Index ausserhalb der Reihe aendert nichts", () => {
  assert.deepEqual(loeschePunkt(kuechenzeile(), 9), kuechenzeile());
});

/**
 * Ausrichten ohne vorherige Auswahl.
 *
 * Rainer, 2026-08-28: "why no align waagrecht and senkrecht? Im just trying to
 * make it easier for the 'Bauen' part."
 *
 * Der erste Anlauf zeigte die beiden Befehle nur, wenn schon zwei Punkte
 * gewaehlt waren. Wer den Lauf anklickt, um ihn gerade zu ziehen, bekam
 * stattdessen den Hinweis "Punkt anklicken, Shift fuer mehrere" -- ein
 * Menue, das erklaert statt zu tun.
 *
 * Der haeufigste Fall ist ohnehin "die ganze Zeile soll gerade sein".
 */

/** Worauf sich das Ausrichten bezieht: die Auswahl, sonst der ganze Lauf. */
function zielIndices(punkte, auswahl) {
  return auswahl.length > 1 ? auswahl : punkte.map((_, i) => i);
}

test("ohne Auswahl richtet sich der ganze Lauf aus", () => {
  const lauf = kuechenzeile();
  assert.deepEqual(zielIndices(lauf, []), [0, 1, 2]);
});

test("ein einzelner gewaehlter Punkt richtet trotzdem den ganzen Lauf aus", () => {
  // Ein Punkt allein ergibt keine Linie -- gemeint ist dann der Lauf.
  assert.deepEqual(zielIndices(kuechenzeile(), [1]), [0, 1, 2]);
});

test("zwei oder mehr gewaehlte Punkte gewinnen gegen den ganzen Lauf", () => {
  assert.deepEqual(zielIndices(kuechenzeile(), [0, 1]), [0, 1]);
});

test("der ganze Lauf waagerecht macht aus der Kuechenzeile eine Gerade", () => {
  // Der Fall fuer den Bau: die Zeile soll an einer Linie liegen.
  const lauf = kuechenzeile();
  const neu = richtePunkteAus(lauf, zielIndices(lauf, []), 1);
  assert.deepEqual(neu.map((p) => p[1]), [840, 840, 840]);
});

/**
 * Ein Rechtsklick raeumt die Auswahl nicht ab.
 *
 * Rainer, 2026-08-28: "but the second point gets deselected when i right
 * click."
 *
 * Der Rechtsklick rief dieselbe Auswahlregel wie der Linksklick, und die
 * ersetzt ohne Shift die Auswahl durch den einen Punkt. Wer zwei Punkte
 * waehlt und dann rechtsklickt, um sie auszurichten, hatte danach einen.
 */

/** Was ein Rechtsklick auf `punkt` aus der Auswahl macht. */
function auswahlNachRechtsklick(auswahl, punkt) {
  return auswahl.includes(punkt) ? auswahl : [punkt];
}

test("ein Rechtsklick auf einen bereits gewaehlten Punkt laesst die Auswahl stehen", () => {
  assert.deepEqual(auswahlNachRechtsklick([0, 1], 1), [0, 1]);
  assert.deepEqual(auswahlNachRechtsklick([0, 1, 2], 0), [0, 1, 2]);
});

test("ein Rechtsklick daneben waehlt nur diesen Punkt", () => {
  // Sonst richtete das Menue Punkte aus, die man gar nicht mehr im Blick hat.
  assert.deepEqual(auswahlNachRechtsklick([0, 1], 3), [3]);
});

test("ein Rechtsklick ohne Auswahl waehlt den angeklickten Punkt", () => {
  assert.deepEqual(auswahlNachRechtsklick([], 2), [2]);
});

/*
 * Rainer, 2026-10-09: "eine gerade zeile mit 2 punkten endet immer in 3
 * punkte davon sind 2 fast aufeinander". Herausgezoomt (~12 mm/px) ist ein
 * Wackler von 7 px rund 90 mm -- entdoppelt() mit 60 mm laesst ihn stehen.
 * Deshalb verwirft der Editor den zweiten Druck eines Doppelklicks schon
 * beim Druecken, gemessen in Bildschirm-Pixeln. Dieselbe Logik wie
 * istDoppelklickDruck() in furniture.tsx.
 */
const DOPPELKLICK_MS = 500;
const DOPPELKLICK_PX = 10;

function istDoppelklickDruck(vorher, jetzt) {
  if (!vorher) return false;
  return jetzt.t - vorher.t < DOPPELKLICK_MS
    && Math.hypot(jetzt.x - vorher.x, jetzt.y - vorher.y) < DOPPELKLICK_PX;
}

/** Druecke nacheinander -- welche Punkte landen im Entwurf? */
function zeichne(druecke) {
  const entwurf = [];
  let vorher = null;
  for (const druck of druecke) {
    const verwerfen = istDoppelklickDruck(vorher, druck);
    vorher = druck;
    if (!verwerfen) entwurf.push([druck.x, druck.y]);
  }
  return entwurf;
}

test("Klick, dann Doppelklick: genau zwei Punkte", () => {
  const punkte = zeichne([
    { t: 0, x: 100, y: 200 },
    { t: 900, x: 400, y: 200 },
    { t: 1020, x: 400, y: 200 },
  ]);
  assert.equal(punkte.length, 2);
});

test("der zweite Druck wackelt 7 px -- trotzdem zwei Punkte", () => {
  // Der gemeldete Fall: bei ~12 mm/px waeren das ~90 mm, ueber DOPPELT_MM.
  const punkte = zeichne([
    { t: 0, x: 100, y: 200 },
    { t: 900, x: 400, y: 200 },
    { t: 1020, x: 407, y: 202 },
  ]);
  assert.deepEqual(punkte, [[100, 200], [400, 200]]);
  assert.ok(7 * 12 > DOPPELT_MM, "entdoppelt() allein haette den Punkt behalten");
});

test("zwei schnelle Klicks weit auseinander bleiben zwei Punkte", () => {
  const punkte = zeichne([
    { t: 0, x: 100, y: 200 },
    { t: 200, x: 130, y: 200 },
  ]);
  assert.equal(punkte.length, 2);
});

test("zwei langsame Klicks auf dieselbe Stelle bleiben zwei Druecke", () => {
  // Kein Doppelklick -- das Zusammenziehen ist dann Sache von entdoppelt().
  const punkte = zeichne([
    { t: 0, x: 100, y: 200 },
    { t: 800, x: 102, y: 200 },
  ]);
  assert.equal(punkte.length, 2);
});

/*
 * Rainer, 2026-10-09: "können wir wenn ein raum ohne möbel ist bitte
 * warnmeldung beim 'weiter zum Bauen' drücken". Dieselbe Logik wie
 * leereRaeume() in furniture.tsx. Flur, Treppe, Garage usw. bleiben
 * ueblicherweise leer und werden nicht gemeldet (Rainer: "so wie du es
 * vorschlägst ist gut").
 */
const DARF_LEER_SEIN = ["flur", "diele", "treppe", "galerie", "luftraum",
  "abstell", "garage", "carport", "balkon", "terrasse"];

function imPolygon(x, y, poly) {
  let drin = false;
  for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
    const [xi, yi] = poly[i];
    const [xj, yj] = poly[j];
    if ((yi > y) !== (yj > y)
        && x < ((xj - xi) * (y - yi)) / ((yj - yi) || 1e-9) + xi) drin = !drin;
  }
  return drin;
}

function mitteVonMoebel(item) {
  if (item?.position_mm) return [item.position_mm[0], item.position_mm[1]];
  const punkte = item?.points_mm;
  if (!punkte?.length) return null;
  return [punkte.reduce((s, p) => s + p[0], 0) / punkte.length,
          punkte.reduce((s, p) => s + p[1], 0) / punkte.length];
}

function leereRaeume(symbols, rooms) {
  const mitten = (symbols || []).map(mitteVonMoebel).filter(Boolean);
  return (rooms || []).filter((raum) => {
    const poly = raum.polygon || raum.polygon_mm;
    if (!poly || poly.length < 3) return false;
    const name = `${raum.name || ""}`.toLocaleLowerCase("de-DE");
    if (DARF_LEER_SEIN.some((wort) => name.includes(wort))) return false;
    return !mitten.some(([x, y]) => imPolygon(x, y, poly));
  });
}

const quadrat = (x, y, w) => [[x, y], [x + w, y], [x + w, y + w], [x, y + w]];

test("leerer Raum: ein Raum ohne Moebel wird gemeldet", () => {
  const raeume = [{ name: "Bad", polygon: quadrat(0, 0, 3000) },
                  { name: "Schlafen", polygon: quadrat(3000, 0, 4000) }];
  const moebel = [{ position_mm: [5000, 2000] }];
  assert.deepEqual(leereRaeume(moebel, raeume).map((r) => r.name), ["Bad"]);
});

test("leerer Raum: ein gezeichneter Lauf zaehlt ueber seine Mitte", () => {
  const raeume = [{ name: "Küche", polygon: quadrat(0, 0, 4000) }];
  const moebel = [{ points_mm: [[200, 300], [3000, 300]] }];
  assert.equal(leereRaeume(moebel, raeume).length, 0);
});

test("leerer Raum: Moebel knapp ausserhalb macht den Raum nicht voll", () => {
  const raeume = [{ name: "Kind 2", polygon: quadrat(0, 0, 3000) }];
  const moebel = [{ position_mm: [3100, 1500] }];
  assert.equal(leereRaeume(moebel, raeume).length, 1);
});

test("leerer Raum: Flur, Treppe, Garage und Co. duerfen leer sein", () => {
  const raeume = ["Flur", "Diele", "Treppe", "Galerie", "Luftraum", "Abstellraum",
                  "Garage", "Carport", "Balkon", "Dachterrasse"]
    .map((name, i) => ({ name, polygon: quadrat(i * 5000, 0, 3000) }));
  assert.equal(leereRaeume([], raeume).length, 0);
});

test("leerer Raum: alles moebliert, keine Meldung", () => {
  const raeume = [{ name: "Wohnen", polygon: quadrat(0, 0, 5000) }];
  assert.equal(leereRaeume([{ position_mm: [2500, 2500] }], raeume).length, 0);
});

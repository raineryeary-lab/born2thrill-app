/**
 * Bereich einrichten -- MOEBEL-BEREICH-EINRICHTEN-001.
 *
 * Prueft den ECHTEN Code (src/lib/generator/moebel-vorschlag.mjs), keine
 * Kopie: die Datei ist reines JavaScript ohne React.
 *
 * Rainer, 2026-10-09: Nachttisch = Stuff-Kasten, Dusche vor Wanne.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  richteBereichEin, richteAlleRaeumeEin, rechteckVon, raumtypAusName, TUER_FREIRAUM_MM, RAUMTYPEN,
} from "../src/lib/generator/moebel-vorschlag.mjs";

const rechteck = (x, y, w, h) => [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];
const liegtIn = (r, poly) => r.x0 >= Math.min(...poly.map((p) => p[0])) - 1 && r.x1 <= Math.max(...poly.map((p) => p[0])) + 1
  && r.y0 >= Math.min(...poly.map((p) => p[1])) - 1 && r.y1 <= Math.max(...poly.map((p) => p[1])) + 1;

function ueberlappen(a, b) {
  return a.x0 < b.x1 - 5 && b.x0 < a.x1 - 5 && a.y0 < b.y1 - 5 && b.y0 < a.y1 - 5;
}

/** Eine von Hand gezeichnete Kuechenzeile, wie sie die Seite uebergibt. */
function zeileVon(punkte) {
  const m = { symbol: "kuechenzeile", points_mm: punkte };
  const xs = punkte.map((p) => p[0]);
  const ys = punkte.map((p) => p[1]);
  return { ...(punkte.length === 2 ? rechteckVon(m) : { x0: Math.min(...xs), y0: Math.min(...ys),
                                                       x1: Math.max(...xs), y1: Math.max(...ys) }), ...m };
}

function pruefeGrundregeln(ergebnis, poly, ausnahmen = []) {
  const xs = poly.map((p) => p[0]);
  const ys = poly.map((p) => p[1]);
  const rahmen = { x0: Math.min(...xs), y0: Math.min(...ys), x1: Math.max(...xs), y1: Math.max(...ys) };
  const rs = ergebnis.moebel.map((m) => ({ key: m.symbol, ...rechteckVon(m) }));
  for (const r of rs) {
    assert.ok(r.x0 >= rahmen.x0 - 5 && r.x1 <= rahmen.x1 + 5
           && r.y0 >= rahmen.y0 - 5 && r.y1 <= rahmen.y1 + 5, `${r.key} liegt ausserhalb`);
  }
  for (let i = 0; i < rs.length; i += 1) {
    for (let j = i + 1; j < rs.length; j += 1) {
      const paar = [rs[i].key, rs[j].key].sort().join("+");
      if (ausnahmen.includes(paar)) continue;
      assert.ok(!ueberlappen(rs[i], rs[j]), `${rs[i].key} ueberlappt ${rs[j].key}`);
    }
  }
  return rs;
}

// Schlafzimmer 3,5 x 4 m, Tuer an der kurzen Oberkante links.
const SCHLAF = rechteck(0, 0, 3500, 4000);
const SCHLAF_TUER = [{ a: [200, 0], b: [1100, 0], typ: "door" }];

test("Schlafzimmer: Bett, zwei Nachttische, Kleiderschrank", () => {
  const e = richteBereichEin({ polygon: SCHLAF, oeffnungen: SCHLAF_TUER }, "schlafzimmer");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.includes("doppelbett"));
  assert.equal(keys.filter((k) => k === "stuff").length, 2, "zwei Nachttische als Stuff");
  assert.ok(keys.includes("kleiderschrank"));
  assert.deepEqual(e.weggelassen, []);
  pruefeGrundregeln(e, SCHLAF);
});

test("Schlafzimmer: das Bett steht an einer langen Wand ohne Tuer", () => {
  const e = richteBereichEin({ polygon: SCHLAF, oeffnungen: SCHLAF_TUER }, "schlafzimmer");
  const bett = e.moebel.find((m) => m.symbol === "doppelbett");
  // Lange Waende sind links (x=0) und rechts (x=3500): Bett quer zur x-Achse.
  assert.ok([90, 270].includes(bett.rotation_deg), `Drehung ${bett.rotation_deg}`);
});

test("Schlafzimmer: nichts steht im Freiraum vor der Tuer", () => {
  const e = richteBereichEin({ polygon: SCHLAF, oeffnungen: SCHLAF_TUER }, "schlafzimmer");
  const zone = { x0: 200, y0: 0, x1: 1100, y1: TUER_FREIRAUM_MM };
  for (const m of e.moebel) {
    assert.ok(!ueberlappen(rechteckVon(m), zone), `${m.symbol} steht vor der Tuer`);
  }
});

test("Schlafzimmer: der Kleiderschrank steht nicht vor dem Fenster", () => {
  const fenster = [{ a: [0, 500], b: [0, 3500], typ: "window" },
                   { a: [3500, 500], b: [3500, 3500], typ: "window" },
                   { a: [500, 4000], b: [3000, 4000], typ: "window" }];
  const e = richteBereichEin({ polygon: SCHLAF, oeffnungen: [...SCHLAF_TUER, ...fenster] }, "schlafzimmer");
  const schrank = e.moebel.find((m) => m.symbol === "kleiderschrank");
  if (!schrank) {
    assert.ok(e.weggelassen.includes("Kleiderschrank"), "fehlt, aber dann gemeldet");
    return;
  }
  const r = rechteckVon(schrank);
  for (const f of fenster) {
    const zone = { x0: Math.min(f.a[0], f.b[0]) - (f.a[0] === f.b[0] ? 600 : 0),
                   x1: Math.max(f.a[0], f.b[0]) + (f.a[0] === f.b[0] ? 600 : 0),
                   y0: Math.min(f.a[1], f.b[1]) - (f.a[1] === f.b[1] ? 600 : 0),
                   y1: Math.max(f.a[1], f.b[1]) + (f.a[1] === f.b[1] ? 600 : 0) };
    assert.ok(!ueberlappen(r, zone), "Schrank vor Fenster");
  }
});

// Rainer, 2026-10-09: "the bathroom was missing the badewanne" -- ein Bad
// bekommt Dusche UND Wanne (geaendert; vorher "Dusche statt Wanne").
test("Bad: Dusche und Badewanne, dazu Waschtisch und WC", () => {
  const poly = rechteck(0, 0, 3300, 4700);
  const e = richteBereichEin({ polygon: poly, oeffnungen: [{ a: [2200, 4700], b: [3100, 4700], typ: "door" }] }, "bad");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.some((k) => k.startsWith("dusche")), keys.join(","));
  assert.ok(keys.includes("badewanne"), `${keys.join(",")} / weg: ${e.weggelassen.join(",")}`);
  assert.ok(keys.includes("waschtisch"));
  assert.ok(keys.includes("wand_wc"));
  pruefeGrundregeln(e, poly);
});

test("Bad: zu klein fuer die Wanne -> Dusche bleibt, Wanne gemeldet", () => {
  const poly = rechteck(0, 0, 1600, 2400);
  const e = richteBereichEin({ polygon: poly }, "bad");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.some((k) => k.startsWith("dusche")), keys.join(","));
  assert.ok(!keys.includes("badewanne"));
  assert.ok(e.weggelassen.includes("Badewanne"));
});

test("Du/Bad: nur Dusche, keine Wanne", () => {
  const poly = rechteck(0, 0, 3300, 4700);
  const e = richteBereichEin({ polygon: poly }, "duschbad");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.some((k) => k.startsWith("dusche")));
  assert.ok(!keys.includes("badewanne"));
  assert.ok(keys.includes("wand_wc"));
});

test("Bad: die Dusche steht in einer Ecke", () => {
  const poly = rechteck(0, 0, 2500, 3000);
  const e = richteBereichEin({ polygon: poly }, "bad");
  const r = rechteckVon(e.moebel.find((m) => m.symbol.startsWith("dusche")));
  const anX = r.x0 <= 5 || r.x1 >= 2495;
  const anY = r.y0 <= 5 || r.y1 >= 2995;
  assert.ok(anX && anY, JSON.stringify(r));
});

test("Wohnzimmer: Sofa, Lowboard gegenueber, Couchtisch dazwischen", () => {
  const poly = rechteck(0, 0, 5000, 4000);
  const e = richteBereichEin({ polygon: poly, oeffnungen: [{ a: [0, 3000], b: [0, 3900], typ: "door" }] }, "wohnzimmer");
  const by = Object.fromEntries(e.moebel.map((m) => [m.symbol, m]));
  // Rainer, 2026-10-09: "please use the eckcouch for wohnzimmer" (vorher 3-Sitzer).
  assert.ok(by.ecksofa && by.lowboard && by.couchtisch && by.fernseher, Object.keys(by).join(","));
  // Das Ecksofa-Symbol hat seine Vorderseite bei lokal -y (so setzt Rainer es
  // von Hand) -- gegenueber dem Lowboard steht es deshalb mit GLEICHER Drehung.
  assert.equal(by.ecksofa.rotation_deg, by.lowboard.rotation_deg, "gegenueber");
  // Couchtisch liegt zwischen Sofa und Lowboard.
  const [s, l, c] = [by.ecksofa, by.lowboard, by.couchtisch].map((m) => m.position_mm);
  // Sofa an Ober-/Unterwand (0/180 Grad) -> sie stehen sich in y gegenueber.
  const achse = by.ecksofa.rotation_deg % 180 === 0 ? 1 : 0;
  assert.ok((c[achse] - s[achse]) * (c[achse] - l[achse]) < 0, "Couchtisch nicht dazwischen");
  pruefeGrundregeln(e, poly, ["fernseher+lowboard", "couchtisch+ecksofa"]);
});

test("zu kleiner Bereich: weniger Moebel, Rest gemeldet, kein Absturz", () => {
  const e = richteBereichEin({ polygon: rechteck(0, 0, 1000, 1000) }, "schlafzimmer");
  assert.equal(e.moebel.length, 0);
  assert.ok(e.weggelassen.includes("Bett"));
});

test("vorhandene Moebel werden nicht ueberdeckt", () => {
  const vorhanden = { x0: 0, y0: 0, x1: 3500, y1: 4000 }; // alles belegt
  const e = richteBereichEin({ polygon: SCHLAF, vorhandene: [vorhanden] }, "schlafzimmer");
  assert.equal(e.moebel.length, 0);
});

test("L-foermiger Raum: nichts steht in der fehlenden Ecke", () => {
  const poly = [[0, 0], [5000, 0], [5000, 2000], [2500, 2000], [2500, 4000], [0, 4000]];
  const e = richteBereichEin({ polygon: poly }, "wohnzimmer");
  for (const m of e.moebel) {
    const r = rechteckVon(m);
    assert.ok(!(r.x1 > 2505 && r.y1 > 2005), `${m.symbol} ragt in die fehlende Ecke`);
  }
});

test("Raumtyp aus dem Namen", () => {
  assert.equal(raumtypAusName("Eltern / Schlafen"), "schlafzimmer");
  assert.equal(raumtypAusName("Bad"), "bad");
  // Rainer, 2026-10-09: ein kombinierter Raum ist mehrere Bereiche -- kein
  // Typ vorwaehlen, er zeichnet und waehlt selbst.
  assert.equal(raumtypAusName("Wohnen / Essen / Kochen"), null);
  assert.equal(raumtypAusName("Wohnzimmer"), "wohnzimmer");
  assert.equal(raumtypAusName("Küche"), "kueche");
  assert.equal(raumtypAusName("Essen"), "esszimmer");
  // Seit den restlichen Raumtypen hat auch das WC und die Diele einen Typ.
  assert.equal(raumtypAusName("WC"), "wc");
  assert.equal(raumtypAusName("Gäste-WC"), "wc");
  assert.equal(raumtypAusName("Flur"), "diele");
  assert.equal(raumtypAusName("Kind"), "kinderzimmer");
  assert.equal(raumtypAusName("Gast"), "gast");
  assert.equal(raumtypAusName("HWR / HTR"), "hwr");
  assert.equal(raumtypAusName("Duschbad"), "duschbad");
  assert.equal(raumtypAusName("Elternbad"), "bad");
  assert.equal(raumtypAusName("Büro"), "buero");
});

test("unbekannter Raumtyp: nichts, aber eine Meldung", () => {
  const e = richteBereichEin({ polygon: SCHLAF }, "sauna");
  assert.equal(e.moebel.length, 0);
  assert.equal(e.weggelassen.length, 1);
});

// --- Esszimmer und Kueche (Rainer, 2026-10-09: "i need to be able to tell
// you if it is a dining or a living or a kitchen") ---------------------------

test("Esszimmer: Essgruppe frei in der Mitte, nicht an der Wand", () => {
  const poly = rechteck(0, 0, 4000, 3500);
  const e = richteBereichEin({ polygon: poly }, "esszimmer");
  assert.equal(e.moebel.length, 1);
  const g = e.moebel[0];
  assert.equal(g.symbol, "essgruppe_6");
  assert.ok(Math.abs(g.position_mm[0] - 2000) <= 100 && Math.abs(g.position_mm[1] - 1750) <= 100,
            JSON.stringify(g.position_mm));
  pruefeGrundregeln(e, poly);
});

test("Esszimmer: zu schmal fuer die Essgruppe -> Tisch einzeln, fehlende Stuehle gemeldet", () => {
  const poly = rechteck(0, 0, 1700, 1400);
  const e = richteBereichEin({ polygon: poly }, "esszimmer");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.includes("esstisch"), keys.join(","));
  assert.ok(!keys.includes("essgruppe_6"));
  assert.ok(e.weggelassen.some((w) => w.includes("Stühle")), e.weggelassen.join(","));
  pruefeGrundregeln(e, poly);
});

test("Kueche: gezeichnete Zeile bekommt Spuele, Kochfeld, Hochschrank und Kuehlschrank", () => {
  const poly = rechteck(0, 0, 4500, 3000);
  const zeile = zeileVon([[1000, 300], [3500, 300]]);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeile],
    oeffnungen: [{ a: [0, 1000], b: [0, 1900], typ: "door" }] }, "kueche");
  const by = Object.fromEntries(e.moebel.map((m) => [m.symbol, m]));
  for (const k of ["kuehlschrank", "hochschrank_herd", "spuele", "kochfeld"]) {
    assert.ok(by[k], `${k} fehlt: ${Object.keys(by).join(",")} / ${e.weggelassen.join(",")}`);
  }
  assert.ok(!by.kuechenzeile, "keine zweite Zeile");
  // Spuele und Kochfeld liegen auf der Zeile, die hohen Geraete nicht.
  for (const k of ["spuele", "kochfeld"]) assert.ok(ueberlappen(rechteckVon(by[k]), zeile), `${k} nicht auf der Zeile`);
  for (const k of ["kuehlschrank", "hochschrank_herd"]) assert.ok(!ueberlappen(rechteckVon(by[k]), zeile), `${k} auf der Zeile`);
  pruefeGrundregeln(e, poly);
});

test("Kueche: ohne gezeichnete Zeile -> alle Teile an die Wand, aber keine Zeile", () => {
  // Rainer, 2026-10-30: "i want to have kochfeld spuele hochschrank herd
  // refridgerator and the kuecheninsel please dont do the kuechenzeile".
  const e = richteBereichEin({ polygon: rechteck(0, 0, 6000, 5000) }, "kueche");
  const keys = e.moebel.map((m) => m.symbol).sort();
  assert.deepEqual(keys, ["hochschrank_herd", "kochfeld", "kuecheninsel", "kuehlschrank", "spuele"], e.weggelassen.join(","));
  for (const m of e.moebel) assert.ok(liegtIn(rechteckVon(m), rechteck(0, 0, 6000, 5000)), m.symbol);
});

test("Kueche: ohne Wandplatz -> Meldung statt Stille", () => {
  const e = richteBereichEin({ polygon: rechteck(0, 0, 900, 900) }, "kueche");
  assert.equal(e.moebel.length, 0);
  assert.deepEqual(e.weggelassen, ["Küche (kein freier Wandplatz)"]);
});

test("eigener Bereich im grossen Raum: Moebel an die echte Wand, nicht an die offene Kante", () => {
  // Grosser Raum 10 x 5 m, Rainer zeichnet links 4 x 5 m als Wohnzimmer.
  const raum = rechteck(0, 0, 10000, 5000);
  const raumKanten = raum.map((a, i) => [a, raum[(i + 1) % raum.length]]);
  const bereich = rechteck(0, 0, 4000, 5000);
  const e = richteBereichEin({ polygon: bereich, raumKanten }, "wohnzimmer");
  const sofa = e.moebel.find((m) => m.symbol.startsWith("sofa") || m.symbol === "ecksofa");
  assert.ok(sofa, e.weggelassen.join(","));
  const r = rechteckVon(sofa);
  // Die offene Kante ist x = 4000 -- dort darf das Sofa nicht mit dem Ruecken stehen.
  assert.ok(r.x1 < 3900, `Sofa an der offenen Kante: ${JSON.stringify(r)}`);
});

// --- die restlichen Raumtypen (Rainer, 2026-10-09: "ok do the rest") -------

test("Kueche: kurze Zeile hat trotzdem Spuele UND Kochfeld", () => {
  const poly = rechteck(0, 0, 2000, 1500);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon([[0, 300], [2000, 300]])] }, "kueche");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.includes("spuele") && keys.includes("kochfeld"), `${keys.join(",")} / ${e.weggelassen.join(",")}`);
});

test("WC: Wand-WC und Handwaschbecken", () => {
  const poly = rechteck(0, 0, 1200, 2000);
  const e = richteBereichEin({ polygon: poly, oeffnungen: [{ a: [200, 2000], b: [1000, 2000], typ: "door" }] }, "wc");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.includes("wand_wc") && keys.includes("handwaschbecken"), `${keys.join(",")} / ${e.weggelassen.join(",")}`);
  pruefeGrundregeln(e, poly);
});

test("Diele: Garderobe und Schrank an der Wand, die Mitte bleibt frei", () => {
  const poly = rechteck(0, 0, 4000, 1800);
  const e = richteBereichEin({ polygon: poly }, "diele");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.includes("garderobe") && keys.includes("schrank_40"), keys.join(","));
  for (const m of e.moebel) {
    const r = rechteckVon(m);
    assert.ok(r.y0 <= 5 || r.y1 >= 1795 || r.x0 <= 5 || r.x1 >= 3995, `${m.symbol} steht nicht an der Wand`);
  }
  pruefeGrundregeln(e, poly);
});

test("HWR: Waschmaschine und Trockner nebeneinander, dazu ein Schrank", () => {
  const poly = rechteck(0, 0, 3000, 2500);
  const e = richteBereichEin({ polygon: poly }, "hwr");
  const by = Object.fromEntries(e.moebel.map((m) => [m.symbol, m]));
  assert.ok(by.waschmaschine && by.trockner && by.schrank_60, Object.keys(by).join(","));
  const a = rechteckVon(by.waschmaschine);
  const b = rechteckVon(by.trockner);
  const nebeneinander = (Math.abs(a.x1 - b.x0) <= 5 || Math.abs(b.x1 - a.x0) <= 5) && Math.abs(a.y0 - b.y0) <= 5
                     || (Math.abs(a.y1 - b.y0) <= 5 || Math.abs(b.y1 - a.y0) <= 5) && Math.abs(a.x0 - b.x0) <= 5;
  assert.ok(nebeneinander, JSON.stringify([a, b]));
  pruefeGrundregeln(e, poly);
});

test("Kinderzimmer: Einzelbett in der Ecke, Nachttisch, Schreibtisch am Fenster, Schrank", () => {
  const poly = rechteck(0, 0, 3500, 4000);
  const oeffnungen = [{ a: [1200, 4000], b: [2400, 4000], typ: "window" },
                      { a: [0, 200], b: [0, 1100], typ: "door" }];
  const e = richteBereichEin({ polygon: poly, oeffnungen }, "kinderzimmer");
  const by = Object.fromEntries(e.moebel.map((m) => [m.symbol, m]));
  for (const k of ["einzelbett", "stuff", "schreibtisch_kind", "kleiderschrank"]) {
    assert.ok(by[k], `${k} fehlt: ${Object.keys(by).join(",")} / ${e.weggelassen.join(",")}`);
  }
  // Der Schreibtisch steht an der Fensterwand (y = 4000).
  assert.ok(rechteckVon(by.schreibtisch_kind).y1 >= 3900, /* 50 mm Wandabstand laut Katalog */ JSON.stringify(rechteckVon(by.schreibtisch_kind)));
  // Das Bett beruehrt zwei Waende (Ecke).
  const r = rechteckVon(by.einzelbett);
  const waende = [r.x0 <= 60, r.x1 >= 3440, r.y0 <= 60, r.y1 >= 3940].filter(Boolean).length;
  assert.ok(waende >= 2, JSON.stringify(r));
  pruefeGrundregeln(e, poly);
});

test("Gast: wie ein Schlafzimmer", () => {
  const e = richteBereichEin({ polygon: SCHLAF, oeffnungen: SCHLAF_TUER }, "gast");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.includes("doppelbett") || keys.includes("einzelbett"), keys.join(","));
  assert.ok(keys.includes("kleiderschrank"));
});

test("alle Raumtypen aus der Auswahl haben eine Regel", () => {
  for (const { key } of RAUMTYPEN) {
    const e = richteBereichEin({ polygon: rechteck(0, 0, 4000, 4000) }, key);
    assert.ok(e.moebel.length > 0, `${key}: ${e.weggelassen.join(",")}`);
  }
});

test("Buero: Schreibtisch an der Fensterwand, Stuhl davor zum Tisch, Sideboard", () => {
  // Rainer, 2026-10-09: "büro fehlt".
  const poly = rechteck(0, 0, 3500, 3600);
  const oeffnungen = [{ a: [1000, 3600], b: [2500, 3600], typ: "window" },
                      { a: [0, 200], b: [0, 1100], typ: "door" }];
  const e = richteBereichEin({ polygon: poly, oeffnungen }, "buero");
  const by = Object.fromEntries(e.moebel.map((m) => [m.symbol, m]));
  assert.ok(by.schreibtisch && by.schreibtischstuhl && (by.sideboard || by.schrank_40),
            `${Object.keys(by).join(",")} / ${e.weggelassen.join(",")}`);
  const tisch = rechteckVon(by.schreibtisch);
  assert.ok(tisch.y1 >= 3500, `Tisch nicht am Fenster: ${JSON.stringify(tisch)}`);
  // Stuhl vor dem Tisch (raumseitig) und mit dem Gesicht zum Tisch.
  assert.ok(by.schreibtischstuhl.position_mm[1] < by.schreibtisch.position_mm[1]);
  assert.equal(by.schreibtischstuhl.rotation_deg, (by.schreibtisch.rotation_deg + 180) % 360);
  pruefeGrundregeln(e, poly, ["schreibtisch+schreibtischstuhl"]);
});

test("Fenster etwas innerhalb der Raumkante zaehlt trotzdem als Fensterwand", () => {
  // Echte Daten onehalfstorey_020, Buero: Raumkante x = 902.9, Fenster x = 1023.
  const poly = [[902.9, 5315.9], [4596.6, 5315.9], [4596.6, 8777.1], [902.9, 8777.1]];
  const oeffnungen = [{ a: [1023, 7458], b: [1023, 6630], typ: "window" },
                      { a: [4313, 8777], b: [3438, 8777], typ: "door" }];
  const e = richteBereichEin({ polygon: poly, oeffnungen }, "buero");
  const tisch = rechteckVon(e.moebel.find((m) => m.symbol === "schreibtisch"));
  assert.ok(tisch.x0 <= 1000, `Tisch nicht an der Fensterwand: ${JSON.stringify(tisch)}`);
});

test("Wohnzimmer: Ecksofa in der Ecke, die Liege zur Ecke hin", () => {
  const poly = rechteck(0, 0, 5000, 4000);
  const e = richteBereichEin({ polygon: poly, oeffnungen: [{ a: [0, 3000], b: [0, 3900], typ: "door" }] }, "wohnzimmer");
  const sofa = e.moebel.find((m) => m.symbol === "ecksofa");
  assert.ok(sofa, e.weggelassen.join(","));
  const r = rechteckVon(sofa);
  const waende = [r.x0 <= 120, r.x1 >= 4880, r.y0 <= 120, r.y1 >= 3880].filter(Boolean).length;
  assert.ok(waende >= 2, `nicht in der Ecke: ${JSON.stringify(r)}`);
  // Lehne an der Wand: die Vorderseite (lokal -y) zeigt in den Raum.
  const wv = (sofa.rotation_deg * Math.PI) / 180;
  const vorn = [Math.round(Math.sin(wv)), Math.round(-Math.cos(wv))];
  const vornPunkt = [sofa.position_mm[0] + vorn[0] * 1500, sofa.position_mm[1] + vorn[1] * 1500];
  assert.ok(vornPunkt[0] > 0 && vornPunkt[0] < 5000 && vornPunkt[1] > 0 && vornPunkt[1] < 4000,
            "Vorderseite zeigt in die Wand");
  // Liege = lokal -x (ungespiegelt) bzw. +x (gespiegelt), in Weltrichtung:
  const w = (sofa.rotation_deg * Math.PI) / 180;
  const lokalX = [Math.round(Math.cos(w)), Math.round(Math.sin(w))];
  const liege = sofa.mirrored ? lokalX : [-lokalX[0], -lokalX[1]];
  const mitte = sofa.position_mm;
  const liegePunkt = [mitte[0] + liege[0] * 1000, mitte[1] + liege[1] * 1000];
  // Die Liege zeigt zur naechsten Seitenwand.
  const abstand = liege[0] !== 0 ? Math.min(liegePunkt[0], 5000 - liegePunkt[0]) : Math.min(liegePunkt[1], 4000 - liegePunkt[1]);
  const abstandMitte = liege[0] !== 0 ? Math.min(mitte[0], 5000 - mitte[0]) : Math.min(mitte[1], 4000 - mitte[1]);
  assert.ok(abstand < abstandMitte, "Liege zeigt von der Ecke weg");
});

test("Wohnzimmer: zu klein fuers Ecksofa -> 3-Sitzer", () => {
  // Das Ecksofa braucht 2,8 m Wand; hier ist keine so lang.
  const poly = rechteck(0, 0, 2500, 2500);
  const e = richteBereichEin({ polygon: poly }, "wohnzimmer");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(!keys.includes("ecksofa"));
  assert.ok(keys.includes("sofa_3sitzer") || keys.includes("sofa_2sitzer"), keys.join(","));
});

// --- Alle Raeume einrichten (moebel-alles-einrichten-v1) -----------------
// Rainer, 2026-10-23: "the room names are there why not just populate
// automatically?"
const ALLE = async () => (await import("../src/lib/generator/moebel-vorschlag.mjs")).richteAlleRaeumeEin;
const RAEUME = [
  { id: "s", name: "Eltern / Schlafen", kind: "sleeping", polygon_mm: rechteck(0, 0, 3500, 4000) },
  { id: "b", name: "Bad", kind: "sanitary", polygon_mm: rechteck(3500, 0, 3000, 2500) },
  { id: "k", name: "Kind", kind: "sleeping", polygon_mm: rechteck(0, 4000, 3500, 3500) },
  { id: "w", name: "Wohnen / Essen / Kochen", kind: "living", polygon_mm: rechteck(3500, 2500, 6000, 5000) },
  { id: "l", name: "Luftraum", kind: "luftraum", polygon_mm: rechteck(9500, 0, 2000, 2000) },
  { id: "t", name: "Terrasse", kind: "other", polygon_mm: rechteck(9500, 2000, 2000, 2000) },
];
const OEFF = [
  { a: [200, 0], b: [1100, 0], typ: "door" },
  { a: [3600, 2500], b: [4400, 2500], typ: "door" },
  { a: [200, 7500], b: [1100, 7500], typ: "door" },
];

test("alle Raeume: Schlafen, Bad, Kind werden eingerichtet", async () => {
  const e = (await ALLE())({ raeume: RAEUME, oeffnungen: OEFF, vorhandene: [] });
  assert.deepEqual(e.eingerichtet.sort(), ["Bad", "Eltern / Schlafen", "Kind", "Wohnen / Essen / Kochen"]);
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.includes("doppelbett"), keys.join(","));
  assert.ok(keys.some((k) => /badewanne|dusche/.test(k)), keys.join(","));
  assert.ok(keys.some((k) => /einzelbett|kinder/.test(k)), keys.join(","));
});

test("alle Raeume: Luftraum, Terrasse und Raeume ohne Typ bleiben aus", async () => {
  const raeume = [...RAEUME, { id: "x", name: "Sonstiges", polygon_mm: rechteck(12000, 0, 3000, 3000) }];
  const e = (await ALLE())({ raeume, oeffnungen: OEFF, vorhandene: [] });
  const grund = Object.fromEntries(e.uebersprungen.map((u) => [u.name, u.grund]));
  assert.match(grund.Sonstiges, /eindeutig/);
  assert.ok(grund.Luftraum && grund.Terrasse);
});

test("Kinderzimmer: Playstation-Gruppe steht an der Wand, das Wohnzimmer bekommt keine", () => {
  // Rainer, 2026-11-01: "put the playstation gruppe to the kidsroom and not the living room".
  const poly = rechteck(0, 0, 4500, 5000);
  const e = richteBereichEin({ polygon: poly }, "kinderzimmer");
  assert.ok(e.moebel.some((m) => m.symbol === "playstation_gruppe"), e.weggelassen.join(","));
  pruefeGrundregeln(e, poly);
  const wohnen = richteBereichEin({ polygon: rechteck(0, 0, 6000, 5000) }, "wohnzimmer");
  assert.ok(!wohnen.moebel.some((m) => m.symbol === "playstation_gruppe"));
});

test("Kinderzimmer: zu klein fuer die Playstation-Gruppe -> wird gemeldet, der Rest steht", () => {
  const e = richteBereichEin({ polygon: rechteck(0, 0, 2000, 2300) }, "kinderzimmer");
  assert.ok(e.weggelassen.includes("Playstation-Gruppe"), e.weggelassen.join(","));
  assert.ok(e.moebel.some((m) => m.symbol === "einzelbett"));
});

// --- Kombiraeume -------------------------------------------------------------
// Rainer, 2026-11-01: "do anything with kochen like wohnen essen koschen or essen
// kochen add all of our kichten stuff" und "the same with essen jsut add the table".

const KUECHE_TEILE = ["spuele", "kochfeld", "hochschrank_herd", "kuehlschrank", "kuecheninsel"];
const hatTisch = (keys) => keys.some((k) => k === "essgruppe_6" || k === "esstisch");
const kombi = (name, vorhandene = []) => richteAlleRaeumeEin({
  raeume: [{ name, polygon: rechteck(0, 0, 9000, 7000) }], vorhandene });

test("Kombiraum: Wohnen / Essen / Kochen bekommt alle Kuechenteile und den Tisch", () => {
  const e = kombi("Wohnen / Essen / Kochen");
  const keys = e.moebel.map((m) => m.symbol);
  for (const key of KUECHE_TEILE) assert.ok(keys.includes(key), `${key}: ${keys.join(",")}`);
  assert.ok(hatTisch(keys), keys.join(","));
  assert.ok(!keys.includes("kuechenzeile"));
  assert.ok(!keys.includes("sofa_3sitzer"), "Wohnen wird nicht eingerichtet");
  assert.deepEqual(e.eingerichtet, ["Wohnen / Essen / Kochen"]);
  assert.deepEqual(e.weggelassen, []);
});

test("Kombiraum: jede Schreibweise mit Kochen oder Kueche", () => {
  for (const name of ["Essen / Kochen", "Küche / Essen", "Wohnen / Essen / Küche", "K\ufffdche / Essen"]) {
    const keys = kombi(name).moebel.map((m) => m.symbol);
    for (const key of KUECHE_TEILE) assert.ok(keys.includes(key), `${name} ${key}`);
    assert.ok(hatTisch(keys), name);
  }
});

test("Kombiraum: Wohnen / Essen bekommt nur den Tisch", () => {
  const keys = kombi("Wohnen / Essen").moebel.map((m) => m.symbol);
  assert.ok(hatTisch(keys), keys.join(","));
  for (const key of KUECHE_TEILE) assert.ok(!keys.includes(key), key);
});

test("Kombiraum: Tisch und Kueche ueberschneiden sich nicht", () => {
  const moebel = kombi("Wohnen / Essen / Kochen").moebel.map(rechteckVon);
  moebel.forEach((a, i) => moebel.slice(i + 1).forEach((b) => {
    assert.ok(a.x1 <= b.x0 || b.x1 <= a.x0 || a.y1 <= b.y0 || b.y1 <= a.y0, JSON.stringify([a, b]));
  }));
});

test("Kombiraum: zwischen Tisch und Kueche bleibt ein Gang", () => {
  const moebel = kombi("Wohnen / Essen / Kochen").moebel;
  const tisch = rechteckVon(moebel.find((m) => hatTisch([m.symbol])));
  for (const m of moebel.filter((x) => KUECHE_TEILE.includes(x.symbol))) {
    const r = rechteckVon(m);
    const luecke = Math.max(tisch.x0 - r.x1, r.x0 - tisch.x1, tisch.y0 - r.y1, r.y0 - tisch.y1);
    assert.ok(luecke >= 895, `${m.symbol}: ${luecke}`);
  }
});

test("Kombiraum: kein Platz fuer den Gang -> Tisch steht trotzdem", () => {
  const keys = richteAlleRaeumeEin({ raeume: [{ name: "Essen / Kochen", polygon: rechteck(0, 0, 4200, 5200) }] })
    .moebel.map((m) => m.symbol);
  assert.ok(hatTisch(keys), keys.join(","));
});

test("Kueche: Zeile von Wand zu Wand -> hohe Geraete nah und beisammen", () => {
  const e = richteBereichEin({ polygon: rechteck(0, 0, 4000, 9000),
    raumKanten: [[[0, 0], [0, 9000]], [[4000, 0], [4000, 9000]]],
    vorhandene: [zeileVon([[0, 300], [4000, 300]])] }, "kueche");
  const [a, b] = ["hochschrank_herd", "kuehlschrank"].map((k) => rechteckVon(e.moebel.find((m) => m.symbol === k)));
  assert.ok(a.y0 < 2500 && b.y0 < 2500, JSON.stringify([a, b]));
  assert.ok(Math.abs(a.x0 - b.x0) < 1 && Math.min(Math.abs(a.y0 - b.y1), Math.abs(b.y0 - a.y1)) < 100, JSON.stringify([a, b]));
});

test("Kombiraum: ein Sofa haelt die Kueche nicht auf", () => {
  const sofa = { x0: 6000, y0: 5000, x1: 8500, y1: 6000, symbol: "sofa_3sitzer" };
  const keys = kombi("Wohnen / Essen / Kochen", [sofa]).moebel.map((m) => m.symbol);
  for (const key of KUECHE_TEILE) assert.ok(keys.includes(key), key);
  assert.ok(hatTisch(keys), keys.join(","));
});

test("Kombiraum: was schon steht, kommt nicht doppelt", () => {
  const tisch = { x0: 5000, y0: 3000, x1: 7000, y1: 4000, symbol: "esstisch" };
  const spuele = { x0: 2000, y0: 0, x1: 2600, y1: 600, symbol: "spuele" };
  const keys = kombi("Wohnen / Essen / Kochen", [tisch, spuele]).moebel.map((m) => m.symbol);
  assert.ok(!keys.includes("spuele") && !hatTisch(keys), keys.join(","));
  assert.ok(keys.includes("kochfeld"), keys.join(","));
});

test("Kombiraum: alles da -> schon eingerichtet", () => {
  const erst = kombi("Wohnen / Essen / Kochen");
  const vorhanden = erst.moebel.map((m) => ({ ...rechteckVon(m), symbol: m.symbol }));
  const e = kombi("Wohnen / Essen / Kochen", vorhanden);
  assert.deepEqual(e.moebel, []);
  assert.equal(e.uebersprungen[0].grund, "schon eingerichtet");
});

test("alle Raeume: ein schon eingerichteter Raum bleibt wie er ist", async () => {
  const vorhanden = [{ x0: 1000, y0: 1000, x1: 2000, y1: 2000 }];   // steht im Schlafzimmer
  const e = (await ALLE())({ raeume: RAEUME, oeffnungen: OEFF, vorhandene: vorhanden });
  assert.ok(!e.eingerichtet.includes("Eltern / Schlafen"));
  assert.match(e.uebersprungen.find((u) => u.name === "Eltern / Schlafen").grund, /schon/);
});

test("alle Raeume: nichts ueberlappt ueber Raumgrenzen, gleiche Eingabe gleiches Ergebnis", async () => {
  const f = await ALLE();
  const a = f({ raeume: RAEUME, oeffnungen: OEFF, vorhandene: [] });
  const b = f({ raeume: RAEUME, oeffnungen: OEFF, vorhandene: [] });
  assert.deepEqual(a, b);
  const rs = a.moebel.map((m) => rechteckVon(m));
  for (let i = 0; i < rs.length; i += 1) {
    for (let j = i + 1; j < rs.length; j += 1) {
      const u = rs[i], v = rs[j];
      const ueber = u.x0 < v.x1 - 5 && v.x0 < u.x1 - 5 && u.y0 < v.y1 - 5 && v.y0 < u.y1 - 5;
      if (ueber) {
        // nur innerhalb desselben Raums erlaubt (Stuehle unterm Tisch usw.)
        const raum = (r) => RAEUME.findIndex((x) => {
          const xs = x.polygon_mm.map((p) => p[0]), ys = x.polygon_mm.map((p) => p[1]);
          const cx = (r.x0 + r.x1) / 2, cy = (r.y0 + r.y1) / 2;
          return cx > Math.min(...xs) && cx < Math.max(...xs) && cy > Math.min(...ys) && cy < Math.max(...ys);
        });
        assert.equal(raum(u), raum(v), "Ueberlappung ueber Raumgrenze");
      }
    }
  }
});

test("die Naht: der Moebel-Schritt hat den Knopf", async () => {
  const { readFileSync } = await import("node:fs");
  const seite = readFileSync(new URL("../src/app/floorplan-workbench/page.tsx", import.meta.url), "utf8");
  assert.match(seite, /richteAlleRaeumeEin\(/);
  assert.match(seite, /Alle Räume einrichten/);
});

test("alle Raeume: die Treppe ist ein Hindernis, kein 'schon eingerichtet'", async () => {
  const f = await ALLE();
  const diele = [{ id: "d", name: "Diele", kind: "circulation", polygon_mm: rechteck(0, 0, 4000, 3000) }];
  const treppe = { x0: 0, y0: 1000, x1: 4000, y1: 2000 };   // quer durch die Diele
  const e = f({ raeume: diele, oeffnungen: [{ a: [3000, 3000], b: [3900, 3000], typ: "door" }],
                vorhandene: [], hindernisse: [treppe] });
  assert.deepEqual(e.eingerichtet, ["Diele"]);
  for (const m of e.moebel) {
    const r = rechteckVon(m);
    const ueber = r.x0 < treppe.x1 - 5 && treppe.x0 < r.x1 - 5 && r.y0 < treppe.y1 - 5 && treppe.y0 < r.y1 - 5;
    assert.ok(!ueber, `${m.symbol} steht auf der Treppe`);
  }
});

test("die Naht: der Knopf gibt die Treppe als Hindernis mit", async () => {
  const { readFileSync } = await import("node:fs");
  const seite = readFileSync(new URL("../src/app/floorplan-workbench/page.tsx", import.meta.url), "utf8");
  assert.match(seite, /hindernisse/);
});

// --- KUECHE-EINRICHTEN-AN-ZEILE-001 ------------------------------------------
// Rainer, 2026-10-30: "küche bracuht kücheninsel kochfeld spüle hohschrank fridge".

function inselVon(e) {
  const m = e.moebel.find((x) => x.symbol === "kuecheninsel");
  return m ? rechteckVon(m) : null;
}

test("Kueche: alle fuenf Teile, nichts gemeldet", () => {
  const poly = rechteck(0, 0, 5000, 4500);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon([[1200, 300], [3800, 300]])] }, "kueche");
  assert.deepEqual(e.moebel.map((m) => m.symbol).sort(),
    ["hochschrank_herd", "kochfeld", "kuecheninsel", "kuehlschrank", "spuele"]);
  assert.deepEqual(e.weggelassen, []);
});

test("Kueche: Insel parallel zur Zeile, 1100 mm Gang, zwei Gegenecken", () => {
  const poly = rechteck(0, 0, 5000, 4500);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon([[1200, 300], [3800, 300]])] }, "kueche");
  const m = e.moebel.find((x) => x.symbol === "kuecheninsel");
  assert.equal(m.points_mm.length, 2);
  const r = rechteckVon(m);
  assert.equal(r.y0 - 600, 1100);
  assert.equal(r.x1 - r.x0, 2000);
  assert.equal(r.y1 - r.y0, 1000);
});

test("Kueche: Kuehlschrank ganz aussen, Hochschrank an der Zeile", () => {
  const poly = rechteck(0, 0, 5000, 4500);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon([[1200, 300], [3800, 300]])] }, "kueche");
  const x = (k) => e.moebel.find((m) => m.symbol === k).position_mm[0];
  assert.ok(Math.abs(x("kuehlschrank") - 2500) > Math.abs(x("hochschrank_herd") - 2500));
});

test("Kueche: hohe Geraete zeigen zur Raumseite, an allen vier Waenden", () => {
  const poly = rechteck(0, 0, 6000, 6000);
  const faelle = [
    [[[1500, 300], [4500, 300]], 0],     // Oberkante, vorn = +y
    [[[1500, 5700], [4500, 5700]], 180], // Unterkante, vorn = -y
    [[[300, 1500], [300, 4500]], 270],   // links, vorn = +x
    [[[5700, 1500], [5700, 4500]], 90],  // rechts, vorn = -x
  ];
  for (const [punkte, drehung] of faelle) {
    const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon(punkte)] }, "kueche");
    for (const k of ["kuehlschrank", "hochschrank_herd"]) {
      assert.equal(e.moebel.find((m) => m.symbol === k).rotation_deg, drehung, `${k} ${JSON.stringify(punkte)}`);
    }
  }
});

test("Kueche: zweiter Klick setzt nichts doppelt", () => {
  const poly = rechteck(0, 0, 5000, 4500);
  const zeile = zeileVon([[1200, 300], [3800, 300]]);
  const erst = richteBereichEin({ polygon: poly, vorhandene: [zeile] }, "kueche");
  const da = erst.moebel.map((m) => ({ ...rechteckVon(m), symbol: m.symbol, points_mm: m.points_mm }));
  const zweit = richteBereichEin({ polygon: poly, vorhandene: [zeile, ...da] }, "kueche");
  assert.deepEqual(zweit.moebel, []);
});

test("Kueche: L-Zeile sperrt nur ihre Schenkel, Teile stehen nicht in der Ecke", () => {
  const poly = rechteck(0, 0, 6000, 5000);
  const e = richteBereichEin({ polygon: poly,
    vorhandene: [zeileVon([[300, 2500], [300, 300], [3500, 300]])] }, "kueche");
  const by = Object.fromEntries(e.moebel.map((m) => [m.symbol, m]));
  for (const k of ["spuele", "kochfeld", "hochschrank_herd", "kuehlschrank", "kuecheninsel"]) {
    assert.ok(by[k], `${k} fehlt: ${e.weggelassen.join(",")}`);
  }
  // Der laengste Schenkel laeuft in x; die Ecke (0..600) bleibt frei.
  for (const k of ["spuele", "kochfeld"]) {
    assert.equal(by[k].rotation_deg, 0);
    assert.ok(rechteckVon(by[k]).x0 >= 595, `${k} in der Ecke`);
  }
});

test("Kueche: 50 mm schiefe Zeile, wie von Hand gezeichnet", () => {
  const poly = rechteck(0, 0, 5000, 4500);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon([[1200, 330], [3800, 280]])] }, "kueche");
  assert.ok(e.moebel.some((m) => m.symbol === "spuele"), e.weggelassen.join(","));
  assert.ok(e.moebel.every((m) => (m.rotation_deg || 0) === 0));
});

test("Kueche: Zeile von Wand zu Wand -> hohe Geraete an eine freie Wand", () => {
  const poly = rechteck(0, 0, 3500, 4500);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon([[0, 300], [3500, 300]])] }, "kueche");
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.includes("kuehlschrank") && keys.includes("hochschrank_herd"),
            `${keys.join(",")} / ${e.weggelassen.join(",")}`);
  pruefeGrundregeln(e, poly);
});

test("Kueche: Fenster am Zeilenende -> kein hohes Geraet davor", () => {
  const poly = rechteck(0, 0, 5000, 4500);
  const fenster = [{ a: [3800, 0], b: [5000, 0], typ: "window" }];
  const e = richteBereichEin({ polygon: poly, oeffnungen: fenster,
    vorhandene: [zeileVon([[1800, 300], [3800, 300]])] }, "kueche");
  for (const k of ["kuehlschrank", "hochschrank_herd"]) {
    const m = e.moebel.find((x) => x.symbol === k);
    assert.ok(m, `${k} fehlt: ${e.weggelassen.join(",")}`);
    assert.ok(m.position_mm[0] < 3800, `${k} vor dem Fenster`);
  }
});

test("Kueche: zu wenig Platz fuer die Insel -> gemeldet", () => {
  const poly = rechteck(0, 0, 4500, 3000);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon([[1000, 300], [3500, 300]])] }, "kueche");
  assert.equal(inselVon(e), null);
  assert.ok(e.weggelassen.includes("Kücheninsel (zu wenig Platz)"), e.weggelassen.join(","));
});

test("Kueche: fremde Zeile im Nachbarraum zaehlt nicht", () => {
  const poly = rechteck(0, 0, 4000, 4000);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon([[6000, 300], [8000, 300]])] }, "kueche");
  assert.ok(e.moebel.some((m) => m.symbol === "spuele"), e.weggelassen.join(","));
  for (const m of e.moebel) assert.ok(liegtIn(rechteckVon(m), poly), m.symbol);
});

test("Alle Raeume: Kueche mit nur einer Zeile wird eingerichtet, mit mehr nicht", () => {
  const raeume = [{ name: "Küche", polygon: rechteck(0, 0, 5000, 4500) }];
  const zeile = zeileVon([[1200, 300], [3800, 300]]);
  const nurZeile = richteAlleRaeumeEin({ raeume, vorhandene: [zeile] });
  assert.deepEqual(nurZeile.eingerichtet, ["Küche"]);
  const spuele = { x0: 2000, y0: 0, x1: 2600, y1: 600, symbol: "spuele" };
  const mehr = richteAlleRaeumeEin({ raeume, vorhandene: [zeile, spuele] });
  assert.deepEqual(mehr.eingerichtet, []);
  assert.equal(mehr.uebersprungen[0].grund, "schon eingerichtet");
});

// --- DUWC-DUSCHE-001 ---------------------------------------------------------
// Rainer, 2026-10-30: "when there is a DuWC why is hter no shower added".

test("DU-WC ist ein Duschbad, in jeder Schreibweise", () => {
  for (const name of ["DU-WC", "Du-WC", "Du/WC", "Du WC", "DuWC", "DUWC"]) {
    assert.equal(raumtypAusName(name), "duschbad", name);
  }
});

test("WC und Gaeste-WC bleiben WC", () => {
  for (const name of ["WC", "Gäste-WC", "Gaeste WC"]) assert.equal(raumtypAusName(name), "wc", name);
  assert.equal(raumtypAusName("Du/Bad"), "duschbad");
  assert.equal(raumtypAusName("Bad"), "bad");
});

test("DU-WC bekommt beim Einrichten eine Dusche", () => {
  const raeume = [{ name: "DU-WC", polygon: rechteck(0, 0, 2000, 2500) }];
  const e = richteAlleRaeumeEin({ raeume });
  const keys = e.moebel.map((m) => m.symbol);
  assert.ok(keys.some((k) => k.startsWith("dusche")), keys.join(","));
  assert.ok(keys.includes("wand_wc"), keys.join(","));
});

test("Kueche: enge Kueche -> Insel mit 800 mm Gang statt gar keiner", () => {
  // 3,1 m tief: nur die kleine Insel passt, und nur mit 800 mm Gang.
  const poly = rechteck(0, 0, 5000, 3100);
  const e = richteBereichEin({ polygon: poly, vorhandene: [zeileVon([[1200, 300], [3800, 300]])] }, "kueche");
  const r = inselVon(e);
  assert.ok(r, e.weggelassen.join(","));
  assert.equal(r.y0 - 600, 800);
  assert.equal(r.x1 - r.x0, 1200);
});

test("Kueche: Bereich neben der Zeile -> findet die Zeile im Raum", () => {
  // Rainer, 2026-10-30: "Kitchen einrichtung delivers nothing any more".
  // Der Bereich beginnt 200 mm neben der Zeile im selben grossen Raum.
  const raum = rechteck(0, 0, 9000, 7000);
  const zeile = zeileVon([[300, 500], [300, 4500]]);
  const e = richteBereichEin({ polygon: rechteck(800, 500, 3500, 4000), vorhandene: [zeile], raumPolygone: [raum] }, "kueche");
  const keys = e.moebel.map((m) => m.symbol);
  for (const k of ["spuele", "kochfeld"]) assert.ok(keys.includes(k), `${k}: ${e.weggelassen.join(",")}`);
});

test("Kueche: Zeile ragt aus dem Bereich -> Teile kommen trotzdem auf die Zeile", () => {
  const raum = rechteck(0, 0, 9000, 7000);
  const zeile = zeileVon([[300, 500], [300, 5500]]);
  const e = richteBereichEin({ polygon: rechteck(0, 2000, 4000, 2000), vorhandene: [zeile], raumPolygone: [raum] }, "kueche");
  const keys = e.moebel.map((m) => m.symbol);
  for (const k of ["spuele", "kochfeld"]) assert.ok(keys.includes(k), `${k}: ${e.weggelassen.join(",")}`);
});

test("Kueche: Zeile in einem anderen Raum zaehlt nicht", () => {
  const anderer = rechteck(0, 0, 3000, 4000);
  const hier = rechteck(3000, 0, 5000, 4000);
  const e = richteBereichEin({ polygon: hier, vorhandene: [zeileVon([[300, 500], [300, 3500]])],
                               raumPolygone: [anderer, hier] }, "kueche");
  assert.ok(e.moebel.some((m) => m.symbol === "spuele"), e.weggelassen.join(","));
  for (const m of e.moebel) assert.ok(liegtIn(rechteckVon(m), hier), m.symbol);
});

test("Kueche ohne Zeile: fensterlose Wand zuerst, hohe Geraete zusammen", () => {
  // twostorey_xvv2_2: lange Fensterwand oben, die Kueche gehoert an die Wand ohne Fenster.
  const poly = rechteck(0, 0, 8000, 6000);
  const oeffnungen = [{ a: [1500, 6000], b: [3000, 6000], typ: "window" },
                      { a: [5000, 6000], b: [6500, 6000], typ: "window" }];
  const e = richteBereichEin({ polygon: poly, oeffnungen }, "kueche");
  const by = Object.fromEntries(e.moebel.map((m) => [m.symbol, m]));
  assert.ok(by.spuele && by.kochfeld && by.hochschrank_herd && by.kuehlschrank, e.weggelassen.join(","));
  const y = (k) => (rechteckVon(by[k]).y0 + rechteckVon(by[k]).y1) / 2;
  for (const k of ["spuele", "kochfeld", "hochschrank_herd", "kuehlschrank"]) assert.ok(y(k) < 4000, `${k} an der Fensterwand`);
  const a = rechteckVon(by.hochschrank_herd);
  const b = rechteckVon(by.kuehlschrank);
  assert.ok(Math.abs((a.x0 + a.x1) - (b.x0 + b.x1)) / 2 + Math.abs((a.y0 + a.y1) - (b.y0 + b.y1)) / 2 <= 600);
});

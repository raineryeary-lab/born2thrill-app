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
  richteBereichEin, rechteckVon, raumtypAusName, TUER_FREIRAUM_MM, RAUMTYPEN,
} from "../src/lib/generator/moebel-vorschlag.mjs";

const rechteck = (x, y, w, h) => [[x, y], [x + w, y], [x + w, y + h], [x, y + h]];

function ueberlappen(a, b) {
  return a.x0 < b.x1 - 5 && b.x0 < a.x1 - 5 && a.y0 < b.y1 - 5 && b.y0 < a.y1 - 5;
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

test("Kueche: Zeile an der Wand, Hochschrank und Kuehlschrank am Ende, Spuele und Kochfeld drauf", () => {
  const poly = rechteck(0, 0, 4500, 3000);
  const e = richteBereichEin({ polygon: poly, oeffnungen: [{ a: [0, 1000], b: [0, 1900], typ: "door" }] }, "kueche");
  const by = Object.fromEntries(e.moebel.map((m) => [m.symbol, m]));
  for (const k of ["kuechenzeile", "kuehlschrank", "hochschrank_herd", "spuele", "kochfeld"]) {
    assert.ok(by[k], `${k} fehlt: ${Object.keys(by).join(",")} / ${e.weggelassen.join(",")}`);
  }
  // Die Mittellinie liegt 300 mm vor einer Wand.
  const [p, q] = by.kuechenzeile.points_mm;
  const aufWand = (p[1] === q[1] && (Math.abs(p[1] - 300) <= 1 || Math.abs(p[1] - 2700) <= 1))
               || (p[0] === q[0] && (Math.abs(p[0] - 300) <= 1 || Math.abs(p[0] - 4200) <= 1));
  assert.ok(aufWand, JSON.stringify(by.kuechenzeile.points_mm));
  // Spuele und Kochfeld liegen auf der Zeile, die hohen Geraete nicht.
  const zeile = rechteckVon(by.kuechenzeile);
  for (const k of ["spuele", "kochfeld"]) assert.ok(ueberlappen(rechteckVon(by[k]), zeile), `${k} nicht auf der Zeile`);
  for (const k of ["kuehlschrank", "hochschrank_herd"]) assert.ok(!ueberlappen(rechteckVon(by[k]), zeile), `${k} auf der Zeile`);
  pruefeGrundregeln(e, poly, ["kochfeld+kuechenzeile", "kuechenzeile+spuele"]);
});

test("Kueche: zu kurze Wand -> keine Zeile, Meldung", () => {
  const e = richteBereichEin({ polygon: rechteck(0, 0, 1000, 1000) }, "kueche");
  assert.equal(e.moebel.length, 0);
  assert.ok(e.weggelassen.includes("Küchenzeile"));
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
  // 2 m Wand: frueher Hochschrank + 1,4 m Platte ohne Kochfeld.
  const poly = rechteck(0, 0, 2000, 1500);
  const e = richteBereichEin({ polygon: poly }, "kueche");
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

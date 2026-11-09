/**
 * Zoomen im Grundriss-Editor -- die Rechenregeln.
 *
 * Rainer, 2026-08-31: "can we add a zoom to the furniture setting? it would be
 * easier to place the furniture."
 *
 * Die Zahlen unten sind die echten aus
 * german_catalog_review_bungalow_3_3_2_b_100_2: der Grundriss misst
 * 15000 x 12773 mm und steht auf 680 Bildpunkten Hoehe -- rund 19 mm je
 * Punkt. Ein Wand-WC ist 360 mm breit, also 19 Punkte.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { sichtKasten, zoomUmZeiger, zoomKlemmen, ZOOM_MIN, ZOOM_MAX }
  from "./sicht.mjs";

const HAUS = { minX: 0, minY: 0, width: 15000, height: 12773 };

test("ohne Sicht bleibt der Kasten, wie er ist", () => {
  assert.equal(sichtKasten(HAUS, null), HAUS);
});

test("Zoom 1 zeigt weiter alles", () => {
  assert.equal(sichtKasten(HAUS, { zoom: 1, cx: 7500, cy: 6386 }), HAUS);
});

test("Zoom 2 zeigt ein Viertel der Flaeche", () => {
  const k = sichtKasten(HAUS, { zoom: 2, cx: 7500, cy: 6386 });
  assert.equal(k.width, 7500);
  assert.equal(k.height, 12773 / 2);
  assert.equal(k.minX, 3750);
});

test("der Ausschnitt bleibt im Grundriss", () => {
  // Am Rand gezoomt -- sonst sieht man weisse Flaeche und sucht das Haus.
  const k = sichtKasten(HAUS, { zoom: 4, cx: -9000, cy: 99999 });
  assert.ok(k.minX >= HAUS.minX, `minX ${k.minX}`);
  assert.ok(k.minY + k.height <= HAUS.minY + HAUS.height + 1e-6,
            `unten ${k.minY + k.height}`);
});

test("Zoom wird begrenzt, nicht durchgereicht", () => {
  assert.equal(zoomKlemmen(0.2), ZOOM_MIN);
  assert.equal(zoomKlemmen(999), ZOOM_MAX);
  assert.equal(zoomKlemmen(Number.NaN), ZOOM_MIN);
});

test("der Punkt unter dem Zeiger bleibt unter dem Zeiger", () => {
  // Das ist der Sinn der Uebung: wer auf das Bad zeigt und zoomt, will das
  // Bad groesser sehen -- nicht die Mitte des Hauses.
  const anteil = { x: 0.25, y: 0.75 };
  const vorher = sichtKasten(HAUS, null);
  const zeigerX = vorher.minX + anteil.x * vorher.width;
  const zeigerY = vorher.minY + anteil.y * vorher.height;
  const sicht = zoomUmZeiger(HAUS, null, 4, anteil);
  const nachher = sichtKasten(HAUS, sicht);
  assert.ok(Math.abs((nachher.minX + anteil.x * nachher.width) - zeigerX) < 1,
            "x verrutscht");
  assert.ok(Math.abs((nachher.minY + anteil.y * nachher.height) - zeigerY) < 1,
            "y verrutscht");
});

test("bis auf Zoom 1 herausgezoomt heisst wieder alles zeigen", () => {
  assert.equal(zoomUmZeiger(HAUS, { zoom: 2, cx: 7500, cy: 6386 }, 1,
                            { x: 0.5, y: 0.5 }), null);
});

test("zweimal hintereinander um denselben Zeiger bleibt stabil", () => {
  const anteil = { x: 0.3, y: 0.3 };
  const eins = zoomUmZeiger(HAUS, null, 2, anteil);
  const zwei = zoomUmZeiger(HAUS, eins, 4, anteil);
  const k = sichtKasten(HAUS, zwei);
  const soll = { x: 0.3 * HAUS.width, y: 0.3 * HAUS.height };
  assert.ok(Math.abs((k.minX + anteil.x * k.width) - soll.x) < 1);
  assert.ok(Math.abs((k.minY + anteil.y * k.height) - soll.y) < 1);
});

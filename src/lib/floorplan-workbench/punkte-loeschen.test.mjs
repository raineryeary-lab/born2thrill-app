/**
 * Loeschen bei gewaehltem Punkt: nur der Punkt, nicht die ganze Zeile.
 * Rainer, 2026-11-03: "if one point on a küchenzeile is active and not the
 * whole zeile and i press on delete please just delete that one pont and not
 * the whole küchenzeile".
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { loeschZiel } from "./punkte-loeschen.mjs";

const zeile = [[0, 0], [3000, 0], [3000, 2000], [4000, 2000]];

test("ein Punkt gewaehlt: nur dieser Punkt geht", () => {
  assert.deepEqual(loeschZiel(zeile, [1]),
    { art: "punkte", punkte: [[0, 0], [3000, 2000], [4000, 2000]] });
});

test("mehrere Punkte gewaehlt: alle diese gehen", () => {
  assert.deepEqual(loeschZiel(zeile, [0, 3]), { art: "punkte", punkte: [[3000, 0], [3000, 2000]] });
});

test("nichts gewaehlt oder kein gezeichneter Lauf: das ganze Moebel wie bisher", () => {
  assert.deepEqual(loeschZiel(zeile, []), { art: "ganz" });
  assert.deepEqual(loeschZiel(undefined, [1]), { art: "ganz" });
});

test("unter zwei Punkte faellt der Lauf nie, auch nicht ins Ganze", () => {
  assert.deepEqual(loeschZiel([[0, 0], [1000, 0]], [0]), { art: "zuWenig" });
  assert.deepEqual(loeschZiel(zeile, [0, 1, 2]), { art: "zuWenig" });
});

test("ungueltige Indizes zaehlen nicht", () => {
  assert.deepEqual(loeschZiel(zeile, [9]), { art: "ganz" });
  assert.deepEqual(loeschZiel(zeile, [2, 2, 9]),
    { art: "punkte", punkte: [[0, 0], [3000, 0], [4000, 2000]] });
});

/**
 * Im Moebel-Schritt muss man speichern koennen.
 *
 * Rainer, 2026-08-30, zum dritten Mal derselbe Abbruch:
 *
 *     floor-0.json: die RAEUME dieses Geschosses wurden umgezeichnet, seit
 *     diese Moebel gesetzt wurden
 *
 * Der Handgriff lautet "im Moebel-Schritt einmal speichern". Nachgesehen:
 * `furniture/floor-0.json` trug weiter `updated_at 2026-08-29T08:05:48Z` und
 * die alte `geometry_identity` -- gespeichert wurde also nie.
 *
 * Der Grund ist nicht Vergesslichkeit. Im eingebetteten Moebel-Schritt
 * (`mode=furniture-embed`) blendet die Workbench alles ausser dem Plan aus:
 *
 *     .wb-embed > *:not(.wb-plan) { display:none !important; }
 *
 * Der Knopfbalken mit "Save draft" ist ein direktes Kind von `main` und faellt
 * damit mit heraus. Im Browser nachgemessen: 52 sichtbare Bedienelemente, alle
 * aus der Moebelpalette -- "Save draft" war NICHT darunter.
 *
 * Es war also unmoeglich, den Schritt abzuschliessen, und der Bauer hat
 * dreimal zu Recht dasselbe gemeldet.
 *
 * Codex hatte fuer diese Ansicht ausdruecklich "Geschossauswahl, Plan,
 * Moebelpalette, SPEICHERN, gut sichtbares Weiter zu Bauen" vorgesehen. Das
 * Speichern fehlte.
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const seite = readFileSync(
  new URL("../src/app/floorplan-workbench/page.tsx", import.meta.url), "utf8");

test("der Knopfbalken traegt eine eigene Klasse", () => {
  assert.match(seite, /className="[^"]*wb-aktionen/);
});

test("Save draft ist als der eine wichtige Knopf gekennzeichnet", () => {
  assert.match(seite, /wb-speichern[^"]*"[^>]*>Save draft|Save draft/);
  assert.match(seite, /className="[^"]*wb-speichern/);
});

test("die Ausblendregel laesst den Balken stehen", () => {
  // Vorher: `> *:not(.wb-plan)`. Jetzt muss .wb-aktionen ausgenommen sein.
  const regel = seite.match(/\.wb-embed > \*:not\([^)]*\)[^;]*display:none[^;]*;/);
  assert.ok(regel, "Ausblendregel nicht gefunden");
  assert.match(regel[0], /wb-aktionen/);
});

test("im eingebetteten Schritt bleibt nur Speichern uebrig", () => {
  // Validate/Approve/Reject/Export gehoeren in die volle Ansicht, nicht in
  // den Moebel-Schritt -- dort waere jeder davon ein Umweg oder ein Unfall.
  assert.match(seite, /\.wb-embed \.wb-aktionen button:not\(\.wb-speichern\)[^}]*display:none/);
});

test("die volle Ansicht behaelt alle Knoepfe", () => {
  // Die Regeln stehen in EMBED_CSS und gelten nur unter .wb-embed.
  const css = seite.slice(seite.indexOf("const EMBED_CSS"),
                          seite.indexOf("return <main"));
  for (const zeile of css.split("\n")) {
    if (zeile.includes("display:none")) {
      assert.match(zeile, /\.wb-embed/, `ohne .wb-embed: ${zeile.trim()}`);
    }
  }
});

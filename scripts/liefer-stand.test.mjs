/**
 * Was der Tab "Hochladen & Freigeben" sagt (LIEFERN-STATUS-SICHTBAR-001).
 *
 * Rainer, 2026-10-30: "wiseo sthet nicht 'jetzt hochladen' 'ist hochgeladen'
 * 'jetzt freigeben' 'ist freigegeben am...'"
 */
import { test } from "node:test";
import assert from "node:assert/strict";
import { lieferStand } from "../src/lib/floorplan-workbench/liefer-stand.mjs";

const fertig = { online: 10, fehlenLokal: 0, frei: 10, katalogOk: true,
  freigegebenAm: "2026-10-30T08:58:30" };

test("nichts online: Jetzt hochladen, Freigeben gesperrt", () => {
  const s = lieferStand({ ...fertig, online: 0, frei: 0, katalogOk: false, freigegebenAm: null });
  assert.equal(s.hochladen.stand, "offen");
  assert.equal(s.hochladen.text, "Jetzt hochladen");
  assert.equal(s.freigabe.stand, "gesperrt");
  assert.equal(s.freigabe.text, "Erst hochladen");
});

test("lokal fehlen Bilder: Jetzt hochladen mit Anzahl", () => {
  const s = lieferStand({ ...fertig, fehlenLokal: 3 });
  assert.equal(s.hochladen.stand, "teilweise");
  assert.equal(s.hochladen.text, "Jetzt hochladen");
  assert.equal(s.hochladen.detail, "3 Bilder fehlen noch");
  assert.equal(lieferStand({ ...fertig, fehlenLokal: 1 }).hochladen.detail, "1 Bild fehlt noch");
});

test("alles online: Ist hochgeladen", () => {
  const s = lieferStand(fertig);
  assert.equal(s.hochladen.stand, "erledigt");
  assert.equal(s.hochladen.text, "Ist hochgeladen");
  assert.equal(s.hochladen.detail, "10 Bilder");
});

test("online, nichts frei: Jetzt freigeben", () => {
  const s = lieferStand({ ...fertig, frei: 0, katalogOk: false, freigegebenAm: null });
  assert.equal(s.freigabe.stand, "offen");
  assert.equal(s.freigabe.text, "Jetzt freigeben");
});

test("teilweise frei: Jetzt freigeben mit Anzahl", () => {
  const s = lieferStand({ ...fertig, frei: 6 });
  assert.equal(s.freigabe.stand, "teilweise");
  assert.equal(s.freigabe.text, "Jetzt freigeben");
  assert.equal(s.freigabe.detail, "6 von 10 Bildern frei");
});

test("alles frei und Katalog ja: Ist freigegeben am Datum", () => {
  const s = lieferStand(fertig);
  assert.equal(s.freigabe.stand, "erledigt");
  assert.equal(s.freigabe.text, "Ist freigegeben am 30.10.2026");
});

test("ohne Datum: Ist freigegeben, Datum nicht erfasst", () => {
  for (const freigegebenAm of [null, "", "kaputt"]) {
    const s = lieferStand({ ...fertig, freigegebenAm });
    assert.equal(s.freigabe.text, "Ist freigegeben");
    assert.equal(s.freigabe.detail, "Datum nicht erfasst");
  }
});

test("Katalog offen: nie Ist freigegeben, auch wenn alle Bilder frei sind", () => {
  const s = lieferStand({ ...fertig, katalogOk: false });
  assert.equal(s.freigabe.stand, "offen");
  assert.equal(s.freigabe.text, "Jetzt freigeben");
});

test("Katalog unbekannt: nie Ist freigegeben", () => {
  const s = lieferStand({ ...fertig, katalogOk: null });
  assert.equal(s.freigabe.stand, "unbekannt");
  assert.notEqual(s.freigabe.text, "Jetzt freigeben");
});

test("neues Bild nach der Freigabe: zurueck auf Jetzt", () => {
  const s = lieferStand({ ...fertig, online: 11 });
  assert.equal(s.freigabe.stand, "teilweise");
  assert.equal(s.freigabe.detail, "10 von 11 Bildern frei");
  assert.equal(lieferStand({ ...fertig, fehlenLokal: 1 }).hochladen.stand, "teilweise");
});

test("Bilder laden noch: nicht fehlt, sondern wird geladen", () => {
  const s = lieferStand({ online: null, fehlenLokal: 0, frei: 0, katalogOk: null, freigegebenAm: null });
  assert.equal(s.hochladen.stand, "laedt");
  assert.equal(s.freigabe.stand, "laedt");
  assert.match(s.hochladen.text, /wird geladen/);
});

test("Katalog nicht erreichbar: Stand unbekannt", () => {
  const s = lieferStand({ online: 0, fehlenLokal: 0, frei: 0, katalogOk: null,
    freigegebenAm: null, bilderFehler: true });
  assert.equal(s.hochladen.stand, "unbekannt");
  assert.equal(s.freigabe.stand, "unbekannt");
  assert.match(s.hochladen.text, /unbekannt/);
});

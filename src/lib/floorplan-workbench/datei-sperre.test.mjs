// node src/lib/floorplan-workbench/datei-sperre.test.mjs
//
// Runde 5 (Codex N1/N3): das Ledger wird unter einer BETRIEBSSYSTEM-Sperre
// geschrieben, die ein Kindprozess (scripts/sperre-halten.py) haelt, solange
// sein Besitzer lebt. Kein Zeitablauf, keine Uebernahme -- die Tests hier
// laufen mit echten Kindprozessen.
import assert from "node:assert/strict";
import { mkdtemp, readFile, writeFile, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import { spawn } from "node:child_process";
import { osSperreHalten, ledgerLesen, ledgerAbgleichen, ledgerTransaktion } from "./datei-sperre.mjs";

const SKRIPT = resolve(import.meta.dirname, "..", "..", "..", "scripts", "sperre-halten.py");
const PYTHON = process.env.PYTHON_EXECUTABLE || "python";
const opts = (frist = 1500) => ({ python: PYTHON, skript: SKRIPT, fristMs: frist });

let n = 0;
async function fall(name, f) { await f(); n += 1; console.log("ok -", name); }

const ordner = await mkdtemp(join(tmpdir(), "sperre-"));
try {
  await fall("freie Sperre wird genommen und beim Loesen freigegeben", async () => {
    const pfad = join(ordner, "a.lock");
    const s = await osSperreHalten(pfad, opts());
    assert.equal(s.ok, true);
    await s.loesen();
    const wieder = await osSperreHalten(pfad, opts());
    assert.equal(wieder.ok, true);
    await wieder.loesen();
  });

  await fall("zweiter Bewerber bekommt BESETZT, solange der erste lebt", async () => {
    const pfad = join(ordner, "b.lock");
    const erste = await osSperreHalten(pfad, opts());
    assert.equal(erste.ok, true);
    const zweite = await osSperreHalten(pfad, opts(800));
    assert.equal(zweite.ok, false);
    assert.equal(zweite.grund, "besetzt");
    assert.match(zweite.text, /BESETZT/);
    await erste.loesen();
    const dritte = await osSperreHalten(pfad, opts());
    assert.equal(dritte.ok, true);
    await dritte.loesen();
  });

  await fall("kein Zeitablauf: eine 'uralte' Besitzerzeile aendert nichts, solange er lebt", async () => {
    const pfad = join(ordner, "c.lock");
    const erste = await osSperreHalten(pfad, opts());
    assert.equal(erste.ok, true);
    // Besitzerzeile so faelschen, als liefe die Sperre seit einer Stunde.
    // Die alte Generationen-Sperre haette nach 120 s uebernommen.
    const zeile = JSON.parse((await readFile(pfad, "utf8")).split("\n")[0]);
    await writeFile(pfad, JSON.stringify({ ...zeile, seit: Date.now() / 1000 - 3600 }) + "\n")
      .catch(() => {});   // Windows: Datei ist offen, Schreiben darf scheitern
    const zweite = await osSperreHalten(pfad, opts(800));
    assert.equal(zweite.ok, false);
    await erste.loesen();
  });

  await fall("drei Bewerber gleichzeitig auf eine freie Sperre: genau einer", async () => {
    const pfad = join(ordner, "d.lock");
    for (let runde = 0; runde < 3; runde++) {
      const alle = await Promise.all([1, 2, 3].map(() => osSperreHalten(pfad, opts(300))));
      const gewinner = alle.filter((s) => s.ok);
      assert.equal(gewinner.length, 1, `Runde ${runde}: ${gewinner.length} Besitzer`);
      for (const s of gewinner) await s.loesen();
    }
  });

  await fall("stirbt der Halter (kill), ist die Sperre frei", async () => {
    const pfad = join(ordner, "e.lock");
    const erste = await osSperreHalten(pfad, opts());
    assert.equal(erste.ok, true);
    erste.kind.kill("SIGKILL");
    await new Promise((r) => erste.kind.once("exit", r));
    const zweite = await osSperreHalten(pfad, opts(3000));
    assert.equal(zweite.ok, true);
    await zweite.loesen();
  });

  await fall("wartender Bewerber bekommt sie, sobald der erste loest", async () => {
    const pfad = join(ordner, "f.lock");
    const erste = await osSperreHalten(pfad, opts());
    const wartet = osSperreHalten(pfad, opts(5000));
    setTimeout(() => { erste.loesen(); }, 300);
    const zweite = await wartet;
    assert.equal(zweite.ok, true);
    await zweite.loesen();
  });

  await fall("fehlendes Skript: ok:false mit grund, kein Haenger", async () => {
    const s = await osSperreHalten(join(ordner, "g.lock"),
      { python: PYTHON, skript: join(ordner, "gibt-es-nicht.py"), fristMs: 500 });
    assert.equal(s.ok, false);
    assert.notEqual(s.grund, "besetzt");
  });

  // Ledger lesen (Codex Runde 5): nur FEHLEN darf ein leeres Ledger ergeben.
  await fall("Ledger lesen: fehlt -> leer, ok", async () => {
    const l = await ledgerLesen(join(ordner, "kein-ledger.json"));
    assert.deepEqual(l, { ok: true, ledger: {} });
  });

  await fall("Ledger lesen: kaputtes JSON -> Fehler, nicht {}", async () => {
    const pfad = join(ordner, "kaputt.json");
    await writeFile(pfad, '{"a": {"version": "1.');
    const l = await ledgerLesen(pfad);
    assert.equal(l.ok, false);
    assert.ok(l.fehler);
  });

  await fall("Ledger lesen: Liste statt Objekt -> Fehler", async () => {
    const pfad = join(ordner, "liste.json");
    await writeFile(pfad, "[]");
    assert.equal((await ledgerLesen(pfad)).ok, false);
  });

  await fall("Ledger lesen: Eintrag ohne version -> Fehler", async () => {
    const pfad = join(ordner, "schema.json");
    await writeFile(pfad, JSON.stringify({ a: { build: "x" } }));
    assert.equal((await ledgerLesen(pfad)).ok, false);
  });

  await fall("Ledger lesen: gueltig -> unveraendert", async () => {
    const pfad = join(ordner, "gut.json");
    const inhalt = { a: { version: "1.0", build: "b", seit: "s", zuletzt: "z" } };
    await writeFile(pfad, JSON.stringify(inhalt));
    assert.deepEqual(await ledgerLesen(pfad), { ok: true, ledger: inhalt });
  });

  await fall("Ledger: fremde Haeuser bleiben, eigenes neues Haus kommt dazu", () => {
    const platte = { a: { version: "1.0", build: "aa", seit: "s", zuletzt: "z" } };
    const { ledger, versionen } = ledgerAbgleichen(platte,
      new Map([["b", { build: "bb", jetzt: "T" }]]), { b: "bb" });
    assert.deepEqual(ledger.a, platte.a);
    assert.deepEqual(ledger.b, { version: "1.0", build: "bb", seit: "T", zuletzt: "T" });
    assert.equal(versionen.b, "1.0");
  });

  // Codex Runde 4, N3: ein verspaeteter Lauf darf eine neuere Version nicht
  // mit seiner alten ueberschreiben.
  await fall("Ledger: veralteter Schnappschuss ueberschreibt keine neuere Version", () => {
    const platte = { a: { version: "1.2", build: "neu", seit: "s", zuletzt: "z" } };
    const { ledger, versionen } = ledgerAbgleichen(platte,
      new Map([["a", { build: "alt", jetzt: "T" }]]), { a: "neu" });
    assert.deepEqual(ledger.a, platte.a);
    assert.equal(versionen.a, "1.2");
  });

  await fall("Ledger: gleicher Build auf der Platte bleibt unveraendert", () => {
    const platte = { a: { version: "1.1", build: "x", seit: "s", zuletzt: "z" } };
    const { ledger } = ledgerAbgleichen(platte, new Map([["a", { build: "x", jetzt: "T" }]]), { a: "x" });
    assert.deepEqual(ledger.a, platte.a);
  });

  await fall("Ledger: neuer Build zaehlt gegen den HEUTIGEN Platteneintrag hoch", () => {
    const platte = { a: { version: "1.1", build: "b1", seit: "s", zuletzt: "z" } };
    const { ledger } = ledgerAbgleichen(platte, new Map([["a", { build: "b2", jetzt: "T" }]]), { a: "b2" });
    assert.deepEqual(ledger.a, { version: "1.2", build: "b2", seit: "s", zuletzt: "T" });
  });

  await fall("Ledger: fehlendes Ledger (leer gelesen) beginnt mit den eigenen Eintraegen", () => {
    const { ledger } = ledgerAbgleichen({}, new Map([["x", { build: "xx", jetzt: "T" }]]), { x: "xx" });
    assert.deepEqual(Object.keys(ledger), ["x"]);
  });

  await fall("Ledger: ohne gueltige Platte wird nicht abgeglichen (wirft)", () => {
    assert.throws(() => ledgerAbgleichen(null, new Map(), {}));
  });

  // ---- Runde 6 (Codex Runde 5): Schreiben NUR im Sperr-Halter, als
  // Vergleichen-und-Tauschen. Node schreibt das Ledger nie selbst.
  const eintrag = (version, build) => ({ version, build, seit: "s", zuletzt: "z" });
  const topts = (frist = 3000) => ({ python: PYTHON, skript: SKRIPT, fristMs: frist });
  const lies = async (p) => JSON.parse(await readFile(p, "utf8"));

  await fall("Transaktion: schreibt den abgeglichenen Stand ueber den Halter", async () => {
    const pfad = join(ordner, "t1.json");
    await writeFile(pfad, JSON.stringify({ a: eintrag("2.4", "b4") }), "utf8");
    const r = await ledgerTransaktion(pfad, topts(), async (ledger) => {
      assert.equal(ledger.a.version, "2.4");
      return { ledger: { ...ledger, a: eintrag("2.5", "b5") }, versionen: { a: "2.5" } };
    });
    assert.equal(r.ok, true);
    assert.equal(r.geschrieben, true);
    assert.deepEqual(r.versionen, { a: "2.5" });
    assert.equal((await lies(pfad)).a.version, "2.5");
  });

  await fall("Transaktion: fehlendes Ledger kommt als {} und wird angelegt", async () => {
    const pfad = join(ordner, "t2.json");
    const r = await ledgerTransaktion(pfad, topts(), async (ledger) => {
      assert.deepEqual(ledger, {});
      return { ledger: { x: eintrag("1.0", "xx") }, versionen: { x: "1.0" } };
    });
    assert.equal(r.geschrieben, true);
    assert.equal((await lies(pfad)).x.version, "1.0");
  });

  // Codex Runde 5, genau das Szenario: A liest 2.4, As Halter stirbt, B
  // schreibt 2.5, A darf danach NICHTS mehr schreiben.
  await fall("Transaktion: stirbt der Halter von A, kann A nicht mehr schreiben (B behaelt 2.5)", async () => {
    const pfad = join(ordner, "t3.json");
    await writeFile(pfad, JSON.stringify({ a: eintrag("2.4", "b4") }), "utf8");
    const a = await ledgerTransaktion(pfad, topts(), async (ledger, { kind }) => {
      assert.equal(ledger.a.version, "2.4");
      const tot = new Promise((r) => kind.once("close", r));
      kind.kill();
      await tot;
      const b = await ledgerTransaktion(pfad, topts(), async (l) => {
        assert.equal(l.a.version, "2.4");
        return { ledger: { ...l, a: eintrag("2.5", "b5") }, versionen: { a: "2.5" } };
      });
      assert.equal(b.geschrieben, true);
      return { ledger: { ...ledger, a: eintrag("2.4", "b4-alt") }, versionen: { a: "2.4" } };
    });
    assert.equal(a.ok, false);
    assert.notEqual(a.geschrieben, true);
    const platte = await lies(pfad);
    assert.equal(platte.a.version, "2.5");
    assert.equal(platte.a.build, "b5");
  });

  await fall("Transaktion: nichts zu schreiben (null) laesst die Datei unberuehrt", async () => {
    const pfad = join(ordner, "t4.json");
    const vorher = JSON.stringify({ a: eintrag("1.1", "x") });
    await writeFile(pfad, vorher, "utf8");
    const r = await ledgerTransaktion(pfad, topts(), async () => null);
    assert.equal(r.ok, true);
    assert.equal(r.geschrieben, false);
    assert.equal(await readFile(pfad, "utf8"), vorher);
  });

  await fall("Transaktion: kaputtes Ledger wird nicht ueberschrieben (ledger_fehler)", async () => {
    const pfad = join(ordner, "t5.json");
    await writeFile(pfad, "{kaputt", "utf8");
    let gerufen = false;
    const r = await ledgerTransaktion(pfad, topts(), async () => { gerufen = true; return null; });
    assert.equal(r.ok, false);
    assert.equal(r.grund, "ledger_fehler");
    assert.equal(gerufen, false);
    assert.equal(await readFile(pfad, "utf8"), "{kaputt");
  });

  await fall("Transaktion: besetzte Sperre -> nichts geschrieben", async () => {
    const pfad = join(ordner, "t6.json");
    await writeFile(pfad, JSON.stringify({ a: eintrag("1.0", "x") }), "utf8");
    const halter = await osSperreHalten(`${pfad}.oslock`, opts());
    assert.equal(halter.ok, true);
    try {
      const r = await ledgerTransaktion(pfad, topts(500), async () => {
        throw new Error("darf nicht laufen");
      });
      assert.equal(r.ok, false);
      assert.equal(r.grund, "besetzt");
    } finally {
      await halter.loesen();
    }
  });

  // Der Halter selbst: falsche Basis -> VERALTET, ABBRUCH -> nichts,
  // kein JSON-Objekt -> VERWEIGERT. Direkt ueber das Protokoll.
  async function halterProtokoll(pfad, zeile) {
    const kind = spawn(PYTHON, [SKRIPT, `${pfad}.oslock`, "--frist", "3", "--ledger", pfad],
      { stdio: ["pipe", "pipe", "pipe"] });
    let aus = "";
    kind.stdout.on("data", (c) => { aus += String(c); });
    while (!/^LEDGER /m.test(aus)) await new Promise((r) => setTimeout(r, 20));
    const kopf = JSON.parse(aus.split("\n").find((l) => l.startsWith("LEDGER ")).slice(7));
    kind.stdin.end(typeof zeile === "function" ? zeile(kopf) : zeile);
    await new Promise((r) => kind.once("close", r));
    return { aus, kopf };
  }

  await fall("Halter: falsche Basis -> VERALTET, Datei unveraendert", async () => {
    const pfad = join(ordner, "h1.json");
    const vorher = JSON.stringify({ a: eintrag("1.0", "x") });
    await writeFile(pfad, vorher, "utf8");
    const { aus } = await halterProtokoll(pfad,
      JSON.stringify({ basis: "0".repeat(64), inhalt: JSON.stringify({ a: eintrag("9.9", "y") }) }) + "\n");
    assert.match(aus, /VERALTET/);
    assert.doesNotMatch(aus, /GESCHRIEBEN/);
    assert.equal(await readFile(pfad, "utf8"), vorher);
  });

  await fall("Halter: ABBRUCH schreibt nichts", async () => {
    const pfad = join(ordner, "h2.json");
    const vorher = JSON.stringify({ a: eintrag("1.0", "x") });
    await writeFile(pfad, vorher, "utf8");
    const { aus } = await halterProtokoll(pfad, "ABBRUCH\n");
    assert.doesNotMatch(aus, /GESCHRIEBEN/);
    assert.equal(await readFile(pfad, "utf8"), vorher);
  });

  await fall("Halter: Inhalt ohne JSON-Objekt wird verweigert", async () => {
    const pfad = join(ordner, "h3.json");
    const vorher = JSON.stringify({ a: eintrag("1.0", "x") });
    await writeFile(pfad, vorher, "utf8");
    const { aus } = await halterProtokoll(pfad,
      (kopf) => JSON.stringify({ basis: kopf.basis, inhalt: "[1, 2]" }) + "\n");
    assert.match(aus, /VERWEIGERT/);
    assert.equal(await readFile(pfad, "utf8"), vorher);
  });

  await fall("Halter: richtige Basis -> GESCHRIEBEN", async () => {
    const pfad = join(ordner, "h4.json");
    await writeFile(pfad, JSON.stringify({ a: eintrag("1.0", "x") }), "utf8");
    const { aus } = await halterProtokoll(pfad,
      (kopf) => JSON.stringify({ basis: kopf.basis, inhalt: JSON.stringify({ a: eintrag("1.1", "y") }) }) + "\n");
    assert.match(aus, /GESCHRIEBEN/);
    assert.equal((await lies(pfad)).a.version, "1.1");
  });
} finally {
  await rm(ordner, { recursive: true, force: true });
}
console.log(`${n} Faelle ok`);

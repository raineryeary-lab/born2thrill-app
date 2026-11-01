// BAU-STOPPEN-001 (Rainer, 2026-11-01): "a stop build button on the build tab".
import test from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { GESTOPPT_CODE, laeuftBau, lauf, stoppen } from "./pipeline-lauf.mjs";

const PYTHON = process.env.PYTHON_EXECUTABLE || "python";

function warte(ms) {
  return new Promise((r) => setTimeout(r, ms));
}

function lebt(pid) {
  const zeilen = execFileSync("tasklist", ["/FI", `PID eq ${pid}`, "/NH"], { encoding: "latin1" });
  return zeilen.includes(String(pid));
}

test("Stoppen beendet den ganzen Baum, auch den Enkel (Blender)", async () => {
  const ordner = mkdtempSync(join(tmpdir(), "bau-stoppen-"));
  try {
    const enkel = join(ordner, "enkel.py");
    const pidDatei = join(ordner, "enkel.pid");
    writeFileSync(enkel, `import os, time\nopen(${JSON.stringify(pidDatei)}, "w").write(str(os.getpid()))\ntime.sleep(60)\n`);
    const kind = join(ordner, "kind.py");
    writeFileSync(kind, `import subprocess, sys\nsubprocess.run([sys.executable, ${JSON.stringify(enkel)}])\n`);

    const ergebnis = lauf(PYTHON, [kind], ordner, undefined, "haus_a");
    let pid = "";
    for (let i = 0; i < 100 && !pid; i += 1) {
      await warte(100);
      try { pid = readFileSync(pidDatei, "utf8"); } catch { /* noch nicht */ }
    }
    assert.ok(pid, "Enkel ist nicht gestartet");
    assert.equal(laeuftBau("haus_a"), true);

    assert.equal(stoppen("haus_a"), true);
    const fertig = await ergebnis;
    assert.equal(fertig.code, GESTOPPT_CODE);
    assert.equal(fertig.gestoppt, true);
    assert.match(fertig.ausgabe, /GESTOPPT/);
    assert.equal(laeuftBau("haus_a"), false);
    await warte(300);
    assert.equal(lebt(pid), false);
  } finally {
    rmSync(ordner, { recursive: true, force: true });
  }
});

test("Stoppen ohne Lauf meldet nur: nichts da", () => {
  assert.equal(stoppen("haus_ohne_lauf"), false);
});

test("Ein fertiger Lauf steht nicht mehr im Verzeichnis", async () => {
  const fertig = await lauf(PYTHON, ["-c", "print('ok')"], tmpdir(), undefined, "haus_b");
  assert.equal(fertig.code, 0);
  assert.match(fertig.ausgabe, /ok/);
  assert.equal(laeuftBau("haus_b"), false);
});

test("Ohne Schluessel steht ein Lauf nicht im Verzeichnis", async () => {
  const ergebnis = lauf(PYTHON, ["-c", "import time; time.sleep(0.3)"], tmpdir());
  assert.equal(stoppen("undefined"), false);
  assert.equal((await ergebnis).code, 0);
});

test("Zeitlimit bleibt Code 124", async () => {
  const fertig = await lauf(PYTHON, ["-c", "import time; time.sleep(30)"], tmpdir(), 300);
  assert.equal(fertig.code, 124);
  assert.equal(fertig.zeitlimit, true);
  assert.notEqual(fertig.gestoppt, true);
});

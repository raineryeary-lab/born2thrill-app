// Ledger-Sperre und Ledger-Abgleich fuer die Statusroute (ZUVERLAESSIGKEIT-001).
//
// Bauen/Hochladen sperrt go.py selbst (scripts/os_sperre.py). Fuer das
// fertig-Ledger haelt seit Runde 5 ebenfalls das BETRIEBSSYSTEM die Sperre:
// Node kann das nicht, also haelt ein Kindprozess (scripts/sperre-halten.py)
// sie fuer die Route, bis die Route stdin schliesst oder stirbt.
//
// Warum nicht mehr die Generationen-Dateien der Runde 4 (Codex Runde 5, N1):
// die nahmen einer Sperre nach 120 s die Gueltigkeit, ohne den alten
// Besitzer am Schreiben hindern zu koennen. Ein langsamer, aber LEBENDER
// Schreiber konnte so das Ledger eines neueren ueberschreiben. Eine
// Betriebssystem-Sperre laeuft nicht ab: sie gehoert dem Halter, bis er
// loest oder stirbt.
import { readFile } from "node:fs/promises";
import { spawn } from "node:child_process";
import { naechsteFertigVersion } from "./house-state.mjs";

/**
 * Betriebssystem-Sperre auf `pfad` nehmen, gehalten von sperre-halten.py.
 *
 * @param {string} pfad
 * @param {{python?: string, skript: string, fristMs?: number}} optionen
 * @returns {Promise<{ok: true, kind, loesen: () => Promise<void>}
 *                 | {ok: false, grund: "besetzt" | "fehler", text: string}>}
 */
export function osSperreHalten(pfad, { python = "python", skript, fristMs = 10_000 } = {}) {
  return new Promise((fertig) => {
    let erledigt = false;
    let aus = "";
    let err = "";
    const sekunden = Math.max(0.1, fristMs / 1000).toFixed(2);
    let kind;
    try {
      kind = spawn(python, [skript, pfad, "--frist", sekunden], { stdio: ["pipe", "pipe", "pipe"] });
    } catch (e) {
      fertig({ ok: false, grund: "fehler", text: String(e) });
      return;
    }
    const ende = (wert) => {
      if (erledigt) return;
      erledigt = true;
      clearTimeout(wache);
      fertig(wert);
    };
    // Wartet das Kind selbst hoechstens fristMs, plus Startzeit von Python.
    const wache = setTimeout(() => {
      try { kind.kill(); } catch { /* schon weg */ }
      ende({ ok: false, grund: "fehler", text: "sperre-halten.py antwortet nicht" });
    }, fristMs + 15_000);
    kind.stdout.on("data", (c) => {
      aus += String(c);
      if (aus.includes("GESPERRT")) {
        const zu = new Promise((r) => {
          if (kind.exitCode !== null || kind.signalCode !== null) r(undefined);
          else kind.once("close", () => r(undefined));
        });
        ende({
          ok: true,
          kind,
          async loesen() {
            try { kind.stdin.end(); } catch { /* schon zu */ }
            await zu;
          },
        });
      }
    });
    kind.stderr.on("data", (c) => { if (err.length < 4000) err += String(c); });
    kind.stdin.on("error", () => { /* Kind schon beendet */ });
    kind.on("error", (e) => ende({ ok: false, grund: "fehler", text: String(e) }));
    kind.on("close", (code) => {
      if (aus.includes("BESETZT")) ende({ ok: false, grund: "besetzt", text: aus.trim() });
      else ende({ ok: false, grund: "fehler", text: (err || aus || `Ausgang ${code}`).trim() });
    });
  });
}

/**
 * Das Ledger von der Platte lesen (Codex Runde 5).
 * Nur eine FEHLENDE Datei ergibt ein leeres Ledger. Unlesbar, kaputtes JSON
 * oder ein falsches Schema ist ein Fehler: dann wird nicht geschrieben,
 * sonst ersetzte ein voruebergehender Lesefehler die ganze Geschichte durch
 * ein Teil-Ledger, das wieder bei 1.0 anfaengt.
 *
 * @returns {Promise<{ok: true, ledger: object} | {ok: false, fehler: string}>}
 */
export async function ledgerLesen(pfad) {
  let text;
  try {
    text = await readFile(pfad, "utf8");
  } catch (e) {
    if (e && e.code === "ENOENT") return { ok: true, ledger: {} };
    return { ok: false, fehler: `Ledger unlesbar: ${e && e.message ? e.message : e}` };
  }
  return ledgerAusText(text);
}

/** Ledger-Text pruefen (dieselbe Regel fuer ledgerLesen und den Halter). */
export function ledgerAusText(text) {
  let daten;
  try {
    daten = JSON.parse(text.replace(/^﻿/, ""));
  } catch (e) {
    return { ok: false, fehler: `Ledger kaputt: ${e && e.message ? e.message : e}` };
  }
  if (!daten || typeof daten !== "object" || Array.isArray(daten)) {
    return { ok: false, fehler: "Ledger hat kein gueltiges Format (kein Objekt)" };
  }
  for (const [plan, eintrag] of Object.entries(daten)) {
    if (!eintrag || typeof eintrag !== "object" || typeof eintrag.version !== "string") {
      return { ok: false, fehler: `Ledger hat kein gueltiges Format (Eintrag ${plan})` };
    }
  }
  return { ok: true, ledger: daten };
}

/**
 * Eine Ledger-Transaktion: lesen, abgleichen, schreiben -- das Schreiben
 * erledigt der Sperr-Halter selbst (sperre-halten.py --ledger), als
 * Vergleichen-und-Tauschen gegen genau die Bytes, die er vorher gelesen hat.
 *
 * Codex Runde 5: schrieb Node selbst, konnte der Halter sterben, Node lief
 * weiter und schrieb ohne Sperre einen aelteren Stand ueber einen neueren.
 * Jetzt gilt: stirbt der Halter vor "GESCHRIEBEN", ist nichts geschrieben.
 *
 * abgleich(ledger, {kind}) -> {ledger, versionen} | null (nichts zu tun)
 *
 * @param {string} ledgerPfad
 * @param {{python?: string, skript: string, fristMs?: number, sperrPfad?: string}} optionen
 * @param {(ledger: Record<string, any>, ctx: {kind: any}) =>
 *   Promise<{ledger: object, versionen: object} | null> | {ledger: object, versionen: object} | null} abgleich
 * @returns {Promise<{ok: true, geschrieben: boolean, versionen?: object}
 *   | {ok: false, grund: "besetzt"|"fehler"|"ledger_fehler"|"veraltet", text: string}>}
 */
export function ledgerTransaktion(ledgerPfad, { python = "python", skript, fristMs = 10_000,
  sperrPfad = `${ledgerPfad}.oslock` } = {}, abgleich) {
  return new Promise((fertig) => {
    let erledigt = false;
    let aus = "";
    let err = "";
    let phase = "warten"; // warten -> abgleich -> gesendet
    let versionen;
    let abgleichLaeuft = null;
    const sekunden = Math.max(0.1, fristMs / 1000).toFixed(2);
    let kind;
    try {
      kind = spawn(python, [skript, sperrPfad, "--frist", sekunden, "--ledger", ledgerPfad],
        { stdio: ["pipe", "pipe", "pipe"] });
    } catch (e) {
      fertig({ ok: false, grund: "fehler", text: String(e) });
      return;
    }
    const ende = (wert) => {
      if (erledigt) return;
      erledigt = true;
      clearTimeout(wache);
      try { kind.stdin.end(); } catch { /* schon zu */ }
      fertig(wert);
    };
    const wache = setTimeout(() => {
      try { kind.kill(); } catch { /* schon weg */ }
      ende({ ok: false, grund: "fehler", text: "sperre-halten.py antwortet nicht" });
    }, fristMs + 60_000);
    const senden = (zeile) => {
      try { kind.stdin.write(zeile + "\n"); } catch { /* Kind tot: close meldet */ }
    };
    kind.stdout.on("data", async (c) => {
      aus += String(c);
      if (phase === "warten") {
        const kopfZeile = aus.split("\n").find((l) => l.startsWith("LEDGER "));
        if (!kopfZeile || !aus.includes("\n", aus.indexOf("LEDGER "))) return;
        phase = "abgleich";
        let kopf;
        try { kopf = JSON.parse(kopfZeile.slice(7)); } catch (e) {
          senden("ABBRUCH");
          ende({ ok: false, grund: "fehler", text: `Halter-Antwort unlesbar: ${e}` });
          return;
        }
        if (kopf.fehler) {
          senden("ABBRUCH");
          ende({ ok: false, grund: "ledger_fehler", text: kopf.fehler });
          return;
        }
        const gelesen = kopf.text === null ? { ok: true, ledger: {} } : ledgerAusText(kopf.text);
        if (!gelesen.ok) {
          senden("ABBRUCH");
          ende({ ok: false, grund: "ledger_fehler", text: gelesen.fehler });
          return;
        }
        let ergebnis;
        try {
          abgleichLaeuft = Promise.resolve().then(() => abgleich(gelesen.ledger, { kind }));
          ergebnis = await abgleichLaeuft;
        } catch (e) {
          senden("ABBRUCH");
          ende({ ok: false, grund: "fehler", text: `Abgleich fehlgeschlagen: ${e && e.message ? e.message : e}` });
          return;
        }
        if (!ergebnis) {
          senden("ABBRUCH");
          ende({ ok: true, geschrieben: false });
          return;
        }
        versionen = ergebnis.versionen;
        phase = "gesendet";
        senden(JSON.stringify({ basis: kopf.basis, inhalt: JSON.stringify(ergebnis.ledger, null, 2) }));
        return;
      }
      if (phase === "gesendet") {
        if (/^GESCHRIEBEN$/m.test(aus)) ende({ ok: true, geschrieben: true, versionen });
        else if (/^VERALTET$/m.test(aus)) ende({ ok: false, grund: "veraltet", text: "Ledger hat sich geaendert" });
        else if (/^VERWEIGERT/m.test(aus)) ende({ ok: false, grund: "fehler", text: aus.trim() });
      }
    });
    kind.stderr.on("data", (c) => { if (err.length < 4000) err += String(c); });
    kind.stdin.on("error", () => { /* Kind schon beendet */ });
    kind.on("error", (e) => ende({ ok: false, grund: "fehler", text: String(e) }));
    kind.on("close", async (code) => {
      // Ohne "GESCHRIEBEN" ist NICHTS geschrieben -- auch wenn der Halter
      // waehrend des Abgleichs starb (Codex Runde 5). Erst den laufenden
      // Abgleich zu Ende laufen lassen, dann melden.
      if (abgleichLaeuft) { try { await abgleichLaeuft; } catch { /* gemeldet */ } }
      if (aus.includes("BESETZT")) ende({ ok: false, grund: "besetzt", text: aus.trim() });
      else ende({ ok: false, grund: "fehler",
                  text: (err || `Sperr-Halter beendet (Ausgang ${code}), nichts geschrieben`).trim() });
    });
  });
}

/**
 * Ledger unter der Sperre abgleichen (Codex Runde 4, N3).
 *
 * platte:   das HEUTE auf der Platte stehende Ledger (frisch, mit ledgerLesen)
 * wuensche: Map plan -> { build, jetzt } aus dieser Anfrage
 * aktuell:  plan -> Build-Kennung des Manifests, unter der Sperre neu gelesen
 *
 * Ein Wunsch, dessen Build nicht mehr dem heutigen Manifest entspricht,
 * stammt aus einem veralteten Schnappschuss und wird verworfen. Die Version
 * zaehlt immer gegen den heutigen Platteneintrag hoch, nie gegen den Stand
 * vor der Sperre.
 */
export function ledgerAbgleichen(platte, wuensche, aktuell) {
  // Nur ein gueltig gelesenes Ledger (ledgerLesen) wird abgeglichen. Ein
  // null aus einem Lesefehler hier still zu {} zu machen war der Fehler.
  if (!platte || typeof platte !== "object" || Array.isArray(platte)) {
    throw new Error("ledgerAbgleichen: kein gueltig gelesenes Ledger");
  }
  const ledger = { ...platte };
  const versionen = {};
  for (const [plan, { build, jetzt }] of wuensche) {
    const vorher = ledger[plan] || null;
    if ((aktuell?.[plan] ?? "") !== (build ?? "")) {
      if (vorher) versionen[plan] = vorher.version;
      continue;
    }
    const naechste = naechsteFertigVersion(vorher, build);
    if (!vorher || naechste.version !== vorher.version || (!vorher.build && build)) {
      ledger[plan] = { version: naechste.version, seit: vorher?.seit || jetzt, zuletzt: jetzt,
                       build: naechste.build || build };
    }
    versionen[plan] = ledger[plan].version;
  }
  return { ledger, versionen };
}

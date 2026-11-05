// Ein Pipeline-Prozess mit Zeitlimit -- und beim Bau mit Stopp von aussen.
// BAU-STOPPEN-001, Rainer 2026-11-01: "a stop build button on the build tab,
// in case i made a mistake and want to change it".
import { spawn } from "node:child_process";

/** Nach dem Abbruch hoechstens so lange auf "close" warten: ein Enkel, der
 *  die Pipes noch offen haelt, darf die Antwort nicht ewig aufhalten. */
const NACHLAUF_MS = 15_000;

export const GESTOPPT_CODE = 130;

// Auf globalThis: Next laedt die Route im Betrieb neu, der Bau laeuft weiter.
const laeufe = (globalThis.__pipelineLaeufe ??= new Map());

/** Den ganzen Prozessbaum beenden: go.py startet publish-renders.py als Kind,
 *  und kill() traefe unter Windows nur den aeusseren Python-Prozess. */
function beenden(kind) {
  const pid = kind.pid;
  if (!pid) return;
  // Runde 2 (Codex): taskkill kann selbst scheitern (nicht startbar, Exit
  // != 0). Dann wenigstens den aeusseren Prozess direkt beenden.
  const direkt = () => { try { kind.kill("SIGKILL"); } catch { /* weg */ } };
  if (process.platform === "win32") {
    const tk = spawn("taskkill", ["/pid", String(pid), "/T", "/F"], { windowsHide: true });
    tk.on("error", direkt);
    tk.on("exit", (code) => { if (code !== 0) direkt(); });
  } else {
    try { process.kill(-pid, "SIGKILL"); } catch { direkt(); }
  }
}

/** `schluessel`: unter diesem Namen laesst sich der Lauf stoppen. */
export function lauf(befehl, args, cwd, zeitlimitMs, schluessel) {
  return new Promise((fertig) => {
    const kind = spawn(befehl, args, { cwd, windowsHide: true });
    let ausgabe = "";
    let abgebrochen = false;
    let gestoppt = false;
    let erledigt = false;
    let nachlauf = null;
    const ende = (ergebnis) => {
      if (erledigt) return;
      erledigt = true;
      if (uhr) clearTimeout(uhr);
      if (nachlauf) clearTimeout(nachlauf);
      if (schluessel) laeufe.delete(schluessel);
      fertig(ergebnis);
    };
    const sammeln = (d) => { ausgabe += d.toString("utf8"); };
    const uhr = zeitlimitMs
      ? setTimeout(() => {
          abgebrochen = true;
          ausgabe += `\nZEITLIMIT: nach ${Math.round(zeitlimitMs / 60_000)} min abgebrochen. `
            + "Ob etwas angekommen ist, zeigt der Katalog -- erst nachsehen, dann erneut versuchen.\n";
          beenden(kind);
          nachlauf = setTimeout(() => ende({ code: 124, ausgabe, zeitlimit: true }), NACHLAUF_MS);
        }, zeitlimitMs)
      : null;
    if (schluessel) {
      laeufe.set(schluessel, () => {
        if (gestoppt || abgebrochen) return;
        gestoppt = true;
        ausgabe += "\nGESTOPPT: Der Bau wurde von Hand abgebrochen.\n";
        beenden(kind);
        nachlauf = setTimeout(() => ende({ code: GESTOPPT_CODE, ausgabe, gestoppt: true }), NACHLAUF_MS);
      });
    }
    kind.stdout.on("data", sammeln);
    kind.stderr.on("data", sammeln);
    kind.on("close", (code) => {
      if (gestoppt) ende({ code: GESTOPPT_CODE, ausgabe, gestoppt: true });
      else ende({ code: abgebrochen ? 124 : (code ?? -1), ausgabe, zeitlimit: abgebrochen || undefined });
    });
    kind.on("error", (e) => {
      ende({ code: -1, ausgabe: ausgabe + String(e) });
    });
  });
}

export function laeuftBau(schluessel) {
  return laeufe.has(schluessel);
}

/** true, wenn ein Lauf gestoppt wurde; false, wenn keiner lief. */
export function stoppen(schluessel) {
  const stopp = laeufe.get(schluessel);
  if (!stopp) return false;
  stopp();
  return true;
}

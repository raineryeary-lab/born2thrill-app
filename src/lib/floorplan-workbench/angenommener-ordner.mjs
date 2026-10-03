/**
 * Welcher Lieferordner ist DER Ordner eines Hauses?
 *
 * Rainer, 2026-08-29: "why is this not working, i do not understand how there
 * can be any confusion into where the stuff is saved."
 *
 * Die Antwort ist: vier Stellen im Code haben sich je einen eigenen
 * Ordnernamen ausgedacht, zu verschiedenen Zeiten, und keine wusste von den
 * anderen --
 *
 *     make-codex-job.py      schreibt in den Auftrag  codex-<plan>-<datum>
 *     publish/route.ts       las fuer den Bilder-Tab  codex-final-*, neuester
 *     state/route.ts         zaehlte fuer den Status  codex-final-*
 *     codex-rueckgabe/route  kopiert nach             codex-final-<stempel>
 *
 * Seit dem 2026-08-27 gibt es eine Wahrheit je Haus: `renders/ANGENOMMEN.json`,
 * geschrieben von `lieferung-pruefen.py --annehmen`. Nur war sie zuerst bloss
 * an den Pruefer und den Upload angeschlossen; der Bilder-Tab riet weiter und
 * fand die sechs angenommenen Bilder von `3_3_1` nicht, weil sie nicht
 * `codex-final-` heissen.
 *
 * Diese Datei ist die eine Stelle, die die Frage beantwortet. Wer wissen will,
 * welcher Ordner gilt, fragt hier -- und raet nicht am Namen.
 */

import { readdir, readFile } from "node:fs/promises";

/** Der Zeiger eines Hauses, oder null. */
export async function angenommenerZeiger(rendersOrdner) {
  if (!rendersOrdner) return null;
  try {
    return JSON.parse(await readFile(`${rendersOrdner}/ANGENOMMEN.json`, "utf8"));
  } catch {
    return null;
  }
}

/**
 * Der Ordnername, der gilt.
 *
 * Ohne Zeiger die alte Regel: `codex-final-*`, der alphabetisch letzte. Sie
 * bleibt eine Falle -- `bungalow_039` hatte acht solcher Ordner, und
 * alphabetisch schlaegt `codex-final-2026-08-26-v2` das juengere
 * `codex-final-2026-08-26-2110`. Genau deshalb gibt es den Zeiger. Die alte
 * Regel steht hier nur, damit Haeuser ohne Zeiger nicht ueber Nacht leer
 * werden.
 */
export function ordnerAusZeiger(zeiger, ordnerNamen) {
  if (zeiger?.ordner) return zeiger.ordner;
  const alt = (ordnerNamen || [])
    .filter((name) => name.startsWith("codex-final-"))
    .sort();
  return alt.at(-1) || null;
}

/** Beides zusammen: den Zeiger lesen und den Ordner bestimmen. */
export async function angenommenerOrdner(rendersOrdner) {
  if (!rendersOrdner) return null;
  const zeiger = await angenommenerZeiger(rendersOrdner);
  const namen = await readdir(rendersOrdner).catch(() => []);
  return ordnerAusZeiger(zeiger, namen);
}

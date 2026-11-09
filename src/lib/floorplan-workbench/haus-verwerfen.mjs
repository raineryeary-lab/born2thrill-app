/**
 * Schlechte Grundrisse verwerfen (haus-verwerfen-v1).
 * Rainer, 2026-11-06: "floorplans that are just shitty so I can delete them".
 *
 * Verschiebt projects/<plan> nach projects/_verworfen/<plan>. Loescht nie --
 * dieser Baum ist kein Git-Repo, ein Fehlklick kostete sonst ein Haus.
 * Zurueck: Ordner wieder herausziehen.
 */
import { mkdir, rename, stat } from "node:fs/promises";
import { join } from "node:path";

export const VERWORFEN = "_verworfen";

export function planNameOk(plan) {
  return typeof plan === "string" && /^[A-Za-z0-9][A-Za-z0-9._-]*$/.test(plan) && !plan.includes("..");
}

async function gibtEs(pfad) {
  try { await stat(pfad); return true; } catch { return false; }
}

export async function hausVerwerfen({ projects, plan, veroeffentlicht = false, imBau = false }) {
  if (!planNameOk(plan)) return { ok: false, fehler: "Unzulässiger Planname." };
  if (veroeffentlicht) return { ok: false, fehler: `${plan} ist im Katalog veröffentlicht – erst im Katalog entfernen.` };
  if (imBau) return { ok: false, fehler: `Für ${plan} läuft gerade ein Bau – erst abwarten oder stoppen.` };
  const quelle = join(projects, plan);
  try {
    if (!(await stat(quelle)).isDirectory()) return { ok: false, fehler: `${plan} ist kein Ordner.` };
  } catch {
    return { ok: false, fehler: `${plan} gibt es nicht (mehr).` };
  }
  const ziel = join(projects, VERWORFEN);
  await mkdir(ziel, { recursive: true });
  let name = plan;
  for (let i = 1; await gibtEs(join(ziel, name)); i += 1) name = `${plan}-${i}`;
  await rename(quelle, join(ziel, name));
  return { ok: true, verschoben_nach: join(ziel, name) };
}

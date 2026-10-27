/**
 * Eine .blend-Datei aus dem Codex-Auftrag in Blenders eigenem Fenster
 * oeffnen, damit man sie ansehen kann bevor Codex daran arbeitet.
 *
 * Rainer, 2026-08-22: "place one button per blender fiel that has been
 * created so i can check what they look like before codex tries to render
 * them."
 *
 * Anders als jeder bisherige Blender-Aufruf in dieser Suite (immer
 * --background fuers Rendern): das hier startet Blender interaktiv, als
 * eigenen, losgeloesten Prozess. Die Antwort kommt sofort -- der Request
 * wartet nicht darauf, dass Rainer das Fenster wieder schliesst.
 */
import { spawn } from "node:child_process";
import { readdir } from "node:fs/promises";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

/** Nur lokal. Dieselbe Schranke wie die anderen Workbench-Routen. */
function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(
    request.headers.get("x-forwarded-host") || request.headers.get("host") || "",
  );
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(urlHost)
    && ["127.0.0.1", "localhost", "::1"].includes(headerHost);
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const body = await request.json().catch(() => ({}));
  const plan = String(body.plan || "");
  const datei = String(body.datei || "");

  if (!/^[A-Za-z0-9_.-]+$/.test(plan)) {
    return Response.json({ error: "Kein gültiger Plan." }, { status: 400 });
  }
  // Nur ein blosser Dateiname, keine Pfadbestandteile -- sonst waere "datei"
  // ein Weg, eine beliebige Datei ausserhalb dieses Ordners zu oeffnen.
  if (!/^[A-Za-z0-9_.-]+\.blend$/i.test(datei)) {
    return Response.json({ error: "Kein gültiger Dateiname." }, { status: 400 });
  }

  const _konfiguriert = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!_konfiguriert) {
    throw new Error("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- "
      + "verweigere, den Datenordner zu erraten. Siehe .env.local.");
  }
  const dataRoot = resolve(_konfiguriert);
  const ordner = join(dataRoot, "corrections", plan, "renders", "go-baseline");

  // Die Datei muss WIRKLICH in diesem Ordner liegen -- ein plausibler Name
  // allein reicht nicht, sonst koennte "datei" auf eine Datei zeigen, die
  // gar nicht zu diesem Auftrag gehoert.
  const vorhanden = await readdir(ordner).catch(() => [] as string[]);
  if (!vorhanden.includes(datei)) {
    return Response.json({ error: `${datei} liegt nicht in ${ordner}.` }, { status: 404 });
  }

  const blenderExe = process.env.FLOORPLAN_BLENDER_EXE?.trim()
    || String.raw`C:\Program Files\Blender Foundation\Blender 5.0\blender.exe`;
  const pfad = join(ordner, datei);

  try {
    const kind = spawn(blenderExe, [pfad], { detached: true, stdio: "ignore", windowsHide: false });
    kind.unref();
  } catch (fehler) {
    return Response.json({ error: `Blender liess sich nicht starten: ${String(fehler)}` },
      { status: 500 });
  }

  return Response.json({ ok: true, pfad }, { headers: { "Cache-Control": "no-store" } });
}

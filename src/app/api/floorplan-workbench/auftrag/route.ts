/**
 * Den Codex-Auftrag ausliefern, damit er auf der Seite steht statt im Explorer.
 *
 * Rainer, 2026-08-20: "you gae me that link C:\...\go-baseline". Ein Ordnerpfad
 * ist keine Antwort -- er muesste ihn suchen, oeffnen, die Datei finden und den
 * Text herauskopieren. Der Auftrag ist Text; Text kann die Seite zeigen.
 */
import { readFile, readdir } from "node:fs/promises";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(
    request.headers.get("x-forwarded-host") || request.headers.get("host") || "",
  );
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(urlHost)
    && ["127.0.0.1", "localhost", "::1"].includes(headerHost);
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const plan = new URL(request.url).searchParams.get("plan") || "";
  if (!/^[A-Za-z0-9_.-]+$/.test(plan)) {
    return Response.json({ error: "Kein gültiger Plan." }, { status: 400 });
  }

  const suite = resolve(process.cwd(), "..");
  // Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein
  // stiller Rueckfall auf den alten C:-Nachbarordner wuerde unbemerkt
  // gegen veraltete Daten arbeiten (Codex-Review desselben Tages).
  const _konfiguriert = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!_konfiguriert) {
    throw new Error("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- "
      + "verweigere, den Datenordner zu erraten. Siehe .env.local.");
  }
  const dataRoot = resolve(_konfiguriert);
  const ordner = join(dataRoot, "corrections", plan, "renders", "go-baseline");

  // Die .blend-Dateien, die Codex bekommen soll -- damit man sie sich vorher
  // selbst in Blender ansehen kann, statt Codex als erste Kontrolle zu
  // benutzen (Rainer, 2026-08-22: "place one button per blender fiel ...
  // so i can check what they look like before codex tries to render them").
  const dateien = await readdir(ordner).catch(() => [] as string[]);
  const blends = dateien.filter((n) => n.toLowerCase().endsWith(".blend")).sort();

  // Die Objektkarte: der Baseline-Render mit nummerierten Markern auf
  // Garderobe, Stuff und Sanitaer. Die Seite zeigt sie selbst -- ein
  // Dateiname allein hiesse wieder Explorer aufmachen.
  const karte = dateien.filter((n) => /^OBJEKTKARTE-.+\.png$/i.test(n)).sort()[0] || null;

  try {
    const vertrag = await readFile(join(ordner, "CODEX-AUFTRAG.md"), "utf8");
    // Das Regelwerk gehoert IN den kopierten Text, nicht nur als Datei daneben.
    // Der Knopf "Auftrag kopieren" ist der Weg, auf dem der Auftrag bei Codex
    // landet -- ein Verweis auf eine Datei, die dabei nicht mitkopiert wird,
    // waere fuer Codex unsichtbar (Rainer, 2026-08-26: "and now when i press
    // 'Auftrag schreiben' this will all be in there?").
    const regeln = await readFile(join(ordner, "CODEX-REGELN.md"), "utf8")
      .catch(() => "");
    const text = regeln
      ? `${vertrag}\n\n---\n\n${regeln}`
      : vertrag;
    return Response.json({ plan, ordner, text, blends, karte, regeln: Boolean(regeln) },
      { headers: { "Cache-Control": "no-store" } });
  } catch {
    return Response.json({ plan, ordner, text: null, blends, karte,
      hinweis: "Noch kein Auftrag geschrieben." },
      { headers: { "Cache-Control": "no-store" } });
  }
}

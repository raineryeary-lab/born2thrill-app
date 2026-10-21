/**
 * Die Objektkarte eines Auftrags ausliefern, damit sie auf der Hausseite
 * steht statt im Explorer.
 *
 * `make-codex-job.py` legt `OBJEKTKARTE-<stem>.png` neben die .blend: den
 * Baseline-Render mit nummerierten Markern auf Garderobe, Stuff und
 * Sanitaer. Ohne diese Route waere davon auf der Seite nur ein Dateiname in
 * einem Ordner zu sehen -- genau die Antwort, die Rainer am 2026-08-20 schon
 * einmal zurueckgewiesen hat ("you gave me that link ...\go-baseline").
 *
 * Der Dateiname kommt bewusst NICHT aus der Anfrage. Die Route sucht sich die
 * Karte im Ordner selbst; damit gibt es keinen Parameter, ueber den man aus
 * dem Ordner herauslaufen koennte.
 */
import { readdir, readFile } from "node:fs/promises";
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

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const plan = new URL(request.url).searchParams.get("plan") || "";
  if (!/^[A-Za-z0-9_.-]+$/.test(plan)) {
    return Response.json({ error: "Kein gültiger Plan." }, { status: 400 });
  }

  // Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein stiller
  // Rueckfall auf den alten Nachbarordner wuerde unbemerkt gegen veraltete
  // Daten arbeiten.
  const _konfiguriert = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!_konfiguriert) {
    throw new Error("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- "
      + "verweigere, den Datenordner zu erraten. Siehe .env.local.");
  }
  const ordner = join(resolve(_konfiguriert), "corrections", plan,
                      "renders", "go-baseline");

  const namen = await readdir(ordner).catch(() => [] as string[]);
  const datei = namen.filter((n) => /^OBJEKTKARTE-.+\.png$/i.test(n)).sort()[0];
  if (!datei) {
    return Response.json({ error: "Keine Objektkarte in " + ordner }, { status: 404 });
  }

  const bytes = await readFile(join(ordner, datei)).catch(() => null);
  if (!bytes) {
    return Response.json({ error: datei + " liess sich nicht lesen." }, { status: 500 });
  }
  return new Response(new Uint8Array(bytes), {
    headers: {
      "Content-Type": "image/png",
      // Die Karte wird bei jedem "Auftrag schreiben" neu gezeichnet. Eine
      // zwischengespeicherte alte Karte zeigte Marker auf Objekten, die es
      // nicht mehr gibt -- schlimmer als gar keine Karte.
      "Cache-Control": "no-store",
    },
  });
}

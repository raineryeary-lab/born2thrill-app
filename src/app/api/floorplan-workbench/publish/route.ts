/**
 * Push one reviewed render to the born2thrill catalogue.
 *
 * Rainer, 2026-08-18: "this page needs a way to upload to the wordpress site".
 * Until now that meant leaving the workbench, finding the file and running
 * publish-renders.py by hand.
 *
 * The link between a picture and its plan is the FILENAME: an attachment whose
 * slug starts with "<plan_id>-" belongs to that plan. So this route renames on
 * the way out and does nothing else clever — same convention as the script, no
 * second index to keep in step.
 *
 * Credentials come from the environment (WP_USER + WP_APP_PASSWORD, an
 * Application Password) and never from the browser. The page cannot upload to
 * anywhere except the configured site.
 *
 * The delivery folder's catalog.json carries a description_de, style, palette,
 * materials, rooms and features per image. All of it travels with the upload —
 * a picture in the media library with no words attached is not findable and
 * cannot be handed to a customer.
 *
 * GET  ?plan=<id>   what the site already holds for that plan
 * POST {root, path, plan}
 */
import { readFile, readdir } from "node:fs/promises";
import { angenommenerOrdner } from "@/lib/floorplan-workbench/angenommener-ordner.mjs";
import { basename, dirname, extname, join } from "node:path";
import { resolveAssetPath } from "@/lib/floorplan-workbench/inventory";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SITE = (process.env.B2T_SITE || "https://born2thrill.de").replace(/\/+$/, "");
const MIME: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
};

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

function credentials() {
  const user = process.env.WP_USER;
  const password = process.env.WP_APP_PASSWORD;
  if (!user || !password) return null;
  return `Basic ${Buffer.from(`${user}:${password.replace(/\s+/g, "")}`).toString("base64")}`;
}

/** WordPress' slug rules, near enough to predict what the upload will become. */
function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/-{2,}/g, "-").replace(/^-|-$/g, "");
}

function targetName(plan: string, file: string) {
  if (file.toLowerCase().startsWith(`${plan.toLowerCase()}-`)) return file;
  const extension = extname(file).toLowerCase();
  return `${plan}-${slugify(basename(file, extname(file)))}${extension}`;
}

type CatalogAsset = {
  asset_id?: string;
  file?: string;
  asset_type?: string;
  style?: string;
  description_de?: string;
  palette?: string[];
  materials?: string[];
  rooms_visible?: string[];
  features?: string[];
  qc_status?: string;
};

/** The delivery's own catalog, whichever of the two names it uses. */
async function sidecarAsset(imagePath: string): Promise<CatalogAsset | null> {
  const folder = dirname(imagePath);
  const file = basename(imagePath);
  for (const name of ["catalog.json", "selected-catalog.json"]) {
    try {
      const parsed = JSON.parse(await readFile(join(folder, name), "utf8"));
      const assets: CatalogAsset[] = Array.isArray(parsed?.assets) ? parsed.assets : [];
      const found = assets.find((asset) => asset.file === file);
      if (found) return found;
    } catch {
      // no catalog here, or unreadable -- try the next name
    }
  }
  return null;
}

function line(label: string, values?: string[] | string) {
  const text = Array.isArray(values) ? values.join(", ") : values;
  return text ? `${label}: ${text}` : null;
}

/** Everything the delivery knows about this picture, as media-library fields. */
function describe(asset: CatalogAsset | null, plan: string, file: string) {
  const title = asset?.asset_id ? `${plan} - ${asset.asset_id}` : `${plan} - ${basename(file, extname(file))}`;
  const caption = asset?.description_de || "";
  const detail = [
    line("Stil", asset?.style),
    line("Typ", asset?.asset_type),
    line("Farben", asset?.palette),
    line("Materialien", asset?.materials),
    line("Raeume", asset?.rooms_visible),
    line("Merkmale", asset?.features),
    line("QC", asset?.qc_status),
  ].filter(Boolean).join("\n");
  return {
    title,
    alt_text: caption || title,
    caption,
    description: [caption, detail].filter(Boolean).join("\n\n"),
  };
}

async function published(plan: string) {
  const response = await fetch(`${SITE}/wp-json/b2t/v1/bilder?plan=${encodeURIComponent(plan)}`, {
    cache: "no-store",
  });
  if (!response.ok) throw new Error(`catalogue lookup failed: HTTP ${response.status}`);
  return (await response.json()) as
    { id: number; name: string; full: string; send: boolean; cover?: boolean }[];
}

// Technische Render-Paesse, die neben den Bildern liegen — nie anzeigen.
const AUX_SUFFIXES = ["-depth", "-edge", "-mask", "-normal"];
// Arbeitsmittel, keine Bilder des Hauses. Die Objektkarte ist der
// Baseline-Render mit nummerierten Markern -- sie gehoert in den
// Codex-Auftrag, nicht in den Bilder-Tab und erst recht nicht in den
// Katalog (Rainer, 2026-08-27: "there is still one with numbers all
// over it how is that ok?").
const AUX_PREFIXES = ["reference-", "OBJEKTKARTE-"];

/**
 * Die frischen lokalen Renders eines Plans, aus renders/go-baseline/.
 *
 * Der Bilder-Tab zeigte AUSSCHLIESSLICH, was auf born2thrill.de liegt —
 * ein eben gebautes Haus war dort unsichtbar, und nach dem Attachment-
 * Verlust bei bungalow_039 stand der Tab fast leer, obwohl alle Renders
 * lokal existierten (Rainer, 2026-08-22: "where are the Bilder?").
 * Ausgeliefert werden die Dateien ueber die vorhandene, localhost-
 * gebundene Asset-Route (root=primary + Relativpfad), nicht ueber einen
 * neuen Serving-Pfad.
 */
async function imagesIn(relative: string, stufe: "final" | "rohbau") {
  const folder = resolveAssetPath("primary", relative);
  if (!folder) return [];
  const entries = await readdir(folder).catch(() => [] as string[]);
  return entries
    .filter((name) => {
      const extension = extname(name).toLowerCase();
      if (!MIME[extension]) return false;
      const stem = basename(name, extension);
      // Technische Paesse und Codex' eigene Referenz-Zwischenstaende raus.
      return !AUX_SUFFIXES.some((suffix) => stem.endsWith(suffix))
        && !AUX_PREFIXES.some((prefix) => stem.startsWith(prefix));
    })
    .sort()
    .map((name) => ({
      name: basename(name, extname(name)),
      stufe,
      url: `/api/floorplan-workbench/overview/asset?root=primary&path=${
        encodeURIComponent(`${relative}/${name}`)}&w=768`,
    }));
}

async function localRenders(plan: string) {
  if (!/^[A-Za-z0-9_.-]+$/.test(plan)) return [];
  const rendersRelative = `corrections/${plan}/renders`;

  // go-baseline sind ROHBAU-Nachweise: absichtlich weiss und materiallos,
  // Input fuer Codex, nie das Produkt ("those images are Bullshit" --
  // Rainer, 2026-08-22, nachdem der Tab sie als die Bilder des Hauses
  // zeigte und freigeben sie in den Katalog uebernahm). Das PRODUKT ist der
  // angenommene Satz -- welcher das ist, beantwortet angenommener-ordner.mjs.
  const rendersFolder = resolveAssetPath("primary", rendersRelative);
  let finals: Awaited<ReturnType<typeof imagesIn>> = [];
  if (rendersFolder) {
    // DER Ordner steht in `renders/ANGENOMMEN.json`. Die Entscheidung liegt
    // in einer einzigen Datei -- siehe angenommener-ordner.mjs, dort steht
    // auch, warum es sie gibt.
    const chosen = await angenommenerOrdner(rendersFolder);
    if (chosen) finals = await imagesIn(`${rendersRelative}/${chosen}`, "final");
  }
  const baseline = await imagesIn(`${rendersRelative}/go-baseline`, "rohbau");
  return [...finals, ...baseline];
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const parameters = new URL(request.url).searchParams;

  // ?plans=1 -> every plan_id the catalogue knows, so the page can offer real
  // ids instead of letting someone invent one. A typo here is the expensive
  // mistake: the upload succeeds and the pictures belong to nothing.
  if (parameters.get("plans")) {
    try {
      const response = await fetch(`${SITE}/wp-json/b2t/v1/grundrisse`, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const rows = (await response.json()) as { id: string }[];
      return Response.json({ plans: rows.map((row) => row.id) }, { headers: { "Cache-Control": "no-store" } });
    } catch (error) {
      return Response.json({ error: error instanceof Error ? error.message : String(error) }, { status: 502 });
    }
  }

  const plan = parameters.get("plan") || "";
  if (!plan) return Response.json({ error: "plan is required." }, { status: 400 });
  try {
    // Online-Katalog und lokale Renders unabhaengig: faellt WordPress aus,
    // bleiben die lokalen Bilder trotzdem sichtbar (und umgekehrt).
    const [images, local] = await Promise.all([
      published(plan).catch(() => [] as Awaited<ReturnType<typeof published>>),
      localRenders(plan),
    ]);
    return Response.json(
      { site: SITE, plan, configured: Boolean(credentials()), images, local },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : String(error) }, { status: 502 });
  }
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const authorization = credentials();
  if (!authorization) {
    return Response.json(
      { error: "Kein Zugang: WP_USER und WP_APP_PASSWORD fehlen. In born2thrill-local-workbench\.env.local eintragen und den Dev-Server neu starten." },
      { status: 503 },
    );
  }

  let body: Record<string, unknown>;
  try {
    body = JSON.parse(await request.text());
  } catch {
    return Response.json({ error: "Invalid JSON." }, { status: 400 });
  }

  const plan = String(body.plan || "").trim();
  if (!/^[A-Za-z0-9_-]+$/.test(plan)) {
    return Response.json({ error: "plan must be a plan_id." }, { status: 400 });
  }
  const absolute = resolveAssetPath(String(body.root || ""), String(body.path || ""));
  if (!absolute) return Response.json({ error: "Unknown asset." }, { status: 400 });

  const extension = extname(absolute).toLowerCase();
  if (!MIME[extension]) return Response.json({ error: `Not an image: ${extension}` }, { status: 400 });

  // A typo'd plan_id uploads fine and then the pictures belong to a record
  // nobody will ever search for. Refuse instead.
  let existing;
  try {
    existing = await published(plan);
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : String(error) }, { status: 502 });
  }

  const name = targetName(plan, basename(absolute));
  const slug = slugify(basename(name, extname(name))).replace(`${slugify(plan)}-`, "");
  const already = existing.find((image) => image.name === slug);
  if (already) {
    return Response.json({ ok: true, skipped: true, name, url: already.full, id: already.id });
  }

  const bytes = await readFile(absolute);
  const upload = await fetch(`${SITE}/wp-json/wp/v2/media`, {
    method: "POST",
    headers: {
      Authorization: authorization,
      "Content-Type": MIME[extension],
      "Content-Disposition": `attachment; filename="${name}"`,
    },
    body: new Uint8Array(bytes),
  });

  if (!upload.ok) {
    const detail = (await upload.text()).slice(0, 300);
    return Response.json({ error: `upload failed: HTTP ${upload.status}`, detail }, { status: 502 });
  }

  const media = (await upload.json()) as { id: number; source_url: string };

  // The bytes are up; now give the picture its words. A separate call because a
  // raw-body upload has no room for fields. A failure here is not fatal -- the
  // picture is already published -- so it is reported, not thrown.
  const fields = describe(await sidecarAsset(absolute), plan, name);
  let described = true;
  try {
    const patch = await fetch(`${SITE}/wp-json/wp/v2/media/${media.id}`, {
      method: "POST",
      headers: { Authorization: authorization, "Content-Type": "application/json" },
      body: JSON.stringify(fields),
    });
    described = patch.ok;
  } catch {
    described = false;
  }

  return Response.json({
    ok: true,
    skipped: false,
    name,
    id: media.id,
    url: media.source_url,
    described,
    caption: fields.caption,
  });
}

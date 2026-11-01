"use client";
/* eslint-disable @next/next/no-img-element */
/**
 * Overview tab: every render, plan, revision, furniture layout and annotation
 * package the suite has produced, newest first.
 *
 * Mostly reading, but no longer only reading: an image can be discarded
 * (moved to _verworfen/, never unlinked) and a whole package can be pushed to
 * the born2thrill catalogue in one go.
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import type {
  AssetRef,
  Inventory,
  ProjectEntry,
  RenderSet,
  RootKey,
  WorkbenchTree,
} from "@/lib/floorplan-workbench/inventory";

const ROOT_BADGE: Record<RootKey, { short: string; className: string }> = {
  primary: { short: "data root A", className: "bg-sky-100 text-sky-900 ring-1 ring-sky-300" },
  secondary: { short: "data root B", className: "bg-fuchsia-100 text-fuchsia-900 ring-1 ring-fuchsia-300" },
  annotations: { short: "annotator", className: "bg-stone-200 text-stone-800 ring-1 ring-stone-300" },
  deliveries: { short: "delivered", className: "bg-emerald-100 text-emerald-900 ring-1 ring-emerald-300" },
};

const READINESS: Record<ProjectEntry["readiness"], { label: string; className: string }> = {
  codex_ready: { label: "Codex-ready", className: "bg-emerald-600 text-white" },
  rendered_no_handoff: { label: "Rendered · no handoff", className: "bg-amber-500 text-black" },
  corrected: { label: "Corrected geometry only", className: "bg-blue-100 text-blue-900 ring-1 ring-blue-300" },
  annotated: { label: "Annotation only", className: "bg-stone-200 text-stone-700" },
  empty: { label: "Empty folder", className: "bg-red-100 text-red-800 ring-1 ring-red-300" },
};

type FilterId = "all" | "codex_ready" | "renders" | "revisions" | "furniture" | "exports"
  | "annotated" | "empty" | "env_todo" | "env_no_source" | "env_empty";

const FILTERS: { id: FilterId; label: string }[] = [
  { id: "env_todo", label: "Umgebung offen" },
  { id: "codex_ready", label: "Codex-ready" },
  { id: "renders", label: "Has renders" },
  { id: "revisions", label: "Has revisions" },
  { id: "furniture", label: "Has furniture" },
  { id: "exports", label: "Has exports" },
  { id: "annotated", label: "Annotation only" },
  { id: "empty", label: "Empty folders" },
  { id: "all", label: "Everything" },
];

/**
 * The annotator is a separate app (Flask, :8765) -- "sometimes in the workbench
 * I see things that need to be changed in the annotator again ... it's hard
 * jumping back and forth" (Rainer, 2026-08-18). Same project, one click.
 */
const ANNOTATOR = "http://127.0.0.1:8765";
const annotatorUrl = (projectId: string) =>
  `${ANNOTATOR}/annotate.html?project=${encodeURIComponent(projectId)}`;

function assetUrl(asset: AssetRef, width?: number) {
  const query = new URLSearchParams({ root: asset.root, path: asset.path });
  if (width) query.set("w", String(width));
  return `/api/floorplan-workbench/overview/asset?${query.toString()}`;
}

function shortTime(value: string | null | undefined) {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("de-DE", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

function megabytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} kB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function Chip({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <span className={`inline-block rounded-full px-2.5 py-1 text-xs font-semibold ${className || "bg-stone-100 text-stone-700"}`}>{children}</span>;
}

function RootChip({ root }: { root: RootKey }) {
  const badge = ROOT_BADGE[root];
  return <Chip className={badge.className}>{badge.short}</Chip>;
}

type Verdict = "accepted" | "changes_requested";
type ReviewEntry = { image: string; verdict: Verdict; note: string; decided_at: string };

/**
 * Accept / request changes on one image. Geometry had an approval gate; the
 * images Codex returns had none (Rainer, 2026-08-18: "where do i accept the
 * image and where do i ask for changes?"). The verdict is written to
 * review.json in the same folder as the image and its catalog.json, so the
 * delivery carries its own review.
 */
function ReviewControls({ asset }: { asset: AssetRef }) {
  const [entry, setEntry] = useState<ReviewEntry | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const query = new URLSearchParams({ root: asset.root, path: asset.path });
    fetch(`/api/floorplan-workbench/image-reviews?${query.toString()}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        const found = (data?.reviews || []).find((r: ReviewEntry) => r.image === asset.name);
        if (found) { setEntry(found); setNote(found.note || ""); }
      })
      .catch(() => undefined);
  }, [asset.root, asset.path, asset.name]);

  async function decide(verdict: Verdict) {
    setBusy(true);
    try {
      const response = await fetch("/api/floorplan-workbench/image-reviews", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root: asset.root, path: asset.path, verdict, note }),
      });
      if (response.ok) setEntry((await response.json()).entry);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mt-1">
      <div className="flex gap-1">
        <button
          type="button"
          disabled={busy}
          onClick={() => decide("accepted")}
          className={`flex-1 rounded px-1 py-0.5 text-[10px] ring-1 ${
            entry?.verdict === "accepted"
              ? "bg-emerald-600 text-white ring-emerald-700"
              : "bg-white text-emerald-800 ring-emerald-300 hover:bg-emerald-50"}`}
        >
          Accept
        </button>
        <button
          type="button"
          disabled={busy}
          onClick={() => setOpen((value) => !value)}
          className={`flex-1 rounded px-1 py-0.5 text-[10px] ring-1 ${
            entry?.verdict === "changes_requested"
              ? "bg-amber-500 text-black ring-amber-600"
              : "bg-white text-amber-800 ring-amber-300 hover:bg-amber-50"}`}
        >
          Changes
        </button>
      </div>
      {open && (
        <div className="mt-1">
          <textarea
            value={note}
            onChange={(event) => setNote(event.target.value)}
            placeholder="What has to change?"
            rows={2}
            className="w-full rounded border border-stone-300 p-1 text-[10px]"
          />
          <button
            type="button"
            disabled={busy}
            onClick={() => { void decide("changes_requested"); setOpen(false); }}
            className="mt-1 w-full rounded bg-amber-500 px-1 py-0.5 text-[10px] text-black"
          >
            Send back
          </button>
        </div>
      )}
      {entry && !open && (
        <p className="mt-0.5 truncate text-[10px] text-stone-500" title={entry.note}>
          {entry.verdict === "accepted" ? "accepted" : "changes"} · {shortTime(entry.decided_at)}
          {entry.note ? ` · ${entry.note}` : ""}
        </p>
      )}
    </div>
  );
}

/**
 * The trashcan. It moves the file into _verworfen/ next to it — this tree is
 * not a git repo, so an unlink here would be unrecoverable and a mis-click
 * would cost a render (Rainer: "check for a copy before deleting anything").
 */
function DiscardButton({ asset, onGone }: { asset: AssetRef; onGone: () => void }) {
  const [busy, setBusy] = useState(false);
  const [armed, setArmed] = useState(false);

  async function discard() {
    setBusy(true);
    try {
      const response = await fetch("/api/floorplan-workbench/discard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root: asset.root, path: asset.path }),
      });
      if (response.ok) onGone();
      else setArmed(false);
    } finally {
      setBusy(false);
    }
  }

  if (armed) {
    return (
      <div className="mt-1 flex gap-1">
        <button type="button" disabled={busy} onClick={() => void discard()}
          className="flex-1 rounded bg-red-600 px-1 py-0.5 text-[10px] text-white">
          {busy ? "…" : "Wirklich"}
        </button>
        <button type="button" onClick={() => setArmed(false)}
          className="rounded px-1 py-0.5 text-[10px] text-stone-600 ring-1 ring-stone-300">
          Nein
        </button>
      </div>
    );
  }
  return (
    <button
      type="button"
      onClick={() => setArmed(true)}
      title="Verwerfen — verschiebt die Datei nach _verworfen/, löscht sie nicht"
      className="mt-1 w-full rounded px-1 py-0.5 text-[10px] text-stone-500 ring-1 ring-stone-300 hover:bg-red-50 hover:text-red-700"
    >
      🗑 Verwerfen
    </button>
  );
}

function Thumbnail({ asset, review = false }: { asset: AssetRef; review?: boolean }) {
  const [gone, setGone] = useState(false);
  if (gone) return null;
  return (
    <div className="w-36 shrink-0">
      <a href={assetUrl(asset)} target="_blank" rel="noreferrer" className="block" title={`${asset.path} · ${megabytes(asset.bytes)} · ${shortTime(asset.modified_at)}`}>
        <img
          src={assetUrl(asset, 288)}
          alt={asset.name}
          loading="lazy"
          className="h-24 w-36 rounded-lg border border-stone-300 bg-white object-cover"
        />
        <span className="mt-1 block truncate text-[10px] text-stone-600">{asset.name}</span>
      </a>
      {review && <ReviewControls asset={asset} />}
      <DiscardButton asset={asset} onGone={() => setGone(true)} />
    </div>
  );
}

/** The site derives an attachment slug from the filename; mirror that here so
 *  the page can say which pictures are already up before anything is sent. */
function slugify(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9_-]+/g, "-").replace(/-{2,}/g, "-").replace(/^-|-$/g, "");
}

function expectedSlug(plan: string, fileName: string) {
  const stem = fileName.replace(/\.[^.]+$/, "");
  const prefix = `${slugify(plan)}-`;
  const slug = slugify(stem);
  return slug.startsWith(prefix) ? slug.slice(prefix.length) : slug;
}

type PublishedImage = { id: number; name: string; full: string; send: boolean };

/**
 * The 310 plan_ids the catalogue actually knows. Every package has to carry
 * one -- it is the only thing that tells the deliveries apart once the
 * pictures leave this machine. Offering the real list beats letting anyone
 * type an id that exists nowhere.
 */
let PLAN_CACHE: string[] | null = null;

/**
 * The outer wall and the surroundings were added to the pipeline late, so
 * almost every house still needs a pass in the annotator: measured 231 of 233
 * annotations carry no floor_scale, 230 no exterior_areas.
 *
 * Scale first — annotation_exterior_areas() bails on a missing scale before it
 * reads the areas, so surroundings drawn without a scale render as bare ground
 * and look like the drawing never saved.
 */
type EnvQueue = {
  ready: string[]; todo: string[]; no_source: string[];
  empty: string[]; blank: string[]; unreadable: string[];
};
let ENV_CACHE: EnvQueue | null = null;

function useEnvironmentQueue() {
  const [queue, setQueue] = useState(ENV_CACHE);
  useEffect(() => {
    if (ENV_CACHE) return;
    fetch("/api/floorplan-workbench/environment")
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (!data || data.error) return;
        ENV_CACHE = {
          ready: data.ready || [], todo: data.todo || [], no_source: data.no_source || [],
          empty: data.empty || [], blank: data.blank || [], unreadable: data.unreadable || [],
        };
        setQueue(ENV_CACHE);
      })
      .catch(() => undefined);
  }, []);
  return queue;
}

/**
 * "stuff thats already uploaded and projects where all of the entities have
 * been deleted we can just clear, that way we have just the new ones to work
 * with" — Rainer, 2026-08-18. Finished and emptied packages collapse to a
 * single line instead of filling the page. Nothing is hidden permanently: the
 * switch in the header brings them all back.
 */
const OpenOnlyContext = createContext(true);

function useCataloguePlans() {
  const [plans, setPlans] = useState<string[]>(PLAN_CACHE || []);
  useEffect(() => {
    if (PLAN_CACHE) return;
    fetch("/api/floorplan-workbench/publish?plans=1")
      .then((response) => (response.ok ? response.json() : null))
      .then((data) => {
        if (Array.isArray(data?.plans)) { PLAN_CACHE = data.plans; setPlans(data.plans); }
      })
      .catch(() => undefined);
  }, []);
  return plans;
}

/**
 * One package: its pictures, which of them are already on born2thrill, and one
 * button to push the rest. The plan_id is the only thing that has to be right —
 * it is what ties every picture to its catalogue record, and the route refuses
 * an id the catalogue does not know rather than parking pictures where nobody
 * will find them.
 */
export type PackageState = { total: number; left: number; done: boolean; emptied: boolean };

function PackagePanel({ images, defaultPlan, hintName = "", big = false, onState }:
  { images: AssetRef[]; defaultPlan: string; hintName?: string; big?: boolean;
    onState?: (state: PackageState) => void }) {
  const [plan, setPlan] = useState(defaultPlan);
  const [touched, setTouched] = useState(false);
  const [online, setOnline] = useState<PublishedImage[] | null>(null);
  const [configured, setConfigured] = useState(true);
  const [checking, setChecking] = useState(false);
  const [busy, setBusy] = useState(false);
  const [lines, setLines] = useState<string[]>([]);
  const [discarded, setDiscarded] = useState<string[]>([]);
  const knownPlans = useCataloguePlans();

  const shown = images.filter((image) => !discarded.includes(image.path));
  const known = knownPlans.length === 0 || knownPlans.includes(plan.trim());

  async function refresh(planId: string) {
    if (!planId.trim()) { setOnline(null); return; }
    setChecking(true);
    try {
      const response = await fetch(`/api/floorplan-workbench/publish?plan=${encodeURIComponent(planId)}`);
      if (!response.ok) { setOnline(null); return; }
      const data = await response.json();
      setOnline(data.images || []);
      setConfigured(data.configured !== false);
    } catch {
      setOnline(null);
    } finally {
      setChecking(false);
    }
  }

  // A delivery folder is named "<plan_id>-<what it is>-<date>", so the id is
  // sitting right there. Trust it only when it matches a plan the catalogue
  // really has -- guessing is what produces pictures attached to nothing.
  useEffect(() => {
    if (touched || knownPlans.length === 0) return;
    if (plan.trim() && knownPlans.includes(plan.trim())) return;
    const source = `${defaultPlan} ${hintName}`.trim();
    const inferred = knownPlans
      .filter((candidate) => source.startsWith(candidate) || hintName.startsWith(candidate))
      .sort((a, b) => b.length - a.length)[0];
    if (inferred && inferred !== plan) setPlan(inferred);
  }, [knownPlans, defaultPlan, hintName, touched, plan]);

  // One place refreshes, keyed on the id in the box. Two effects raced here and
  // the empty default kept wiping out the result of the inferred one, so the
  // panel claimed 0 uploaded for pictures that were already on the site.
  useEffect(() => { void refresh(plan); }, [plan]);

  const onlineSlugs = useMemo(() => new Set((online || []).map((image) => image.name)), [online]);
  const isUp = (asset: AssetRef) => Boolean(plan.trim()) && onlineSlugs.has(expectedSlug(plan, asset.name));
  const pending = shown.filter((asset) => !isUp(asset));

  // Report upward so a package with nothing left can be folded away. "done"
  // needs the catalogue answer in hand -- before it arrives every picture
  // looks pending, and a package would flicker into view and out again.
  useEffect(() => {
    onState?.({
      total: images.length,
      left: pending.length,
      done: online !== null && shown.length > 0 && pending.length === 0,
      emptied: shown.length === 0,
    });
  }, [images.length, pending.length, shown.length, online, onState]);

  async function publish() {
    setBusy(true);
    setLines([]);
    const done: string[] = [];
    for (const image of pending) {
      const response = await fetch("/api/floorplan-workbench/publish", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ root: image.root, path: image.path, plan }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) done.push(`x ${image.name} - ${data.error || response.status}`);
      else if (data.skipped) done.push(`. ${image.name} - war schon oben`);
      else done.push(`ok ${image.name}`);
      setLines([...done]);
      if (!response.ok && response.status === 503) break; // no credentials: stop, do not spam
    }
    setBusy(false);
    await refresh(plan);
  }

  return (
    <>
      <div className={`mt-3 flex gap-${big ? "3" : "2"} overflow-x-auto pb-1`}>
        {shown.map((image) => (
          <PackageShot
            key={image.path}
            asset={image}
            big={big}
            online={isUp(image)}
            onGone={() => setDiscarded((current) => [...current, image.path])}
          />
        ))}
      </div>

      <div className="mt-3 rounded-xl bg-white p-3 ring-1 ring-stone-200">
        <div className="flex flex-wrap items-center gap-2">
          <label className="text-xs font-semibold text-stone-700">plan_id</label>
          <input
            list="gk-plan-ids"
            value={plan}
            onChange={(event) => { setTouched(true); setPlan(event.target.value); }}
            placeholder="z. B. onehalfstorey_020"
            className={`w-56 rounded border px-2 py-1 font-mono text-xs ${
              plan.trim() && !known ? "border-red-500 bg-red-50" : "border-stone-300"}`}
          />
          <button
            type="button"
            disabled={busy || !configured || !plan.trim() || !known || pending.length === 0}
            onClick={() => void publish()}
            className="rounded-full bg-violet-700 px-3 py-1 text-xs font-semibold text-white disabled:bg-stone-300"
          >
            {busy ? "laedt hoch ..." : pending.length === 0 ? "alles hochgeladen" : `${pending.length} hochladen`}
          </button>
          <span className="text-xs text-stone-600">
            {checking ? "pruefe ..."
              : online === null ? (plan.trim() ? "Katalog nicht erreichbar" : "plan_id eintragen")
              : `${shown.length - pending.length}/${shown.length} auf der Website`}
          </span>
          <a href="https://born2thrill.de/grundriss-katalog/" target="_blank" rel="noreferrer"
            className="text-xs text-violet-700 underline">Katalog</a>
        </div>
        {!configured && (
          <p className="mt-1 text-xs text-amber-800">
            Der Dev-Server hat keine Zugangsdaten. WP_USER und WP_APP_PASSWORD in
            <code className="mx-1 font-mono">.env.local</code>
            eintragen und den Server neu starten.
          </p>
        )}
        {plan.trim() && !known && (
          <p className="mt-1 text-xs text-red-700">
            Diese plan_id steht nicht im Katalog. Hochladen wuerde die Bilder einem
            Datensatz zuordnen, den niemand findet.
          </p>
        )}
        {lines.length > 0 && (
          <ul className="mt-2 space-y-0.5 font-mono text-[10px] text-stone-600">
            {lines.map((line) => <li key={line}>{line}</li>)}
          </ul>
        )}
      </div>
    </>
  );
}

/**
 * Wraps one package. Renders it normally while there is work left; once every
 * picture is on the site — or every picture has been discarded — it collapses
 * to one line so the page shows only what still needs doing.
 */
function PackageBlock({ title, images, defaultPlan, hintName = "", big = false, children }:
  { title: string; images: AssetRef[]; defaultPlan: string; hintName?: string;
    big?: boolean; children?: React.ReactNode }) {
  const openOnly = useContext(OpenOnlyContext);
  const [state, setState] = useState<PackageState | null>(null);
  const [expanded, setExpanded] = useState(false);
  const onState = useCallback((next: PackageState) => setState(next), []);

  const folded = openOnly && !expanded && state !== null && (state.done || state.emptied);

  if (folded) {
    return (
      <button
        type="button"
        onClick={() => setExpanded(true)}
        className="flex w-full items-center gap-2 rounded-xl bg-stone-100 px-3 py-1.5 text-left text-xs text-stone-500 hover:bg-stone-200"
      >
        <span className="text-emerald-700">{state.emptied ? "leer" : "erledigt"}</span>
        <span className="truncate font-mono">{title}</span>
        <span className="ml-auto shrink-0">
          {state.emptied ? "alle verworfen" : `${state.total} Bilder auf der Website`} · zeigen
        </span>
      </button>
    );
  }

  return (
    <>
      {children}
      <PackagePanel
        images={images}
        defaultPlan={defaultPlan}
        hintName={hintName}
        big={big}
        onState={onState}
      />
    </>
  );
}

/**
 * The funnel, at the top, before the 292 rows.
 *
 * Rainer, 2026-08-18: "is there any way to show an overview of the annotator
 * and the files already annotated and the same with the workbench?" — there
 * was, but only as 292 cards you had to count yourself. Each stage is a real
 * count over the same inventory the list below uses, and each one filters the
 * list when clicked, so "which ones?" is one click from "how many?".
 */
/**
 * One house, every stage, the next action. Nothing else.
 *
 * Rainer, 2026-08-18: "we're just all messed up all over the place ... come up
 * with an easier way to navigate all of these steps so i can work faster."
 *
 * The mess is structural: three apps (annotator on :8765, this workbench, the
 * catalogue on born2thrill) and two data roots for one pipeline. This does not
 * add a fourth surface -- it collects the stages into a panel that opens from
 * the tile you were already looking at, so the jumping stops being navigation
 * and becomes one click on whatever is actually due next.
 */
function ProjectPanel({ project, onClose }: { project: ProjectEntry | null; onClose: () => void }) {
  const envQueue = useEnvironmentQueue();
  const [live, setLive] = useState<{ images: number; released: number; approved: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState<string | null>(null);

  useEffect(() => {
    if (!project) { setLive(null); setNote(null); return; }
    let cancelled = false;
    const id = encodeURIComponent(project.project_id);
    Promise.all([
      fetch(`/api/floorplan-workbench/publish?plan=${id}`).then((r) => (r.ok ? r.json() : null)).catch(() => null),
      fetch("/api/floorplan-workbench/publish?plans=1").then((r) => (r.ok ? r.json() : null)).catch(() => null),
    ]).then(([shots, plans]) => {
      if (cancelled) return;
      const known = Array.isArray(plans?.plans) && plans.plans.includes(project.project_id);
      const images = Array.isArray(shots?.images) ? shots.images : [];
      setLive({
        images: images.length,
        released: images.filter((i: PublishedImage) => i.send).length,
        approved: known ? "im Katalog" : "nicht im Katalog",
      });
    });
    return () => { cancelled = true; };
  }, [project]);

  if (!project) return null;
  const id = project.project_id;
  const envReady = (envQueue?.ready || []).includes(id);
  const editor = `/floorplan-workbench?reference=${encodeURIComponent(id)}`;
  const approvedGeometry = project.latest_revision_status === "approved";

  async function sendToRender() {
    setBusy(true);
    setNote("Render wird gestartet ...");
    try {
      const response = await fetch("/api/floorplan-workbench/corrections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "send_to_render", reference: id }),
      });
      const payload = await response.json();
      setNote(!response.ok || !payload.ok ? (payload.error || `Fehler ${response.status}`)
        : `Render laeuft -- ${payload.out_dir}`);
    } catch (error) {
      setNote(`${error}`);
    } finally {
      setBusy(false);
    }
  }

  type Stage = {
    label: string; done: boolean; detail: string;
    action?: { label: string; href?: string; run?: () => void };
  };
  const stages: Stage[] = [
    { label: "Annotiert", done: Boolean(project.annotation),
      detail: project.annotation ? "Annotation vorhanden" : "noch nicht annotiert",
      action: { label: "Annotator oeffnen", href: annotatorUrl(id) } },
    { label: "Massstab + Umgebung", done: envReady,
      detail: envReady ? "Massstab und Umgebung vorhanden" : "fehlt - Annotator",
      action: { label: "Annotator oeffnen", href: annotatorUrl(id) } },
    { label: "Geometrie korrigiert", done: project.revision_count > 0,
      detail: `${project.revision_count} Revision(en)`,
      action: { label: "Korrektur-Editor", href: editor } },
    { label: "Geometrie freigegeben", done: approvedGeometry,
      detail: project.latest_revision_status || "keine Revision",
      action: { label: "Im Editor freigeben", href: editor } },
    { label: "Moebliert", done: project.furniture_symbol_count > 0,
      detail: `${project.furniture_symbol_count} Symbole`,
      action: { label: "Moebel platzieren", href: editor } },
    { label: "Gerendert", done: project.render_image_count > 0,
      detail: `${project.render_image_count} Bild(er) lokal`,
      action: approvedGeometry ? { label: "An Render senden", run: sendToRender } : undefined },
    { label: "Hochgeladen", done: (live?.images ?? 0) > 0,
      detail: live ? `${live.images} im Katalog - ${live.approved}` : "...",
      action: { label: "Pakete zeigen", href: "#" } },
    { label: "Fuer Kunden frei", done: (live?.released ?? 0) > 0,
      detail: live ? `${live.released}/${live.images} angehakt` : "...",
      action: { label: "Katalog oeffnen", href: "https://born2thrill.de/grundriss-katalog/" } },
  ];
  const next = stages.find((stage) => !stage.done);

  return (
    <aside className="fixed right-0 top-0 z-40 flex h-full w-[26rem] max-w-full flex-col gap-3 overflow-y-auto bg-white p-5 shadow-2xl ring-1 ring-stone-300">
      <div className="flex items-start gap-2">
        <div className="min-w-0">
          <h2 className="truncate font-mono text-lg font-semibold">{id}</h2>
          <p className="text-xs text-stone-600">{project.house_type || "Haustyp unbekannt"}</p>
        </div>
        <button type="button" onClick={onClose}
          className="ml-auto rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold hover:bg-stone-200">
          Schliessen
        </button>
      </div>

      <PreflightPanel plan={id} />

      {next && (
        <div className="rounded-2xl bg-violet-50 p-3 ring-1 ring-violet-200">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-violet-700">Als naechstes</p>
          <p className="mt-1 text-sm font-semibold text-violet-900">{next.label}</p>
          {next.action && (next.action.href
            ? <a href={next.action.href}
                target={next.action.href.startsWith("http") ? "_blank" : undefined}
                rel="noreferrer"
                className="mt-2 inline-block rounded-full bg-violet-700 px-3 py-1.5 text-xs font-semibold text-white">
                {next.action.label}
              </a>
            : <button type="button" disabled={busy} onClick={() => void next.action?.run?.()}
                className="mt-2 rounded-full bg-violet-700 px-3 py-1.5 text-xs font-semibold text-white disabled:bg-stone-300">
                {busy ? "..." : next.action.label}
              </button>)}
        </div>
      )}
      {note && <p className="break-all rounded-xl bg-stone-100 p-2 font-mono text-[10px]">{note}</p>}

      <ol className="grid gap-1">
        {stages.map((stage) => (
          <li key={stage.label}
            className={`flex items-center gap-2 rounded-xl px-2 py-1.5 text-xs ${
              stage.done ? "bg-emerald-50" : "bg-stone-50"}`}>
            <span className={stage.done ? "text-emerald-700" : "text-stone-400"}>
              {stage.done ? "\u2713" : "\u25cb"}
            </span>
            <span className="font-semibold">{stage.label}</span>
            <span className="ml-auto truncate text-right text-stone-500">{stage.detail}</span>
          </li>
        ))}
      </ol>

      <div className="mt-auto flex flex-wrap gap-2 border-t border-stone-200 pt-3">
        <a href={annotatorUrl(id)} target="annotator" rel="noreferrer"
          className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold hover:bg-stone-200">Annotator &#8599;</a>
        <a href={editor}
          className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold hover:bg-stone-200">Workbench</a>
        <a href="https://born2thrill.de/grundriss-katalog/" target="_blank" rel="noreferrer"
          className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold hover:bg-stone-200">Katalog &#8599;</a>
      </div>
    </aside>
  );
}

type Finding = { level: "blocker" | "warning" | "ok"; what: string; detail: string; fix?: string };
type Preflight = { plan: string; ready: boolean; blockers: number; findings: Finding[] };

/**
 * What is wrong with this house, on the tile you are about to click.
 *
 * Rainer, 2026-08-19: "every single floorplan is a fight from beginning to
 * end." The reason was that every failure was silent -- a scale on the wrong
 * floor looked done, drawn Aussenflaechen were discarded without a word. The
 * findings come from the annotation itself, so they are true before any render
 * is attempted.
 */
function PreflightPanel({ plan }: { plan: string }) {
  const [data, setData] = useState<Preflight | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setData(null);
    setFailed(false);
    fetch(`/api/floorplan-workbench/preflight?plan=${encodeURIComponent(plan)}`)
      .then((response) => (response.ok ? response.json() : null))
      .then((payload) => {
        if (cancelled) return;
        if (payload && Array.isArray(payload.findings)) setData(payload);
        else setFailed(true);
      })
      .catch(() => { if (!cancelled) setFailed(true); });
    return () => { cancelled = true; };
  }, [plan]);

  if (failed) return null;
  if (!data) return <p className="text-xs text-stone-500">Pruefe das Haus ...</p>;

  const mark = { blocker: "\u2716", warning: "!", ok: "\u2713" };
  const tone = {
    blocker: "bg-red-50 text-red-900 ring-red-200",
    warning: "bg-amber-50 text-amber-900 ring-amber-200",
    ok: "bg-emerald-50 text-emerald-900 ring-emerald-200",
  };
  return (
    <div className="grid gap-1">
      <p className={`rounded-xl px-2 py-1 text-xs font-semibold ring-1 ${
        data.ready ? tone.ok : tone.blocker}`}>
        {data.ready ? "Bereit \u2014 nichts blockiert" : `${data.blockers} Blocker`}
      </p>
      {data.findings.map((finding) => (
        <div key={finding.what} className={`rounded-xl px-2 py-1 text-xs ring-1 ${tone[finding.level]}`}>
          <span className="font-semibold">{mark[finding.level]} {finding.what}</span>
          <span className="ml-1">{finding.detail}</span>
          {finding.fix && <span className="mt-0.5 block opacity-80">{finding.fix}</span>}
        </div>
      ))}
    </div>
  );
}

type MenuState = { x: number; y: number; project: ProjectEntry } | null;

/**
 * Tile view. Rainer, 2026-08-18: "like an overview tiles, right click open in
 * annotator, right click open in workbench or new, and also a green overlay
 * already rendered."
 *
 * The green wash is the whole point of the view: at a glance, which houses
 * exist as pictures and which are still only drawings. Everything else is one
 * right-click away.
 */
/**
 * A tile carries its own actions.
 *
 * Rainer right-clicked next to a tile and got Chrome's menu (2026-08-18). That
 * is the flaw in hiding actions behind right-click: it fights the browser's own
 * menu and nothing on screen says it exists. The two links are visible on hover
 * instead, the whole tile still opens the panel, and the context menu stays as
 * a bonus for anyone who finds it.
 *
 * A <div role="button"> rather than a <button>, because the actions are links
 * and a button may not contain interactive children.
 */
function ProjectTile({ project, onMenu, onOpen, envState }:
  { project: ProjectEntry; onMenu: (state: MenuState) => void; onOpen: (project: ProjectEntry) => void;
    envState?: string }) {
  const rendered = project.render_image_count > 0;
  const cover = project.thumbnails[0];
  const readiness = READINESS[project.readiness];
  const id = project.project_id;
  const stop = (event: React.MouseEvent) => event.stopPropagation();
  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => onOpen(project)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") { event.preventDefault(); onOpen(project); }
      }}
      onContextMenu={(event) => {
        event.preventDefault();
        onMenu({ x: event.clientX, y: event.clientY, project });
      }}
      title={`${id} - klicken oeffnet die Uebersicht`}
      className={`group relative cursor-pointer overflow-hidden rounded-xl text-left ring-1 transition hover:ring-2 ${
        rendered ? "ring-emerald-400" : "ring-stone-200"}`}
    >
      <div className="relative h-28 w-full bg-stone-100">
        {cover
          ? <img src={assetUrl(cover, 288)} alt={id} loading="lazy" className="h-28 w-full object-cover" />
          : <span className="flex h-28 w-full items-center justify-center text-[10px] text-stone-400">
              kein Bild
            </span>}
        {envState === "todo" && (
          <span className="absolute right-1 top-1 rounded-full bg-amber-500 px-1.5 py-0.5 text-[9px] font-semibold text-black"
            title="Massstab und/oder Umgebung fehlen - kann im Annotator gemacht werden">
            Umgebung
          </span>
        )}
        {envState === "no_source" && (
          <span className="absolute right-1 top-1 rounded-full bg-stone-700 px-1.5 py-0.5 text-[9px] font-semibold text-white"
            title="Raeume sind gezeichnet, aber die Vorlage liegt nicht im Ordner. Der Massstab wird am Bild gemessen, also ist die Umgebung ohne Vorlage nicht machbar.">
            keine Vorlage
          </span>
        )}
        {(envState === "empty" || envState === "unreadable" || envState === "blank") && (
          <span className="absolute right-1 top-1 rounded-full bg-stone-300 px-1.5 py-0.5 text-[9px] font-semibold text-stone-700"
            title="Leerer oder unlesbarer Projektordner">
            leer
          </span>
        )}
        {rendered && (
          <>
            <span className="pointer-events-none absolute inset-0 bg-emerald-500/25" />
            <span className="absolute left-1 top-1 rounded-full bg-emerald-600 px-1.5 py-0.5 text-[9px] font-semibold text-white">
              gerendert
            </span>
          </>
        )}

        {/* Visible on hover and on keyboard focus -- never hidden behind a right-click. */}
        <div className="absolute bottom-1 right-1 flex gap-1 opacity-0 transition group-hover:opacity-100 group-focus-within:opacity-100">
          <a href={annotatorUrl(id)} target="annotator" rel="noreferrer" onClick={stop}
            title="Im Annotator oeffnen (immer derselbe Tab)"
            className="rounded bg-white/95 px-1.5 py-0.5 text-[10px] font-semibold text-stone-800 shadow hover:bg-white">
            Annotator
          </a>
          <a href={`/floorplan-workbench?reference=${encodeURIComponent(id)}`} onClick={stop}
            title="Im Workbench oeffnen"
            className="rounded bg-white/95 px-1.5 py-0.5 text-[10px] font-semibold text-stone-800 shadow hover:bg-white">
            Workbench
          </a>
        </div>
      </div>
      <div className="p-2">
        <span className="block truncate font-mono text-[11px] font-semibold">{id}</span>
        <span className={`mt-1 inline-block rounded-full px-1.5 py-0.5 text-[9px] font-semibold ${readiness.className}`}>
          {readiness.label}
        </span>
      </div>
    </div>
  );
}

function TileMenu({ state, onClose }: { state: MenuState; onClose: () => void }) {
  useEffect(() => {
    if (!state) return;
    const close = () => onClose();
    window.addEventListener("click", close);
    window.addEventListener("scroll", close, true);
    return () => {
      window.removeEventListener("click", close);
      window.removeEventListener("scroll", close, true);
    };
  }, [state, onClose]);
  if (!state) return null;
  const id = state.project.project_id;
  const workbench = `/floorplan-workbench?reference=${encodeURIComponent(id)}`;
  const items: { label: string; href: string; blank?: boolean; target?: string }[] = [
    { label: "Im Workbench öffnen", href: workbench },
    { label: "Im Workbench, zweiter Tab", href: workbench, blank: true },
    { label: "Im Annotator öffnen", href: annotatorUrl(id), target: "annotator" },
  ];
  return (
    <div
      style={{ top: state.y, left: state.x }}
      className="fixed z-50 min-w-[15rem] overflow-hidden rounded-xl bg-white py-1 shadow-lg ring-1 ring-stone-300"
    >
      <p className="truncate px-3 py-1 font-mono text-[10px] text-stone-500">{id}</p>
      {items.map((item) => (
        <a key={item.label} href={item.href}
          target={item.target || (item.blank ? "_blank" : undefined)}
          rel={item.blank || item.target ? "noreferrer" : undefined}
          className="block px-3 py-1.5 text-xs hover:bg-stone-100">
          {item.label}{item.blank ? " ↗" : ""}
        </a>
      ))}
    </div>
  );
}

function ProjectTiles({ projects }: { projects: ProjectEntry[] }) {
  const [menu, setMenu] = useState<MenuState>(null);
  const [panel, setPanel] = useState<ProjectEntry | null>(null);
  const queue = useEnvironmentQueue();
  const envStateOf = useMemo(() => {
    const map = new Map<string, string>();
    for (const key of ["todo", "no_source", "empty", "blank", "unreadable", "ready"] as const) {
      for (const id of queue?.[key] || []) map.set(id, key);
    }
    return (id: string) => map.get(id);
  }, [queue]);
  return (
    <>
      <div className="grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fill,minmax(9.5rem,1fr))" }}>
        {projects.map((project) => (
          <ProjectTile key={project.project_id} project={project} onMenu={setMenu} onOpen={setPanel}
            envState={envStateOf(project.project_id)} />
        ))}
      </div>
      <TileMenu state={menu} onClose={() => setMenu(null)} />
      <ProjectPanel project={panel} onClose={() => setPanel(null)} />
    </>
  );
}

type HouseState = {
  plan: string; state: string; blocker: string; action: string; version?: string | null;
  blends: number; catalogue_images: number; approved: string | null;
};

const STATE_LABEL: Record<string, { label: string; tone: string }> = {
  fertig: { label: "Fertig", tone: "bg-emerald-600 text-white" },
  // FERTIG-BLEIBT-FERTIG-001: still done, a newer build/images are waiting.
  fertig_update: { label: "Fertig · Update", tone: "bg-teal-500 text-white" },
  veroeffentlicht_build_alt: { label: "Veröffentlicht", tone: "bg-emerald-500 text-white" },
  warten_auf_freigabe: { label: "Freigabe offen", tone: "bg-violet-600 text-white" },
  bilder_hochladen: { label: "Bilder hochladen", tone: "bg-violet-500 text-white" },
  warten_auf_codex: { label: "Warten auf Codex", tone: "bg-amber-500 text-black" },
  baubereit: { label: "Baubereit", tone: "bg-sky-500 text-white" },
  korrektur_noetig: { label: "Korrektur noetig", tone: "bg-orange-400 text-black" },
  vermessung_noetig: { label: "Vermessung noetig", tone: "bg-stone-700 text-white" },
  keine_vorlage: { label: "Keine Vorlage", tone: "bg-stone-400 text-white" },
  unbegonnen: { label: "Unbegonnen", tone: "bg-stone-200 text-stone-700" },
};

/**
 * The queue, closest to finished first.
 *
 * Codex ranked this first for going from 1 finished house to 50: an
 * authoritative per-house state with a truthful blocker and ONE next action.
 * "Finished" here means what it means to the business -- searchable in the
 * catalogue with approved images -- not "a render exists".
 */
function WorkQueue() {
  const [data, setData] = useState<{ total: number; counts: Record<string, number>;
    houses: HouseState[] } | null>(null);
  const [only, setOnly] = useState<string | null>(null);

  useEffect(() => {
    fetch("/api/floorplan-workbench/state")
      .then((r) => (r.ok ? r.json() : null))
      .then((d) => { if (d && d.houses) setData(d); })
      .catch(() => undefined);
  }, []);

  if (!data) return null;
  const shown = only ? data.houses.filter((h) => h.state === only) : data.houses;

  return (
    <section className="rounded-3xl bg-white p-5 ring-1 ring-stone-200">
      <div className="flex flex-wrap items-baseline gap-x-3">
        <h2 className="text-xl font-semibold">Warteschlange</h2>
        <span className="text-sm text-stone-600">{data.total} Haeuser, am weitesten fortgeschritten zuerst</span>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {Object.entries(data.counts).map(([state, count]) => (
          <button key={state} type="button"
            onClick={() => setOnly(only === state ? null : state)}
            className={`rounded-full px-3 py-1 text-xs font-semibold ${
              only === state ? "ring-2 ring-stone-900 " : ""}${
              STATE_LABEL[state]?.tone || "bg-stone-200 text-stone-700"}`}>
            {count} {STATE_LABEL[state]?.label || state}
          </button>
        ))}
      </div>
      <div className="mt-3 max-h-[26rem] overflow-y-auto">
        <table className="w-full text-left text-xs">
          <tbody>
            {shown.slice(0, 200).map((house) => (
              <tr key={house.plan} className="border-t border-stone-100">
                <td className="py-1 pr-2 font-mono">
                  {/*
                   * Rainer, 2026-09-03: "there are no links to the houses".
                   * Die Kacheln hatten Rechtsklick -> Annotator/Workbench,
                   * die Warteschlange gar nichts -- ausgerechnet die Liste,
                   * die sagt WAS zu tun ist, liess einen nicht dorthin.
                   * Der Name fuehrt jetzt in den Workbench, das Pfeilchen
                   * daneben in den Annotator; die 16 Ausrichtungsfaelle
                   * gehoeren dorthin.
                   */}
                  <a
                    href={`/floorplan-workbench?reference=${encodeURIComponent(house.plan)}`}
                    className="underline decoration-stone-300 underline-offset-2 hover:decoration-stone-900"
                  >
                    {house.plan}
                  </a>
                  <a
                    href={annotatorUrl(house.plan)}
                    target="_blank"
                    rel="noreferrer"
                    title="im Annotator oeffnen"
                    className="ml-1 text-stone-400 hover:text-stone-900"
                  >
                    ↗
                  </a>
                </td>
                <td className="py-1 pr-2">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold ${
                    STATE_LABEL[house.state]?.tone || "bg-stone-200"}`}>
                    {STATE_LABEL[house.state]?.label || house.state}
                    {house.version ? ` v${house.version}` : ""}
                  </span>
                </td>
                <td className="py-1 pr-2 text-stone-600">{house.blocker}</td>
                <td className="py-1 text-stone-900">{house.action}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {shown.length > 200 && (
          <p className="mt-2 text-xs text-stone-500">... und {shown.length - 200} weitere</p>
        )}
      </div>
    </section>
  );
}

function PipelineSummary({ projects, onPick, active }:
  { projects: ProjectEntry[]; onPick: (id: FilterId) => void; active: FilterId }) {
  const count = (test: (project: ProjectEntry) => boolean) => projects.filter(test).length;
  const queue = useEnvironmentQueue();
  const stages: { label: string; hint: string; value: number; filter: FilterId }[] = [
    { label: "Annotiert", hint: "Annotation im Annotator vorhanden",
      value: count((p) => Boolean(p.annotation)), filter: "annotated" },
    { label: "Umgebung offen", hint: "Vorlage und Zeichnung da, Massstab und/oder Umgebung fehlen. "
      + "Massstab zuerst: ohne ihn werden gezeichnete Flaechen verworfen. Das ist die echte Warteschlange.",
      value: queue ? queue.todo.length : 0, filter: "env_todo" },
    { label: "Keine Vorlage", hint: "Raeume gezeichnet, aber kein Bild im Ordner. Der Massstab wird am Bild "
      + "gemessen, also ist die Umgebung so nicht machbar - und es gibt keinen Weg zurueck zur Vorlage: "
      + "jedes Projekt nennt nur einen generischen Dateinamen, keine Kennung.",
      value: queue ? queue.no_source.length : 0, filter: "env_no_source" },
    { label: "Leer (Annotator)", hint: "Leere oder unlesbare Ordner im Annotator",
      value: queue ? queue.empty.length + queue.unreadable.length + queue.blank.length : 0,
      filter: "env_empty" },
    { label: "Korrigiert", hint: "mindestens eine Korrektur-Revision",
      value: count((p) => p.revision_count > 0), filter: "revisions" },
    { label: "Freigegeben", hint: "neueste Revision ist approved — nur daraus darf gerendert werden",
      value: count((p) => p.latest_revision_status === "approved"), filter: "revisions" },
    { label: "Möbliert", hint: "Möbel platziert",
      value: count((p) => p.furniture_symbol_count > 0), filter: "furniture" },
    { label: "Gerendert", hint: "Renders auf dieser Maschine",
      value: count((p) => p.render_image_count > 0), filter: "renders" },
    { label: "Exportiert", hint: "Export-Paket geschrieben",
      value: count((p) => p.export_count > 0), filter: "exports" },
    { label: "Leer (Workbench)", hint: "Korrektur-Ordner ohne Inhalt",
      value: count((p) => p.readiness === "empty"), filter: "empty" },
  ];
  return (
    <section className="rounded-3xl bg-white p-5 ring-1 ring-stone-200">
      <div className="flex flex-wrap items-baseline gap-x-3">
        <h2 className="text-xl font-semibold">Pipeline</h2>
        <span className="text-sm text-stone-600">{projects.length} Projekte insgesamt</span>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {stages.map((stage) => (
          <button
            key={stage.label}
            type="button"
            title={stage.hint}
            onClick={() => onPick(stage.filter)}
            className={`min-w-[7.5rem] rounded-2xl px-4 py-3 text-left ring-1 transition ${
              active === stage.filter
                ? "bg-violet-700 text-white ring-violet-700"
                : "bg-stone-50 text-stone-800 ring-stone-200 hover:bg-stone-100"}`}
          >
            <span className="block text-2xl font-semibold tabular-nums">{stage.value}</span>
            <span className="block text-xs">{stage.label}</span>
          </button>
        ))}
      </div>
      {queue && (
        <p className="mt-2 rounded-xl bg-amber-50 p-2 text-xs text-amber-900 ring-1 ring-amber-200">
          <strong>{queue.todo.length}</strong> Haeuser brauchen einen Durchgang im Annotator
          (Aussenwand-Massstab und Umgebung kamen spaeter dazu) &mdash; die orangen Kacheln.
          Weitere <strong>{queue.no_source.length}</strong> haben gezeichnete Raeume, aber keine
          Vorlage im Ordner; ohne Bild laesst sich kein Massstab messen, also sind sie keine
          offene Arbeit, sondern eine Entscheidung.
        </p>
      )}
      <p className="mt-2 text-xs text-stone-500">
        Eine Stufe anklicken filtert die Liste darunter. Gerendert wird nur aus
        freigegebener Geometrie — die Lücke zwischen „Korrigiert" und
        „Freigegeben" ist die Warteschlange.
      </p>
    </section>
  );
}

function PlanIdList() {
  const plans = useCataloguePlans();
  return (
    <datalist id="gk-plan-ids">
      {plans.map((plan) => <option key={plan} value={plan} />)}
    </datalist>
  );
}

function PackageShot({ asset, online, big, onGone }: { asset: AssetRef; online: boolean; big: boolean; onGone: () => void }) {
  const [gone, setGone] = useState(false);
  if (gone) return null;
  return (
    <div className={big ? "w-[220px] shrink-0" : "w-36 shrink-0"}>
      <a href={assetUrl(asset)} target="_blank" rel="noreferrer" className="relative block"
        title={`${asset.path} · ${megabytes(asset.bytes)} · ${shortTime(asset.modified_at)}`}>
        <img
          src={assetUrl(asset, big ? 320 : 288)}
          alt={asset.name}
          loading="lazy"
          className={`w-full rounded-lg border border-stone-300 bg-white object-cover ${big ? "h-40" : "h-24"}`}
        />
        <span
          title={online ? "steht im Katalog" : "noch nicht hochgeladen"}
          className={`absolute right-1 top-1 rounded-full px-1.5 py-0.5 text-[9px] font-semibold ${
            online ? "bg-emerald-600 text-white" : "bg-stone-900/60 text-white"}`}
        >
          {online ? "online" : "lokal"}
        </span>
        <span className="mt-1 block truncate text-[10px] text-stone-600">{asset.name}</span>
      </a>
      <ReviewControls asset={asset} />
      <DiscardButton asset={asset} onGone={() => { setGone(true); onGone(); }} />
    </div>
  );
}

function RenderSetCard({ set, planId }: { set: RenderSet; planId: string }) {
  return (
    <div className="rounded-2xl bg-stone-50 p-4 ring-1 ring-stone-200">
      <div className="flex flex-wrap items-center gap-2">
        <strong className="text-sm">{set.name}</strong>
        <RootChip root={set.root} />
        <Chip>{set.images.length} images</Chip>
        {set.aux_image_count > 0 && <Chip>{set.aux_image_count} depth/edge/mask</Chip>}
        {set.blend_count > 0 && <Chip>{set.blend_count} .blend</Chip>}
        {set.log_count > 0 && <Chip>{set.log_count} logs</Chip>}
        <Chip>{megabytes(set.total_bytes)}</Chip>
        <span className="text-xs text-stone-500">{shortTime(set.modified_at)}</span>
      </div>
      <p className="mt-1 break-all font-mono text-[10px] text-stone-500">{set.path}</p>

      {set.handoff ? (
        <div className="mt-3 rounded-xl bg-emerald-50 p-3 text-xs ring-1 ring-emerald-300">
          <p className="font-semibold text-emerald-900">handoff.json · {set.handoff.schema || "unknown schema"}</p>
          <p className="mt-1">
            Verified styles: {set.handoff.styles_verified.length ? set.handoff.styles_verified.join(", ") : <em>none</em>}
            {set.handoff.styles_unverified.length > 0 && <> · listed but not verified: {set.handoff.styles_unverified.join(", ")}</>}
          </p>
          <p className="mt-1">
            Excluded: {set.handoff.excluded.length === 0 ? "none" : set.handoff.excluded.map((item) => `${item.style || "unnamed"}${item.reason ? ` (${item.reason})` : ""}`).join(", ")}
          </p>
        </div>
      ) : (
        <p className="mt-3 rounded-xl bg-amber-50 p-3 text-xs text-amber-900 ring-1 ring-amber-300">No handoff.json in this render set — not ready to hand to Codex.</p>
      )}

      {set.catalog && (
        <div className="mt-2 rounded-xl bg-white p-3 text-xs ring-1 ring-stone-200">
          <p className="font-semibold">catalog.json · {set.catalog.schema_version || "unknown schema"}</p>
          <p className="mt-1">{set.catalog.asset_count} assets{set.catalog.styles.length ? ` · styles ${set.catalog.styles.join(", ")}` : ""} · family {set.catalog.plan_family_id || "—"} · created {set.catalog.created_at || "—"}</p>
        </div>
      )}

      {set.plans.length > 0 && (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[640px] text-left text-xs">
            <thead className="text-stone-500">
              <tr>
                <th className="py-1 pr-3">plan file</th>
                <th className="py-1 pr-3">style</th>
                <th className="py-1 pr-3">built from</th>
                <th className="py-1 pr-3">rooms</th>
                <th className="py-1 pr-3">m²</th>
                <th className="py-1 pr-3">furniture</th>
                <th className="py-1 pr-3">roof</th>
                <th className="py-1">geometry hash</th>
              </tr>
            </thead>
            <tbody>
              {set.plans.map((plan) => (
                <tr key={plan.file} className="border-t border-stone-200 align-top">
                  <td className="py-1 pr-3 font-mono">{plan.file}</td>
                  <td className="py-1 pr-3">{plan.style || "—"}</td>
                  <td className="py-1 pr-3">
                    {plan.source || "unknown"}
                    {plan.correction_status && <span className="text-stone-500"> · {plan.correction_status}</span>}
                  </td>
                  <td className="py-1 pr-3">{plan.room_count} <span className="text-stone-400">/ {plan.floor_count} fl</span></td>
                  <td className="py-1 pr-3">{plan.total_area_m2 === null ? "—" : plan.total_area_m2.toFixed(1)}</td>
                  <td className="py-1 pr-3">{plan.furniture_placements}</td>
                  <td className="py-1 pr-3">{plan.roof_type || "—"}</td>
                  <td className="py-1 font-mono text-[10px] break-all">{plan.source_geometry_hash ? plan.source_geometry_hash.slice(0, 12) : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {set.images.length > 0 && (
        <PackageBlock
          title={set.name}
          images={set.images}
          defaultPlan={planId || set.plans[0]?.plan_id || set.catalog?.plan_family_id || ""}
          hintName={planId}
        />
      )}
    </div>
  );
}

function TreeCard({ tree, planId }: { tree: WorkbenchTree; planId: string }) {
  const latestRevision = tree.revisions.at(-1);
  return (
    <div className="rounded-2xl bg-white p-4 ring-1 ring-stone-200">
      <div className="flex flex-wrap items-center gap-2">
        <RootChip root={tree.root} />
        <span className="break-all font-mono text-[11px] text-stone-600">{tree.root_path}\{tree.path.replace(/\//g, "\\")}</span>
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-3">
        <div className="rounded-xl bg-stone-50 p-3 text-xs ring-1 ring-stone-200">
          <p className="font-semibold">Revisions · {tree.revisions.length}</p>
          {latestRevision ? (
            <>
              <p className="mt-1">latest {latestRevision.file} · status <strong>{latestRevision.status || "?"}</strong>{latestRevision.validation_valid === null ? "" : latestRevision.validation_valid ? " · validation PASS" : " · validation BLOCKED"}</p>
              <p className="mt-1">{latestRevision.floor_count} floors · {latestRevision.room_count} rooms{latestRevision.total_area_m2 === null ? "" : ` · ${latestRevision.total_area_m2.toFixed(1)} m²`} · {latestRevision.wall_count} walls · {latestRevision.opening_count} openings</p>
              <p className="mt-1 break-all font-mono text-[10px] text-stone-500">{latestRevision.geometry_hash || "no hash"}</p>
              <p className="mt-1 text-stone-500">updated {shortTime(latestRevision.updated_at || latestRevision.modified_at)}</p>
            </>
          ) : <p className="mt-1 text-stone-500">none</p>}
        </div>

        <div className="rounded-xl bg-stone-50 p-3 text-xs ring-1 ring-stone-200">
          <p className="font-semibold">Furniture · {tree.furniture.length} floor file(s)</p>
          {tree.furniture.length ? tree.furniture.map((item) => (
            <p key={item.file} className="mt-1">
              {item.floor_id || item.file}: {item.symbol_count} symbols
              <br />
              <span className="text-stone-500">{item.coordinate_space || "no coordinate_space"} · {shortTime(item.updated_at || item.modified_at)}</span>
            </p>
          )) : <p className="mt-1 text-stone-500">none</p>}
        </div>

        <div className="rounded-xl bg-stone-50 p-3 text-xs ring-1 ring-stone-200">
          <p className="font-semibold">Exports · {tree.exports.length}</p>
          {tree.exports.length ? (
            <p className="mt-1">
              latest {tree.exports.at(-1)!.name} · {tree.exports.at(-1)!.file_count} files
              {tree.exports.at(-1)!.wordpress_eligible ? " · WordPress-eligible" : " · internal only"}
              <br />
              <span className="text-stone-500">{shortTime(tree.exports.at(-1)!.modified_at)}</span>
            </p>
          ) : <p className="mt-1 text-stone-500">none</p>}
          {tree.blender_scene_count > 0 && <p className="mt-2">{tree.blender_scene_count} ad-hoc Blender scene PNG(s)</p>}
          {tree.notes.map((note) => <p key={note} className="mt-2 text-amber-800">{note}</p>)}
        </div>
      </div>

      {tree.render_sets.length > 0 && (
        <div className="mt-3 space-y-3">
          {tree.render_sets.map((set) => <RenderSetCard key={`${set.root}:${set.path}`} set={set} planId={planId} />)}
        </div>
      )}
    </div>
  );
}

/**
 * What to do with this project next, as a button.
 *
 * Editing always opens the editor at this reference. The forward action
 * depends on where the project actually is; approval is deliberately NOT one
 * of them — a human approves geometry in the editor after looking at it, not
 * from a list.
 */
function NextStep({ project }: { project: ProjectEntry }) {
  const [status, setStatus] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const editorUrl = `/floorplan-workbench?reference=${encodeURIComponent(project.project_id)}`;

  const approved = project.latest_revision_status === "approved";
  const rendered = project.render_image_count > 0;

  async function sendToRender() {
    setBusy(true);
    setStatus("Render wird gestartet …");
    try {
      const response = await fetch("/api/floorplan-workbench/corrections", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "send_to_render", reference: project.project_id }),
      });
      const payload = await response.json();
      setStatus(!response.ok || !payload.ok
        ? (payload.error || `Fehler ${response.status}`)
        : `Render läuft — ${payload.out_dir}`);
    } catch (error) {
      setStatus(`${error}`);
    } finally {
      setBusy(false);
    }
  }

  const forward = !project.annotation ? { label: "Annotieren", href: editorUrl }
    : project.revision_count === 0 ? { label: "Korrigieren", href: editorUrl }
    : !approved ? { label: "Freigeben im Editor", href: editorUrl }
    : rendered ? { label: "Nochmal rendern", action: sendToRender }
    : { label: "An Render senden", action: sendToRender };

  return (
    <div className="mt-2 flex flex-wrap items-center gap-2">
      <a href={editorUrl}
        className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-800 hover:bg-stone-200">
        Bearbeiten
      </a>
      <a href={annotatorUrl(project.project_id)} target="annotator" rel="noreferrer"
        title="Annotator (eigene App auf Port 8765) - benutzt immer denselben Tab"
        className="rounded-full bg-stone-100 px-3 py-1 text-xs font-semibold text-stone-800 hover:bg-stone-200">
        Annotator &#8599;
      </a>
      {forward.href ? (
        <a href={forward.href}
          className="rounded-full bg-violet-700 px-3 py-1 text-xs font-semibold text-white hover:bg-violet-800">
          {forward.label} →
        </a>
      ) : (
        <button type="button" disabled={busy} onClick={() => void forward.action?.()}
          className="rounded-full bg-violet-700 px-3 py-1 text-xs font-semibold text-white disabled:bg-stone-300">
          {busy ? "…" : `${forward.label} →`}
        </button>
      )}
      {status && <span className="text-xs text-stone-600">{status}</span>}
    </div>
  );
}

function ProjectCard({ project }: { project: ProjectEntry }) {
  const [open, setOpen] = useState(false);
  const readiness = READINESS[project.readiness];
  const annotation = project.annotation;
  return (
    <article className="rounded-3xl bg-white p-5 shadow-sm ring-1 ring-stone-200">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="text-lg font-semibold">{project.project_id}</h3>
            <Chip className={readiness.className}>{readiness.label}</Chip>
            {project.is_scratch && <Chip className="bg-stone-200 text-stone-600">scratch/test run</Chip>}
            {project.trees.map((tree) => <RootChip key={tree.root} root={tree.root} />)}
            {annotation && <RootChip root="annotations" />}
          </div>
          <p className="mt-1 text-xs text-stone-600">
            {project.house_type || "house type unknown"}
            {project.package_status ? ` · ${project.package_status}` : ""}
            {project.room_count === null ? "" : ` · ${project.room_count} rooms`}
            {project.total_area_m2 === null ? "" : ` · ${project.total_area_m2.toFixed(1)} m²`}
            {" · last touched "}{shortTime(project.latest_activity)}
          </p>
          <NextStep project={project} />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <a href={`/floorplan-workbench?reference=${encodeURIComponent(project.project_id)}`} className="rounded-full bg-slate-900 px-3 py-2 text-xs font-semibold text-white">Open in editor</a>
          <button onClick={() => setOpen((value) => !value)} className="rounded-full bg-stone-200 px-3 py-2 text-xs font-semibold">{open ? "Hide details" : "Show details"}</button>
        </div>
      </div>

      <div className="mt-3 flex flex-wrap gap-2 text-xs">
        <Chip className={project.render_image_count ? "bg-emerald-100 text-emerald-900" : "bg-stone-100 text-stone-500"}>{project.render_image_count} render images</Chip>
        <Chip className={project.revision_count ? "bg-blue-100 text-blue-900" : "bg-stone-100 text-stone-500"}>{project.revision_count} revisions{project.latest_revision_status ? ` · newest is ${project.latest_revision_status}` : ""}</Chip>
        {project.trees.length > 1 && <Chip className="bg-red-100 text-red-800 ring-1 ring-red-300">split across {project.trees.length} data roots</Chip>}
        <Chip className={project.furniture_symbol_count ? "bg-amber-100 text-amber-900" : "bg-stone-100 text-stone-500"}>{project.furniture_symbol_count} furniture symbols</Chip>
        <Chip className={project.export_count ? "bg-violet-100 text-violet-900" : "bg-stone-100 text-stone-500"}>{project.export_count} exports</Chip>
        {project.styles_verified.length > 0 && <Chip className="bg-emerald-600 text-white">verified: {project.styles_verified.join(", ")}</Chip>}
        {project.styles_excluded.length > 0 && <Chip className="bg-red-100 text-red-800">excluded: {project.styles_excluded.join(", ")}</Chip>}
        {project.plan_sources.map((source) => <Chip key={source} className="bg-stone-800 text-white">plan from {source}</Chip>)}
        {project.furniture_spaces.map((space) => <Chip key={space} className="bg-stone-100 font-mono text-[10px] text-stone-700">{space}</Chip>)}
      </div>

      {project.thumbnails.length > 0 && (
        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {project.thumbnails.map((asset) => <Thumbnail key={`${asset.root}:${asset.path}`} asset={asset} />)}
        </div>
      )}

      {open && (
        <div className="mt-4 space-y-3 border-t border-stone-200 pt-4">
          {annotation && (
            <div className="rounded-2xl bg-white p-4 ring-1 ring-stone-200">
              <div className="flex flex-wrap items-center gap-2">
                <RootChip root="annotations" />
                <strong className="text-sm">Annotation package</strong>
                <span className="break-all font-mono text-[11px] text-stone-600">{annotation.path}</span>
              </div>
              {annotation.has_annotations_json || annotation.has_data_json ? (
                <>
                  <p className="mt-2 text-xs">
                    {annotation.house_type || "house type missing"} · {annotation.package_status || "status missing"} · schema {annotation.annotation_schema_version || "—"}
                    {" · "}{annotation.room_count} annotated rooms
                    {annotation.floor_levels.length ? ` on ${annotation.floor_levels.join(", ")}` : ""}
                  </p>
                  <p className="mt-1 text-xs">
                    elements: {Object.entries(annotation.element_counts).map(([type, count]) => `${count} ${type}`).join(", ") || "none"}
                    {annotation.symbol_count > 0 && ` · ${annotation.symbol_count} symbols`}
                    {annotation.exterior_area_count > 0 && ` · ${annotation.exterior_area_count} exterior areas`}
                    {annotation.roof_type_modern && ` · roof modern ${annotation.roof_type_modern}`}
                    {annotation.roof_type_classic && ` / classic ${annotation.roof_type_classic}`}
                  </p>
                  <p className="mt-1 text-xs text-stone-600">
                    quality {annotation.quality_passed === null ? "not recorded" : annotation.quality_passed ? "passed" : "FAILED"}
                    {annotation.quality_warnings.length > 0 && ` · ${annotation.quality_warnings.length} warning(s): ${annotation.quality_warnings.slice(0, 3).join(" · ")}`}
                  </p>
                  <p className="mt-1 text-xs text-stone-500">created {annotation.created_at || "—"} · annotation updated {shortTime(annotation.updated_at)} · files touched {shortTime(annotation.modified_at)}</p>
                  <p className="mt-1 text-xs text-stone-500">No absolute m² in the annotation package — areas are ratios only; m² comes from a render plan or a correction revision.</p>
                  {annotation.concept_images.length > 0 && (
                    <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
                      {annotation.concept_images.map((asset) => <Thumbnail key={asset.path} asset={asset} />)}
                    </div>
                  )}
                </>
              ) : (
                <p className="mt-2 text-xs text-red-700">Folder exists but contains no annotations.json and no data.json.</p>
              )}
            </div>
          )}
          {project.trees.length === 0 && <p className="text-xs text-stone-500">No workbench tree under corrections\ in either data root.</p>}
          {project.trees.map((tree) => <TreeCard key={tree.root} tree={tree} planId={project.project_id} />)}
        </div>
      )}
    </article>
  );
}

export default function FloorplanOverviewPage() {
  const [inventory, setInventory] = useState<Inventory | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterId>("codex_ready");
  const [search, setSearch] = useState("");
  const [hideScratch, setHideScratch] = useState(true);
  const [openOnly, setOpenOnly] = useState(true);
  const [tiles, setTiles] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const response = await fetch("/api/floorplan-workbench/overview", { cache: "no-store" });
        const body = await response.json();
        if (cancelled) return;
        if (!response.ok) setError(body?.error || `Inventory request failed (${response.status}).`);
        else setInventory(body as Inventory);
      } catch (requestError) {
        if (!cancelled) setError(requestError instanceof Error ? requestError.message : String(requestError));
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const envQueue = useEnvironmentQueue();
  const filtered = useMemo(() => {
    if (!inventory) return [];
    const needle = search.trim().toLowerCase();
    // The environment states come from the annotator folders, not from the
    // inventory, so they are matched by id rather than by a project field.
    const inSet = (key: "todo" | "no_source" | "empty" | "blank" | "unreadable") =>
      new Set(envQueue?.[key] || []);
    const envTodo = inSet("todo");
    const envNoSource = inSet("no_source");
    const envEmpty = new Set([...inSet("empty"), ...inSet("blank"), ...inSet("unreadable")]);
    return inventory.projects.filter((project) => {
      if (hideScratch && project.is_scratch) return false;
      if (needle && !project.project_id.toLowerCase().includes(needle) && !(project.house_type || "").toLowerCase().includes(needle)) return false;
      switch (filter) {
        case "codex_ready": return project.codex_ready;
        case "renders": return project.render_image_count > 0;
        case "revisions": return project.revision_count > 0;
        case "furniture": return project.furniture_symbol_count > 0;
        case "exports": return project.export_count > 0;
        case "annotated": return project.readiness === "annotated";
        case "empty": return project.readiness === "empty";
        // These three say exactly what the pipeline strip counts, so clicking a
        // number shows those houses and nothing else.
        case "env_todo": return envTodo.has(project.project_id);
        case "env_no_source": return envNoSource.has(project.project_id);
        case "env_empty": return envEmpty.has(project.project_id);
        default: return true;
      }
    });
  }, [inventory, filter, search, hideScratch, envQueue]);

  if (error) return <main className="mx-auto max-w-3xl p-8"><p className="rounded-2xl bg-red-100 p-5 text-red-900">{error}</p></main>;
  if (!inventory) return <main className="mx-auto max-w-3xl p-8"><p className="text-stone-600">Scanning the data roots…</p></main>;

  const totals = inventory.totals;
  return (
    <OpenOnlyContext.Provider value={openOnly}>
    <main className="mx-auto max-w-[1500px] space-y-6 p-5">
      <header className="rounded-3xl bg-amber-100 p-6 ring-2 ring-amber-600">
        <p className="font-black tracking-widest text-amber-950">INTERNAL REVIEW – NOT FOR CUSTOMER DELIVERY</p>
        <h1 className="mt-2 text-3xl font-semibold">Produced work · overview</h1>
        <p className="mt-2 text-sm">Everything the floorplan suite has written so far: baseline renders, render plans, correction revisions, furniture layouts, exported packages and annotation packages. This page only reads — nothing here writes, moves or deletes a file.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <a href="/floorplan-workbench" className="rounded-full bg-white px-4 py-2 text-sm font-semibold">Correction editor</a>
          <span className="rounded-full bg-violet-700 px-4 py-2 text-sm font-semibold text-white">Overview</span>
          <label className="flex cursor-pointer items-center gap-2 rounded-full bg-white px-4 py-2 text-sm font-semibold">
            <input
              type="checkbox"
              checked={openOnly}
              onChange={(event) => setOpenOnly(event.target.checked)}
              className="accent-violet-700"
            />
            Nur offene Pakete
          </label>
          <div className="flex overflow-hidden rounded-full bg-white text-sm font-semibold">
            <button type="button" onClick={() => setTiles(true)}
              className={`px-4 py-2 ${tiles ? "bg-violet-700 text-white" : "text-stone-700"}`}>Kacheln</button>
            <button type="button" onClick={() => setTiles(false)}
              className={`px-4 py-2 ${tiles ? "text-stone-700" : "bg-violet-700 text-white"}`}>Liste</button>
          </div>
        </div>
      </header>
      {/* every plan_id the catalogue knows -- typed ids are checked against it */}
      <PlanIdList />
      <WorkQueue />
      <PipelineSummary projects={inventory.projects} onPick={setFilter} active={filter} />


      {/* Finished packages first: these are the product. They live in the
          repo's own exports/ folder, which is neither data root — the reason
          they looked missing. */}
      {(inventory.deliveries || []).length > 0 && (
        <section className="rounded-3xl bg-emerald-50 p-5 ring-2 ring-emerald-300">
          <h2 className="text-xl font-semibold text-emerald-950">Fertige Häuser · delivered packages</h2>
          <p className="mt-1 text-sm text-emerald-900">
            Handed to Codex and rendered. From {inventory.roots.find((root) => root.key === "deliveries")?.path ?? "exports/"}.
          </p>
          <div className="mt-4 space-y-5">
            {inventory.deliveries.map((bundle) => (
              <div key={bundle.name} className="rounded-2xl bg-white p-4 ring-1 ring-emerald-200">
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="font-semibold">{bundle.name}</span>
                  <span className="text-xs text-stone-600">
                    {bundle.images.length} images
                    {bundle.asset_count ? ` · ${bundle.asset_count} catalogued` : ""}
                    {bundle.created_at ? ` · ${bundle.created_at}` : ""}
                    {bundle.plan_family_id ? ` · ${bundle.plan_family_id}` : ""}
                    {bundle.zip ? " · zip" : ""}
                  </span>
                </div>
                {bundle.styles.length > 0 && (
                  <div className="mt-1 flex flex-wrap gap-1">
                    {bundle.styles.map((style) => (
                      <span key={style} className="rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] text-emerald-900">{style}</span>
                    ))}
                  </div>
                )}
                {bundle.images.length > 0 && (
                  <PackageBlock
                    title={bundle.name}
                    images={bundle.images}
                    defaultPlan={bundle.plan_family_id || ""}
                    hintName={bundle.name}
                    big
                  />
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <section className="grid gap-3 sm:grid-cols-3 lg:grid-cols-6">
        {[
          { label: "Projects", value: totals.projects },
          { label: "Codex-ready", value: totals.codex_ready, className: "bg-emerald-600 text-white" },
          { label: "With renders", value: totals.with_renders },
          { label: "Render images", value: totals.render_images },
          { label: "Correction revisions", value: totals.revisions },
          { label: "Exported packages", value: totals.exports },
        ].map((tile) => (
          <div key={tile.label} className={`rounded-2xl p-4 ring-1 ring-stone-200 ${tile.className || "bg-white"}`}>
            <p className="text-2xl font-semibold">{tile.value}</p>
            <p className="text-xs">{tile.label}</p>
          </div>
        ))}
      </section>

      <section className="rounded-3xl bg-white p-5 ring-1 ring-stone-200">
        <h2 className="text-sm font-semibold">Where the files live</h2>
        <ul className="mt-2 space-y-1 text-xs">
          {inventory.roots.map((root) => (
            <li key={root.key} className="flex flex-wrap items-center gap-2">
              <RootChip root={root.key} />
              <span className="break-all font-mono">{root.path}</span>
              <span className={root.exists ? "text-emerald-700" : "text-red-700"}>{root.exists ? "present" : "MISSING"}</span>
              <span className="text-stone-500">{root.label}</span>
            </li>
          ))}
        </ul>
        {inventory.warnings.map((warning) => (
          <p key={warning} className="mt-3 rounded-xl bg-amber-50 p-3 text-xs text-amber-900 ring-1 ring-amber-300">{warning}</p>
        ))}
        <p className="mt-3 text-xs text-stone-500">
          {totals.with_revisions} projects carry correction revisions · {totals.with_furniture} carry furniture · {totals.annotation_only} are annotation-only ·
          {" "}{totals.empty_folders} project folders are empty · {totals.scratch_projects} are scratch/test runs · {totals.blend_files} .blend files · {totals.render_sets} render sets.
          Generated {shortTime(inventory.generated_at)}.
        </p>
      </section>

      <section className="flex flex-wrap items-center gap-2 rounded-3xl bg-white p-4 ring-1 ring-stone-200">
        {FILTERS.map((option) => (
          <button
            key={option.id}
            onClick={() => setFilter(option.id)}
            className={`rounded-full px-4 py-2 text-sm ${filter === option.id ? "bg-slate-900 text-white" : "bg-stone-200"}`}
          >{option.label}</button>
        ))}
        <label className="ml-auto flex items-center gap-2 text-xs">
          <input type="checkbox" checked={hideScratch} onChange={(event) => setHideScratch(event.target.checked)} />
          Hide scratch/test runs
        </label>
        <input
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Filter by project id or house type"
          className="rounded-full border border-stone-300 px-4 py-2 text-sm"
        />
      </section>

      <p className="text-sm text-stone-600">
        {filtered.length} of {inventory.projects.length} projects · newest activity first.
        {tiles ? " Rechtsklick auf eine Kachel für Annotator / Workbench. Grün = schon gerendert." : ""}
      </p>

      <section className="space-y-4">
        {tiles
          ? <ProjectTiles projects={filtered} />
          : filtered.map((project) => <ProjectCard key={project.project_id} project={project} />)}
        {filtered.length === 0 && <p className="rounded-3xl bg-white p-6 text-sm text-stone-600 ring-1 ring-stone-200">Nothing matches this filter.</p>}
      </section>
    </main>
    </OpenOnlyContext.Provider>
  );
}

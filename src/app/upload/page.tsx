"use client";

import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";

const sourceTypes = [
  {
    value: "bestseller",
    label: "Bestseller",
    hint: "Eigene Verkaufsrenner, Katalogpläne, gute Marktbeispiele",
  },
  {
    value: "simplifier",
    label: "Simplifier-Paket",
    hint: "Unsere annotierten Trainingspakete mit JSON, PNG und SVG",
  },
  {
    value: "cubicasa",
    label: "CubiCasa-Referenz",
    hint: "Externe Beispiele nur als semantische Zusatzreferenz",
  },
  {
    value: "user_test",
    label: "Testlauf / Kritik",
    hint: "Material aus echten Testläufen, Screenshots oder Korrekturen",
  },
  {
    value: "other",
    label: "Sonstiges",
    hint: "Alles, was noch nicht sauber einsortiert ist",
  },
] as const;

type SourceType = (typeof sourceTypes)[number]["value"];

const reviewStatuses = [
  { value: "uploaded", label: "hochgeladen", tone: "bg-stone-100 text-stone-700" },
  { value: "reviewed", label: "gesichtet", tone: "bg-sky-50 text-sky-900" },
  { value: "usable", label: "brauchbar", tone: "bg-emerald-50 text-emerald-900" },
  { value: "not_usable", label: "nicht brauchbar", tone: "bg-red-50 text-red-900" },
  { value: "normalize", label: "normalisieren", tone: "bg-amber-50 text-amber-900" },
  { value: "normalized", label: "normalisiert", tone: "bg-purple-50 text-purple-900" },
] as const;

type ReviewStatus = (typeof reviewStatuses)[number]["value"];

type TrainingUpload = {
  id: string;
  created_at: string;
  source_type: SourceType;
  storage_path: string;
  original_filename: string;
  mime_type: string | null;
  size_bytes: number | null;
  notes: string;
  review_notes: string;
  status: ReviewStatus | "rejected";
};

function formatBytes(bytes: number | null) {
  if (!bytes) return "unbekannt";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
}

function statusLabel(status: string) {
  return reviewStatuses.find((item) => item.value === status)?.label ?? status;
}

function statusTone(status: string) {
  return reviewStatuses.find((item) => item.value === status)?.tone ?? "bg-stone-100 text-stone-700";
}

type PresignResponse = {
  upload_id?: string;
  storage_provider?: string;
  storage_bucket?: string;
  storage_path?: string;
  upload_url?: string;
  error?: string;
};

export default function UploadPage() {
  const [sourceType, setSourceType] = useState<SourceType>("bestseller");
  const [notes, setNotes] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [uploads, setUploads] = useState<TrainingUpload[]>([]);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [isUploading, setIsUploading] = useState(false);
  const [reviewDrafts, setReviewDrafts] = useState<Record<string, { status: ReviewStatus; review_notes: string }>>({});
  const [savingReviewId, setSavingReviewId] = useState<string | null>(null);

  async function loadUploads() {
    const response = await fetch("/api/training-uploads", {
      method: "GET",
      cache: "no-store",
    });
    const result = (await response.json()) as { uploads?: TrainingUpload[]; error?: string };

    if (!response.ok) {
      setError(`Upload-Liste konnte noch nicht geladen werden: ${result.error ?? "unbekannter Fehler"}`);
      return;
    }

    const nextUploads = result.uploads ?? [];
    setUploads(nextUploads);
    setReviewDrafts((current) => {
      const next = { ...current };
      for (const upload of nextUploads) {
        if (!next[upload.id]) {
          next[upload.id] = {
            status: upload.status === "rejected" ? "not_usable" : upload.status,
            review_notes: upload.review_notes ?? "",
          };
        }
      }
      return next;
    });
  }

  useEffect(() => {
    void loadUploads();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setStatus("");

    if (!file) {
      setError("Bitte zuerst eine Datei auswählen.");
      return;
    }

    setIsUploading(true);

    const presignResponse = await fetch("/api/storage/presign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_type: sourceType,
        filename: file.name,
      }),
    });
    const presignResult = (await presignResponse.json()) as PresignResponse;

    if (!presignResponse.ok || !presignResult.upload_url || !presignResult.storage_path) {
      setIsUploading(false);
      setError(
        `Upload ist noch nicht aktiv: ${presignResult.error ?? "Object Storage ist noch nicht konfiguriert."}`,
      );
      return;
    }

    const uploadResponse = await fetch(presignResult.upload_url, {
      method: "PUT",
      body: file,
    });

    if (!uploadResponse.ok) {
      setIsUploading(false);
      setError(
        `Datei konnte nicht in den Object Storage hochgeladen werden (${uploadResponse.status}). Bitte prüfen: Bucket, CORS-Regeln und R2/S3-Zugangsdaten.`,
      );
      return;
    }

    const insertResponse = await fetch("/api/training-uploads", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: presignResult.upload_id,
        source_type: sourceType,
        storage_provider: presignResult.storage_provider ?? "s3",
        storage_bucket: presignResult.storage_bucket,
        storage_path: presignResult.storage_path,
        original_filename: file.name,
        mime_type: file.type || null,
        size_bytes: file.size,
        notes,
        metadata: {
          collected_for: "floorplan_generator_training",
          app_route: "/upload",
        },
      }),
    });
    const insertResult = (await insertResponse.json()) as { error?: string };

    setIsUploading(false);

    if (!insertResponse.ok) {
      setError(
        `Datei ist im Storage, aber der Datenbankeintrag fehlt: ${insertResult.error ?? "unbekannter Fehler"}. Das ist reparierbar, aber die Datenbank/Variablen müssen geprüft werden.`,
      );
      return;
    }

    setStatus("Upload gespeichert. Das Material ist jetzt für Sichtung und spätere Normalisierung vorgemerkt.");
    setFile(null);
    setNotes("");
    await loadUploads();
  }

  async function saveReview(uploadId: string) {
    const draft = reviewDrafts[uploadId];
    if (!draft) return;

    setError("");
    setStatus("");
    setSavingReviewId(uploadId);

    const response = await fetch("/api/training-uploads", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        id: uploadId,
        status: draft.status,
        review_notes: draft.review_notes,
      }),
    });
    const result = (await response.json()) as { upload?: TrainingUpload; error?: string };

    setSavingReviewId(null);

    if (!response.ok || !result.upload) {
      setError(`Sichtung konnte nicht gespeichert werden: ${result.error ?? "unbekannter Fehler"}`);
      return;
    }

    setUploads((current) => current.map((upload) => (upload.id === uploadId ? result.upload! : upload)));
    setStatus("Sichtung gespeichert. Dieses Material ist jetzt besser für die spätere Normalisierung einsortiert.");
  }

  return (
    <main className="min-h-screen bg-[#f3f1eb] px-6 py-8 text-stone-900 lg:px-10">
      <div className="mx-auto max-w-6xl">
        <nav className="flex flex-wrap items-center justify-between gap-4">
          <Link href="/" className="text-sm font-bold tracking-[0.2em] uppercase">
            Born2Thrill
          </Link>
          <div className="flex flex-wrap gap-3 text-sm font-semibold">
            <Link href="/testlauf" className="rounded-full border border-stone-300 px-4 py-2 hover:border-stone-900">
              Testlauf
            </Link>
            <Link href="/questionnaire?test=1" className="rounded-full border border-stone-300 px-4 py-2 hover:border-stone-900">
              Fragebogen
            </Link>
            <a href="#sichtung" className="rounded-full border border-stone-300 px-4 py-2 hover:border-stone-900">
              Sichtung
            </a>
          </div>
        </nav>

        <section className="mt-12 grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <div>
            <p className="text-xs font-semibold tracking-[0.24em] text-emerald-800 uppercase">
              Trainingsmaterial sammeln
            </p>
            <h1 className="mt-5 max-w-2xl text-4xl font-medium tracking-[-0.04em] sm:text-6xl">
              Upload für Grundriss-Beispiele
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-8 text-stone-600">
              Hier laden wir Bestseller, CubiCasa-Referenzen, Simplifier-Pakete und Testmaterial hoch. Der Generator lernt noch nicht automatisch daraus — aber wir bauen damit den sauberen Datenpool, den er später braucht.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="rounded-[2rem] bg-white p-6 shadow-sm ring-1 ring-stone-200 sm:p-8">
            <label className="block text-sm font-semibold text-stone-700" htmlFor="source-type">
              Kategorie
            </label>
            <select
              id="source-type"
              value={sourceType}
              onChange={(event) => setSourceType(event.target.value as SourceType)}
              className="mt-2 w-full rounded-2xl border border-stone-300 bg-white px-4 py-3 text-base outline-none focus:border-emerald-800"
            >
              {sourceTypes.map((type) => (
                <option key={type.value} value={type.value}>
                  {type.label}
                </option>
              ))}
            </select>
            <p className="mt-2 text-sm text-stone-500">
              {sourceTypes.find((type) => type.value === sourceType)?.hint}
            </p>

            <label className="mt-6 block text-sm font-semibold text-stone-700" htmlFor="training-file">
              Datei
            </label>
            <input
              id="training-file"
              type="file"
              accept=".pdf,.png,.jpg,.jpeg,.svg,.zip,application/pdf,image/png,image/jpeg,image/svg+xml,application/zip"
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
              className="mt-2 w-full rounded-2xl border border-dashed border-stone-300 bg-[#faf9f6] px-4 py-6 text-sm"
            />
            {file && (
              <p className="mt-2 text-sm text-stone-500">
                Ausgewählt: {file.name} · {formatBytes(file.size)}
              </p>
            )}

            <label className="mt-6 block text-sm font-semibold text-stone-700" htmlFor="notes">
              Notiz
            </label>
            <textarea
              id="notes"
              value={notes}
              onChange={(event) => setNotes(event.target.value)}
              rows={5}
              placeholder="Warum ist diese Datei wichtig? Beispiel: Bestseller 145 m², gute Treppenlage, offener Wohn-Ess-Kochbereich…"
              className="mt-2 w-full rounded-2xl border border-stone-300 px-4 py-3 text-base outline-none focus:border-emerald-800"
            />

            <button
              type="submit"
              disabled={isUploading}
              className="mt-6 w-full rounded-full bg-[#18392f] px-6 py-4 text-sm font-semibold text-white hover:bg-[#245446] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isUploading ? "Upload läuft…" : "Hochladen und vormerken"}
            </button>

            <p className="mt-4 rounded-2xl bg-amber-50 p-4 text-sm font-semibold text-amber-900">
              Uploads gehen jetzt über Object Storage, z. B. Cloudflare R2. Wenn noch keine R2/S3-Variablen in Railway gesetzt sind, meldet die App das beim Hochladen klar zurück.
            </p>
            {status && <p className="mt-4 rounded-2xl bg-emerald-50 p-4 text-sm font-semibold text-emerald-900">{status}</p>}
            {error && <p className="mt-4 rounded-2xl bg-red-50 p-4 text-sm font-semibold text-red-900">{error}</p>}
          </form>
        </section>

        <section id="sichtung" className="mt-10 rounded-[2rem] bg-white p-6 shadow-sm ring-1 ring-stone-200 sm:p-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">
                Letzte Uploads
              </p>
              <h2 className="mt-2 text-2xl font-medium">Materialsammlung & Sichtung</h2>
              <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-600">
                Hier sortieren wir hochgeladene Dateien für die 10 Goldstandard-Beispiele vor. Noch kein Training — aber ab hier entsteht der brauchbare Datenpool.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void loadUploads()}
              className="rounded-full border border-stone-300 px-4 py-2 text-sm font-semibold hover:border-stone-900"
            >
              Aktualisieren
            </button>
          </div>

          <div className="mt-6 overflow-hidden rounded-3xl border border-stone-200">
            {uploads.length === 0 ? (
              <p className="p-6 text-stone-500">
                Noch keine Uploads sichtbar. Lade zuerst ein Beispiel hoch oder prüfe die Datenbankverbindung.
              </p>
            ) : (
              <div className="divide-y divide-stone-200">
                {uploads.map((upload) => (
                  <article key={upload.id} className="grid gap-5 p-5 lg:grid-cols-[180px_1fr_320px]">
                    <div>
                      <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900">
                        {sourceTypes.find((type) => type.value === upload.source_type)?.label ?? upload.source_type}
                      </span>
                      <span className={`mt-3 inline-block rounded-full px-3 py-1 text-xs font-bold ${statusTone(upload.status)}`}>
                        {statusLabel(upload.status)}
                      </span>
                      <p className="mt-3 text-xs text-stone-500">
                        {new Date(upload.created_at).toLocaleString("de-DE")}
                      </p>
                      <p className="mt-1 text-xs text-stone-500">{formatBytes(upload.size_bytes)}</p>
                    </div>
                    <div>
                      <h3 className="font-semibold">{upload.original_filename}</h3>
                      <p className="mt-1 break-all text-sm text-stone-500">{upload.storage_path}</p>
                      {upload.notes && (
                        <p className="mt-3 rounded-2xl bg-stone-50 p-3 text-sm leading-6 text-stone-700">
                          <span className="font-semibold">Upload-Notiz:</span> {upload.notes}
                        </p>
                      )}
                      {upload.review_notes && (
                        <p className="mt-3 rounded-2xl bg-emerald-50 p-3 text-sm leading-6 text-emerald-950">
                          <span className="font-semibold">Sichtung:</span> {upload.review_notes}
                        </p>
                      )}
                    </div>
                    <div className="rounded-3xl bg-[#faf9f6] p-4">
                      <label className="block text-xs font-bold tracking-[0.16em] text-stone-500 uppercase" htmlFor={`review-status-${upload.id}`}>
                        Status
                      </label>
                      <select
                        id={`review-status-${upload.id}`}
                        value={reviewDrafts[upload.id]?.status ?? (upload.status === "rejected" ? "not_usable" : upload.status)}
                        onChange={(event) =>
                          setReviewDrafts((current) => ({
                            ...current,
                            [upload.id]: {
                              status: event.target.value as ReviewStatus,
                              review_notes: current[upload.id]?.review_notes ?? upload.review_notes ?? "",
                            },
                          }))
                        }
                        className="mt-2 w-full rounded-2xl border border-stone-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-800"
                      >
                        {reviewStatuses.map((item) => (
                          <option key={item.value} value={item.value}>
                            {item.label}
                          </option>
                        ))}
                      </select>

                      <label className="mt-4 block text-xs font-bold tracking-[0.16em] text-stone-500 uppercase" htmlFor={`review-notes-${upload.id}`}>
                        Bewertungsnotiz
                      </label>
                      <textarea
                        id={`review-notes-${upload.id}`}
                        value={reviewDrafts[upload.id]?.review_notes ?? upload.review_notes ?? ""}
                        onChange={(event) =>
                          setReviewDrafts((current) => ({
                            ...current,
                            [upload.id]: {
                              status: current[upload.id]?.status ?? (upload.status === "rejected" ? "not_usable" : upload.status),
                              review_notes: event.target.value,
                            },
                          }))
                        }
                        rows={4}
                        placeholder="z. B. gute Treppenlage, kurzer Flur, Technik/Bad sinnvoll gebündelt…"
                        className="mt-2 w-full rounded-2xl border border-stone-300 bg-white px-3 py-2 text-sm outline-none focus:border-emerald-800"
                      />

                      <button
                        type="button"
                        onClick={() => void saveReview(upload.id)}
                        disabled={savingReviewId === upload.id}
                        className="mt-4 w-full rounded-full bg-[#18392f] px-4 py-3 text-sm font-semibold text-white hover:bg-[#245446] disabled:cursor-not-allowed disabled:opacity-60"
                      >
                        {savingReviewId === upload.id ? "Speichert…" : "Sichtung speichern"}
                      </button>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}

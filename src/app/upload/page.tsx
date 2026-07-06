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

type TrainingUpload = {
  id: string;
  created_at: string;
  source_type: SourceType;
  storage_path: string;
  original_filename: string;
  mime_type: string | null;
  size_bytes: number | null;
  notes: string;
  status: string;
};

function formatBytes(bytes: number | null) {
  if (!bytes) return "unbekannt";
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} KB`;
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`;
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

    setUploads(result.uploads ?? []);
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

        <section className="mt-10 rounded-[2rem] bg-white p-6 shadow-sm ring-1 ring-stone-200 sm:p-8">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">
                Letzte Uploads
              </p>
              <h2 className="mt-2 text-2xl font-medium">Materialsammlung</h2>
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
                Noch keine Uploads sichtbar. Falls du schon etwas hochgeladen hast, muss wahrscheinlich zuerst die Supabase-Migration ausgeführt werden.
              </p>
            ) : (
              <div className="divide-y divide-stone-200">
                {uploads.map((upload) => (
                  <article key={upload.id} className="grid gap-3 p-5 md:grid-cols-[180px_1fr_140px]">
                    <div>
                      <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-900">
                        {sourceTypes.find((type) => type.value === upload.source_type)?.label ?? upload.source_type}
                      </span>
                      <p className="mt-3 text-xs text-stone-500">
                        {new Date(upload.created_at).toLocaleString("de-DE")}
                      </p>
                    </div>
                    <div>
                      <h3 className="font-semibold">{upload.original_filename}</h3>
                      <p className="mt-1 break-all text-sm text-stone-500">{upload.storage_path}</p>
                      {upload.notes && <p className="mt-3 text-sm leading-6 text-stone-700">{upload.notes}</p>}
                    </div>
                    <div className="text-sm text-stone-500 md:text-right">
                      <p>{formatBytes(upload.size_bytes)}</p>
                      <p className="mt-1">{upload.status}</p>
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

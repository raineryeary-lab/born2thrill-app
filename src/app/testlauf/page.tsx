"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  generateVariants,
  parseBrief,
  type FloorPlan,
  type HouseBrief,
  type PlanVariant,
} from "@/lib/generator/floorplan";

type FeedbackRating = "up" | "down";

type TestlaufFeedback = {
  id: string;
  createdAt: string;
  rating: FeedbackRating;
  reason: string;
  variantId: string;
  variantName: string;
  score: number;
  brief: HouseBrief;
  metrics: PlanVariant["metrics"];
  failedChecks: string[];
};

function FloorSvg({ plan }: { plan: FloorPlan }) {
  const stair = plan.stair;
  return (
    <svg viewBox="0 0 700 500" className="w-full rounded-xl bg-[#faf9f6]" aria-label={`Grundriss ${plan.name}`}>
      <rect x="20" y="20" width="660" height="460" fill="white" stroke="#1c1917" strokeWidth="8" />
      <rect x="220" y="24" width="260" height="452" fill="#f0eee8" stroke="#78716c" strokeWidth="2" />
      <text x="248" y="55" textAnchor="middle" fontSize="12" fill="#57534e">FLUR</text>
      {plan.hasStair && stair && (
        <g>
          <rect x="284" y="66" width="132" height="184" rx="3" fill="#e7e5e4" stroke="#292524" strokeWidth="2" />
          <rect x="284" y="66" width="132" height="58" fill="#d6d3d1" stroke="#292524" strokeWidth="1.5" />
          <line x1="345" x2="345" y1="124" y2="250" stroke="#292524" strokeWidth="2" />
          {Array.from({ length: 7 }, (_, index) => (
            <g key={index}>
              <line x1="284" x2="345" y1={142 + index * 16} y2={142 + index * 16} stroke="#78716c" />
              <line x1="345" x2="416" y1={142 + index * 16} y2={142 + index * 16} stroke="#78716c" />
            </g>
          ))}
          <path d="M314 235 L314 137 M314 137 L307 150 M314 137 L321 150" fill="none" stroke="#18392f" strokeWidth="3" />
          <path d="M380 137 L380 235 M380 235 L373 222 M380 235 L387 222" fill="none" stroke="#18392f" strokeWidth="3" />
          <rect x="224" y="66" width="52" height="270" fill="#fff" fillOpacity=".45" stroke="#0f766e" strokeDasharray="5 4" />
          <rect x="424" y="66" width="52" height="270" fill="#fff" fillOpacity=".45" stroke="#0f766e" strokeDasharray="5 4" />
          <text x="250" y="200" textAnchor="middle" fontSize="10" fill="#0f766e" transform="rotate(-90 250 200)">1,00 m FREIER WEG</text>
          <text x="450" y="200" textAnchor="middle" fontSize="10" fill="#0f766e" transform="rotate(90 450 200)">1,00 m FREIER WEG</text>
          <rect x="284" y="258" width="132" height="62" fill="none" stroke="#0f766e" strokeDasharray="6 4" />
          <text x="350" y="286" textAnchor="middle" fontSize="10" fill="#0f766e">FREIE ANKUNFT</text>
          <text x="350" y="302" textAnchor="middle" fontSize="9" fill="#57534e">mind. {stair.clearArrivalDepthM.toFixed(2)} m</text>
          <text x="350" y="45" textAnchor="middle" fontSize="10" fill="#57534e">U-TREPPE {stair.footprintWidthM.toFixed(2)} × {stair.footprintLengthM.toFixed(2)} m</text>
        </g>
      )}
      {plan.floor === 0 && (
        <g>
          <line x1="330" y1="480" x2="370" y2="480" stroke="white" strokeWidth="10" />
          <path d="M330 476 A40 40 0 0 1 370 436" fill="none" stroke="#0f766e" strokeWidth="2" />
        </g>
      )}
      {plan.rooms.map((room) => {
        const doorX = room.side === "left" ? room.x + room.width : room.x;
        const windowX = room.side === "left" ? room.x : room.x + room.width;
        const cy = room.y + room.height / 2;
        const fill = room.kind === "wet" ? "#dbeafe" : room.kind === "living" ? "#dcfce7" : room.kind === "service" ? "#fef3c7" : "#f5f5f4";
        return (
          <g key={room.id}>
            <rect x={room.x} y={room.y} width={room.width} height={room.height} fill={fill} stroke="#57534e" strokeWidth="2" />
            <text x={room.x + room.width / 2} y={cy - 5} textAnchor="middle" fontSize="15" fontWeight="600" fill="#292524">{room.name}</text>
            <text x={room.x + room.width / 2} y={cy + 16} textAnchor="middle" fontSize="12" fill="#78716c">ca. {room.area} m²</text>
            <line x1={windowX} x2={windowX} y1={cy - 23} y2={cy + 23} stroke="white" strokeWidth="10" />
            <line x1={windowX} x2={windowX} y1={cy - 20} y2={cy + 20} stroke="#0ea5e9" strokeWidth="5" />
            <line x1={doorX} x2={doorX} y1={cy - 17} y2={cy + 17} stroke="white" strokeWidth="8" />
            <path
              d={room.side === "left" ? `M${doorX} ${cy + 17} A34 34 0 0 0 ${doorX - 34} ${cy - 17}` : `M${doorX} ${cy + 17} A34 34 0 0 1 ${doorX + 34} ${cy - 17}`}
              fill="none" stroke="#0f766e" strokeWidth="2"
            />
          </g>
        );
      })}
      <text x="30" y="16" fontSize="11" fill="#78716c">N ↑</text>
    </svg>
  );
}

function HouseRendering({ brief }: { brief: HouseBrief }) {
  const flat = brief.roof === "flat";
  return (
    <svg viewBox="0 0 900 520" className="w-full rounded-2xl bg-[#dfe8e2]" aria-label="Generierte Hausansicht">
      <defs>
        <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#c9ddd9" /><stop offset="1" stopColor="#f4efe6" /></linearGradient>
        <linearGradient id="facade" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#f8f5ed" /><stop offset="1" stopColor="#d8d1c5" /></linearGradient>
      </defs>
      <rect width="900" height="520" fill="url(#sky)" />
      <circle cx="710" cy="95" r="42" fill="#fff4c4" opacity=".8" />
      <path d="M0 405 Q180 360 330 401 T650 392 T900 385 V520 H0Z" fill="#73936f" />
      <path d="M80 445 Q300 395 520 445 T900 430" fill="none" stroke="#b6a184" strokeWidth="26" opacity=".6" />
      <rect x="235" y={brief.floors > 1 ? 190 : 270} width="450" height={brief.floors > 1 ? 235 : 155} fill="url(#facade)" stroke="#554b40" strokeWidth="3" />
      {flat ? (
        <rect x="220" y={brief.floors > 1 ? 174 : 254} width="480" height="24" fill="#4b4b45" />
      ) : (
        <path d={brief.floors > 1 ? "M205 195 L460 75 L715 195Z" : "M205 275 L460 155 L715 275Z"} fill="#4f4a43" stroke="#352f2a" strokeWidth="4" />
      )}
      {Array.from({ length: brief.floors > 1 ? 2 : 1 }, (_, row) =>
        [285, 410, 555].map((x) => (
          <g key={`${row}-${x}`}>
            <rect x={x} y={brief.floors > 1 ? 230 + row * 100 : 310} width="72" height="65" fill="#8fb4bf" stroke="#3f4d50" strokeWidth="4" />
            <line x1={x + 36} x2={x + 36} y1={brief.floors > 1 ? 230 + row * 100 : 310} y2={brief.floors > 1 ? 295 + row * 100 : 375} stroke="#e9f2f2" strokeWidth="3" />
          </g>
        )),
      )}
      <rect x="442" y={brief.floors > 1 ? 332 : 332} width="52" height="93" fill="#8d6d4f" />
      <path d="M120 420 Q145 330 170 420 M735 420 Q760 315 790 420" stroke="#355f3d" strokeWidth="18" fill="none" />
      <text x="35" y="45" fontSize="16" fill="#38534d">KONZEPTANSICHT · {brief.projectName.toUpperCase()}</text>
      <text x="35" y="70" fontSize="12" fill="#59716b">{brief.style.replaceAll("-", " ")} · Garten {brief.gardenDirection}</text>
    </svg>
  );
}

function feedbackLabel(rating: FeedbackRating) {
  return rating === "up" ? "Daumen hoch" : "Daumen runter";
}

export default function TestlaufPage() {
  const [entries, setEntries] = useState<Array<[string, string]>>([]);
  const [selected, setSelected] = useState(0);
  const [feedbackRating, setFeedbackRating] = useState<FeedbackRating | null>(null);
  const [feedbackReason, setFeedbackReason] = useState("");
  const [feedbackStatus, setFeedbackStatus] = useState("");
  const [feedbackCount, setFeedbackCount] = useState(0);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const raw = window.sessionStorage.getItem("born2thrill-test-brief");
      if (raw) setEntries(JSON.parse(raw) as Array<[string, string]>);
      const feedbackRaw = window.localStorage.getItem("born2thrill-test-feedback");
      if (feedbackRaw) setFeedbackCount((JSON.parse(feedbackRaw) as TestlaufFeedback[]).length);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const brief = useMemo(() => parseBrief(entries), [entries]);
  const variants = useMemo(() => generateVariants(brief), [brief]);
  const variant: PlanVariant = variants[selected];

  const saveFeedback = () => {
    if (!feedbackRating) {
      setFeedbackStatus("Bitte zuerst Daumen hoch oder runter auswählen.");
      return;
    }

    const raw = window.localStorage.getItem("born2thrill-test-feedback");
    const existing = raw ? (JSON.parse(raw) as TestlaufFeedback[]) : [];
    const item: TestlaufFeedback = {
      id: `${Date.now()}-${variant.id}`,
      createdAt: new Date().toISOString(),
      rating: feedbackRating,
      reason: feedbackReason.trim(),
      variantId: variant.id,
      variantName: variant.name,
      score: variant.score,
      brief,
      metrics: variant.metrics,
      failedChecks: variant.checks.filter((check) => !check.passed).map((check) => check.label),
    };

    window.localStorage.setItem("born2thrill-test-feedback", JSON.stringify([item, ...existing].slice(0, 100)));
    setFeedbackCount(existing.length + 1);
    setFeedbackReason("");
    setFeedbackStatus(`${feedbackLabel(feedbackRating)} gespeichert. Das wird später unser Lernmaterial.`);
  };

  const saveFeedbackAndTryNext = () => {
    saveFeedback();
    setSelected((current) => (current + 1) % variants.length);
    setFeedbackRating(null);
  };

  return (
    <main className="min-h-screen bg-[#f3f1eb] px-5 py-8 text-stone-900 sm:py-12">
      <div className="mx-auto max-w-7xl">
        <header className="flex items-center justify-between"><Link href="/" className="text-sm font-bold tracking-[0.18em] uppercase">Born2Thrill</Link><span className="text-xs text-amber-700">Generator MVP · Testmodus</span></header>
        <div className="mt-10 rounded-[2rem] bg-[#18392f] p-8 text-white sm:p-12">
          <p className="text-xs font-semibold tracking-[0.2em] text-emerald-200 uppercase">Generierung abgeschlossen</p>
          <div className="mt-4 flex flex-wrap items-end justify-between gap-5"><div><h1 className="text-4xl font-medium tracking-tight">{brief.projectName}</h1><p className="mt-3 text-emerald-100/70">{brief.area} m² · {brief.floors} Geschosse · {brief.bedrooms} Schlafzimmer</p></div><div className="rounded-full bg-emerald-200 px-5 py-2 text-sm font-bold text-emerald-950">Planungswert {variant.score}/100</div></div>
        </div>

        <div className="mt-8 flex gap-3 overflow-x-auto pb-2">
          {variants.map((item, index) => <button key={item.id} onClick={() => setSelected(index)} className={`whitespace-nowrap rounded-full px-5 py-3 text-sm font-semibold ${selected === index ? "bg-[#18392f] text-white" : "bg-white text-stone-600"}`}>{item.name}</button>)}
        </div>

        <section className="mt-6 rounded-[2rem] bg-white p-6 shadow-[0_20px_60px_rgba(41,37,36,.08)] sm:p-10">
          <div className="flex flex-wrap items-start justify-between gap-5"><div><h2 className="text-3xl font-medium">{variant.name}</h2><p className="mt-3 max-w-2xl leading-7 text-stone-600">{variant.description}</p><div className="mt-5 inline-flex rounded-full bg-emerald-50 px-4 py-2 text-xs font-semibold text-emerald-900">Referenz: {variant.metrics.referenceProfile}</div></div><div className="text-right text-sm text-stone-500"><p>{variant.metrics.footprintWidthM} × {variant.metrics.footprintDepthM} m</p><p>{variant.metrics.plannedAreaM2} m² Wohnfläche</p>{variant.metrics.upperFloorAreaM2 > 0 && <p>EG ca. {variant.metrics.groundFloorAreaM2} m² · OG ca. {variant.metrics.upperFloorAreaM2} m²</p>}</div></div>
          <div className="mt-8 grid gap-8 xl:grid-cols-2">{variant.floors.map((floor) => <article key={floor.floor}><h3 className="mb-3 text-sm font-semibold">{floor.name}</h3><FloorSvg plan={floor} /></article>)}</div>
        </section>

        <section className="mt-8 grid gap-8 lg:grid-cols-[1.35fr_.65fr]">
          <div className="rounded-[2rem] bg-white p-6 sm:p-10"><p className="mb-5 text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Konzeptvisualisierung</p><HouseRendering brief={brief} /><p className="mt-4 text-xs leading-5 text-stone-500">Stilistische Konzeptansicht. Kubatur, Öffnungen und Dachform werden in späteren Stufen aus dem freigegebenen Grundrissmodell abgeleitet.</p></div>
          <div className="rounded-[2rem] bg-white p-6 sm:p-8"><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Regelprüfung</p><div className="mt-6 space-y-4">{variant.checks.map((check) => <div key={check.label} className="flex gap-3 text-sm leading-6"><span className={`mt-1 flex size-5 shrink-0 items-center justify-center rounded-full text-xs ${check.passed ? "bg-emerald-100 text-emerald-800" : "bg-red-100 text-red-700"}`}>{check.passed ? "✓" : "!"}</span><span>{check.label}</span></div>)}</div>{variant.floors[0]?.stair && <div className="mt-7 rounded-2xl bg-stone-100 p-4 text-xs leading-5 text-stone-600"><p className="font-semibold text-stone-800">Treppengeometrie · Konzeptziel</p><p className="mt-2">Geschosshöhe {variant.floors[0].stair.floorToFloorHeightM.toFixed(2)} m · {variant.floors[0].stair.risers} Steigungen · Auftritt {variant.floors[0].stair.treadDepthCm} cm · Laufbreite {variant.floors[0].stair.usableFlightWidthM.toFixed(2)} m · Podest {variant.floors[0].stair.landingDepthM.toFixed(2)} m</p></div>}<div className="mt-8 border-t border-stone-200 pt-6 text-xs leading-5 text-stone-500">Konservative Konzeptziele für frühe Varianten. Die Treppe muss in der Fachplanung nach DIN 18065, Landesbauordnung, Statik und Brandschutz geprüft werden; dies ist keine Genehmigungs- oder Ausführungsplanung.</div></div>
        </section>

        <section className="mt-8 rounded-[2rem] bg-white p-6 shadow-[0_20px_60px_rgba(41,37,36,.08)] sm:p-10">
          <div className="grid gap-8 lg:grid-cols-[.8fr_1.2fr]">
            <div>
              <p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Learning by doing</p>
              <h2 className="mt-3 text-2xl font-medium">Ist dieser Grundriss brauchbar?</h2>
              <p className="mt-3 leading-7 text-stone-600">
                Bewerte jede Variante kurz. Gute Varianten werden später verstärkt, schlechte Varianten geben uns konkrete Regeln, was der Generator vermeiden soll.
              </p>
              <p className="mt-4 text-xs text-stone-500">Gespeicherte Testbewertungen in diesem Browser: {feedbackCount}</p>
            </div>
            <div>
              <div className="flex flex-wrap gap-3">
                <button
                  type="button"
                  onClick={() => setFeedbackRating("up")}
                  className={`rounded-full px-5 py-3 text-sm font-bold ${feedbackRating === "up" ? "bg-emerald-700 text-white" : "bg-emerald-50 text-emerald-900"}`}
                >
                  👍 Gut / weiter so
                </button>
                <button
                  type="button"
                  onClick={() => setFeedbackRating("down")}
                  className={`rounded-full px-5 py-3 text-sm font-bold ${feedbackRating === "down" ? "bg-red-700 text-white" : "bg-red-50 text-red-900"}`}
                >
                  👎 Nicht gut
                </button>
              </div>
              <label className="mt-5 block text-sm font-semibold text-stone-700" htmlFor="feedback-reason">
                Warum? Was soll besser werden?
              </label>
              <textarea
                id="feedback-reason"
                value={feedbackReason}
                onChange={(event) => setFeedbackReason(event.target.value)}
                rows={4}
                placeholder="z. B. Treppe falsch platziert, Küche zu klein, Flur zu groß, Bad nicht am Installationskern, Fenster fehlen..."
                className="mt-2 w-full rounded-2xl border border-stone-200 bg-stone-50 p-4 text-sm outline-none transition focus:border-emerald-700 focus:bg-white"
              />
              {feedbackStatus && <p className="mt-3 text-sm text-emerald-800">{feedbackStatus}</p>}
              <div className="mt-5 flex flex-wrap gap-3">
                <button type="button" onClick={saveFeedback} className="rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white">
                  Feedback speichern
                </button>
                <button type="button" onClick={saveFeedbackAndTryNext} className="rounded-full border border-stone-300 bg-white px-6 py-3 text-sm font-semibold text-stone-700">
                  Speichern & nächste Variante testen
                </button>
              </div>
            </div>
          </div>
        </section>

        <div className="mt-8 flex flex-wrap gap-3"><Link href="/questionnaire?test=1" className="rounded-full border border-stone-300 bg-white px-6 py-3 text-sm font-semibold">Angaben ändern</Link><button onClick={() => window.print()} className="rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white">Konzept drucken</button></div>
      </div>
    </main>
  );
}

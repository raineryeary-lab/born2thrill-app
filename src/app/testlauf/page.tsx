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

function FloorSvg({ plan }: { plan: FloorPlan }) {
  return (
    <svg viewBox="0 0 700 500" className="w-full rounded-xl bg-[#faf9f6]" aria-label={`Grundriss ${plan.name}`}>
      <rect x="20" y="20" width="660" height="460" fill="white" stroke="#1c1917" strokeWidth="8" />
      <rect x="296" y="24" width="108" height="452" fill="#f0eee8" stroke="#78716c" strokeWidth="2" />
      <text x="350" y="55" textAnchor="middle" fontSize="13" fill="#57534e">FLUR</text>
      {plan.hasStair && (
        <g>
          <rect x="313" y="170" width="74" height="154" rx="3" fill="#e7e5e4" stroke="#292524" strokeWidth="2" />
          {Array.from({ length: 9 }, (_, index) => (
            <line key={index} x1="313" x2="387" y1={184 + index * 15} y2={184 + index * 15} stroke="#78716c" />
          ))}
          <path d="M350 302 L350 192 M350 192 L341 207 M350 192 L359 207" fill="none" stroke="#18392f" strokeWidth="3" />
          <text x="350" y="344" textAnchor="middle" fontSize="11" fill="#57534e">TREPPENKERN</text>
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

export default function TestlaufPage() {
  const [entries, setEntries] = useState<Array<[string, string]>>([]);
  const [selected, setSelected] = useState(0);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const raw = window.sessionStorage.getItem("born2thrill-test-brief");
      if (raw) setEntries(JSON.parse(raw) as Array<[string, string]>);
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  const brief = useMemo(() => parseBrief(entries), [entries]);
  const variants = useMemo(() => generateVariants(brief), [brief]);
  const variant: PlanVariant = variants[selected];

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
          <div className="flex flex-wrap items-start justify-between gap-5"><div><h2 className="text-3xl font-medium">{variant.name}</h2><p className="mt-3 max-w-2xl leading-7 text-stone-600">{variant.description}</p></div><div className="text-right text-sm text-stone-500"><p>{variant.metrics.footprintWidthM} × {variant.metrics.footprintDepthM} m</p><p>{variant.metrics.plannedAreaM2} m² Wohnfläche</p></div></div>
          <div className="mt-8 grid gap-8 xl:grid-cols-2">{variant.floors.map((floor) => <article key={floor.floor}><h3 className="mb-3 text-sm font-semibold">{floor.name}</h3><FloorSvg plan={floor} /></article>)}</div>
        </section>

        <section className="mt-8 grid gap-8 lg:grid-cols-[1.35fr_.65fr]">
          <div className="rounded-[2rem] bg-white p-6 sm:p-10"><p className="mb-5 text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Konzeptvisualisierung</p><HouseRendering brief={brief} /><p className="mt-4 text-xs leading-5 text-stone-500">Stilistische Konzeptansicht. Kubatur, Öffnungen und Dachform werden in späteren Stufen aus dem freigegebenen Grundrissmodell abgeleitet.</p></div>
          <div className="rounded-[2rem] bg-white p-6 sm:p-8"><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Regelprüfung</p><div className="mt-6 space-y-4">{variant.checks.map((check) => <div key={check.label} className="flex gap-3 text-sm leading-6"><span className="mt-1 flex size-5 shrink-0 items-center justify-center rounded-full bg-emerald-100 text-xs text-emerald-800">✓</span><span>{check.label}</span></div>)}</div><div className="mt-8 border-t border-stone-200 pt-6 text-xs leading-5 text-stone-500">MVP-Logik für frühe Konzeptvarianten. Noch keine Genehmigungs- oder Ausführungsplanung.</div></div>
        </section>

        <div className="mt-8 flex flex-wrap gap-3"><Link href="/questionnaire?test=1" className="rounded-full border border-stone-300 bg-white px-6 py-3 text-sm font-semibold">Angaben ändern</Link><button onClick={() => window.print()} className="rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white">Konzept drucken</button></div>
      </div>
    </main>
  );
}

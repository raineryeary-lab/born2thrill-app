"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export default function TestlaufPage() {
  const [hasBrief, setHasBrief] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setHasBrief(Boolean(window.sessionStorage.getItem("born2thrill-test-brief")));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  return (
    <main className="min-h-screen bg-[#f3f1eb] px-5 py-10 text-stone-900 sm:py-16">
      <div className="mx-auto max-w-4xl rounded-[2rem] bg-white p-7 shadow-[0_24px_70px_rgba(41,37,36,0.08)] sm:p-12">
        <p className="text-xs font-semibold tracking-[0.2em] text-amber-700 uppercase">Interner Testlauf</p>
        <h1 className="mt-4 text-4xl font-medium tracking-tight">Übergabe an die Generierungs-Pipeline</h1>
        <p className="mt-4 max-w-2xl leading-7 text-stone-600">
          {hasBrief
            ? "Das Hausprofil wurde ohne E-Mail und Konto übernommen. Hier schließen wir als Nächstes den echten Grundriss-Generator und die Rendering-Engine an."
            : "Für diesen Testlauf wurden noch keine Fragebogendaten gefunden."}
        </p>
        <div className="mt-10 grid gap-3 sm:grid-cols-2">
          {["Raumprogramm prüfen", "Grundrissvarianten erzeugen", "Planungsregeln bewerten", "Außenansicht rendern"].map((item, index) => (
            <div key={item} className="rounded-2xl border border-stone-200 p-5">
              <span className="text-xs text-stone-400">0{index + 1}</span>
              <p className="mt-5 font-semibold">{item}</p>
              <p className="mt-2 text-xs text-amber-700">Schnittstelle vorbereitet</p>
            </div>
          ))}
        </div>
        <Link href="/questionnaire?test=1" className="mt-10 inline-flex rounded-full bg-[#18392f] px-6 py-3 text-sm font-semibold text-white">
          Testangaben bearbeiten
        </Link>
      </div>
    </main>
  );
}

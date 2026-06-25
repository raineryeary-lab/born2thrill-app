import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen overflow-hidden bg-[#f3f1eb] text-stone-900">
      <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-7 lg:px-10">
        <span className="text-sm font-bold tracking-[0.2em] uppercase">Born2Thrill</span>
        <Link href="/login" className="rounded-full border border-stone-300 px-5 py-2.5 text-sm font-semibold hover:border-stone-900">Anmelden</Link>
      </nav>
      <section className="mx-auto grid min-h-[calc(100vh-96px)] max-w-7xl items-center gap-12 px-6 pb-16 lg:grid-cols-[1.05fr_0.95fr] lg:px-10">
        <div className="py-10">
          <p className="text-xs font-semibold tracking-[0.24em] text-emerald-800 uppercase">Konzeptplanung für deutsche Einfamilienhäuser</p>
          <h1 className="mt-7 max-w-3xl text-5xl leading-[0.98] font-medium tracking-[-0.045em] sm:text-7xl">Ein Zuhause, geplant für Ihr echtes Leben.</h1>
          <p className="mt-8 max-w-xl text-lg leading-8 text-stone-600">Aus Grundstück, Raumbedarf, Ausrichtung und Alltag entsteht ein strukturiertes Raumprogramm – die Grundlage für praktische Grundrissideen und stilvolle Visualisierungen.</p>
          <div className="mt-10 flex flex-wrap gap-4">
            <Link href="/questionnaire?test=1" className="rounded-full bg-[#18392f] px-7 py-4 text-sm font-semibold text-white hover:bg-[#245446]">Hausprofil erstellen</Link>
            <a href="#how" className="rounded-full border border-stone-300 px-7 py-4 text-sm font-semibold hover:border-stone-900">So funktioniert es</a>
          </div>
        </div>
        <div className="relative min-h-[480px] overflow-hidden rounded-[2.5rem] bg-[#18392f] p-8 text-white sm:p-12">
          <div className="absolute -top-20 -right-20 size-80 rounded-full border border-emerald-200/20" />
          <div className="absolute top-14 right-14 size-48 rounded-full border border-emerald-200/20" />
          <p className="relative text-xs font-semibold tracking-[0.2em] text-emerald-200 uppercase">Die Planungslogik</p>
          <div className="relative mt-16 grid grid-cols-2 gap-3 text-sm">
            {["Räume & Fläche", "Sonne & Ausblicke", "Kurze Wege", "Gebündelte Leitungen", "Durchgängige Treppen", "Türen & Fenster"].map((item, index) => <div key={item} className={`rounded-2xl border border-white/15 p-5 ${index === 0 || index === 5 ? "bg-emerald-200 text-emerald-950" : "bg-white/5"}`}>{String(index + 1).padStart(2, "0")}<span className="mt-8 block font-semibold">{item}</span></div>)}
          </div>
        </div>
      </section>
      <section id="how" className="bg-white px-6 py-24 lg:px-10">
        <div className="mx-auto max-w-7xl"><p className="text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">Drei durchdachte Schritte</p><div className="mt-10 grid gap-10 md:grid-cols-3">{[["01", "Beschreiben", "Ein geführter Fragebogen übersetzt Wünsche und Rahmenbedingungen in ein strukturiertes Hausprofil."], ["02", "Entwerfen", "Planungsregeln prüfen Raumbeziehungen, Tageslicht, Erschließung, Treppen und Haustechnik."], ["03", "Erleben", "Überzeugende Konzepte werden zu klaren Grundrissen und einer stilvollen Darstellung des Hauses im Grundstück."]].map(([n,t,d]) => <article key={n} className="border-t border-stone-200 pt-6"><span className="text-sm text-stone-400">{n}</span><h2 className="mt-8 text-2xl font-medium">{t}</h2><p className="mt-3 leading-7 text-stone-600">{d}</p></article>)}</div></div>
      </section>
    </main>
  );
}

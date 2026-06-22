import Link from "next/link";
import { createClient } from "@/lib/supabase/server";
import QuestionnaireForm from "./questionnaire-form";

export default async function QuestionnairePage({
  searchParams,
}: {
  searchParams: Promise<{ test?: string; resume?: string }>;
}) {
  const params = await searchParams;
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  const testMode = params.test === "1";

  return (
    <main className="min-h-screen bg-[#f3f1eb] px-5 py-8 text-stone-900 sm:py-12">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 flex items-center justify-between">
          <Link href="/" className="text-sm font-bold tracking-[0.18em] uppercase">Born2Thrill</Link>
          <span className="max-w-[240px] truncate text-xs text-stone-500">
            {testMode ? "Testmodus · ohne E-Mail" : user?.email ?? "Kostenlos · Anmeldung erst am Ende"}
          </span>
        </header>
        <div className="grid gap-8 lg:grid-cols-[300px_1fr]">
          <aside className="rounded-[2rem] bg-[#18392f] p-8 text-white">
            <p className="text-xs font-semibold tracking-[0.2em] text-emerald-200 uppercase">Hausprofil 01</p>
            <h1 className="mt-5 text-3xl font-medium tracking-tight">Ein praktisches Zuhause beginnt mit klaren Rahmenbedingungen.</h1>
            <p className="mt-5 text-sm leading-6 text-emerald-100/70">Ihre Antworten werden zu strukturierten Planungsanforderungen – nicht zu einem vagen Bildprompt. Damit prüfen wir Raumbeziehungen, Tageslicht, Erschließung, Leitungsführung und durchgängige Treppen.</p>
            <div className="mt-10 border-t border-white/15 pt-6 text-xs leading-5 text-emerald-100/60">Nur Konzeptideen. Planungsrecht, Tragwerk, Brandschutz, Energieplanung und Genehmigungsfähigkeit müssen durch qualifizierte Fachleute in Deutschland geprüft werden.</div>
          </aside>
          <section className="rounded-[2rem] bg-white p-6 shadow-[0_24px_70px_rgba(41,37,36,0.08)] sm:p-10">
            <QuestionnaireForm testMode={testMode} resume={params.resume === "1"} />
          </section>
        </div>
      </div>
    </main>
  );
}

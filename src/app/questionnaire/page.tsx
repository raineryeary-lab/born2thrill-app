import Link from "next/link";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import QuestionnaireForm from "./questionnaire-form";

export default async function QuestionnairePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) redirect("/login");

  return (
    <main className="min-h-screen bg-[#f3f1eb] px-5 py-8 text-stone-900 sm:py-12">
      <div className="mx-auto max-w-6xl">
        <header className="mb-8 flex items-center justify-between">
          <Link href="/" className="text-sm font-bold tracking-[0.18em] uppercase">Born2Thrill</Link>
          <span className="max-w-[180px] truncate text-xs text-stone-500">{user.email}</span>
        </header>
        <div className="grid gap-8 lg:grid-cols-[300px_1fr]">
          <aside className="rounded-[2rem] bg-[#18392f] p-8 text-white">
            <p className="text-xs font-semibold tracking-[0.2em] text-emerald-200 uppercase">House brief 01</p>
            <h1 className="mt-5 text-3xl font-medium tracking-tight">A practical home starts with constraints.</h1>
            <p className="mt-5 text-sm leading-6 text-emerald-100/70">Your answers become structured planning requirements—not a vague image prompt. We will use them to test adjacencies, daylight, circulation, plumbing, and stair continuity.</p>
            <div className="mt-10 border-t border-white/15 pt-6 text-xs leading-5 text-emerald-100/60">Concept ideas only. Local planning law, structure, fire safety, energy design, and approvals must be verified by qualified German professionals.</div>
          </aside>
          <section className="rounded-[2rem] bg-white p-6 shadow-[0_24px_70px_rgba(41,37,36,0.08)] sm:p-10">
            <QuestionnaireForm />
          </section>
        </div>
      </div>
    </main>
  );
}

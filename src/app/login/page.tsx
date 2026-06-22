import Link from "next/link";
import { login, signup } from "./actions";

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ error?: string; message?: string }>;
}) {
  const params = await searchParams;

  return (
    <main className="min-h-screen bg-stone-100 px-5 py-10 text-stone-900 sm:py-16">
      <div className="mx-auto grid max-w-5xl overflow-hidden rounded-[2rem] bg-white shadow-[0_30px_90px_rgba(41,37,36,0.12)] lg:grid-cols-[1.05fr_0.95fr]">
        <section className="hidden min-h-[680px] flex-col justify-between bg-[#18392f] p-12 text-stone-50 lg:flex">
          <Link href="/" className="text-sm font-semibold tracking-[0.2em] uppercase">
            Born2Thrill
          </Link>
          <div>
            <p className="mb-5 text-xs font-semibold tracking-[0.24em] text-emerald-200 uppercase">
              From wishes to a buildable idea
            </p>
            <h1 className="max-w-md text-5xl leading-[1.03] font-medium tracking-tight">
              Your home begins with the right questions.
            </h1>
          </div>
          <p className="max-w-sm text-sm leading-6 text-emerald-100/75">
            Concept planning for German Einfamilienhäuser. Every result remains
            an idea for discussion with qualified architects and engineers.
          </p>
        </section>

        <section className="p-7 sm:p-12 lg:p-14">
          <p className="mb-3 text-xs font-semibold tracking-[0.2em] text-emerald-800 uppercase">
            Welcome
          </p>
          <h2 className="text-3xl font-medium tracking-tight">Create your house brief</h2>
          <p className="mt-3 text-sm leading-6 text-stone-500">
            Sign in, or create an account to save your questionnaire and return later.
          </p>

          {(params.error || params.message) && (
            <p
              className={`mt-6 rounded-xl px-4 py-3 text-sm ${
                params.error
                  ? "bg-red-50 text-red-700"
                  : "bg-emerald-50 text-emerald-800"
              }`}
            >
              {params.error ?? params.message}
            </p>
          )}

          <form className="mt-8 space-y-5">
            <label className="block text-sm font-medium">
              Name <span className="font-normal text-stone-400">(for new accounts)</span>
              <input
                name="displayName"
                autoComplete="name"
                className="mt-2 w-full rounded-xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-emerald-700 focus:bg-white"
                placeholder="Anna & Max"
              />
            </label>
            <label className="block text-sm font-medium">
              Email
              <input
                required
                name="email"
                type="email"
                autoComplete="email"
                className="mt-2 w-full rounded-xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-emerald-700 focus:bg-white"
                placeholder="you@example.de"
              />
            </label>
            <label className="block text-sm font-medium">
              Password
              <input
                required
                minLength={8}
                name="password"
                type="password"
                autoComplete="current-password"
                className="mt-2 w-full rounded-xl border border-stone-200 bg-stone-50 px-4 py-3 outline-none transition focus:border-emerald-700 focus:bg-white"
                placeholder="At least 8 characters"
              />
            </label>
            <div className="grid gap-3 pt-2 sm:grid-cols-2">
              <button
                formAction={login}
                className="rounded-full bg-[#18392f] px-5 py-3.5 text-sm font-semibold text-white transition hover:bg-[#245446]"
              >
                Sign in
              </button>
              <button
                formAction={signup}
                className="rounded-full border border-stone-300 px-5 py-3.5 text-sm font-semibold transition hover:border-emerald-800 hover:text-emerald-900"
              >
                Create account
              </button>
            </div>
          </form>
          <Link href="/" className="mt-8 inline-block text-sm text-stone-500 hover:text-stone-900">
            ← Back to overview
          </Link>
        </section>
      </div>
    </main>
  );
}

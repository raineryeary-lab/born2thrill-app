"use server";

import { headers } from "next/headers";
import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

function field(formData: FormData, name: string) {
  return String(formData.get(name) ?? "").trim();
}

function loginRedirect(message: string, mode: "error" | "message" = "error") {
  redirect(`/login?${mode}=${encodeURIComponent(message)}`);
}

function authErrorMessage(code?: string) {
  switch (code) {
    case "invalid_credentials":
      return "E-Mail-Adresse oder Passwort ist nicht korrekt.";
    case "email_not_confirmed":
      return "Bitte bestätigen Sie zuerst Ihre E-Mail-Adresse.";
    case "user_already_exists":
    case "email_exists":
      return "Für diese E-Mail-Adresse besteht bereits ein Konto.";
    case "weak_password":
      return "Das Passwort erfüllt die Sicherheitsanforderungen noch nicht.";
    case "over_email_send_rate_limit":
      return "Bitte warten Sie kurz, bevor Sie eine weitere E-Mail anfordern.";
    default:
      return "Die Anmeldung konnte nicht abgeschlossen werden. Bitte versuchen Sie es erneut.";
  }
}

export async function login(formData: FormData) {
  const email = field(formData, "email");
  const password = field(formData, "password");

  if (!email || password.length < 8) {
    loginRedirect("Bitte geben Sie eine gültige E-Mail-Adresse und ein Passwort mit mindestens 8 Zeichen ein.");
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });

  if (error) loginRedirect(authErrorMessage(error.code));
  redirect("/questionnaire");
}

export async function signup(formData: FormData) {
  const email = field(formData, "email");
  const password = field(formData, "password");
  const displayName = field(formData, "displayName");

  if (!email || password.length < 8) {
    loginRedirect("Bitte geben Sie eine gültige E-Mail-Adresse und ein Passwort mit mindestens 8 Zeichen ein.");
  }

  const requestHeaders = await headers();
  const origin =
    process.env.NEXT_PUBLIC_SITE_URL ??
    (process.env.VERCEL_URL
      ? `https://${process.env.VERCEL_URL}`
      : requestHeaders.get("origin") ?? "http://localhost:3000");
  const supabase = await createClient();
  const { data, error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: { display_name: displayName },
      emailRedirectTo: `${origin}/auth/callback?next=/questionnaire`,
    },
  });

  if (error) loginRedirect(authErrorMessage(error.code));
  if (data.session) redirect("/questionnaire");
  loginRedirect("Bitte bestätigen Sie Ihr Konto über den Link in Ihrer E-Mail.", "message");
}

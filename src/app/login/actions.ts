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

export async function login(formData: FormData) {
  const email = field(formData, "email");
  const password = field(formData, "password");

  if (!email || password.length < 8) {
    loginRedirect("Enter a valid email and a password of at least 8 characters.");
  }

  const supabase = await createClient();
  const { error } = await supabase.auth.signInWithPassword({ email, password });

  if (error) loginRedirect(error.message);
  redirect("/questionnaire");
}

export async function signup(formData: FormData) {
  const email = field(formData, "email");
  const password = field(formData, "password");
  const displayName = field(formData, "displayName");

  if (!email || password.length < 8) {
    loginRedirect("Enter a valid email and a password of at least 8 characters.");
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

  if (error) loginRedirect(error.message);
  if (data.session) redirect("/questionnaire");
  loginRedirect("Check your email to confirm your account.", "message");
}

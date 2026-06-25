"use server";

import { createClient } from "@/lib/supabase/server";
import { headers } from "next/headers";

export type SaveState = {
  error?: string;
  emailSent?: string;
  projectId?: string;
  projectName?: string;
};

function text(formData: FormData, key: string) {
  return String(formData.get(key) ?? "").trim();
}

function number(formData: FormData, key: string) {
  const value = Number(formData.get(key));
  return Number.isFinite(value) ? value : 0;
}

export async function saveQuestionnaire(
  _state: SaveState,
  formData: FormData,
): Promise<SaveState> {
  const name = text(formData, "projectName");
  const area = number(formData, "targetArea");
  const floors = number(formData, "floors");
  const bundesland = text(formData, "bundesland");
  if (area < 60 || area > 500 || floors < 1 || floors > 3) {
    return { error: "Bitte prüfen Sie Wohnfläche und Geschosse." };
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    const email = text(formData, "email");
    if (!/^\S+@\S+\.\S+$/.test(email)) {
      return { error: "Bitte geben Sie eine gültige E-Mail-Adresse ein." };
    }

    const requestHeaders = await headers();
    const origin =
      process.env.NEXT_PUBLIC_SITE_URL ??
      (process.env.VERCEL_URL
        ? `https://${process.env.VERCEL_URL}`
        : requestHeaders.get("origin") ?? "http://localhost:3000");
    const { error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${origin}/auth/callback?next=/questionnaire?resume=1`,
        shouldCreateUser: true,
      },
    });

    if (error) {
      return { error: "Die E-Mail konnte nicht versendet werden. Bitte versuchen Sie es erneut." };
    }
    return { emailSent: email };
  }

  const requirements = {
    version: 1,
    building: {
      type: "einfamilienhaus",
      targetAreaM2: area,
      floors,
      basement: text(formData, "basement"),
      roofPreference: text(formData, "roofPreference"),
      constructionStyle: text(formData, "constructionStyle"),
    },
    household: {
      adults: number(formData, "adults"),
      children: number(formData, "children"),
      accessibility: text(formData, "accessibility") === "yes",
    },
    site: {
      bundesland,
      municipality: text(formData, "municipality"),
      streetDirection: text(formData, "streetDirection"),
      gardenDirection: text(formData, "gardenDirection"),
    },
    rooms: {
      bedrooms: number(formData, "bedrooms"),
      bathrooms: number(formData, "bathrooms"),
      guestWc: text(formData, "guestWc") === "yes",
      office: text(formData, "office") === "yes",
      utilityRoom: text(formData, "utilityRoom") === "yes",
      groundFloorSleeping: text(formData, "groundFloorSleeping") === "yes",
    },
    circulation: floors > 1 ? { stairPreference: text(formData, "stairPreference") } : null,
    living: {
      kitchen: text(formData, "kitchen"),
      gardenConnection: text(formData, "gardenConnection"),
    },
    priorities: formData.getAll("priorities").map(String),
  };

  const { data, error } = await supabase
    .from("projects")
    .insert({
      owner_id: user.id,
      name: name || "Hausprofil",
      notes: text(formData, "notes"),
      requirements,
      status: "draft",
    })
    .select("id, name")
    .single();

  if (error) return { error: "Das Hausprofil konnte nicht gespeichert werden. Bitte versuchen Sie es erneut." };
  return { projectId: data.id, projectName: data.name };
}

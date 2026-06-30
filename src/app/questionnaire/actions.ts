"use server";

import { createClient } from "@/lib/supabase/server";
import { hasDatabaseUrl, query, upsertAppUser } from "@/lib/db/postgres";

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

function numberWithFallback(formData: FormData, key: string, fallback: number) {
  const value = number(formData, key);
  return value > 0 ? value : fallback;
}

export async function saveQuestionnaire(
  _state: SaveState,
  formData: FormData,
): Promise<SaveState> {
  const name = text(formData, "projectName");
  const area = Math.min(500, Math.max(60, numberWithFallback(formData, "targetArea", 145)));
  const floors = Math.min(3, Math.max(1, numberWithFallback(formData, "floors", 2)));
  const bundesland = text(formData, "bundesland");

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    return { projectId: "prototype", projectName: name || "Hausprofil" };
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
      adults: numberWithFallback(formData, "adults", 2),
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
      bedrooms: numberWithFallback(formData, "bedrooms", 3),
      bathrooms: numberWithFallback(formData, "bathrooms", 2),
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

  if (hasDatabaseUrl()) {
    const ownerId = await upsertAppUser({
      email: user.email,
      displayName:
        typeof user.user_metadata?.display_name === "string"
          ? user.user_metadata.display_name
          : null,
      externalAuthProvider: "supabase",
      externalAuthId: user.id,
    });

    if (!ownerId) {
      return { error: "Das Benutzerprofil konnte nicht gespeichert werden. Bitte versuchen Sie es erneut." };
    }

    const result = await query<{ id: string; name: string }>(
      `
        insert into public.projects (
          owner_id,
          name,
          notes,
          requirements,
          status
        )
        values ($1, $2, $3, $4, 'draft')
        returning id, name
      `,
      [ownerId, name || "Hausprofil", text(formData, "notes"), requirements],
    );

    const project = result.rows[0];
    if (!project) return { error: "Das Hausprofil konnte nicht gespeichert werden. Bitte versuchen Sie es erneut." };
    return { projectId: project.id, projectName: project.name };
  }

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

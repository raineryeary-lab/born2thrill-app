"use server";

import { createClient } from "@/lib/supabase/server";

export type SaveState = {
  error?: string;
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
  const supabase = await createClient();
  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();

  if (authError || !user) return { error: "Please sign in again before saving." };

  const name = text(formData, "projectName");
  const area = number(formData, "targetArea");
  const floors = number(formData, "floors");
  const bundesland = text(formData, "bundesland");
  if (!name || !bundesland || area < 60 || area > 500 || floors < 1 || floors > 3) {
    return { error: "Please check the project name, area, floors, and Bundesland." };
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
      name,
      notes: text(formData, "notes"),
      requirements,
      status: "draft",
    })
    .select("id, name")
    .single();

  if (error) return { error: `Could not save the brief: ${error.message}` };
  return { projectId: data.id, projectName: data.name };
}

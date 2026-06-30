import { Pool, type QueryResultRow } from "pg";

let pool: Pool | undefined;

export function hasDatabaseUrl() {
  return Boolean(process.env.DATABASE_URL);
}

export function getPool() {
  const connectionString = process.env.DATABASE_URL;

  if (!connectionString) {
    throw new Error("Missing DATABASE_URL");
  }

  pool ??= new Pool({
    connectionString,
    ssl:
      process.env.PGSSLMODE === "require" || connectionString.includes("sslmode=require")
        ? { rejectUnauthorized: false }
        : undefined,
  });

  return pool;
}

export async function query<T extends QueryResultRow = QueryResultRow>(
  text: string,
  values: unknown[] = [],
) {
  return getPool().query<T>(text, values);
}

export type AppUserInput = {
  email?: string | null;
  displayName?: string | null;
  externalAuthProvider: string;
  externalAuthId: string;
};

export async function upsertAppUser(input: AppUserInput) {
  const result = await query<{ id: string }>(
    `
      insert into public.app_users (
        email,
        display_name,
        external_auth_provider,
        external_auth_id
      )
      values ($1, $2, $3, $4)
      on conflict (external_auth_provider, external_auth_id)
      do update set
        email = excluded.email,
        display_name = coalesce(excluded.display_name, public.app_users.display_name),
        updated_at = timezone('utc', now())
      returning id
    `,
    [input.email ?? null, input.displayName ?? null, input.externalAuthProvider, input.externalAuthId],
  );

  return result.rows[0]?.id;
}

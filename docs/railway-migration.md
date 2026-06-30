# Railway interim deployment plan

This project can be deployed to Railway as a Next.js application, but it is not
currently a pure PostgreSQL app. Supabase is used for multiple platform
features. Do not remove Supabase environment variables until the features below
have replacements.

## 1. App framework and runtime

- Framework: Next.js `16.2.9`
- Router: App Router under `src/app`
- Language: TypeScript
- UI: React `19.2.4`, Tailwind CSS `4`
- Package manager: the repo contains `pnpm-lock.yaml`; use pnpm.
- Build command: `pnpm run build`
- Start command: `pnpm run start:railway`
- Node runtime: use Railway's detected Node runtime. If Railway needs an
  explicit setting later, add it through Railway variables/settings instead of
  hardcoding secrets in the repo.
- Next.js is configured with `output: "standalone"` in `next.config.ts` for
  Railway/Nixpacks-style deployment.
- `railway.json` now tells Railway to build from the repo `Dockerfile`.
- The Dockerfile uses `node:22-bookworm-slim`, so Railway no longer guesses
  Node 18 through Nixpacks.
- `.node-version` and `nixpacks.toml` pin Railway/Nixpacks to Node 22 because
  Next.js 16 requires Node `>=20.9.0`.

## 2. Where Supabase is used

Supabase is currently used in code and SQL:

### Auth

- `src/lib/supabase/server.ts`
  - creates an SSR Supabase client with cookies.
- `src/lib/supabase/proxy.ts`
  - refreshes Supabase sessions and redirects logged-in users away from
    `/login`.
- `proxy.ts`
  - wires the Supabase session refresh into Next.js proxy/middleware.
- `src/app/login/actions.ts`
  - `supabase.auth.signInWithPassword`
  - `supabase.auth.signUp`
- `src/app/auth/callback/route.ts`
  - `supabase.auth.exchangeCodeForSession`
- `src/app/questionnaire/page.tsx`
  - `supabase.auth.getUser`
- `src/app/questionnaire/actions.ts`
  - `supabase.auth.getUser`

### Database through Supabase APIs

- `src/app/questionnaire/actions.ts`
  - uses Railway/Postgres via `DATABASE_URL` when present.
  - falls back to `supabase.from("projects")` when `DATABASE_URL` is missing.
- `src/app/api/training-uploads/route.ts`
  - uses Railway/Postgres via `DATABASE_URL` when present.
  - falls back to `supabase.from("training_uploads")` when `DATABASE_URL` is
    missing.

### Storage

- `src/app/upload/page.tsx`
  - uploads files through `supabase.storage.from("training-uploads").upload(...)`.
- `supabase/migrations/202606300001_training_uploads.sql`
  - creates Supabase Storage bucket metadata and policies using
    `storage.buckets` and `storage.objects`.

### Supabase-specific database features

- `supabase/migrations/202606220001_initial_schema.sql`
  - references `auth.users`
  - uses `auth.uid()` in RLS policies
  - enables Supabase-style Row Level Security policies.
- `supabase/migrations/202606300001_training_uploads.sql`
  - references the Supabase `storage` schema.
  - grants anon/authenticated policies for Supabase REST/Storage access.

### Not currently used

- No Supabase Realtime usage was found.
- No Supabase Edge Function usage was found.

## 3. What can move to Railway PostgreSQL now

Railway PostgreSQL can own plain relational data once the schema no longer
depends on Supabase-only schemas.

Good candidates:

- `projects`
- `generation_jobs`
- `generated_outputs`
- `training_uploads` metadata

Not directly portable without replacement work:

- Supabase Auth users and sessions
- RLS policies using `auth.uid()`
- Supabase Storage buckets/files
- browser-side `supabase.from(...)` calls that depend on Supabase REST + anon key

## 4. Recommended interim architecture

For the least risky interim Railway deployment:

1. Deploy the Next.js app to Railway from GitHub.
2. Add Railway PostgreSQL.
3. Set `DATABASE_URL` from Railway's PostgreSQL service.
4. Keep Supabase variables temporarily for Auth and Storage:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_PROJECT_REF`
   - `SUPABASE_SERVICE_ROLE_KEY` only if a trusted server-side task needs it.
5. Move server-side database writes gradually from `supabase.from(...)` to a
   PostgreSQL client that uses `DATABASE_URL`.
6. Replace file uploads with Railway-compatible object storage before removing
   Supabase Storage. Good options are S3-compatible storage, Cloudflare R2,
   UploadThing, or another managed bucket service.
7. Replace Supabase Auth before removing Supabase completely. Good options are
   Auth.js/NextAuth, Clerk, or a custom email/password flow.

This keeps the app working while the database is migrated in pieces.

## 5. Railway deployment notes

Create these Railway services:

- Service 1: Web app from GitHub repository `raineryeary-lab/born2thrill-app`
- Service 2: Railway PostgreSQL

Set variables on the web app service:

```env
NEXT_PUBLIC_SITE_URL=https://<railway-app-domain>
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Temporary until migrated away from Supabase:
NEXT_PUBLIC_SUPABASE_URL=<current Supabase URL>
NEXT_PUBLIC_SUPABASE_ANON_KEY=<current Supabase anon/publishable key>
SUPABASE_PROJECT_REF=<current Supabase project ref>
```

Only add `SUPABASE_SERVICE_ROLE_KEY` if a server-only migration/admin task
needs it. Never expose it with a `NEXT_PUBLIC_` prefix.

Railway build/start:

```bash
pnpm install --frozen-lockfile
pnpm run build
pnpm run start:railway
```

If Railway auto-detects pnpm, the build command can be simply:

```bash
pnpm run build
```

and the start command:

```bash
pnpm run start:railway
```

## 6. Supabase-to-Railway PostgreSQL migration/export plan

### A. Export Supabase data

Use Supabase's connection string or dashboard backup tools. For command-line
exports, keep credentials outside Git.

Schema-only export:

```bash
pg_dump "$SUPABASE_DATABASE_URL" \
  --schema=public \
  --schema-only \
  --no-owner \
  --no-privileges \
  --file=supabase-public-schema.sql
```

Data-only export for portable public tables:

```bash
pg_dump "$SUPABASE_DATABASE_URL" \
  --schema=public \
  --data-only \
  --no-owner \
  --no-privileges \
  --table=public.projects \
  --table=public.generation_jobs \
  --table=public.generated_outputs \
  --table=public.training_uploads \
  --file=supabase-public-data.sql
```

Do not blindly restore Supabase-specific `auth` or `storage` schemas into
Railway unless you intentionally want to maintain compatibility tables.

### B. Create Railway-compatible schema

Create a new migration set for Railway that:

- keeps `pgcrypto` / `gen_random_uuid()`
- removes references to `auth.users`
- replaces `owner_id references auth.users(id)` with a plain `owner_id uuid`
  or with a new app-owned `users` table, depending on the chosen auth system.
- removes policies that call `auth.uid()`
- removes `storage.buckets` / `storage.objects` policies.
- keeps `training_uploads.storage_path` as metadata only.

A first Railway-compatible schema has been added at:

```text
railway/migrations/001_initial_schema.sql
```

This schema deliberately uses `public.app_users` instead of Supabase
`auth.users`, and stores upload/output paths as metadata only. It does not
create a file bucket by itself.

### C. Restore into Railway

Use Railway's `DATABASE_URL`:

```bash
psql "$RAILWAY_DATABASE_URL" --file=railway-schema.sql
psql "$RAILWAY_DATABASE_URL" --file=supabase-public-data.sql
```

For the included initial schema:

```bash
psql "$RAILWAY_DATABASE_URL" --file=railway/migrations/001_initial_schema.sql
```

### D. Verify

Run row counts before switching traffic:

```sql
select 'projects' as table_name, count(*) from public.projects
union all
select 'generation_jobs', count(*) from public.generation_jobs
union all
select 'generated_outputs', count(*) from public.generated_outputs
union all
select 'training_uploads', count(*) from public.training_uploads;
```

## 7. Code migration plan

Do this in small commits:

1. Add a server-only PostgreSQL client using `DATABASE_URL`. Done in
   `src/lib/db/postgres.ts`.
2. Move questionnaire project inserts from Supabase REST to server-side SQL.
   Done when `DATABASE_URL` is present; Supabase Auth still identifies the user.
3. Move upload metadata inserts/selects from Supabase REST to server-side SQL.
   Done through `/api/training-uploads` when `DATABASE_URL` is present;
   Supabase Storage still stores the file bytes.
4. Keep file upload storage on Supabase until a replacement bucket exists.
5. Replace Supabase Auth or keep Supabase Auth temporarily.
6. Remove `@supabase/*` dependencies only after Auth, REST, and Storage are all
   gone.

Until those steps are complete, Railway is an app host plus PostgreSQL target,
not a full Supabase replacement.

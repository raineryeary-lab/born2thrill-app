begin;

create extension if not exists pgcrypto;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = timezone('utc', now());
  return new;
end;
$$;

create table public.profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  display_name text check (char_length(display_name) <= 120),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid not null references auth.users (id) on delete cascade,
  name text not null check (char_length(name) between 1 and 160),
  notes text not null default '',
  requirements jsonb not null default '{}'::jsonb,
  status text not null default 'draft'
    check (status in ('draft', 'ready', 'processing', 'completed', 'archived')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table public.floorplan_uploads (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  storage_bucket text not null default 'floorplans',
  storage_path text not null,
  original_filename text not null,
  mime_type text,
  size_bytes bigint check (size_bytes is null or size_bytes >= 0),
  created_at timestamptz not null default timezone('utc', now()),
  unique (storage_bucket, storage_path)
);

create table public.generation_jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects (id) on delete cascade,
  owner_id uuid not null references auth.users (id) on delete cascade,
  job_type text not null
    check (job_type in ('floorplan', 'render', 'export')),
  status text not null default 'queued'
    check (status in ('queued', 'running', 'succeeded', 'failed', 'cancelled')),
  progress smallint not null default 0 check (progress between 0 and 100),
  input jsonb not null default '{}'::jsonb,
  error_message text,
  started_at timestamptz,
  finished_at timestamptz,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  check (finished_at is null or started_at is not null)
);

create table public.generated_outputs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references public.projects (id) on delete cascade,
  job_id uuid references public.generation_jobs (id) on delete set null,
  owner_id uuid not null references auth.users (id) on delete cascade,
  output_type text not null
    check (output_type in ('floorplan', 'render', 'model', 'pdf', 'other')),
  storage_bucket text not null default 'generated-outputs',
  storage_path text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  unique (storage_bucket, storage_path)
);

create index projects_owner_id_idx on public.projects (owner_id);
create index floorplan_uploads_project_id_idx on public.floorplan_uploads (project_id);
create index floorplan_uploads_owner_id_idx on public.floorplan_uploads (owner_id);
create index generation_jobs_project_id_idx on public.generation_jobs (project_id);
create index generation_jobs_owner_status_idx on public.generation_jobs (owner_id, status);
create index generated_outputs_project_id_idx on public.generated_outputs (project_id);
create index generated_outputs_job_id_idx on public.generated_outputs (job_id);
create index generated_outputs_owner_id_idx on public.generated_outputs (owner_id);

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create trigger projects_set_updated_at
before update on public.projects
for each row execute function public.set_updated_at();

create trigger generation_jobs_set_updated_at
before update on public.generation_jobs
for each row execute function public.set_updated_at();

alter table public.profiles enable row level security;
alter table public.projects enable row level security;
alter table public.floorplan_uploads enable row level security;
alter table public.generation_jobs enable row level security;
alter table public.generated_outputs enable row level security;

create policy "Users can read their profile"
on public.profiles for select
to authenticated
using ((select auth.uid()) = id);

create policy "Users can create their profile"
on public.profiles for insert
to authenticated
with check ((select auth.uid()) = id);

create policy "Users can update their profile"
on public.profiles for update
to authenticated
using ((select auth.uid()) = id)
with check ((select auth.uid()) = id);

create policy "Owners can read projects"
on public.projects for select
to authenticated
using ((select auth.uid()) = owner_id);

create policy "Owners can create projects"
on public.projects for insert
to authenticated
with check ((select auth.uid()) = owner_id);

create policy "Owners can update projects"
on public.projects for update
to authenticated
using ((select auth.uid()) = owner_id)
with check ((select auth.uid()) = owner_id);

create policy "Owners can delete projects"
on public.projects for delete
to authenticated
using ((select auth.uid()) = owner_id);

create policy "Owners can read floorplan uploads"
on public.floorplan_uploads for select
to authenticated
using ((select auth.uid()) = owner_id);

create policy "Owners can create floorplan uploads"
on public.floorplan_uploads for insert
to authenticated
with check (
  (select auth.uid()) = owner_id
  and exists (
    select 1
    from public.projects
    where projects.id = project_id
      and projects.owner_id = (select auth.uid())
  )
);

create policy "Owners can delete floorplan uploads"
on public.floorplan_uploads for delete
to authenticated
using ((select auth.uid()) = owner_id);

create policy "Owners can read generation jobs"
on public.generation_jobs for select
to authenticated
using ((select auth.uid()) = owner_id);

create policy "Owners can read generated outputs"
on public.generated_outputs for select
to authenticated
using ((select auth.uid()) = owner_id);

commit;

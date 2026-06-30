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

create table if not exists public.app_users (
  id uuid primary key default gen_random_uuid(),
  email text unique,
  display_name text check (display_name is null or char_length(display_name) <= 120),
  external_auth_provider text,
  external_auth_id text,
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now()),
  unique (external_auth_provider, external_auth_id)
);

create table if not exists public.projects (
  id uuid primary key default gen_random_uuid(),
  owner_id uuid references public.app_users (id) on delete set null,
  name text not null check (char_length(name) between 1 and 160),
  notes text not null default '',
  requirements jsonb not null default '{}'::jsonb,
  status text not null default 'draft'
    check (status in ('draft', 'ready', 'processing', 'completed', 'archived')),
  created_at timestamptz not null default timezone('utc', now()),
  updated_at timestamptz not null default timezone('utc', now())
);

create table if not exists public.floorplan_uploads (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects (id) on delete cascade,
  owner_id uuid references public.app_users (id) on delete set null,
  storage_provider text not null default 'external',
  storage_bucket text not null default 'floorplans',
  storage_path text not null,
  original_filename text not null,
  mime_type text,
  size_bytes bigint check (size_bytes is null or size_bytes >= 0),
  created_at timestamptz not null default timezone('utc', now()),
  unique (storage_provider, storage_bucket, storage_path)
);

create table if not exists public.generation_jobs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects (id) on delete cascade,
  owner_id uuid references public.app_users (id) on delete set null,
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

create table if not exists public.generated_outputs (
  id uuid primary key default gen_random_uuid(),
  project_id uuid references public.projects (id) on delete cascade,
  job_id uuid references public.generation_jobs (id) on delete set null,
  owner_id uuid references public.app_users (id) on delete set null,
  output_type text not null
    check (output_type in ('floorplan', 'render', 'model', 'pdf', 'other')),
  storage_provider text not null default 'external',
  storage_bucket text not null default 'generated-outputs',
  storage_path text not null,
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  unique (storage_provider, storage_bucket, storage_path)
);

create table if not exists public.training_uploads (
  id uuid primary key default gen_random_uuid(),
  source_type text not null
    check (source_type in ('bestseller', 'cubicasa', 'simplifier', 'user_test', 'other')),
  storage_provider text not null default 'external',
  storage_bucket text not null default 'training-uploads',
  storage_path text not null,
  original_filename text not null,
  mime_type text,
  size_bytes bigint check (size_bytes is null or size_bytes >= 0),
  notes text not null default '',
  status text not null default 'uploaded'
    check (status in ('uploaded', 'reviewing', 'normalized', 'rejected')),
  metadata jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default timezone('utc', now()),
  unique (storage_provider, storage_bucket, storage_path)
);

create index if not exists app_users_email_idx on public.app_users (email);
create index if not exists projects_owner_id_idx on public.projects (owner_id);
create index if not exists floorplan_uploads_project_id_idx on public.floorplan_uploads (project_id);
create index if not exists floorplan_uploads_owner_id_idx on public.floorplan_uploads (owner_id);
create index if not exists generation_jobs_project_id_idx on public.generation_jobs (project_id);
create index if not exists generation_jobs_owner_status_idx on public.generation_jobs (owner_id, status);
create index if not exists generated_outputs_project_id_idx on public.generated_outputs (project_id);
create index if not exists generated_outputs_job_id_idx on public.generated_outputs (job_id);
create index if not exists generated_outputs_owner_id_idx on public.generated_outputs (owner_id);
create index if not exists training_uploads_source_type_idx on public.training_uploads (source_type);
create index if not exists training_uploads_created_at_idx on public.training_uploads (created_at desc);

drop trigger if exists app_users_set_updated_at on public.app_users;
create trigger app_users_set_updated_at
before update on public.app_users
for each row execute function public.set_updated_at();

drop trigger if exists projects_set_updated_at on public.projects;
create trigger projects_set_updated_at
before update on public.projects
for each row execute function public.set_updated_at();

drop trigger if exists generation_jobs_set_updated_at on public.generation_jobs;
create trigger generation_jobs_set_updated_at
before update on public.generation_jobs
for each row execute function public.set_updated_at();

commit;

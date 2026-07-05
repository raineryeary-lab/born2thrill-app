begin;

insert into storage.buckets (
  id,
  name,
  public,
  file_size_limit,
  allowed_mime_types
)
values (
  'training-uploads',
  'training-uploads',
  false,
  52428800,
  array[
    'application/pdf',
    'application/zip',
    'image/jpeg',
    'image/png',
    'image/svg+xml'
  ]
)
on conflict (id) do update
set
  public = excluded.public,
  file_size_limit = excluded.file_size_limit,
  allowed_mime_types = excluded.allowed_mime_types;

create table if not exists public.training_uploads (
  id uuid primary key default gen_random_uuid(),
  source_type text not null
    check (source_type in ('bestseller', 'cubicasa', 'simplifier', 'user_test', 'other')),
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
  unique (storage_bucket, storage_path)
);

create index if not exists training_uploads_source_type_idx
on public.training_uploads (source_type);

create index if not exists training_uploads_created_at_idx
on public.training_uploads (created_at desc);

alter table public.training_uploads enable row level security;

drop policy if exists "Prototype users can create training uploads" on public.training_uploads;
drop policy if exists "Prototype users can read training uploads" on public.training_uploads;

create policy "Prototype users can create training uploads"
on public.training_uploads for insert
to anon, authenticated
with check (storage_bucket = 'training-uploads');

create policy "Prototype users can read training uploads"
on public.training_uploads for select
to anon, authenticated
using (storage_bucket = 'training-uploads');

drop policy if exists "Prototype users can upload training files" on storage.objects;
drop policy if exists "Prototype users can read training files" on storage.objects;

create policy "Prototype users can upload training files"
on storage.objects for insert
to anon, authenticated
with check (bucket_id = 'training-uploads');

create policy "Prototype users can read training files"
on storage.objects for select
to anon, authenticated
using (bucket_id = 'training-uploads');

commit;

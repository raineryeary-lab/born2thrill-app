begin;

alter table public.training_uploads
  add column if not exists review_notes text not null default '';

alter table public.training_uploads
  drop constraint if exists training_uploads_status_check;

update public.training_uploads
set status = 'reviewed'
where status = 'reviewing';

alter table public.training_uploads
  add constraint training_uploads_status_check
  check (status in ('uploaded', 'reviewed', 'usable', 'not_usable', 'normalize', 'normalized', 'rejected'));

commit;

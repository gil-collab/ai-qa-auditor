-- Supabase/Postgres schema for audit storage
-- Enable required extensions
create extension if not exists pgcrypto;

create table if not exists audits (
  id uuid primary key default gen_random_uuid(),
  ticket_id text not null,
  agent text,
  channel text,
  overall numeric,
  effectiveness jsonb not null,
  efficiency jsonb not null,
  tone_and_phrasing jsonb not null,
  zero_tolerance jsonb not null,
  created_at timestamptz not null default now()
);

-- Ensure ticket_id is unique to allow upsert semantics
create unique index if not exists audits_ticket_id_key on audits(ticket_id);

-- Helpful indexes
create index if not exists audits_created_at_desc_idx on audits (created_at desc);
create index if not exists audits_ticket_id_idx on audits (ticket_id);


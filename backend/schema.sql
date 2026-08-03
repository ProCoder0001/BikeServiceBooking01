-- Online Bike Service Booking System
-- Run this whole file once in the Supabase SQL Editor (Project -> SQL Editor -> New query)

create extension if not exists "pgcrypto";

-- ============================================================
-- USERS  (both customers and admins live in this one table)
-- ============================================================
create table if not exists users (
    id                uuid primary key default gen_random_uuid(),
    role              text not null check (role in ('customer', 'admin')),
    first_name        text not null,
    last_name         text not null,
    email             text not null unique,
    password_hash     text not null,
    gender            text,
    contact_no        text,
    age               integer,
    street            text,
    city              text,
    pincode           text,
    wallet_balance    numeric(10, 2) not null default 0,
    created_at        timestamptz not null default now()
);

-- ============================================================
-- BIKES  (added by a customer)
-- ============================================================
create table if not exists bikes (
    id                    uuid primary key default gen_random_uuid(),
    owner_id              uuid not null references users(id) on delete cascade,
    bike_name             text not null,
    company               text not null,
    model_number          text not null,
    registration_number   text not null,
    created_at            timestamptz not null default now()
);

-- ============================================================
-- BOOKINGS  (a customer books a service slot for one of their bikes)
-- ============================================================
create table if not exists bookings (
    id                 uuid primary key default gen_random_uuid(),
    booking_code       text not null unique,
    bike_id            uuid not null references bikes(id) on delete cascade,
    customer_id        uuid not null references users(id) on delete cascade,
    booking_date       date not null default current_date,   -- date the request was made
    service_date       date not null,                          -- requested service date
    booking_status     text not null default 'Pending'  check (booking_status in ('Pending', 'Approved', 'Cancelled')),
    servicing_status   text not null default 'Pending'  check (servicing_status in ('Pending', 'Completed')),
    servicing_fee      numeric(10, 2) not null default 0,
    payment_mode       text check (payment_mode in ('Wallet', 'Cash')),
    payment_status     text not null default 'Pending' check (payment_status in ('Pending', 'Completed')),
    created_at         timestamptz not null default now()
);

create index if not exists idx_bikes_owner on bikes(owner_id);
create index if not exists idx_bookings_customer on bookings(customer_id);
create index if not exists idx_bookings_bike on bookings(bike_id);

-- Row Level Security: the FastAPI backend talks to Supabase with the
-- service_role key and enforces auth/roles itself, so RLS stays disabled.
-- If you ever call Supabase directly from the browser with the anon key,
-- turn RLS on and add policies before doing so.
alter table users    disable row level security;
alter table bikes    disable row level security;
alter table bookings disable row level security;

--- for srevice type selection parts selection mechanic note

ALTER TABLE bookings ADD COLUMN IF NOT EXISTS service_types jsonb NOT NULL DEFAULT '[]';
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS parts_required jsonb NOT NULL DEFAULT '[]';
ALTER TABLE bookings ADD COLUMN IF NOT EXISTS mechanic_notes text;
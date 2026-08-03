-- Razorpay wallet top-up tracking
-- Run this once in the Supabase SQL Editor (Project -> SQL Editor -> New query)

create table if not exists payments (
    id                  uuid primary key default gen_random_uuid(),
    order_id            text not null unique,        -- Razorpay order id (order_...)
    razorpay_payment_id text,                         -- Razorpay payment id (pay_...), set once paid
    customer_id         uuid not null references users(id) on delete cascade,
    amount              numeric(10, 2) not null,      -- rupees
    status              text not null default 'created' check (status in ('created', 'paid', 'failed')),
    created_at          timestamptz not null default now()
);

create index if not exists idx_payments_customer on payments(customer_id);

alter table payments disable row level security;

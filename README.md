# Online Bike Service Booking System
FastAPI + Supabase (Postgres) + HTML/CSS/vanilla JS

- **Backend**: FastAPI, Python, JWT auth, Supabase as the database
- **Frontend**: plain HTML/CSS/JavaScript (no framework, no build step)

## What it does

Two roles, one flow:

```
Customer  -> registers, adds a bike, books a service date
Admin     -> approves/cancels the booking, then marks the service
             Completed with a fee + payment mode (Wallet or Cash)
Wallet    -> if payment mode is Wallet, the fee is debited from the
             customer's wallet balance automatically
```

Customer pages: Register, Login, My Wallet, Add Bike, My Bikes, Book
Service, My Bookings.

Admin pages: All Bikes, All Customers, All Bookings (approve/cancel a
booking, then update servicing status / fee / payment mode).

## Project layout

```
backend/            FastAPI app
  app/
    main.py          app entrypoint, CORS, routers
    database.py      Supabase client + settings
    schemas.py       Pydantic request/response models
    auth.py          JWT + password hashing + role guards
    routers/
      auth.py         register / login / me
      bikes.py         add bike / my bikes / all bikes (admin)
      bookings.py       book / my bookings / all bookings / approve / update service
      wallet.py         balance / top up
      users.py          all customers (admin)
  schema.sql         run this in the Supabase SQL editor
  requirements.txt
  .env.example
  README.md          backend setup steps

frontend/            static site, no build step
  index.html          public homepage (hero, services, about, contact)
  register.html
  login.html
  customer/            wallet, add-bike, my-bikes, book-service, my-bookings
  admin/                all-bikes, all-customers, all-bookings
  css/style.css
  js/api.js            fetch wrapper, session storage, nav rendering
```

## Running it

**1. Backend** — see `backend/README.md` for full steps:
```bash
cd backend
cp .env.example .env   # fill in your Supabase project URL + service_role key
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**2. Frontend** — it's static files, so any static server works:
```bash
cd frontend
python -m http.server 5500
# visit http://localhost:5500/index.html
```
If your backend runs somewhere other than `http://localhost:8000`, set
`window.API_BASE` before `js/api.js` loads (e.g. add a small inline
`<script>window.API_BASE = "https://your-api.example.com";</script>`
above the `js/api.js` tag on each page), and add that frontend origin
to `CORS_ORIGINS` in the backend `.env`.

## Notes / things you may want to extend
- Admin "revenue" in the dashboard is just a sum of paid bookings — there's
  no separate admin ledger table, matching the simple wallet-debit flow
  shown in the source video.
- There's no file/image upload for bikes or profile photos.
- Passwords are hashed with bcrypt; sessions are stateless JWTs stored in
  `localStorage` on the frontend.

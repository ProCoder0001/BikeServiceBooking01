# Bike Service Booking - Backend (FastAPI + Supabase)

## 1. Create the Supabase project
1. Go to https://supabase.com, create a new project.
2. Open **SQL Editor -> New query**, paste the contents of `schema.sql`, and run it.
   This creates the `users`, `bikes`, and `bookings` tables.
3. Open **Project Settings -> API** and copy:
   - **Project URL** -> `SUPABASE_URL`
   - **service_role key** (not the anon key) -> `SUPABASE_SERVICE_KEY`

## 2. Configure the backend
```bash
cd backend
cp .env.example .env
# edit .env and fill in SUPABASE_URL, SUPABASE_SERVICE_KEY, JWT_SECRET, CORS_ORIGINS
```

## 3. Install & run
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The API is now live at `http://localhost:8000` and interactive docs at
`http://localhost:8000/docs`.

## API overview

| Method | Path                          | Who      | Purpose                              |
|--------|-------------------------------|----------|---------------------------------------|
| POST   | /api/auth/register             | anyone   | Register as customer or admin         |
| POST   | /api/auth/login                | anyone   | Login, returns JWT                    |
| GET    | /api/auth/me                   | logged in| Current user profile                  |
| POST   | /api/bikes                     | customer | Add a bike                            |
| GET    | /api/bikes/mine                | customer | List my bikes                         |
| GET    | /api/bikes                     | admin    | List all bikes                        |
| GET    | /api/users/customers           | admin    | List all customers                    |
| GET    | /api/wallet                    | customer | My wallet balance                     |
| POST   | /api/wallet/add                | customer | Top up wallet                         |
| POST   | /api/bookings                  | customer | Book a service for one of my bikes    |
| GET    | /api/bookings/mine              | customer | My bookings                           |
| GET    | /api/bookings                  | admin    | All bookings                          |
| PATCH  | /api/bookings/{id}/status       | admin    | Approve / cancel a booking            |
| PATCH  | /api/bookings/{id}/service      | admin    | Update servicing status, fee, payment |

Every protected route expects `Authorization: Bearer <token>` from `/api/auth/login`.

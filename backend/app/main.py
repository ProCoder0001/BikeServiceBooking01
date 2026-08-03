from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import get_settings
from app.routers import auth, bikes, bookings, users, wallet, payments
from app.routers import forgot_password

app = FastAPI(
    title="Online Bike Service Booking API",
    description="FastAPI + Supabase backend for the bike service booking platform.",
    version="1.0.0",
)

settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(bikes.router)
app.include_router(bookings.router)
app.include_router(wallet.router)
app.include_router(payments.router)
app.include_router(users.router)
app.include_router(forgot_password.router)

@app.get("/api/health", tags=["health"])
def health_check():
    return {"status": "ok"}

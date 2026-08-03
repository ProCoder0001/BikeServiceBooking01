import os
from functools import lru_cache

import razorpay
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()


class Settings:
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    jwt_secret: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expire_minutes: int = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
    cors_origins: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()
    ]
    razorpay_key_id: str = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_key_secret: str = os.getenv("RAZORPAY_KEY_SECRET", "")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5500")
    admin_signup_code: str = os.getenv("ADMIN_SIGNUP_CODE", "")


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_supabase() -> Client:
    settings = get_settings()
    if not settings.supabase_url or not settings.supabase_service_key:
        raise RuntimeError(
            "SUPABASE_URL / SUPABASE_SERVICE_KEY are not set. Copy .env.example to "
            ".env and fill in your Supabase project's values."
        )
    return create_client(settings.supabase_url, settings.supabase_service_key)


@lru_cache
def get_razorpay_client() -> razorpay.Client:
    settings = get_settings()
    if not settings.razorpay_key_id or not settings.razorpay_key_secret:
        raise RuntimeError(
            "RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET are not set. Add them to your .env file."
        )
    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    return client

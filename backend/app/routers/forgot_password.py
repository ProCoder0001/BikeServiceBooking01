from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_settings, get_supabase
from app.auth import hash_password
from app.email import send_reset_email

router = APIRouter(prefix="/password", tags=["Password"])

supabase = get_supabase()

reset_tokens = {}


class ForgotPasswordRequest(BaseModel):
    email: str


class ResetPasswordRequest(BaseModel):
    token: str
    password: str


@router.post("/forgot-password")
def forgot_password(data: ForgotPasswordRequest):

    user = (
        supabase.table("users")
        .select("*")
        .eq("email", data.email)
        .limit(1)
        .execute()
    )

    generic_response = {
        "message": "If an account exists for that email, a reset link has been sent."
    }

    if not user.data:
        # Don't reveal whether the email is registered - same response either way.
        print(f"Forgot-password requested for unknown email: {data.email}")
        return generic_response

    # Create reset token
    token = secrets.token_urlsafe(32)

    reset_tokens[token] = {
        "email": data.email,
        "expires": datetime.utcnow() + timedelta(minutes=15),
    }

    # Create reset link
    settings = get_settings()
    reset_link = f"{settings.frontend_url}/reset-password.html?token={token}"

    print("\n==============================")
    print("PASSWORD RESET LINK")
    print(reset_link)
    print("==============================\n")

    # Send email
    send_reset_email(
        data.email,
        reset_link
    )

    return generic_response


@router.post("/reset-password")
def reset_password(data: ResetPasswordRequest):

    token_data = reset_tokens.get(data.token)

    if token_data is None:
        raise HTTPException(status_code=400, detail="Invalid Token")

    if datetime.utcnow() > token_data["expires"]:
        del reset_tokens[data.token]
        raise HTTPException(status_code=400, detail="Token Expired")

    password_hash = hash_password(data.password)

    (
        supabase.table("users")
        .update(
            {
                "password_hash": password_hash
            }
        )
        .eq(
            "email",
            token_data["email"]
        )
        .execute()
    )

    del reset_tokens[data.token]

    return {
        "message": "Password Updated Successfully"
    }
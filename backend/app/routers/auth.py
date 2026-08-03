from fastapi import APIRouter, Depends, HTTPException, status

from app.auth import create_access_token, get_current_user, hash_password, verify_password
from app.database import get_settings, get_supabase
from app.schemas import LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _to_user_out(row: dict) -> UserOut:
    return UserOut(
        id=row["id"],
        role=row["role"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        email=row["email"],
        contact_no=row.get("contact_no"),
        city=row.get("city"),
        wallet_balance=float(row.get("wallet_balance") or 0),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    supabase = get_supabase()

    if payload.role == "admin":
        settings = get_settings()
        if not settings.admin_signup_code or payload.admin_code != settings.admin_signup_code:
            raise HTTPException(status_code=403, detail="Invalid admin code")

    existing = (
        supabase.table("users").select("id").eq("email", payload.email).limit(1).execute()
    )
    if existing.data:
        raise HTTPException(status_code=400, detail="An account with this email already exists")

    row = {
        "role": payload.role,
        "first_name": payload.first_name,
        "last_name": payload.last_name,
        "email": payload.email,
        "password_hash": hash_password(payload.password),
        "gender": payload.gender,
        "contact_no": payload.contact_no,
        "age": payload.age,
        "street": payload.street,
        "city": payload.city,
        "pincode": payload.pincode,
    }
    inserted = supabase.table("users").insert(row).execute()
    user = inserted.data[0]

    token = create_access_token(user["id"], user["role"])
    return TokenResponse(access_token=token, user=_to_user_out(user))


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    supabase = get_supabase()
    res = (
        supabase.table("users")
        .select("*")
        .eq("email", payload.email)
        .eq("role", payload.role)
        .limit(1)
        .execute()
    )
    if not res.data:
        raise HTTPException(status_code=401, detail="Invalid email, password or role")

    user = res.data[0]
    if not verify_password(payload.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email, password or role")

    token = create_access_token(user["id"], user["role"])
    return TokenResponse(access_token=token, user=_to_user_out(user))


@router.get("/me", response_model=UserOut)
def me(user: dict = Depends(get_current_user)):
    return _to_user_out(user)

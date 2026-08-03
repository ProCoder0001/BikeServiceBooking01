from fastapi import APIRouter, Depends

from app.auth import require_admin, require_customer
from app.database import get_supabase
from app.schemas import BikeCreate, BikeOut

router = APIRouter(prefix="/api/bikes", tags=["bikes"])


@router.post("", response_model=BikeOut, status_code=201)
def add_bike(payload: BikeCreate, user: dict = Depends(require_customer)):
    supabase = get_supabase()
    row = {**payload.model_dump(), "owner_id": user["id"]}
    inserted = supabase.table("bikes").insert(row).execute()
    bike = inserted.data[0]
    return BikeOut(
        **bike,
        owner_name=f"{user['first_name']} {user['last_name']}",
        owner_contact=user.get("contact_no"),
    )


@router.get("/mine", response_model=list[BikeOut])
def my_bikes(user: dict = Depends(require_customer)):
    supabase = get_supabase()
    res = (
        supabase.table("bikes")
        .select("*")
        .eq("owner_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return [
        BikeOut(**b, owner_name=f"{user['first_name']} {user['last_name']}", owner_contact=user.get("contact_no"))
        for b in res.data
    ]


@router.get("", response_model=list[BikeOut])
def all_bikes(_: dict = Depends(require_admin)):
    supabase = get_supabase()
    res = supabase.table("bikes").select("*, users!bikes_owner_id_fkey(first_name,last_name,contact_no)").order(
        "created_at", desc=True
    ).execute()

    out = []
    for b in res.data:
        owner = b.pop("users", None) or {}
        out.append(
            BikeOut(
                **b,
                owner_name=f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip(),
                owner_contact=owner.get("contact_no"),
            )
        )
    return out

from fastapi import APIRouter, Depends

from app.auth import require_admin
from app.database import get_supabase
from app.schemas import CustomerOut

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/customers", response_model=list[CustomerOut])
def all_customers(_: dict = Depends(require_admin)):
    supabase = get_supabase()
    res = (
        supabase.table("users")
        .select("id,first_name,last_name,email,contact_no,street,city,pincode,created_at")
        .eq("role", "customer")
        .order("created_at", desc=True)
        .execute()
    )
    return res.data

from fastapi import APIRouter, Depends

from app.auth import require_customer
from app.database import get_supabase
from app.schemas import WalletOut, WalletTopUp

router = APIRouter(prefix="/api/wallet", tags=["wallet"])


@router.get("", response_model=WalletOut)
def get_wallet(user: dict = Depends(require_customer)):
    return WalletOut(wallet_balance=float(user.get("wallet_balance") or 0))


@router.post("/add", response_model=WalletOut)
def add_money(payload: WalletTopUp, user: dict = Depends(require_customer)):
    supabase = get_supabase()
    new_balance = float(user.get("wallet_balance") or 0) + payload.amount
    supabase.table("users").update({"wallet_balance": new_balance}).eq("id", user["id"]).execute()
    return WalletOut(wallet_balance=new_balance)

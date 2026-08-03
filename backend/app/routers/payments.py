import razorpay
from fastapi import APIRouter, Depends, HTTPException

from app.auth import require_customer
from app.database import get_razorpay_client, get_settings, get_supabase
from app.schemas import CreateOrderRequest, CreateOrderResponse, VerifyPaymentRequest, WalletOut

router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/create-order", response_model=CreateOrderResponse)
def create_order(payload: CreateOrderRequest, user: dict = Depends(require_customer)):
    """Create a Razorpay order for a wallet top-up.

    The amount never leaves the server unchecked - the frontend only ever
    tells Razorpay Checkout to open the order that was created here.
    """
    client = get_razorpay_client()
    settings = get_settings()
    amount_paise = int(round(payload.amount * 100))

    order = client.order.create(
        {
            "amount": amount_paise,
            "currency": "INR",
            "notes": {"customer_id": user["id"]},
        }
    )

    supabase = get_supabase()
    supabase.table("payments").insert(
        {
            "order_id": order["id"],
            "customer_id": user["id"],
            "amount": payload.amount,
            "status": "created",
        }
    ).execute()

    return CreateOrderResponse(
        order_id=order["id"],
        amount=amount_paise,
        currency="INR",
        key_id=settings.razorpay_key_id,
    )


@router.post("/verify", response_model=WalletOut)
def verify_payment(payload: VerifyPaymentRequest, user: dict = Depends(require_customer)):
    """Verify the Razorpay signature and credit the wallet exactly once.

    Razorpay's checkout callback runs in the customer's browser, so it must
    never be trusted directly - the signature check below is what proves the
    payment is genuine, not just that the browser said so.
    """
    supabase = get_supabase()

    payment_res = (
        supabase.table("payments")
        .select("*")
        .eq("order_id", payload.razorpay_order_id)
        .eq("customer_id", user["id"])
        .limit(1)
        .execute()
    )
    if not payment_res.data:
        raise HTTPException(status_code=404, detail="Order not found")
    payment = payment_res.data[0]

    if payment["status"] == "paid":
        # Already credited earlier (e.g. duplicate callback) - just return
        # the current balance instead of crediting twice.
        return WalletOut(wallet_balance=float(user.get("wallet_balance") or 0))

    client = get_razorpay_client()
    try:
        client.utility.verify_payment_signature(
            {
                "razorpay_order_id": payload.razorpay_order_id,
                "razorpay_payment_id": payload.razorpay_payment_id,
                "razorpay_signature": payload.razorpay_signature,
            }
        )
    except razorpay.errors.SignatureVerificationError:
        supabase.table("payments").update({"status": "failed"}).eq(
            "order_id", payload.razorpay_order_id
        ).execute()
        raise HTTPException(status_code=400, detail="Payment signature verification failed")

    new_balance = float(user.get("wallet_balance") or 0) + float(payment["amount"])
    supabase.table("users").update({"wallet_balance": new_balance}).eq("id", user["id"]).execute()
    supabase.table("payments").update(
        {"status": "paid", "razorpay_payment_id": payload.razorpay_payment_id}
    ).eq("order_id", payload.razorpay_order_id).execute()

    return WalletOut(wallet_balance=new_balance)

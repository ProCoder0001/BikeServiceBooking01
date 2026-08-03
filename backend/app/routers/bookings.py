import random
import string
from datetime import date
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from app.auth import get_current_user, require_admin, require_customer
from app.database import get_supabase
from app.email import send_booking_approved_email, send_service_completed_email
from app.schemas import BookingCreate, BookingOut, BookingServiceUpdate, BookingStatusUpdate

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _new_booking_code() -> str:
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=10))


def _to_booking_out(row: dict) -> BookingOut:
    bike = row.pop("bikes", None) or {}
    customer = row.pop("users", None) or {}
    return BookingOut(
        **row,
        bike_name=bike.get("bike_name", ""),
        company=bike.get("company", ""),
        model_number=bike.get("model_number", ""),
        registration_number=bike.get("registration_number", ""),
        customer_name=f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
        customer_contact=customer.get("contact_no"),
    )


_SELECT = "*, bikes(bike_name,company,model_number,registration_number), users!bookings_customer_id_fkey(first_name,last_name,contact_no)"


def _get_customer_contact(supabase, customer_id: str) -> dict:
    res = (
        supabase.table("users")
        .select("email,first_name,last_name")
        .eq("id", customer_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else {}


@router.post("", response_model=BookingOut, status_code=201)
def book_service(payload: BookingCreate, user: dict = Depends(require_customer)):
    supabase = get_supabase()

    bike_res = (
        supabase.table("bikes")
        .select("id")
        .eq("id", payload.bike_id)
        .eq("owner_id", user["id"])
        .limit(1)
        .execute()
    )
    if not bike_res.data:
        raise HTTPException(status_code=404, detail="Bike not found for this customer")

    row = {
        "booking_code": _new_booking_code(),
        "bike_id": payload.bike_id,
        "customer_id": user["id"],
        "booking_date": date.today().isoformat(),
        "service_date": payload.service_date.isoformat(),

        # NEW
        "service_types": payload.service_types,
        "parts_required": payload.parts_required,
        "mechanic_notes": None,
    }
    inserted = supabase.table("bookings").insert(row).execute()
    new_id = inserted.data[0]["id"]
    full = supabase.table("bookings").select(_SELECT).eq("id", new_id).limit(1).execute()
    return _to_booking_out(full.data[0])


@router.get("/mine", response_model=list[BookingOut])
def my_bookings(user: dict = Depends(require_customer)):
    supabase = get_supabase()
    res = (
        supabase.table("bookings")
        .select(_SELECT)
        .eq("customer_id", user["id"])
        .order("created_at", desc=True)
        .execute()
    )
    return [_to_booking_out(r) for r in res.data]


@router.get("", response_model=list[BookingOut])
def all_bookings(_: dict = Depends(require_admin)):
    supabase = get_supabase()
    res = supabase.table("bookings").select(_SELECT).order("created_at", desc=True).execute()
    return [_to_booking_out(r) for r in res.data]


@router.patch("/{booking_id}/status", response_model=BookingOut)
def update_booking_status(
    booking_id: str, payload: BookingStatusUpdate, _: dict = Depends(require_admin)
):
    supabase = get_supabase()
    existing = supabase.table("bookings").select("*").eq("id", booking_id).limit(1).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking = existing.data[0]

    if payload.booking_status == "Cancelled" and booking["payment_status"] == "Completed":
        raise HTTPException(
            status_code=400,
            detail="This booking has already been paid for and can no longer be cancelled. "
            "Process a refund first if the service needs to be called off.",
        )


    supabase.table("bookings").update(
        {"booking_status": payload.booking_status}
    ).eq("id", booking_id).execute()

    if payload.booking_status == "Approved" and booking["booking_status"] != "Approved":
        customer = _get_customer_contact(supabase, booking["customer_id"])
        if customer.get("email"):
            send_booking_approved_email(
                customer["email"],
                f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                booking["booking_code"],
                booking["service_date"],
            )

    res = supabase.table("bookings").select(_SELECT).eq("id", booking_id).limit(1).execute()
    return _to_booking_out(res.data[0])


@router.patch("/{booking_id}/service", response_model=BookingOut)
def update_service_status(
    booking_id: str, payload: BookingServiceUpdate, _: dict = Depends(require_admin)
):
    """Admin updates servicing status / fee / payment mode.

    When the servicing is marked Completed with payment_mode=Wallet, the fee
    is debited from the customer's wallet right away (mirrors the
    book -> service -> debit-from-wallet -> credit-to-admin flow).
    """
    supabase = get_supabase()
    booking_res = supabase.table("bookings").select("*").eq("id", booking_id).limit(1).execute()
    if not booking_res.data:
        raise HTTPException(status_code=404, detail="Booking not found")
    booking = booking_res.data[0]

    update = {"servicing_status": payload.servicing_status}
    if payload.payment_mode is not None:
        update["payment_mode"] = payload.payment_mode
    if payload.servicing_fee is not None:
        update["servicing_fee"] = payload.servicing_fee
    # Save mechanic notes
    if payload.mechanic_notes is not None:
        update["mechanic_notes"] = payload.mechanic_notes

    fee = payload.servicing_fee if payload.servicing_fee is not None else booking["servicing_fee"]
    mode = payload.payment_mode or booking.get("payment_mode")

    if payload.servicing_status == "Completed" and booking["payment_status"] != "Completed":
        if mode == "Wallet":
            customer = (
                supabase.table("users").select("wallet_balance").eq("id", booking["customer_id"]).limit(1).execute()
            ).data[0]
            balance = float(customer.get("wallet_balance") or 0)
            if balance < float(fee):
                raise HTTPException(status_code=400, detail="Customer wallet balance is insufficient")
            supabase.table("users").update({"wallet_balance": balance - float(fee)}).eq(
                "id", booking["customer_id"]
            ).execute()
            update["payment_status"] = "Completed"
        elif mode == "Cash":
            update["payment_status"] = "Completed"

    supabase.table("bookings").update(update).eq("id", booking_id).execute()

    if payload.servicing_status == "Completed" and booking["servicing_status"] != "Completed":
        customer = _get_customer_contact(supabase, booking["customer_id"])
        if customer.get("email"):
            send_service_completed_email(
                customer["email"],
                f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
                booking["booking_code"],
            )

    res = supabase.table("bookings").select(_SELECT).eq("id", booking_id).limit(1).execute()
    return _to_booking_out(res.data[0])


@router.get("/{booking_id}/invoice")
def get_invoice(booking_id: str, user: dict = Depends(get_current_user)):
    """Generate a downloadable PDF receipt, once payment has been completed."""
    supabase = get_supabase()
    res = supabase.table("bookings").select(_SELECT).eq("id", booking_id).limit(1).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Booking not found")
    row = res.data[0]

    if user["role"] == "customer" and row["customer_id"] != user["id"]:
        raise HTTPException(status_code=403, detail="Not your booking")

    if row["payment_status"] != "Completed":
        raise HTTPException(status_code=400, detail="Invoice is only available once payment is completed")

    booking = _to_booking_out(dict(row))  # dict() copy - _to_booking_out mutates its argument

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 60
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "Bike Service Booking - Payment Receipt")
    y -= 30
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Booking code: {booking.booking_code}")
    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Customer")
    y -= 18
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Name: {booking.customer_name}")
    y -= 16
    pdf.drawString(50, y, f"Contact: {booking.customer_contact or '-'}")
    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Bike")
    y -= 18
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"{booking.bike_name} ({booking.company}) - {booking.model_number}")
    y -= 16
    pdf.drawString(50, y, f"Registration number: {booking.registration_number}")
    y -= 30

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Service")
    y -= 18
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Requested date: {booking.service_date}")
    y -= 16
    pdf.drawString(50, y, f"Booking status: {booking.booking_status}")
    y -= 16
    pdf.drawString(50, y, f"Servicing status: {booking.servicing_status}")
    y -= 30

    y -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Service Type")
    y -= 18
    pdf.setFont("Helvetica", 10)

    if booking.service_types:
        for service in booking.service_types:
            pdf.drawString(60, y, f"• {service}")
            y -= 15
    else:
        pdf.drawString(60, y, "-")
        y -= 15
        
    y -= 15
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Requested Parts")
    y -= 18

    pdf.setFont("Helvetica", 10)

    if booking.parts_required:
        for part in booking.parts_required:
            pdf.drawString(60, y, f"• {part}")
            y -= 15
    else:
        pdf.drawString(60, y, "-")
        y -= 15

    y -= 15

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Mechanic Notes")
    y -= 18

    pdf.setFont("Helvetica", 10)

    pdf.drawString(
        60,
        y,
        booking.mechanic_notes or "No mechanic notes."
    )

    y -= 25
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Payment")
    y -= 18
    pdf.setFont("Helvetica", 10)
    pdf.drawString(50, y, f"Amount paid: Rs. {booking.servicing_fee}")
    y -= 16
    pdf.drawString(50, y, f"Payment mode: {booking.payment_mode or '-'}")
    y -= 16
    pdf.drawString(50, y, f"Payment status: {booking.payment_status}")

    pdf.showPage()
    pdf.save()
    buffer.seek(0)

    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="invoice-{booking.booking_code}.pdf"'},
    )

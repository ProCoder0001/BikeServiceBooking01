from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, EmailStr, Field

Role = Literal["customer", "admin"]
BookingStatus = Literal["Pending", "Approved", "Cancelled"]
ServicingStatus = Literal["Pending", "Completed"]
PaymentMode = Literal["Wallet", "Cash"]
PaymentStatus = Literal["Pending", "Completed"]


# ---------- Auth ----------
class RegisterRequest(BaseModel):
    role: Role
    first_name: str
    last_name: str
    email: EmailStr
    password: str = Field(min_length=6)
    gender: Optional[str] = None
    contact_no: Optional[str] = None
    age: Optional[int] = None
    street: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    admin_code: Optional[str] = None


class LoginRequest(BaseModel):
    role: Role
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    role: Role
    first_name: str
    last_name: str
    email: EmailStr
    contact_no: Optional[str] = None
    city: Optional[str] = None
    wallet_balance: float


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Bikes ----------
class BikeCreate(BaseModel):
    bike_name: str
    company: str
    model_number: str
    registration_number: str


class BikeOut(BaseModel):
    id: str
    bike_name: str
    company: str
    model_number: str
    registration_number: str
    owner_id: str
    owner_name: Optional[str] = None
    owner_contact: Optional[str] = None


# ---------- Wallet ----------
class WalletTopUp(BaseModel):
    amount: float = Field(gt=0)


class WalletOut(BaseModel):
    wallet_balance: float


# ---------- Razorpay payments ----------
class CreateOrderRequest(BaseModel):
    amount: float = Field(gt=0, description="Amount in rupees (not paise)")


class CreateOrderResponse(BaseModel):
    order_id: str
    amount: int  # paise, as Razorpay expects on the frontend
    currency: str
    key_id: str


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


# ---------- Bookings ----------
class BookingCreate(BaseModel):
    bike_id: str
    service_date: date

    # Customer selected service types
    service_types: list[str] = []

    # Customer requested parts/accessories
    parts_required: list[str] = []


class BookingStatusUpdate(BaseModel):
    booking_status: BookingStatus


class BookingServiceUpdate(BaseModel):
    servicing_status: ServicingStatus

    payment_mode: Optional[PaymentMode] = None

    servicing_fee: Optional[float] = Field(default=None, ge=0)

    # Filled by Admin / Mechanic
    mechanic_notes: Optional[str] = None


class BookingOut(BaseModel):
    id: str
    booking_code: str
    bike_id: str
    bike_name: str
    company: str
    model_number: str
    registration_number: str
    customer_id: str
    customer_name: str
    customer_contact: Optional[str] = None
    booking_date: date
    service_date: date
    booking_status: BookingStatus
    servicing_status: ServicingStatus
    servicing_fee: float
    payment_mode: Optional[PaymentMode] = None
    payment_status: PaymentStatus
    # -----------------------------
    # NEW FIELDS
    # -----------------------------

    service_types: list[str] = []

    parts_required: list[str] = []

    mechanic_notes: Optional[str] = None

class CustomerOut(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: EmailStr
    contact_no: Optional[str] = None
    street: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    created_at: Optional[datetime] = None

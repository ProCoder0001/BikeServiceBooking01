import os
import smtplib

from email.mime.text import MIMEText
from email.utils import formataddr
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "Bike Service Booking")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_EMAIL)


def _send_email(receiver_email: str, subject: str, body: str):
    print("Sending email to:", receiver_email)

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = formataddr((SMTP_FROM_NAME, SMTP_FROM_EMAIL))
    message["To"] = receiver_email

    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    server.login(SMTP_EMAIL, SMTP_PASSWORD)
    server.sendmail(SMTP_FROM_EMAIL, receiver_email, message.as_string())
    server.quit()

    print("Email sent successfully to:", receiver_email)


def send_reset_email(receiver_email: str, reset_link: str):
    try:
        body = f"""
Hello,

Click the link below to reset your password:

{reset_link}

If you didn't request a password reset, you can ignore this email.
"""
        _send_email(receiver_email, "Bike Service Password Reset", body)
    except Exception as e:
        print("EMAIL ERROR:", e)
        raise e


def send_booking_approved_email(receiver_email: str, customer_name: str, booking_code: str, service_date: str):
    try:
        body = f"""
Hi {customer_name},

Good news - your service booking #{booking_code} has been approved.
Your requested service date is {service_date}.

We'll email you again once your bike is ready for pickup.

Thanks,
Bike Service Booking Team
"""
        _send_email(receiver_email, f"Booking #{booking_code} Approved", body)
    except Exception as e:
        # Notification emails should never break the underlying status update.
        print("EMAIL ERROR (booking approved):", e)


def send_service_completed_email(receiver_email: str, customer_name: str, booking_code: str):
    try:
        body = f"""
Hi {customer_name},

Your bike is ready! Servicing for booking #{booking_code} is complete.

Please visit the service centre to collect your bike. If any payment is
still pending, you can pay by cash at pickup or add funds to your wallet
from the app beforehand.

Thanks,
Bike Service Booking Team
"""
        _send_email(receiver_email, f"Your bike is ready - Booking #{booking_code}", body)
    except Exception as a:
        print("EMAIL ERROR (service completed):", a)
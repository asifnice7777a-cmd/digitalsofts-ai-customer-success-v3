# # import uuid
# # from datetime import datetime, timezone
# # from langchain_core.tools import tool


# # @tool
# # def send_confirmation_email(to_email: str, client_name: str, meeting_details: str) -> str:
# #     """Send a mocked meeting confirmation email to the client with their booking details."""
# #     if not to_email or "@" not in to_email:
# #         raise ValueError(f"Invalid email address: {to_email}")
# #     email_id = str(uuid.uuid4())[:8]
# #     sent_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
# #     return (
# #         f"Confirmation email (ID: {email_id}) sent to {to_email} for {client_name or 'the client'}. "
# #         f"Meeting details: {meeting_details}. Sent at {sent_at}."
# #     )


# import os
# import smtplib
# from email.message import EmailMessage

# from dotenv import load_dotenv
# from langchain_core.tools import tool

# load_dotenv()


# @tool
# def send_confirmation_email(
#     to_email: str,
#     client_name: str,
#     meeting_details: str,
# ) -> str:
#     """
#     Send a real meeting confirmation email using Gmail SMTP.
#     """

#     smtp_email = os.getenv("SMTP_EMAIL")
#     smtp_password = os.getenv("SMTP_PASSWORD")

#     if not smtp_email or not smtp_password:
#         raise ValueError("SMTP_EMAIL or SMTP_PASSWORD not configured.")

#     if not to_email or "@" not in to_email:
#         raise ValueError(f"Invalid email address: {to_email}")

#     msg = EmailMessage()
#     msg["Subject"] = "DigitalSofts - Meeting Confirmation"
#     msg["From"] = smtp_email
#     msg["To"] = to_email

#     msg.set_content(
#         f"""
# Hello {client_name},

# Your meeting with DigitalSofts has been booked successfully.

# Meeting Details
# -------------------------
# {meeting_details}

# Thank you for choosing DigitalSofts.

# Regards,
# DigitalSofts Team
# """
#     )

#     try:
#         with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
#             smtp.starttls()
#             smtp.login(smtp_email, smtp_password)
#             smtp.send_message(msg)

#         return f"Confirmation email sent successfully to {to_email}."

#     except Exception as e:
#         raise RuntimeError(f"Failed to send email: {e}")


import os
from dotenv import load_dotenv
import resend
from langchain_core.tools import tool

load_dotenv()

resend.api_key = os.getenv("RESEND_API_KEY")


@tool
def send_confirmation_email(
    to_email: str,
    client_name: str,
    meeting_details: str,
) -> str:
    """Send meeting confirmation email."""

    params = {
        "from": "DigitalSofts <onboarding@resend.dev>",
        "to": [to_email],
        "subject": "Meeting Confirmation",
        "html": f"""
        <h2>Meeting Confirmed</h2>

        <p>Hello {client_name},</p>

        <p>Your meeting has been booked successfully.</p>

        <p>{meeting_details}</p>

        <p>Thank you for choosing DigitalSofts.</p>
        """,
    }

    resend.Emails.send(params)

    return f"Confirmation email sent to {to_email}"
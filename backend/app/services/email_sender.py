import smtplib
import ssl
from email.message import EmailMessage
from typing import Optional, Tuple

from ..config import (
    RESEND_API_KEY, RESEND_FROM,
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM,
)


def active_transport() -> Optional[str]:
    if SMTP_USER and SMTP_PASSWORD:
        return "smtp"
    if RESEND_API_KEY:
        return "resend"
    return None


def is_configured() -> bool:
    return active_transport() is not None


def send_email(to: str, subject: str, body: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """Returns (ok, message_id, error)."""
    transport = active_transport()
    if transport == "smtp":
        return _send_smtp(to, subject, body)
    if transport == "resend":
        return _send_resend(to, subject, body)
    return False, None, "No email transport configured"


def _send_smtp(to: str, subject: str, body: str) -> Tuple[bool, Optional[str], Optional[str]]:
    sender = SMTP_FROM or SMTP_USER
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to
    msg["Subject"] = subject or "Document request"
    msg.set_content(body)
    msg.add_alternative(
        "<div style=\"font-family: -apple-system, Segoe UI, Roboto, sans-serif; "
        "font-size: 14px; line-height: 1.55; color: #1f2937; white-space: pre-wrap;\">"
        f"{_escape_html(body)}"
        "</div>",
        subtype="html",
    )

    try:
        ctx = ssl.create_default_context()
        if SMTP_PORT == 465:
            with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx, timeout=20) as smtp:
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as smtp:
                smtp.ehlo()
                smtp.starttls(context=ctx)
                smtp.ehlo()
                smtp.login(SMTP_USER, SMTP_PASSWORD)
                smtp.send_message(msg)
    except smtplib.SMTPAuthenticationError as e:
        return False, None, f"SMTP auth failed: {e.smtp_error.decode() if hasattr(e, 'smtp_error') and e.smtp_error else e}"
    except Exception as e:
        return False, None, f"SMTP error: {e}"

    # SMTP doesn't return a provider id; use the Message-ID we set/generated.
    return True, msg.get("Message-ID"), None


def _send_resend(to: str, subject: str, body: str) -> Tuple[bool, Optional[str], Optional[str]]:
    import resend
    resend.api_key = RESEND_API_KEY
    html_body = (
        "<div style=\"font-family: -apple-system, Segoe UI, Roboto, sans-serif; "
        "font-size: 14px; line-height: 1.55; color: #1f2937; white-space: pre-wrap;\">"
        f"{_escape_html(body)}"
        "</div>"
    )
    try:
        result = resend.Emails.send({
            "from": RESEND_FROM,
            "to": [to],
            "subject": subject or "Document request",
            "text": body,
            "html": html_body,
        })
    except Exception as e:
        return False, None, str(e)

    message_id = result.get("id") if isinstance(result, dict) else None
    return True, message_id, None


def _escape_html(text: str) -> str:
    return (
        text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
    )

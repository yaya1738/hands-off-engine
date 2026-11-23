"""Guarded SMTP email transport for CommHub.

No credentials or recipients are stored in source. Delivery is disabled unless
all SMTP settings are provided in the private runtime environment.
"""
import os
import smtplib
from email.message import EmailMessage


def send_email(recipient: str, subject: str, body: str, *, smtp_factory=None) -> str:
    """Send one email; raises ValueError if private configuration is incomplete."""
    host = os.getenv("EMAIL_SMTP_HOST", "").strip()
    username = os.getenv("EMAIL_SMTP_USERNAME", "").strip()
    password = os.getenv("EMAIL_SMTP_PASSWORD", "")
    sender = os.getenv("EMAIL_FROM", "").strip()
    if not all((host, username, password, sender, recipient.strip())):
        raise ValueError("email transport is not fully configured")
    port_text = os.getenv("EMAIL_SMTP_PORT", "465").strip()
    try:
        port = int(port_text)
    except ValueError as exc:
        raise ValueError("EMAIL_SMTP_PORT must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError("EMAIL_SMTP_PORT is outside the valid range")

    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)

    factory = smtp_factory or smtplib.SMTP_SSL
    with factory(host, port, timeout=15) as smtp:
        smtp.login(username, password)
        smtp.send_message(message)
    return "accepted_by_smtp"

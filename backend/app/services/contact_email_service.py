"""Email delivery service for contact form submissions."""

from __future__ import annotations

from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formataddr
import os
import smtplib
import ssl

from app.core.env_loader import load_backend_env

load_backend_env()


@dataclass(frozen=True)
class ContactEmailConfig:
    """SMTP configuration required to send contact-form emails."""

    inbox_email: str
    sender_email: str
    sender_name: str
    smtp_host: str
    smtp_port: int
    smtp_username: str
    smtp_password: str
    smtp_use_tls: bool
    smtp_use_ssl: bool


def _to_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_contact_email_config() -> ContactEmailConfig | None:
    """Load SMTP settings from environment; return None if incomplete."""

    inbox_email = os.getenv("CONTACT_INBOX_EMAIL", "").strip()
    sender_email = os.getenv("CONTACT_SENDER_EMAIL", "").strip()
    sender_name = os.getenv("CONTACT_SENDER_NAME", "CadArena Contact").strip()
    smtp_host = os.getenv("CONTACT_SMTP_HOST", "").strip()
    smtp_port_raw = os.getenv("CONTACT_SMTP_PORT", "").strip()
    smtp_username = os.getenv("CONTACT_SMTP_USERNAME", "").strip()
    smtp_password = os.getenv("CONTACT_SMTP_PASSWORD", "").strip()
    smtp_use_tls = _to_bool(os.getenv("CONTACT_SMTP_USE_TLS"), True)
    smtp_use_ssl = _to_bool(os.getenv("CONTACT_SMTP_USE_SSL"), False)

    if not (inbox_email and sender_email and smtp_host and smtp_port_raw):
        return None

    try:
        smtp_port = int(smtp_port_raw)
    except ValueError:
        return None

    return ContactEmailConfig(
        inbox_email=inbox_email,
        sender_email=sender_email,
        sender_name=sender_name,
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        smtp_username=smtp_username,
        smtp_password=smtp_password,
        smtp_use_tls=smtp_use_tls,
        smtp_use_ssl=smtp_use_ssl,
    )


def send_contact_email(
    *,
    name: str,
    email: str,
    subject: str,
    message: str,
    client_ip: str | None,
    user_agent: str | None,
) -> None:
    """Send contact-form content to configured inbox via SMTP."""

    config = load_contact_email_config()
    if config is None:
        raise RuntimeError("Contact email service is not configured")

    email_message = EmailMessage()
    email_message["From"] = formataddr((config.sender_name, config.sender_email))
    email_message["To"] = config.inbox_email
    email_message["Reply-To"] = email
    email_message["Subject"] = f"[CadArena Contact] {subject}"

    text_body = (
        f"New contact form message\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Subject: {subject}\n"
        f"Client IP: {client_ip or '-'}\n"
        f"User Agent: {user_agent or '-'}\n\n"
        f"Message:\n{message}\n"
    )
    email_message.set_content(text_body)

    timeout_seconds = 20

    try:
        if config.smtp_use_ssl:
            with smtplib.SMTP_SSL(
                host=config.smtp_host,
                port=config.smtp_port,
                timeout=timeout_seconds,
                context=ssl.create_default_context(),
            ) as server:
                if config.smtp_username:
                    server.login(config.smtp_username, config.smtp_password)
                server.send_message(email_message)
            return

        with smtplib.SMTP(host=config.smtp_host, port=config.smtp_port, timeout=timeout_seconds) as server:
            server.ehlo()
            if config.smtp_use_tls:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            if config.smtp_username:
                server.login(config.smtp_username, config.smtp_password)
            server.send_message(email_message)
    except smtplib.SMTPException as exc:
        raise RuntimeError("Unable to send contact email") from exc

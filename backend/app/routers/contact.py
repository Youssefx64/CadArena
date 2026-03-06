"""Contact form router for sending emails from the website."""

from __future__ import annotations

import re

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.services.contact_email_service import send_contact_email

logger = get_logger(__name__)
router = APIRouter()
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class ContactSendEmailRequest(BaseModel):
    """Expected payload for contact form email delivery."""

    name: str = Field(..., min_length=2, max_length=80)
    email: str = Field(..., min_length=5, max_length=254)
    subject: str = Field(..., min_length=3, max_length=160)
    message: str = Field(..., min_length=10, max_length=5000)


@router.post("/contact/send-email")
def contact_send_email(request: ContactSendEmailRequest, req: Request):
    """Send website contact message to configured support inbox."""

    normalized_email = request.email.strip().lower()
    if not _EMAIL_RE.match(normalized_email):
        raise HTTPException(status_code=422, detail="Invalid email format")

    client_host = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent")

    try:
        send_contact_email(
            name=request.name.strip(),
            email=normalized_email,
            subject=request.subject.strip(),
            message=request.message.strip(),
            client_ip=client_host,
            user_agent=user_agent,
        )
    except RuntimeError as exc:
        logger.warning("event=contact_email_failed reason=%s", exc)
        raise HTTPException(status_code=503, detail="Contact email service unavailable") from exc

    return {"success": True, "message": "Email sent successfully"}

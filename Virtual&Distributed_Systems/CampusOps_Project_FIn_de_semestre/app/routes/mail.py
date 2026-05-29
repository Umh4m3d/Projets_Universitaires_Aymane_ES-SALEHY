"""
GET  /api/v1/mail/latest     → last 10 emails from the inbox (admin only)
POST /api/v1/mail/send       → send an email (admin only)
POST /api/v1/mail/process    → parse inbox and create internal notifications (OpenClaw hook)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from pydantic import BaseModel, EmailStr
from typing import Optional

from app.core.dependencies import require_role
from app.core.logging_config import logger
from app.db.session import get_db
from app.models.user import User
from app.models.notification import Notification

router = APIRouter(prefix="/mail", tags=["Mail"])


class SendMailRequest(BaseModel):
    to: EmailStr
    subject: str
    body: str


class MailOut(BaseModel):
    uid: str
    subject: str
    sender: str
    date: str
    preview: str


@router.get("/latest", response_model=list[MailOut])
def get_latest_emails(
    limit: int = 10,
    current_user: User = Depends(require_role("admin")),
):
    """Fetch the latest emails from the IMAP inbox."""
    try:
        from app.services.mail_service import fetch_latest_emails
        emails = fetch_latest_emails(limit=min(limit, 50))
        return emails
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected mail inbox error")
        raise HTTPException(status_code=503, detail=f"Mailbox is unavailable: {e}")


@router.post("/send", status_code=200)
def send_mail(
    data: SendMailRequest,
    current_user: User = Depends(require_role("admin")),
):
    """Send an email via SMTP."""
    try:
        from app.services.mail_service import send_email
        send_email(
            to=data.to,
            subject=data.subject,
            html_body=f"<p>{data.body.replace(chr(10), '<br>')}</p>",
            text_body=data.body,
        )
        return {"message": f"Email sent to {data.to}"}
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected mail send error")
        raise HTTPException(status_code=503, detail=f"Mail service is unavailable: {e}")


@router.post("/process", status_code=200)
def process_inbox(
    current_user: User = Depends(require_role("admin")),
    db: DBSession = Depends(get_db),
):
    """
    Reads the last 20 emails and converts matching ones into internal notifications.

    Matching rules (keyword-based, extend as needed):
      - Subject contains "absence justifiée"  → notification type: absence_justified
      - Subject contains "paiement reçu"      → notification type: payment_received
      - Subject contains "inscription"        → notification type: registration

    Returns a count of notifications created.
    """
    try:
        from app.services.mail_service import fetch_latest_emails
        emails = fetch_latest_emails(limit=20)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Unexpected mail processing error")
        raise HTTPException(status_code=503, detail=f"Mailbox is unavailable: {e}")

    KEYWORD_MAP = {
        "absence justifiée": "absence_justified",
        "justified absence": "absence_justified",
        "paiement reçu":     "payment_received",
        "payment received":  "payment_received",
        "inscription":       "registration",
        "registration":      "registration",
    }

    created = 0
    admins = db.query(User).filter(
        User.role == "admin",
        User.is_active == True
    ).all()

    for mail in emails:
        subject_lower = mail["subject"].lower()
        matched_type = None
        for keyword, notif_type in KEYWORD_MAP.items():
            if keyword in subject_lower:
                matched_type = notif_type
                break

        if not matched_type:
            continue

        message = (
            f"[Email → Notification] {mail['subject']}\n"
            f"From: {mail['sender']}\n"
            f"Date: {mail['date']}\n"
            f"Preview: {mail['preview']}"
        )

        for admin in admins:
            notif = Notification(
                user_id=admin.id,
                type=matched_type,
                message=message[:1000],
                status="pending",
            )
            db.add(notif)
            created += 1

    db.commit()
    logger.info(f"Mail processing: {created} notifications created from inbox")
    return {"message": f"{created} notification(s) created from inbox emails."}

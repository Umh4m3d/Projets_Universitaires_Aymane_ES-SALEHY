# /services/mail_service.py
"""
mail_service.py — IMAP reading + SMTP sending.

Required .env variables:
    MAIL_HOST_SMTP=smtp.gmail.com      (or MAIL_HOST as fallback)
    MAIL_HOST_IMAP=imap.gmail.com      (or MAIL_HOST as fallback)
    MAIL_PORT_IMAP=993
    MAIL_PORT_SMTP=587
    MAIL_USER=you@gmail.com
    MAIL_PASSWORD=your_16char_app_password
    MAIL_FROM_NAME=CampusOps
    FRONTEND_URL=http://localhost:5173
"""

import imaplib
import smtplib
import email as email_lib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import decode_header
import os

from app.core.logging_config import logger

# ── Config ────────────────────────────────────────────────────────────────────

MAIL_HOST_SMTP = os.getenv("MAIL_HOST_SMTP", os.getenv("MAIL_HOST", ""))
MAIL_HOST_IMAP = os.getenv("MAIL_HOST_IMAP", os.getenv("MAIL_HOST", ""))
MAIL_PORT_IMAP = int(os.getenv("MAIL_PORT_IMAP", "993"))
MAIL_PORT_SMTP = int(os.getenv("MAIL_PORT_SMTP", "587"))
MAIL_USER      = os.getenv("MAIL_USER", "")
MAIL_PASSWORD  = os.getenv("MAIL_PASSWORD", "")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME", "CampusOps")
FRONTEND_URL   = os.getenv("FRONTEND_URL", "http://localhost:5173")


def ensure_imap_configured() -> None:
    if not MAIL_HOST_IMAP or not MAIL_USER or not MAIL_PASSWORD:
        raise RuntimeError("Mail inbox is not configured in .env")


def ensure_smtp_configured() -> None:
    if not MAIL_HOST_SMTP or not MAIL_USER or not MAIL_PASSWORD:
        raise RuntimeError("Mail sending is not configured in .env")


def _decode_header_value(value: str) -> str:
    parts = decode_header(value)
    result = []
    for part, enc in parts:
        if isinstance(part, bytes):
            result.append(part.decode(enc or "utf-8", errors="replace"))
        else:
            result.append(part)
    return "".join(result)


def _extract_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace")
    else:
        charset = msg.get_content_charset() or "utf-8"
        return msg.get_payload(decode=True).decode(charset, errors="replace")
    return ""


# ── IMAP: Read emails ─────────────────────────────────────────────────────────

def fetch_latest_emails(limit: int = 10) -> list[dict]:
    ensure_imap_configured()

    try:
        mail = imaplib.IMAP4_SSL(MAIL_HOST_IMAP, MAIL_PORT_IMAP)
        mail.login(MAIL_USER, MAIL_PASSWORD)
        mail.select("INBOX")

        _, data = mail.search(None, "ALL")
        all_ids = data[0].split()
        ids_to_fetch = all_ids[-limit:] if len(all_ids) >= limit else all_ids
        ids_to_fetch = list(reversed(ids_to_fetch))

        messages = []
        for uid in ids_to_fetch:
            _, msg_data = mail.fetch(uid, "(RFC822)")
            raw = msg_data[0][1]
            msg = email_lib.message_from_bytes(raw)

            subject  = _decode_header_value(msg.get("Subject", "(no subject)"))
            sender   = _decode_header_value(msg.get("From", ""))
            date_str = msg.get("Date", "")
            body     = _extract_body(msg)
            preview  = body.strip()[:200].replace("\n", " ")

            messages.append({
                "uid":     uid.decode(),
                "subject": subject,
                "sender":  sender,
                "date":    date_str,
                "preview": preview,
                "body":    body.strip()[:2000],
            })

        mail.logout()
        return messages

    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP error: {e}")
        raise RuntimeError(f"IMAP connection failed: {e}")
    except Exception as e:
        logger.error(f"Unexpected mailbox error: {e}")
        raise RuntimeError(f"Mailbox is unavailable: {e}")


# ── SMTP: Send emails ─────────────────────────────────────────────────────────

def send_email(to: str, subject: str, html_body: str, text_body: str = "") -> None:
    """Sends an email via SMTP (STARTTLS on port 587)."""
    ensure_smtp_configured()

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = f"{MAIL_FROM_NAME} <{MAIL_USER}>"
    msg["To"]      = to

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    try:
        with smtplib.SMTP(MAIL_HOST_SMTP, MAIL_PORT_SMTP) as server:
            server.ehlo()
            server.starttls()
            server.login(MAIL_USER, MAIL_PASSWORD)
            server.sendmail(MAIL_USER, to, msg.as_string())
        logger.info(f"Email sent to {to}: {subject}")
    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"SMTP auth failed — check MAIL_PASSWORD is a Gmail App Password: {e}")
        raise RuntimeError(f"SMTP authentication failed: {e}")
    except smtplib.SMTPException as e:
        logger.error(f"SMTP error sending to {to}: {e}")
        raise RuntimeError(f"Failed to send email: {e}")
    except Exception as e:
        logger.error(f"Unexpected SMTP error sending to {to}: {e}")
        raise RuntimeError(f"Mail service is unavailable: {e}")


# ── Transactional email templates ─────────────────────────────────────────────

def send_password_reset_email(to: str, full_name: str, token: str) -> None:
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
      <h2 style="color: #1e40af;">Password Reset — CampusOps</h2>
      <p>Hello {full_name},</p>
      <p>You requested a password reset. Click the link below to set a new password.
         The link expires in <strong>1 hour</strong>.</p>
      <p>
        <a href="{reset_url}"
           style="background:#1e40af;color:#fff;padding:12px 24px;
                  border-radius:6px;text-decoration:none;display:inline-block;">
          Reset my password
        </a>
      </p>
      <p style="color:#64748b;font-size:13px;">
        If you did not request this, you can safely ignore this email.
      </p>
    </div>
    """
    text = (
        f"Password Reset — CampusOps\n\n"
        f"Hello {full_name},\n\n"
        f"Reset your password here: {reset_url}\n\n"
        f"The link expires in 1 hour.\n"
        f"If you did not request this, ignore this email."
    )
    send_email(to, "Reset your CampusOps password", html, text)


def send_absence_notification(to: str, full_name: str,
                               course: str, date: str, room: str) -> None:
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
      <h2 style="color:#dc2626;">Absence Recorded — CampusOps</h2>
      <p>Hello {full_name},</p>
      <p>An absence has been recorded for you:</p>
      <ul>
        <li><strong>Course:</strong> {course}</li>
        <li><strong>Date:</strong> {date}</li>
        <li><strong>Room:</strong> {room}</li>
      </ul>
      <p>If this is incorrect or you have a justification, please contact your secretary.</p>
    </div>
    """
    text = (
        f"Absence Recorded — CampusOps\n\n"
        f"Hello {full_name},\n\n"
        f"An absence has been recorded for you:\n"
        f"  Course: {course}\n  Date: {date}\n  Room: {room}\n\n"
        f"Contact your secretary if you have a justification."
    )
    send_email(to, f"Absence recorded — {course} on {date}", html, text)


def send_parent_absence_alert(
    to: str,
    parent_name: str,
    student_name: str,
    absence_count: int,
    date: str,
    courses: list[str],
) -> None:
    """
    Sent to the parent/guardian when their student has more than one absence
    on the same day. `courses` is a list of course names for each absence.
    """
    courses_html = "".join(f"<li>{c}</li>" for c in courses)
    courses_text = "\n".join(f"  - {c}" for c in courses)
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
      <h2 style="color:#dc2626;">Multiple Absences Alert — CampusOps</h2>
      <p>Dear {parent_name},</p>
      <p>
        Your student <strong>{student_name}</strong> was recorded absent
        <strong>{absence_count} times</strong> on <strong>{date}</strong>:
      </p>
      <ul>{courses_html}</ul>
      <p>
        Please contact the school secretary if you have a justification or
        need further information.
      </p>
    </div>
    """
    text = (
        f"Multiple Absences Alert — CampusOps\n\n"
        f"Dear {parent_name},\n\n"
        f"{student_name} was absent {absence_count} time(s) on {date}:\n"
        f"{courses_text}\n\n"
        f"Please contact the school secretary for more information."
    )
    send_email(
        to,
        f"Multiple absences for {student_name} on {date}",
        html,
        text,
    )


def send_session_cancellation(
    to: str,
    full_name: str,
    course: str,
    date: str,
    start_time: str,
    end_time: str,
    room: str,
    reason: str | None = None,
) -> None:
    """Sent to every student in the group when their session is cancelled."""
    reason_block = (
        f"<p><strong>Reason:</strong> {reason}</p>" if reason else ""
    )
    reason_text = f"\nReason: {reason}" if reason else ""
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
      <h2 style="color:#d97706;">Session Cancelled — CampusOps</h2>
      <p>Hello {full_name},</p>
      <p>The following session has been <strong>cancelled</strong>:</p>
      <ul>
        <li><strong>Course:</strong> {course}</li>
        <li><strong>Date:</strong> {date}</li>
        <li><strong>Time:</strong> {start_time} – {end_time}</li>
        <li><strong>Room:</strong> {room}</li>
      </ul>
      {reason_block}
      <p style="color:#64748b;font-size:13px;">
        Contact your secretary or teacher for any rescheduling information.
      </p>
    </div>
    """
    text = (
        f"Session Cancelled — CampusOps\n\n"
        f"Hello {full_name},\n\n"
        f"The following session has been cancelled:\n"
        f"  Course: {course}\n"
        f"  Date:   {date}\n"
        f"  Time:   {start_time} – {end_time}\n"
        f"  Room:   {room}"
        f"{reason_text}\n\n"
        f"Contact your secretary or teacher for rescheduling info."
    )
    send_email(to, f"Session cancelled — {course} on {date}", html, text)


def send_payment_overdue_notification(
    to: str, full_name: str,
    amount: float, month: str,
    due_date: str,
) -> None:
    html = f"""
    <div style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
      <h2 style="color:#d97706;">Payment Overdue — CampusOps</h2>
      <p>Hello {full_name},</p>
      <p>A payment is now overdue:</p>
      <ul>
        <li><strong>Amount due:</strong> {amount} DH</li>
        <li><strong>Month:</strong> {month or '—'}</li>
        <li><strong>Due date:</strong> {due_date}</li>
      </ul>
      <p>Please contact the administration to regularize your situation.</p>
    </div>
    """
    text = (
        f"Payment Overdue — CampusOps\n\n"
        f"Hello {full_name},\n\n"
        f"A payment of {amount} DH (month: {month or '—'}) "
        f"was due on {due_date} and is now overdue.\n\n"
        f"Please contact administration."
    )
    send_email(to, "Payment overdue — CampusOps", html, text)


def send_weekly_schedule(
    to: str,
    full_name: str,
    sessions: list[dict],
    week_from: str,
    week_to: str,
) -> None:
    """
    Sends a teacher their full next-week schedule.
    Called by OpenClaw every Sunday at 12:00.
    """
    if not sessions:
        body_html = "<p>No sessions scheduled for next week.</p>"
        body_text = "No sessions scheduled for next week."
    else:
        # Group sessions by date for a cleaner layout
        from collections import defaultdict
        by_date: dict[str, list] = defaultdict(list)
        for s in sessions:
            by_date[s.get("date", "")].append(s)

        rows = ""
        lines = []
        for day_date in sorted(by_date.keys()):
            # Format the date header  e.g. "Monday, 11 May 2026"
            try:
                from datetime import date as date_type
                d = date_type.fromisoformat(day_date)
                day_label = d.strftime("%A, %d %B %Y")
            except Exception:
                day_label = day_date

            rows += (
                f"<tr>"
                f"<td colspan='4' style='padding:10px 8px 4px;font-weight:700;"
                f"color:#1e40af;border-bottom:2px solid #bfdbfe;font-size:13px'>"
                f"{day_label}</td>"
                f"</tr>"
            )
            lines.append(f"\n{day_label}")

            for s in by_date[day_date]:
                start = s.get("start_time", "")[:5]
                end   = s.get("end_time",   "")[:5]
                rows += (
                    f"<tr>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #e2e8f0'>{start}–{end}</td>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #e2e8f0'>{s.get('course_name','')}</td>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #e2e8f0'>{s.get('group_name','')}</td>"
                    f"<td style='padding:6px 8px;border-bottom:1px solid #e2e8f0'>{s.get('room','')}</td>"
                    f"</tr>"
                )
                lines.append(f"  {start}–{end} | {s.get('course_name','')} | {s.get('group_name','')} | Room {s.get('room','')}")

        body_html = f"""
        <table style='width:100%;border-collapse:collapse;font-size:14px'>
          <thead>
            <tr style='background:#eff6ff'>
              <th style='padding:8px;text-align:left;color:#1e40af'>Time</th>
              <th style='padding:8px;text-align:left;color:#1e40af'>Course</th>
              <th style='padding:8px;text-align:left;color:#1e40af'>Group</th>
              <th style='padding:8px;text-align:left;color:#1e40af'>Room</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>"""
        body_text = "\n".join(lines)

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2 style="color:#1e40af;">Your Weekly Schedule — CampusOps</h2>
      <p>Hello {full_name},</p>
      <p>Here is your schedule for next week
         (<strong>{week_from}</strong> → <strong>{week_to}</strong>):
      </p>
      {body_html}
      <p style="color:#64748b;font-size:12px;margin-top:16px">
        This email is sent automatically every Sunday by CampusOps.
      </p>
    </div>"""

    text = (
        f"Your Weekly Schedule — CampusOps\n\n"
        f"Hello {full_name},\n\n"
        f"Schedule for {week_from} → {week_to}:\n"
        f"{body_text}\n"
    )

    send_email(
        to,
        f"Your schedule for next week ({week_from} → {week_to}) — CampusOps",
        html,
        text,
    )


# Keep the old send_daily_schedule for any other use (e.g. Telegram bot)
def send_daily_schedule(to: str, full_name: str, sessions: list[dict]) -> None:
    """Sends tomorrow's schedule — used by the Telegram bot or one-off daily reminders."""
    if not sessions:
        body_html = "<p>No sessions scheduled for tomorrow.</p>"
        body_text = "No sessions scheduled for tomorrow."
    else:
        rows = ""
        lines = []
        for s in sessions:
            rows += (
                f"<tr>"
                f"<td style='padding:8px;border-bottom:1px solid #e2e8f0'>{s.get('start_time','')[:5]}–{s.get('end_time','')[:5]}</td>"
                f"<td style='padding:8px;border-bottom:1px solid #e2e8f0'>{s.get('course_name','')}</td>"
                f"<td style='padding:8px;border-bottom:1px solid #e2e8f0'>{s.get('group_name','')}</td>"
                f"<td style='padding:8px;border-bottom:1px solid #e2e8f0'>{s.get('room','')}</td>"
                f"</tr>"
            )
            lines.append(
                f"  {s.get('start_time','')[:5]}–{s.get('end_time','')[:5]} | "
                f"{s.get('course_name','')} | {s.get('group_name','')} | Room {s.get('room','')}"
            )
        body_html = f"""
        <table style='width:100%;border-collapse:collapse;font-size:14px'>
          <thead>
            <tr style='background:#f1f5f9'>
              <th style='padding:8px;text-align:left'>Time</th>
              <th style='padding:8px;text-align:left'>Course</th>
              <th style='padding:8px;text-align:left'>Group</th>
              <th style='padding:8px;text-align:left'>Room</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </table>"""
        body_text = "\n".join(lines)

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:auto">
      <h2 style="color:#1e40af;">Tomorrow's Schedule — CampusOps</h2>
      <p>Hello {full_name},</p>
      <p>Here is your schedule for tomorrow:</p>
      {body_html}
    </div>"""
    text = f"Tomorrow's Schedule — CampusOps\n\nHello {full_name},\n\n{body_text}"
    send_email(to, "Your schedule for tomorrow — CampusOps", html, text)

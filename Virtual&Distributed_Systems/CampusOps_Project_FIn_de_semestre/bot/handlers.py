from datetime import date

from telegram import Update
from telegram.ext import ContextTypes

from api_client import (
    bot_login,
    get_my_absences,
    get_my_notifications,
    get_my_payments,
    get_overdue_payments,
    get_pending_notifications,
    get_pending_profile_requests,
    get_pending_sessions,
    get_progress_entries,
    get_sessions_today,
    get_sessions_week,
    get_user_by_chat_id,
    link_telegram,
)


def fmt_session(s: dict) -> str:
    return (
        f"📅 {s['date']} | {s['start_time'][:5]} – {s['end_time'][:5]}\n"
        f"📘 {s.get('course_name', 'Unknown')}\n"
        f"🏫 Room {s['room']}\n"
    )


def fmt_absence(a: dict) -> str:
    status = "✅ Justified" if a["is_justified"] else "❌ Unjustified"
    note = f"\nNote: {a['justification']}" if a["justification"] else ""
    course = f" | {a.get('course_name', 'Unknown')}" if a.get("course_name") else ""
    return f"📅 {a['created_at'][:10]}{course} | {status}{note}\n"


def fmt_payment(p: dict) -> str:
    icons = {
        "paid": "✅",
        "partial": "⚠️",
        "overdue": "🔴",
        "pending": "🕐",
    }
    icon = icons.get(p["status"], "❓")
    month = f" ({p['month']})" if p["month"] else ""
    return (
        f"{icon} {p['type'].capitalize()}{month}\n"
        f"Paid: {p['amount_paid']}/{p['amount']} | due {p['due_date']} | {p['status'].upper()}\n"
    )


def fmt_notification(n: dict) -> str:
    stamp = n.get("created_at", "")[:16].replace("T", " ")
    return f"• [{n.get('type', 'info')}] {n.get('message', '')[:140]}\n  {stamp}\n"


def fmt_pending_session(s: dict) -> str:
    return (
        f"• {s.get('date')} {s.get('start_time', '')[:5]}-{s.get('end_time', '')[:5]}\n"
        f"  {s.get('course_name', 'Unknown')} | {s.get('group_name', 'Unknown')}\n"
        f"  Teacher: {s.get('teacher_name', 'Unknown')} | Room {s.get('room', '—')}\n"
    )


def fmt_change_request(r: dict) -> str:
    return (
        f"• {r.get('user_name', 'Unknown')} requested {r.get('field', 'field')}\n"
        f"  {r.get('old_value', '—')} → {r.get('new_value', '—')}\n"
    )


def fmt_overdue_payment(p: dict) -> str:
    return (
        f"• {p.get('student_name', 'Unknown')} | {p.get('type', 'payment')}\n"
        f"  {p.get('amount_paid', 0)}/{p.get('amount', 0)} | due {p.get('due_date', '—')}\n"
    )


def fmt_progress_entry(entry: dict) -> str:
    stamp = entry.get("updated_at", "")[:16].replace("T", " ")
    return (
        f"• {entry.get('teacher_name', 'Unknown')} | {entry.get('course_name', 'Unknown')}\n"
        f"  {entry.get('group_name', 'Unknown')} | {entry.get('chapter', '—')[:70]}\n"
        f"  {entry.get('completion', 0)}% | {stamp}\n"
    )


def build_help_text(role: str) -> str:
    if role == "admin":
        return (
            "CampusOps Bot — Admin Commands:\n\n"
            "/today — daily admin summary\n"
            "/week — pending session requests\n"
            "/requests — session and profile approval queue\n"
            "/notifications — pending alerts\n"
            "/overdue — overdue payments\n"
            "/help — this message"
        )

    if role == "teacher":
        return (
            "CampusOps Bot — Teacher Commands:\n\n"
            "/today — today's sessions\n"
            "/week — this week's sessions\n"
            "/notifications — your recent notifications\n"
            "/help — this message"
        )

    if role == "student":
        return (
            "CampusOps Bot — Student Commands:\n\n"
            "/today — today's sessions\n"
            "/week — this week's sessions\n"
            "/absence — your absences\n"
            "/payments — your payments\n"
            "/notifications — your recent notifications\n"
            "/help — this message"
        )

    return (
        "CampusOps Bot — Commands:\n\n"
        "/today — today's overview\n"
        "/week — this week's overview\n"
        "/notifications — recent notifications\n"
        "/help — this message"
    )


async def get_token(chat_id: int) -> str | None:
    return await bot_login(str(chat_id))


async def require_identity(update: Update) -> tuple[dict | None, str | None]:
    user = await get_user_by_chat_id(str(update.effective_chat.id))
    token = await get_token(update.effective_chat.id)

    if not user or not token:
        await update.message.reply_text(
            "Your account is not linked or has been deactivated.\n"
            "Use /link YOUR_CODE to connect your CampusOps account."
        )
        return None, None

    return user, token


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user_by_chat_id(str(update.effective_chat.id))
    if user:
        await update.message.reply_text(
            f"Welcome back, {user['full_name']} ({user['role']})!\n\n"
            f"{build_help_text(user['role'])}"
        )
    else:
        await update.message.reply_text(
            "Welcome to CampusOps!\n\n"
            "Your Telegram is not linked yet.\n"
            "Log into the web app, generate a link code, then send:\n\n"
            "/link YOUR_CODE"
        )


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "Usage: /link YOUR_CODE\n"
            "Get your code from the CampusOps web app."
        )
        return

    otp = context.args[0].strip()
    chat_id = str(update.effective_chat.id)
    result = await link_telegram(chat_id, otp)

    if result["status"] == 200:
        await update.message.reply_text(
            "Linked successfully!\n"
            "Type /start to see your commands."
        )
    elif result["status"] == 409:
        await update.message.reply_text(
            "This Telegram is already linked to another account."
        )
    else:
        detail = result["data"].get("detail", "Something went wrong")
        await update.message.reply_text(f"Failed: {detail}")


async def today_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, token = await require_identity(update)
    if not user or not token:
        return

    if user["role"] == "admin":
        pending_sessions = await get_pending_sessions(token)
        pending_changes = await get_pending_profile_requests(token)
        pending_notifications = await get_pending_notifications(token)
        overdue_payments = await get_overdue_payments(token)
        progress_entries = await get_progress_entries(token)

        today_prefix = str(date.today())
        today_progress = [
            entry for entry in progress_entries
            if entry.get("updated_at", "").startswith(today_prefix)
        ]

        lines = [
            "📌 Admin daily summary\n",
            f"Pending session requests: {len(pending_sessions)}",
            f"Pending profile changes: {len(pending_changes)}",
            f"Pending alerts: {len(pending_notifications)}",
            f"Overdue payments: {len(overdue_payments)}",
            f"Progress entries updated today: {len(today_progress)}",
        ]

        if today_progress:
            lines.append("\nLatest progress updates:")
            for entry in today_progress[:5]:
                lines.append(fmt_progress_entry(entry))

        await update.message.reply_text("\n".join(lines))
        return

    sessions = await get_sessions_today(token)
    if not sessions:
        await update.message.reply_text("No sessions scheduled for today.")
        return

    lines = [f"📚 Today's sessions ({len(sessions)}):\n"]
    for s in sessions:
        lines.append(fmt_session(s))

    await update.message.reply_text("\n".join(lines))


async def week_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, token = await require_identity(update)
    if not user or not token:
        return

    if user["role"] == "admin":
        sessions = await get_pending_sessions(token)
        if not sessions:
            await update.message.reply_text("No pending session requests.")
            return

        lines = [f"🗂 Pending session requests ({len(sessions)}):\n"]
        for item in sessions[:8]:
            lines.append(fmt_pending_session(item))
        await update.message.reply_text("\n".join(lines))
        return

    sessions = await get_sessions_week(token)
    if not sessions:
        await update.message.reply_text("No sessions this week.")
        return

    by_date: dict[str, list] = {}
    for s in sessions:
        by_date.setdefault(s["date"], []).append(s)

    lines = [f"📅 This week ({len(sessions)} sessions):\n"]
    for day, day_sessions in sorted(by_date.items()):
        lines.append(f"── {day} ──")
        for s in day_sessions:
            lines.append(fmt_session(s))

    await update.message.reply_text("\n".join(lines))


async def requests_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, token = await require_identity(update)
    if not user or not token:
        return

    if user["role"] != "admin":
        await update.message.reply_text("This command is available to admins only.")
        return

    pending_sessions = await get_pending_sessions(token)
    pending_changes = await get_pending_profile_requests(token)

    lines = [
        "🗂 Approval queue\n",
        f"Session requests: {len(pending_sessions)}",
        f"Profile change requests: {len(pending_changes)}",
    ]

    if pending_sessions:
        lines.append("\nPending sessions:")
        for item in pending_sessions[:5]:
            lines.append(fmt_pending_session(item))

    if pending_changes:
        lines.append("\nPending profile changes:")
        for item in pending_changes[:5]:
            lines.append(fmt_change_request(item))

    await update.message.reply_text("\n".join(lines))


async def notifications_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, token = await require_identity(update)
    if not user or not token:
        return

    if user["role"] == "admin":
        notifications = await get_pending_notifications(token)
        title = "🔔 Pending alerts"
    else:
        notifications = await get_my_notifications(token)
        title = "🔔 Your recent notifications"

    if not notifications:
        await update.message.reply_text("No notifications found.")
        return

    lines = [f"{title} ({len(notifications)}):\n"]
    for item in notifications[:8]:
        lines.append(fmt_notification(item))

    await update.message.reply_text("\n".join(lines))


async def overdue_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, token = await require_identity(update)
    if not user or not token:
        return

    if user["role"] not in {"admin", "secretary"}:
        await update.message.reply_text("This command is available to admins and secretaries only.")
        return

    overdue_payments = await get_overdue_payments(token)
    if not overdue_payments:
        await update.message.reply_text("No overdue payments found.")
        return

    lines = [f"💰 Overdue payments ({len(overdue_payments)}):\n"]
    for item in overdue_payments[:8]:
        lines.append(fmt_overdue_payment(item))

    await update.message.reply_text("\n".join(lines))


async def absence_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, token = await require_identity(update)
    if not user or not token:
        return

    if user["role"] != "student":
        await update.message.reply_text("This command is available to students only.")
        return

    absences = await get_my_absences(token)
    if not absences:
        await update.message.reply_text("No absences recorded for you.")
        return

    lines = [f"📋 Your absences ({len(absences)}):\n"]
    for a in absences[:10]:
        lines.append(fmt_absence(a))

    await update.message.reply_text("\n".join(lines))


async def payments_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user, token = await require_identity(update)
    if not user or not token:
        return

    if user["role"] != "student":
        await update.message.reply_text("This command is available to students only.")
        return

    payments = await get_my_payments(token)
    if not payments:
        await update.message.reply_text("No payment records found.")
        return

    lines = [f"💰 Your payments ({len(payments)}):\n"]
    for p in payments[:10]:
        lines.append(fmt_payment(p))

    await update.message.reply_text("\n".join(lines))


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await get_user_by_chat_id(str(update.effective_chat.id))
    role = user["role"] if user else "guest"
    await update.message.reply_text(build_help_text(role))


async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Unknown command. Type /help to see available commands."
    )

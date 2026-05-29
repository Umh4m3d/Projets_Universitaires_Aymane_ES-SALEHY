# openclaw/main.py
"""
OpenClaw — CampusOps orchestrator.

Triggers:
  - Sunday 12:00       : send next week's planning to each teacher by email
  - Every 5 min        : check for overdue payments → notify + create follow-up task
  - Event hook (poll)  : absence created → student notified; >1 absence/day → parent notified
  - Event hook (poll)  : session cancelled → students notified by email

Run:  python openclaw/main.py
Env:  OPENCLAW_KEY, CAMPUSOPS_API_URL, OPENROUTER_API_KEY (optional)
"""

import os
import time
import logging
import requests
import schedule
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# ── load env (try local first, then fall back to backend .env) ────────────────
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | OpenClaw | %(message)s",
)
log = logging.getLogger("openclaw")

API_URL    = os.getenv("CAMPUSOPS_API_URL", "http://localhost:8000/api/v1")
CLAW_KEY   = os.getenv("OPENCLAW_KEY", "")
OR_KEY     = os.getenv("OPENROUTER_API_KEY", "")   # optional — for AI summaries

HEADERS = {"X-OpenClaw-Key": CLAW_KEY, "Content-Type": "application/json"}


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def post(path: str, body: dict) -> dict | None:
    try:
        r = requests.post(f"{API_URL}{path}", json=body, headers=HEADERS, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.error(f"POST {path} failed: {e}")
        return None


def ai_summarize(text: str, prompt: str = "") -> str:
    """
    Optional: call OpenRouter to generate a friendly summary.
    Falls back to the raw text if no key is configured.
    """
    if not OR_KEY:
        return text
    try:
        import openai
        client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OR_KEY,
        )
        resp = client.chat.completions.create(
            model="mistralai/mistral-7b-instruct:free",   # free model on OpenRouter
            messages=[
                {"role": "system", "content": prompt or "You are a helpful academic assistant. Be concise."},
                {"role": "user", "content": text},
            ],
            max_tokens=200,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        log.warning(f"OpenRouter call failed: {e}")
        return text


# ═══════════════════════════════════════════════════════════════════════════════
# Workflow 1 — Weekly planning email (Sunday 12:00)
# ═══════════════════════════════════════════════════════════════════════════════

def job_send_weekly_planning():
    """
    Fetches next week's sessions and emails each teacher their personal schedule.
    Runs every Sunday at 12:00.
    """
    log.info("► Running: send weekly planning emails")
    result = post("/openclaw/send-weekly-planning", {})
    if result:
        log.info(f"  Weekly planning sent: {result.get('message', result)}")
    else:
        log.warning("  Weekly planning job returned no result")


# ═══════════════════════════════════════════════════════════════════════════════
# Workflow 2 — Overdue payment check (every 5 minutes)
# ═══════════════════════════════════════════════════════════════════════════════

def job_check_overdue_payments():
    """
    Marks pending/partial payments as overdue if past due_date,
    then creates follow-up tasks for admins.
    """
    log.info("► Running: overdue payment check")
    result = post("/openclaw/check-overdue-payments", {})
    if result:
        count = result.get("overdue_count", 0)
        tasks = result.get("tasks_created", 0)
        if count:
            log.info(f"  {count} payment(s) marked overdue, {tasks} follow-up task(s) created")
    else:
        log.warning("  Overdue check returned no result")


# ═══════════════════════════════════════════════════════════════════════════════
# Workflow 3 — Session cancellation notifications (poll every 2 minutes)
# ═══════════════════════════════════════════════════════════════════════════════

def job_process_cancellations():
    """
    Polls for newly cancelled sessions and dispatches cancellation emails.
    The backend endpoint is idempotent — it only processes unnotified cancellations.
    """
    log.info("► Running: process session cancellations")
    result = post("/openclaw/process-cancellations", {})
    if result:
        count = result.get("processed", 0)
        if count:
            log.info(f"  {count} cancellation notification(s) dispatched")
    else:
        log.warning("  Cancellation processing returned no result")


# ═══════════════════════════════════════════════════════════════════════════════
# Scheduler setup
# ═══════════════════════════════════════════════════════════════════════════════

def setup_schedule():
    # ── Sunday 12:00 — weekly planning ──────────────────────────────
    schedule.every().sunday.at("12:00").do(job_send_weekly_planning)

    # ── Every 5 minutes — payment overdue check ──────────────────────
    schedule.every(5).minutes.do(job_check_overdue_payments)

    # ── Every 2 minutes — cancellation notifications ─────────────────
    schedule.every(2).minutes.do(job_process_cancellations)

    log.info("Scheduler configured:")
    log.info("  • Sunday 12:00    → weekly planning emails")
    log.info("  • Every 5 min     → overdue payment check")
    log.info("  • Every 2 min     → cancellation notifications")


# ═══════════════════════════════════════════════════════════════════════════════
# Entry point
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    log.info("═" * 50)
    log.info("OpenClaw starting up")
    log.info(f"API target: {API_URL}")
    log.info(f"AI (OpenRouter): {'enabled' if OR_KEY else 'disabled (no key)'}")
    log.info("═" * 50)

    # Sanity-check connectivity
    try:
        r = requests.get(API_URL.replace("/api/v1", "/health"), timeout=5)
        if r.status_code == 200:
            log.info("Backend reachable ✓")
        else:
            log.warning(f"Backend health check returned {r.status_code}")
    except Exception as e:
        log.warning(f"Backend not reachable yet ({e}) — will retry on each job run")

    setup_schedule()

    # Run overdue check immediately on startup
    job_check_overdue_payments()

    log.info("Running scheduler loop… (Ctrl+C to stop)")
    while True:
        schedule.run_pending()
        time.sleep(30)  # check every 30 seconds

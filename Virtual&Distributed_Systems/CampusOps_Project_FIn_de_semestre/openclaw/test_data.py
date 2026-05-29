"""
openclaw/test_data.py

Creates realistic test data to verify all OpenClaw workflows.
Safe to run multiple times — all steps are idempotent.

Usage:
  cd openclaw
  python3 test_data.py
"""

import os
import sys
import requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

BASE     = os.getenv("CAMPUSOPS_API_URL", "http://localhost:8000/api/v1")
CLAW_KEY = os.getenv("OPENCLAW_KEY", "")
CLAW     = {"X-OpenClaw-Key": CLAW_KEY}

ADMIN_EMAIL    = "admin@campusops.com"
ADMIN_PASSWORD = "Admin1234"

session = requests.Session()


def log(msg): print(f"  {msg}")
def ok(msg):  print(f"  ✓ {msg}")
def err(msg): print(f"  ✗ {msg}"); sys.exit(1)


# ── Step 0: login as admin ────────────────────────────────────────────────────
print("\n[0] Logging in as admin...")
r = session.post(f"{BASE}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
if r.status_code != 200:
    err(f"Login failed: {r.text}")
token = r.json()["access_token"]
AUTH  = {"Authorization": f"Bearer {token}"}
ok("Logged in")


def api_get(path):
    return session.get(f"{BASE}{path}", headers=AUTH)

def api_post(path, body):
    return session.post(f"{BASE}{path}", json=body, headers=AUTH)

def claw_post(path, body=None):
    return session.post(f"{BASE}{path}", json=body or {}, headers={**AUTH, **CLAW})


# ── Step 1: group ─────────────────────────────────────────────────────────────
print("\n[1] Setting up group...")
groups = api_get("/groups/").json()
group  = next((g for g in groups if g["name"] == "Test Group A"), None)
if not group:
    r = api_post("/groups/", {"name": "Test Group A", "description": "OpenClaw test group"})
    if r.status_code != 201: err(f"Create group failed: {r.text}")
    group = r.json()
    ok(f"Created group: {group['name']}")
else:
    ok(f"Using existing group: {group['name']}")
GROUP_ID = group["id"]


# ── Step 2: course ────────────────────────────────────────────────────────────
print("\n[2] Setting up course...")
courses = api_get("/courses/").json()
course  = next((c for c in courses if c["name"] == "Mathematics"), None)
if not course:
    r = api_post("/courses/", {"name": "Mathematics", "description": "Test course"})
    if r.status_code != 201: err(f"Create course failed: {r.text}")
    course = r.json()
    ok(f"Created course: {course['name']}")
else:
    ok(f"Using existing course: {course['name']}")
COURSE_ID = course["id"]


# ── Step 3: teacher ───────────────────────────────────────────────────────────
print("\n[3] Setting up teacher...")
teachers = api_get("/users/teachers").json()
teacher  = next((t for t in teachers if t["email"] == "teacher.test@campusops.com"), None)
if not teacher:
    r = api_post("/auth/register", {
        "email":     "teacher.test@campusops.com",
        "password":  "Teacher1234",
        "full_name": "Sarah Martin",
        "role":      "teacher",
    })
    if r.status_code != 201: err(f"Create teacher failed: {r.text}")
    teacher = r.json()
    ok(f"Created teacher: {teacher['full_name']}")
else:
    ok(f"Using existing teacher: {teacher['full_name']}")
TEACHER_ID = teacher["id"]

r_tlogin = session.post(f"{BASE}/auth/login",
                        json={"email": "teacher.test@campusops.com", "password": "Teacher1234"})
if r_tlogin.status_code == 200:
    teacher_token = r_tlogin.json()["access_token"]
    session.patch(f"{BASE}/profile/notification-email",
                  json={"notification_email": "essman0619@gmail.com"},
                  headers={"Authorization": f"Bearer {teacher_token}"})
    ok("Teacher notification email set")


# ── Step 4: student ───────────────────────────────────────────────────────────
print("\n[4] Setting up student...")
students = api_get("/users/students").json()
student  = next((s for s in students if s["email"] == "student.test@campusops.com"), None)
if not student:
    r = api_post("/auth/register", {
        "email":     "student.test@campusops.com",
        "password":  "Student1234",
        "full_name": "Ali Hassan",
        "role":      "student",
    })
    if r.status_code != 201: err(f"Create student failed: {r.text}")
    student = r.json()
    ok(f"Created student: {student['full_name']}")
else:
    ok(f"Using existing student: {student['full_name']}")
STUDENT_ID = student["id"]

r_profile = api_get(f"/students/by-user/{STUDENT_ID}")
if r_profile.status_code == 404:
    r = api_post("/students/", {
        "user_id":       STUDENT_ID,
        "establishment": "Faculty of Sciences",
        "group_id":      GROUP_ID,
        "year":          1,
        "parent_email":  "ahmedbok26@gmail.com",
    })
    if r.status_code != 201: err(f"Create student profile failed: {r.text}")
    ok("Created student profile")
else:
    ok("Student profile already exists")

r_slogin = session.post(f"{BASE}/auth/login",
                        json={"email": "student.test@campusops.com", "password": "Student1234"})
if r_slogin.status_code == 200:
    student_token = r_slogin.json()["access_token"]
    session.patch(f"{BASE}/profile/notification-email",
                  json={"notification_email": "handsuemf@gmail.com"},
                  headers={"Authorization": f"Bearer {student_token}"})
    ok("Student notification email set")


# ── Step 5: overdue payment ───────────────────────────────────────────────────
print("\n[5] Creating overdue payment...")
existing_payments = api_get(f"/payments/?student_id={STUDENT_ID}").json()
has_test_payment  = isinstance(existing_payments, list) and any(
    isinstance(p, dict) and "Test overdue payment" in (p.get("notes") or "")
    for p in existing_payments
)
if has_test_payment:
    log("Test payment already exists — skipping")
else:
    overdue_date = (date.today() - timedelta(days=10)).isoformat()
    r = api_post("/payments/", {
        "student_id": STUDENT_ID,
        "amount":     500.0,
        "type":       "monthly",
        "month":      "2026-04",
        "due_date":   overdue_date,
        "notes":      "Test overdue payment — created by test_data.py",
    })
    if r.status_code == 201:
        ok(f"Created payment of 500 DH due {overdue_date} (10 days ago)")
    else:
        log(f"Payment creation returned {r.status_code}: {r.text}")


# ── Step 6: next-week sessions (use unique rooms per run by appending date) ───
print("\n[6] Creating next-week sessions for planning email test...")
today = date.today()
days_until_monday = (7 - today.weekday()) % 7 or 7
next_monday = today + timedelta(days=days_until_monday)

SLOTS = [
    (0, "09:00", "11:00"),   # Monday
    (2, "14:00", "16:00"),   # Wednesday
    (4, "10:00", "12:00"),   # Friday
]
sessions_created = 0
for i, (day_offset, start, end) in enumerate(SLOTS):
    session_date = (next_monday + timedelta(days=day_offset)).isoformat()
    # Use the date in the room name so re-runs don't conflict with previous weeks
    room = f"Room {100 + i + 1}-{session_date}"
    r = api_post("/sessions/", {
        "course_id":  COURSE_ID,
        "teacher_id": TEACHER_ID,
        "group_id":   GROUP_ID,
        "room":       room,
        "date":       session_date,
        "start_time": f"{start}:00",
        "end_time":   f"{end}:00",
    })
    if r.status_code == 201:
        sessions_created += 1
        ok(f"Session on {session_date} {start}–{end} in {room}")
    else:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text or f"HTTP {r.status_code}"
        log(f"Session on {session_date} skipped: {detail}")

ok(f"{sessions_created} next-week session(s) created")


# ── Step 7: cancelled session (always fresh — use a unique room + tomorrow) ───
print("\n[7] Creating a cancelled session...")
tomorrow = (today + timedelta(days=1)).isoformat()
# Use a timestamp-based room to avoid conflicts on repeated runs
import time as _time
unique_room = f"Room-CANCEL-{int(_time.time())}"
r = api_post("/sessions/", {
    "course_id":  COURSE_ID,
    "teacher_id": TEACHER_ID,
    "group_id":   GROUP_ID,
    "room":       unique_room,
    "date":       tomorrow,
    "start_time": "08:00:00",
    "end_time":   "10:00:00",
})
if r.status_code == 201:
    sess       = r.json()
    SESSION_ID = sess["id"]
    r2 = claw_post("/openclaw/cancel-session",
                   {"session_id": SESSION_ID, "reason": "Teacher unavailable — test cancellation"})
    if r2.status_code == 200:
        ok(f"Session {SESSION_ID[:8]}... created and cancelled")
    else:
        log(f"Cancel endpoint returned {r2.status_code}: {r2.text}")
else:
    try:
        detail = r.json().get("detail", r.text)
    except Exception:
        detail = r.text or f"HTTP {r.status_code}"
    log(f"Cancelled session skipped: {detail}")


# ── Step 8: trigger OpenClaw jobs ─────────────────────────────────────────────
print("\n[8] Triggering OpenClaw jobs manually to verify...")

print("\n  → Overdue payment check:")
r = claw_post("/openclaw/check-overdue-payments")
if r.status_code == 200:
    ok(f"  {r.json()['message']}")
else:
    log(f"  Failed ({r.status_code}): {r.text}")

print("\n  → Cancellation notifications:")
r = claw_post("/openclaw/process-cancellations")
if r.status_code == 200:
    ok(f"  {r.json()['message']}")
else:
    log(f"  Failed ({r.status_code}): {r.text}")

print("\n  → Weekly planning (sends email immediately for testing):")
r = claw_post("/openclaw/send-weekly-planning")
if r.status_code == 200:
    d = r.json()
    ok(f"  {d['message']} ({d.get('week_from')} → {d.get('week_to')})")
else:
    log(f"  Failed ({r.status_code}): {r.text}")


# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "═" * 55)
print("Test data setup complete. Check:")
print("  • Email inboxes for:")
print("      - Overdue payment notification  (student)")
print("      - Session cancellation email    (student)")
print("      - Weekly planning email         (teacher)")
print("  • API for:")
print("      - GET /api/v1/payments/              → status='overdue'")
print("      - GET /api/v1/notifications/mine     → notifications")
print("═" * 55)
print("\nCredentials:")
print("  Teacher : teacher.test@campusops.com / Teacher1234")
print("  Student : student.test@campusops.com / Student1234")
print()

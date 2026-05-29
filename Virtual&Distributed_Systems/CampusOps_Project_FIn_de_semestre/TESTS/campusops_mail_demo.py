#!/usr/bin/env python3
"""
CampusOps mail-flow demo runner.

Designed for the presentation week of June 8-14, 2026, but it works on any day.
It creates fresh demo data and triggers the live mail flows against the running API:

- Weekly planning email to the teacher's personal Gmail
- Overdue payment email to the student's personal Gmail
- Session cancellation email to the student's personal Gmail
- Password reset email to the student's personal Gmail
- Two absence emails to the student's personal Gmail
- Parent alert email to the student's parent email after the second same-day absence

Expected environment:
- CampusOps backend running locally
- /home/aymane/campusops/.env present with CAMPUSOPS_API_URL and OPENCLAW_KEY

Run:
    python3 /home/aymane/TESTS/campusops_mail_demo.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import requests


PROJECT_ROOT = Path("/home/aymane/campusops")
ENV_PATH = PROJECT_ROOT / ".env"

ADMIN_EMAIL = "admin@campusops.com"
ADMIN_PASSWORD = "Admin1234"
TEACHER_EMAIL = "teacher.test@campusops.com"
TEACHER_PASSWORD = "Teacher1234"
STUDENT_EMAIL = "student.test@campusops.com"
STUDENT_PASSWORD = "Student1234"

PRESENTATION_WEEK_START = date(2026, 6, 8)
PRESENTATION_WEEK_END = date(2026, 6, 14)

SLOT_CANDIDATES = [
    ("08:00:00", "09:00:00"),
    ("09:15:00", "10:15:00"),
    ("10:30:00", "11:30:00"),
    ("11:45:00", "12:45:00"),
    ("14:00:00", "15:00:00"),
    ("15:15:00", "16:15:00"),
    ("16:30:00", "17:30:00"),
    ("17:45:00", "18:45:00"),
    ("19:00:00", "20:00:00"),
    ("20:15:00", "21:15:00"),
]


class DemoError(RuntimeError):
    pass


def load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        raise DemoError(f"Missing env file: {path}")

    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def to_minutes(hhmmss: str) -> int:
    hours, minutes, _seconds = hhmmss.split(":")
    return int(hours) * 60 + int(minutes)


def overlaps(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    return to_minutes(a_start) < to_minutes(b_end) and to_minutes(a_end) > to_minutes(b_start)


class DemoRunner:
    def __init__(self) -> None:
        env = load_env_file(ENV_PATH)
        self.base = env.get("CAMPUSOPS_API_URL", "http://localhost:8000/api/v1")
        self.openclaw_key = env.get("OPENCLAW_KEY", "")
        if not self.openclaw_key:
            raise DemoError("OPENCLAW_KEY is missing from /home/aymane/campusops/.env")

        self.http = requests.Session()
        self.results: dict[str, object] = {
            "base": self.base,
            "run_date": str(date.today()),
            "flows": [],
        }

    def api_get(self, path: str, headers: dict[str, str] | None = None) -> requests.Response:
        return self.http.get(f"{self.base}{path}", headers=headers or {}, timeout=20)

    def api_post(
        self,
        path: str,
        body: dict | None = None,
        headers: dict[str, str] | None = None,
    ) -> requests.Response:
        return self.http.post(
            f"{self.base}{path}",
            json=body or {},
            headers=headers or {},
            timeout=20,
        )

    def require_ok(self, response: requests.Response, context: str) -> dict | list:
        if response.status_code >= 400:
            raise DemoError(f"{context} failed: HTTP {response.status_code} {response.text}")
        try:
            return response.json()
        except Exception as exc:
            raise DemoError(f"{context} did not return JSON: {exc}") from exc

    def login(self, email: str, password: str) -> tuple[str, dict]:
        body = self.require_ok(
            self.api_post("/auth/login", {"email": email, "password": password}),
            f"login for {email}",
        )
        return body["access_token"], body["user"]

    def choose_free_slots(
        self,
        target_date: date,
        teacher_id: str,
        group_id: str,
        count: int,
        auth_headers: dict[str, str],
    ) -> list[tuple[str, str]]:
        occupied: list[tuple[str, str]] = []

        for path in (
            f"/sessions/by-teacher/{teacher_id}?date_from={target_date}&date_to={target_date}",
            f"/sessions/by-group/{group_id}?date_from={target_date}&date_to={target_date}",
        ):
            sessions = self.require_ok(self.api_get(path, auth_headers), f"load sessions for {target_date}")
            for session in sessions:
                occupied.append((session["start_time"], session["end_time"]))

        free: list[tuple[str, str]] = []
        for start_time, end_time in SLOT_CANDIDATES:
            if any(overlaps(start_time, end_time, occ_start, occ_end) for occ_start, occ_end in occupied):
                continue
            free.append((start_time, end_time))
            occupied.append((start_time, end_time))
            if len(free) == count:
                return free

        raise DemoError(f"Could not find {count} free slot(s) on {target_date}")

    def create_session(
        self,
        label: str,
        target_date: date,
        start_time: str,
        end_time: str,
        course_id: str,
        teacher_id: str,
        group_id: str,
        auth_headers: dict[str, str],
    ) -> dict:
        payload = {
            "course_id": course_id,
            "teacher_id": teacher_id,
            "group_id": group_id,
            "room": f"{label}-{int(time.time() * 1000)}",
            "date": str(target_date),
            "start_time": start_time,
            "end_time": end_time,
        }
        return self.require_ok(self.api_post("/sessions/", payload, auth_headers), f"create session {label}")

    def run(self) -> None:
        today = date.today()
        in_target_week = PRESENTATION_WEEK_START <= today <= PRESENTATION_WEEK_END
        self.results["presentation_week"] = {
            "expected_window": f"{PRESENTATION_WEEK_START} -> {PRESENTATION_WEEK_END}",
            "run_is_inside_window": in_target_week,
        }

        admin_token, _admin_user = self.login(ADMIN_EMAIL, ADMIN_PASSWORD)
        teacher_token, teacher_user = self.login(TEACHER_EMAIL, TEACHER_PASSWORD)
        student_token, student_user = self.login(STUDENT_EMAIL, STUDENT_PASSWORD)

        auth_headers = {"Authorization": f"Bearer {admin_token}"}
        teacher_headers = {"Authorization": f"Bearer {teacher_token}"}
        student_headers = {"Authorization": f"Bearer {student_token}"}
        claw_headers = {"X-OpenClaw-Key": self.openclaw_key}

        teacher_email = teacher_user.get("notification_email")
        student_email = student_user.get("notification_email")
        if not teacher_email or "@gmail.com" not in teacher_email:
            raise DemoError("teacher.test account must have a personal Gmail notification email")
        if not student_email or "@gmail.com" not in student_email:
            raise DemoError("student.test account must have a personal Gmail notification email")

        teachers = self.require_ok(self.api_get("/users/teachers", auth_headers), "load teachers")
        teacher = next((item for item in teachers if item["email"] == TEACHER_EMAIL), None)
        if teacher is None:
            raise DemoError("Teacher test account was not found")

        students = self.require_ok(self.api_get("/users/students", auth_headers), "load students")
        student = next((item for item in students if item["email"] == STUDENT_EMAIL), None)
        if student is None:
            raise DemoError("Student test account was not found")

        profile = self.require_ok(
            self.api_get(f"/students/by-user/{student['id']}", auth_headers),
            "load student profile",
        )
        parent_email = profile.get("parent_email")
        group_id = profile.get("group_id")
        if not parent_email:
            raise DemoError("student.test must have a parent_email configured")
        if not group_id:
            raise DemoError("student.test must have a group assigned")

        courses = self.require_ok(self.api_get("/courses/", auth_headers), "load courses")
        course = next((item for item in courses if item["name"] == "Mathematics"), None) or (courses[0] if courses else None)
        if course is None:
            raise DemoError("No course exists in the system")

        self.results["recipients"] = {
            "teacher_weekly_planning": teacher_email,
            "student_notifications": student_email,
            "student_parent_alert": parent_email,
        }
        self.results["entities"] = {
            "teacher_id": teacher["id"],
            "student_id": student["id"],
            "group_id": group_id,
            "course_id": course["id"],
            "course_name": course["name"],
        }

        # Weekly planning email: create one next-week approved session and trigger the OpenClaw job.
        next_monday = today + timedelta(days=((7 - today.weekday()) % 7 or 7))
        weekly_slot = self.choose_free_slots(next_monday, teacher["id"], group_id, 1, auth_headers)[0]
        weekly_session = self.create_session(
            "DEMO-WEEKLY",
            next_monday,
            weekly_slot[0],
            weekly_slot[1],
            course["id"],
            teacher["id"],
            group_id,
            auth_headers,
        )
        weekly_result = self.require_ok(
            self.api_post("/openclaw/send-weekly-planning", headers=claw_headers),
            "trigger weekly planning",
        )
        self.results["flows"].append(
            {
                "flow": "weekly_planning",
                "session_id": weekly_session["id"],
                "session_date": str(next_monday),
                "teacher_email": teacher_email,
                "result": weekly_result,
            }
        )

        # Today's flows: two absences, one cancellation, one overdue payment, one password reset.
        today_slots = self.choose_free_slots(today, teacher["id"], group_id, 3, auth_headers)
        absence_session_a = self.create_session(
            "DEMO-ABSENCE-A",
            today,
            today_slots[0][0],
            today_slots[0][1],
            course["id"],
            teacher["id"],
            group_id,
            auth_headers,
        )
        absence_session_b = self.create_session(
            "DEMO-ABSENCE-B",
            today,
            today_slots[1][0],
            today_slots[1][1],
            course["id"],
            teacher["id"],
            group_id,
            auth_headers,
        )
        cancel_session = self.create_session(
            "DEMO-CANCEL",
            today,
            today_slots[2][0],
            today_slots[2][1],
            course["id"],
            teacher["id"],
            group_id,
            auth_headers,
        )

        absence_a = self.require_ok(
            self.api_post(
                "/absences/",
                {"session_id": absence_session_a["id"], "student_id": student["id"], "justification": None},
                teacher_headers,
            ),
            "mark first absence",
        )
        absence_b = self.require_ok(
            self.api_post(
                "/absences/",
                {"session_id": absence_session_b["id"], "student_id": student["id"], "justification": None},
                teacher_headers,
            ),
            "mark second absence",
        )
        self.results["flows"].append(
            {
                "flow": "student_absence_and_parent_alert",
                "student_email": student_email,
                "parent_email": parent_email,
                "absence_ids": [absence_a["id"], absence_b["id"]],
                "session_ids": [absence_session_a["id"], absence_session_b["id"]],
            }
        )

        cancel_result = self.require_ok(
            self.api_post(
                "/openclaw/cancel-session",
                {
                    "session_id": cancel_session["id"],
                    "reason": "Presentation demo cancellation",
                },
                claw_headers,
            ),
            "cancel session through OpenClaw",
        )
        self.results["flows"].append(
            {
                "flow": "session_cancellation",
                "student_email": student_email,
                "session_id": cancel_session["id"],
                "result": cancel_result,
            }
        )

        payment = self.require_ok(
            self.api_post(
                "/payments/",
                {
                    "student_id": student["id"],
                    "amount": 350.0,
                    "type": "monthly",
                    "month": today.strftime("%Y-%m"),
                    "due_date": str(today - timedelta(days=7)),
                    "notes": f"Demo overdue payment {int(time.time())}",
                },
                auth_headers,
            ),
            "create overdue payment",
        )
        overdue_result = self.require_ok(
            self.api_post("/openclaw/check-overdue-payments", headers=claw_headers),
            "trigger overdue payment check",
        )
        self.results["flows"].append(
            {
                "flow": "overdue_payment",
                "student_email": student_email,
                "payment_id": payment["id"],
                "result": overdue_result,
            }
        )

        reset_result = self.require_ok(
            self.api_post("/auth/forgot-password", {"email": STUDENT_EMAIL}),
            "trigger password reset",
        )
        self.results["flows"].append(
            {
                "flow": "password_reset",
                "student_email": student_email,
                "result": reset_result,
            }
        )

        student_today = self.require_ok(self.api_get("/sessions/today", student_headers), "load student today sessions")
        student_payments = self.require_ok(self.api_get("/payments/mine", student_headers), "load student payments")
        student_notifications = self.require_ok(
            self.api_get("/notifications/mine", student_headers),
            "load student notifications",
        )
        absence_stats = self.require_ok(
            self.api_get(
                f"/absences/stats?student_id={student['id']}&date_from={today}&date_to={today}",
                auth_headers,
            ),
            "load absence stats",
        )

        self.results["verification"] = {
            "student_today_session_ids": [item["id"] for item in student_today],
            "cancelled_session_absent_from_today": all(item["id"] != cancel_session["id"] for item in student_today),
            "created_payment_status": next(
                (item["status"] for item in student_payments if item["id"] == payment["id"]),
                "missing",
            ),
            "today_absence_total_for_student": absence_stats["total"],
            "today_unjustified_absences_for_student": absence_stats["unjustified"],
            "recent_student_notification_types": [item["type"] for item in student_notifications[:10]],
        }

    def print_summary(self) -> None:
        print("\nCampusOps mail demo completed.\n")
        print(f"API base: {self.results['base']}")
        window = self.results["presentation_week"]
        print(
            f"Presentation week target: {window['expected_window']} "
            f"(inside window: {window['run_is_inside_window']})"
        )
        print("\nRecipients:")
        print(f"  Teacher weekly planning: {self.results['recipients']['teacher_weekly_planning']}")
        print(f"  Student personal email : {self.results['recipients']['student_notifications']}")
        print(f"  Parent alert email     : {self.results['recipients']['student_parent_alert']}")

        print("\nTriggered flows:")
        for item in self.results["flows"]:
            print(f"  - {item['flow']}")

        print("\nVerification:")
        verification = self.results["verification"]
        print(f"  Cancelled session absent from student today view: {verification['cancelled_session_absent_from_today']}")
        print(f"  Created payment status: {verification['created_payment_status']}")
        print(f"  Today's absence total for student: {verification['today_absence_total_for_student']}")
        print(f"  Recent student notification types: {verification['recent_student_notification_types']}")

        print("\nFull JSON summary:")
        print(json.dumps(self.results, indent=2))


def main() -> int:
    try:
        runner = DemoRunner()
        runner.run()
        runner.print_summary()
        return 0
    except DemoError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except requests.RequestException as exc:
        print(f"HTTP ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

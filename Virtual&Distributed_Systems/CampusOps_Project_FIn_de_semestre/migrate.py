#!/usr/bin/env python3
"""
seed_eidia.py — One-shot realistic seed data for EIDIA faculty.

Run from the project root:
    python seed_eidia.py

What it creates:
  - 2 secretaries
  - 6 teachers (each teaches 2–3 courses across multiple groups)
  - 4 groups: CS1-A, CS1-B (Year 1) and CS2-A, CS2-B (Year 2)
  - 12 courses split across Year1 / Year2
  - 5 students per group (20 students total) with Moroccan names
  - Student profiles linked to groups
  - 2 sessions per course per group spread across next week (Mon–Fri)
  - Progress log entries for each teacher's courses

Safe to run multiple times — skips objects that already exist.
Notification emails are left blank intentionally.
"""

import os, sys, time, random, requests
from datetime import date, timedelta
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

BASE     = os.getenv("CAMPUSOPS_API_URL", "http://localhost:8000/api/v1")
ADMIN_EMAIL    = "admin@campusops.com"
ADMIN_PASSWORD = "Admin1234"

s = requests.Session()

# ── helpers ───────────────────────────────────────────────────
def ok(msg):  print(f"  ✓  {msg}")
def skip(msg): print(f"  –  {msg} (already exists)")
def err(msg): print(f"  ✗  {msg}"); sys.exit(1)

def login(email, password):
    r = s.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        err(f"Login failed for {email}: {r.text}")
    return r.json()["access_token"]


def bootstrap_admin():
    payload = {
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD,
        "full_name": "CampusOps Admin",
        "role": "admin",
    }
    r = s.post(f"{BASE}/auth/register", json=payload)
    if r.status_code == 201:
        ok(f"Created bootstrap admin: {ADMIN_EMAIL}")
        return
    if r.status_code == 400 and "already" in r.text.lower():
        skip(f"Bootstrap admin: {ADMIN_EMAIL}")
        return
    err(f"Bootstrap admin failed: {r.text}")


def ensure_admin_login():
    r = s.post(f"{BASE}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
    if r.status_code == 200:
        ok("Logged in as admin")
        return r.json()["access_token"]

    if r.status_code in {401, 404}:
        print("  –  Admin not found yet, creating bootstrap account...")
        bootstrap_admin()
        r = s.post(f"{BASE}/auth/login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD})
        if r.status_code == 200:
            ok("Logged in as admin")
            return r.json()["access_token"]

    err(f"Login failed for {ADMIN_EMAIL}: {r.text}")

def hdr(token): return {"Authorization": f"Bearer {token}"}

def get(token, path):
    return s.get(f"{BASE}{path}", headers=hdr(token))

def post(token, path, body):
    return s.post(f"{BASE}{path}", json=body, headers=hdr(token))

def register(token, email, password, full_name, role):
    """Register user; return existing user if email already taken."""
    r = post(token, "/auth/register", {
        "email": email, "password": password,
        "full_name": full_name, "role": role,
    })
    if r.status_code == 201:
        ok(f"Created {role}: {full_name}")
        return r.json()
    elif r.status_code == 400 and "already" in r.text.lower():
        # fetch by listing
        if role == "teacher":
            users = get(token, "/users/teachers").json()
        elif role == "student":
            users = get(token, "/users/students").json()
        else:
            users = get(token, "/users/").json()
        user = next((u for u in users if u["email"] == email), None)
        if user:
            skip(f"{role}: {full_name}")
            return user
        err(f"Register failed for {full_name}: {r.text}")
    else:
        err(f"Register failed for {full_name}: {r.text}")

def ensure_group(token, name, description=""):
    groups = get(token, "/groups/").json()
    g = next((x for x in groups if x["name"] == name), None)
    if g:
        skip(f"Group: {name}")
        return g
    r = post(token, "/groups/", {"name": name, "description": description})
    if r.status_code == 201:
        ok(f"Group: {name}")
        return r.json()
    err(f"Could not create group {name}: {r.text}")

def ensure_course(token, name, description=""):
    courses = get(token, "/courses/").json()
    c = next((x for x in courses if x["name"] == name), None)
    if c:
        skip(f"Course: {name}")
        return c
    r = post(token, "/courses/", {"name": name, "description": description})
    if r.status_code == 201:
        ok(f"Course: {name}")
        return r.json()
    err(f"Could not create course {name}: {r.text}")

def ensure_student_profile(token, user_id, group_id, year):
    r = get(token, f"/students/by-user/{user_id}")
    if r.status_code == 200:
        skip(f"Student profile for {user_id[:8]}")
        return r.json()
    body = {
        "user_id": user_id,
        "establishment": "EIDIA",
        "group_id": group_id,
        "year": year,
    }
    r2 = post(token, "/students/", body)
    if r2.status_code == 201:
        ok(f"Student profile: {user_id[:8]}…")
        return r2.json()
    err(f"Could not create student profile: {r2.text}")

def create_session(token, course_id, teacher_id, group_id, room, day_date, start, end):
    body = {
        "course_id": course_id,
        "teacher_id": teacher_id,
        "group_id": group_id,
        "room": room,
        "date": day_date,
        "start_time": f"{start}:00",
        "end_time": f"{end}:00",
    }
    r = post(token, "/sessions/", body)
    if r.status_code == 201:
        return r.json()
    # Conflict is expected when slot is taken — caller handles retry
    return None

def log_progress(token, course_id, group_id, chapter, entry_type, completion, notes=""):
    body = {
        "course_id": course_id,
        "group_id": group_id,
        "chapter": chapter,
        "entry_type": entry_type,
        "completion": completion,
        "notes": notes,
    }
    r = post(token, "/progress/", body)
    if r.status_code == 201:
        ok(f"Progress: {chapter[:40]} ({completion}%)")
    else:
        print(f"  ⚠  Progress log skipped: {r.status_code} {r.text[:80]}")


# ══════════════════════════════════════════════════════════════
# Data definitions
# ══════════════════════════════════════════════════════════════

SECRETARIES = [
    ("fatima.benali@eidia.ma",   "Secr1234", "Fatima Benali"),
    ("khadija.elhassani@eidia.ma", "Secr1234", "Khadija El Hassani"),
]

# 6 teachers — each assigned to specific courses
TEACHERS = [
    ("youssef.alaoui@eidia.ma",    "Teach1234", "Youssef Alaoui"),       # T0
    ("rachid.benchekroun@eidia.ma","Teach1234", "Rachid Benchekroun"),   # T1
    ("meriem.tazi@eidia.ma",       "Teach1234", "Meriem Tazi"),          # T2
    ("hamid.ouahabi@eidia.ma",     "Teach1234", "Hamid Ouahabi"),        # T3
    ("nadia.chraibi@eidia.ma",     "Teach1234", "Nadia Chraibi"),        # T4
    ("omar.berrada@eidia.ma",      "Teach1234", "Omar Berrada"),         # T5
]

YEAR1_COURSES = [
    ("Secure Web Programming",                    "SWP"),
    ("Advanced Networking",                        "AN"),
    ("Administration and Securing Operating Systems", "ASOS"),
    ("Cloud Computing",                            "CC"),
    ("Distributed Applications",                   "DA"),
    ("Introduction to Cybersecurity",              "ICS"),
]

YEAR2_COURSES = [
    ("Cryptology",                                 "CRYPT"),
    ("Security of Smartphone Operating Systems",   "SSOS"),
    ("Network Security",                           "NS"),
    ("DevSecOps",                                  "DSO"),
    ("Digital Forensics and Incident Management",  "DFIM"),
    ("NoSQL Database Security",                    "NDS"),
]

# Teacher index → list of course short codes they teach
# Each teacher teaches 2 courses; some teach in both Year1 & Year2
TEACHER_COURSE_MAP = {
    0: ["SWP",  "DA"],     # Youssef Alaoui
    1: ["AN",   "NS"],     # Rachid Benchekroun
    2: ["ASOS", "SSOS"],   # Meriem Tazi
    3: ["CC",   "DSO"],    # Hamid Ouahabi
    4: ["ICS",  "CRYPT"],  # Nadia Chraibi
    5: ["DFIM", "NDS"],    # Omar Berrada
}

# 5 students per group (20 total)
STUDENTS = {
    "CS1-A": [
        ("amine.belhaj@eidia.ma",     "Stud1234", "Amine Belhaj"),
        ("zineb.moussaoui@eidia.ma",  "Stud1234", "Zineb Moussaoui"),
        ("karim.ouazzani@eidia.ma",   "Stud1234", "Karim Ouazzani"),
        ("houda.benkirane@eidia.ma",  "Stud1234", "Houda Benkirane"),
        ("yassine.filali@eidia.ma",   "Stud1234", "Yassine Filali"),
    ],
    "CS1-B": [
        ("salma.idrissi@eidia.ma",    "Stud1234", "Salma Idrissi"),
        ("mehdi.lahlou@eidia.ma",     "Stud1234", "Mehdi Lahlou"),
        ("nour.hajjaj@eidia.ma",      "Stud1234", "Nour Hajjaj"),
        ("ilyas.benmoussa@eidia.ma",  "Stud1234", "Ilyas Benmoussa"),
        ("rania.berrada@eidia.ma",    "Stud1234", "Rania Berrada"),
    ],
    "CS2-A": [
        ("soufiane.amrani@eidia.ma",  "Stud1234", "Soufiane Amrani"),
        ("hasnae.bouhali@eidia.ma",   "Stud1234", "Hasnae Bouhali"),
        ("tariq.naciri@eidia.ma",     "Stud1234", "Tariq Naciri"),
        ("imane.chafik@eidia.ma",     "Stud1234", "Imane Chafik"),
        ("adil.sebbahi@eidia.ma",     "Stud1234", "Adil Sebbahi"),
    ],
    "CS2-B": [
        ("chaymae.ziani@eidia.ma",    "Stud1234", "Chaymae Ziani"),
        ("reda.bensouda@eidia.ma",    "Stud1234", "Reda Bensouda"),
        ("loubna.elhilali@eidia.ma",  "Stud1234", "Loubna El Hilali"),
        ("othmane.tounsi@eidia.ma",   "Stud1234", "Othmane Tounsi"),
        ("samira.kabbaj@eidia.ma",    "Stud1234", "Samira Kabbaj"),
    ],
}

# Time slots — 4 per day so we can pack 2 sessions per course per group
SLOTS = [
    ("08:30", "10:30"),
    ("10:45", "12:45"),
    ("14:00", "16:00"),
    ("16:15", "18:15"),
]

ROOMS_Y1 = ["Salle A1", "Salle A2", "Salle A3", "Labo Info 1"]
ROOMS_Y2 = ["Salle B1", "Salle B2", "Salle B3", "Labo Réseau"]


# ══════════════════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════════════════

def main():
    print("\n" + "═" * 60)
    print("  EIDIA seed data — CampusOps")
    print("═" * 60)

    # ── login as admin ────────────────────────────────────────
    print("\n[0] Admin login...")
    admin_token = ensure_admin_login()

    # ── secretaries ──────────────────────────────────────────
    print("\n[1] Creating secretaries...")
    for email, pw, name in SECRETARIES:
        register(admin_token, email, pw, name, "secretary")

    # ── teachers ─────────────────────────────────────────────
    print("\n[2] Creating teachers...")
    teacher_objs = []
    for email, pw, name in TEACHERS:
        t = register(admin_token, email, pw, name, "teacher")
        teacher_objs.append(t)

    # ── groups ───────────────────────────────────────────────
    print("\n[3] Creating groups...")
    g_cs1a = ensure_group(admin_token, "CS1-A", "Year 1 — Group A — EIDIA")
    g_cs1b = ensure_group(admin_token, "CS1-B", "Year 1 — Group B — EIDIA")
    g_cs2a = ensure_group(admin_token, "CS2-A", "Year 2 — Group A — EIDIA")
    g_cs2b = ensure_group(admin_token, "CS2-B", "Year 2 — Group B — EIDIA")

    groups_y1 = [g_cs1a, g_cs1b]
    groups_y2 = [g_cs2a, g_cs2b]

    # ── courses ──────────────────────────────────────────────
    print("\n[4] Creating courses...")
    course_map = {}   # short_code → course object
    for name, code in YEAR1_COURSES + YEAR2_COURSES:
        c = ensure_course(admin_token, name, f"EIDIA — {code}")
        course_map[code] = c

    # Build reverse map: short_code → teacher index
    code_to_teacher: dict[str, int] = {}
    for t_idx, codes in TEACHER_COURSE_MAP.items():
        for code in codes:
            code_to_teacher[code] = t_idx

    # ── students ─────────────────────────────────────────────
    print("\n[5] Creating students and profiles...")
    group_obj_map = {
        "CS1-A": g_cs1a, "CS1-B": g_cs1b,
        "CS2-A": g_cs2a, "CS2-B": g_cs2b,
    }
    year_map = {"CS1-A": 1, "CS1-B": 1, "CS2-A": 2, "CS2-B": 2}

    for group_name, student_list in STUDENTS.items():
        gobj = group_obj_map[group_name]
        year = year_map[group_name]
        for email, pw, name in student_list:
            u = register(admin_token, email, pw, name, "student")
            ensure_student_profile(admin_token, u["id"], gobj["id"], year)

    # ── sessions ─────────────────────────────────────────────
    print("\n[6] Creating sessions (2 per course per group, spread across next week)...")

    today = date.today()
    days_until_monday = (7 - today.weekday()) % 7 or 7
    next_monday = today + timedelta(days=days_until_monday)
    # weekdays Mon=0 … Fri=4
    weekdays = [next_monday + timedelta(days=i) for i in range(5)]

    def schedule_sessions(courses_with_codes, groups, rooms, year_label):
        """
        For each course × group, pick 2 distinct (day, slot, room) combos.
        Uses a per-group slot tracker to avoid double-booking.
        """
        # slot_used[(group_id, day_idx, slot_idx)] = True
        slot_used: dict[tuple, bool] = {}
        # teacher_used[(teacher_id, day_idx, slot_idx)] = True
        teacher_used: dict[tuple, bool] = {}

        for course_name, code in courses_with_codes:
            course = course_map[code]
            t_idx  = code_to_teacher[code]
            teacher = teacher_objs[t_idx]
            t_id    = teacher["id"]

            sessions_made = 0
            for group in groups:
                g_id = group["id"]
                count = 0
                attempts = 0
                while count < 2 and attempts < 40:
                    attempts += 1
                    day_idx  = random.randint(0, 4)
                    slot_idx = random.randint(0, 3)
                    room     = random.choice(rooms)
                    day_date = str(weekdays[day_idx])
                    start, end = SLOTS[slot_idx]

                    gk = (g_id, day_idx, slot_idx)
                    tk = (t_id, day_idx, slot_idx)
                    if slot_used.get(gk) or teacher_used.get(tk):
                        continue

                    sess = create_session(
                        admin_token, course["id"], t_id,
                        g_id, room, day_date, start, end
                    )
                    if sess:
                        slot_used[gk]   = True
                        teacher_used[tk] = True
                        count += 1
                        sessions_made += 1
                        ok(f"Session: {code} | {group['name']} | {day_date} {start}–{end} | {room}")
                    # else: conflict, retry

                if count < 2:
                    print(f"  ⚠  Only {count}/2 sessions created for {code}/{group['name']}")

    schedule_sessions(YEAR1_COURSES, groups_y1, ROOMS_Y1, "Year1")
    schedule_sessions(YEAR2_COURSES, groups_y2, ROOMS_Y2, "Year2")

    # ── progress logs ─────────────────────────────────────────
    print("\n[7] Logging progress entries...")

    # Each teacher logs progress for their courses in each relevant group
    PROGRESS_TEMPLATES = {
        "SWP":   [("Chapter 1: HTTP & REST security",   "chapter",    100, "Covered HTTPS, CORS, CSP headers"),
                  ("Chapter 2: Authentication patterns", "chapter",    80,  "JWT, OAuth2 — exam next week"),
                  ("TP1: Securing a Node.js API",        "tp",         90,  "Students completed input validation lab")],
        "DA":    [("Chapter 1: RPC & Message Queues",   "chapter",    100, "RabbitMQ intro"),
                  ("Chapter 2: Microservices patterns",  "chapter",    60,  "In progress — Docker Compose lab")],
        "AN":    [("Chapter 1: OSI & TCP/IP deep dive",  "chapter",    100, ""),
                  ("TP1: Wireshark packet analysis",     "tp",         100, "All students submitted"),
                  ("Chapter 2: VLAN & Routing",          "chapter",    75,  "Lab on Cisco Packet Tracer")],
        "NS":    [("Chapter 1: Firewalls & IDS/IPS",    "chapter",    80,  ""),
                  ("Chapter 2: VPN technologies",        "chapter",    50,  "IPSec lab pending")],
        "ASOS":  [("Chapter 1: Linux hardening",         "chapter",    100, "Covered file permissions, SELinux"),
                  ("TP1: Windows Server security audit", "tp",         85,  ""),
                  ("Chapter 2: Patch management",        "chapter",    40,  "Ongoing")],
        "SSOS":  [("Chapter 1: Android security model", "chapter",    90,  ""),
                  ("Chapter 2: iOS sandboxing",          "chapter",    60,  "In progress")],
        "CC":    [("Chapter 1: Cloud fundamentals",      "chapter",    100, "AWS & Azure overview"),
                  ("Chapter 2: IAM & Cloud security",    "chapter",    70,  ""),
                  ("TP1: Terraform basics",              "tp",         55,  "Students setting up accounts")],
        "DSO":   [("Chapter 1: DevOps pipelines",        "chapter",    100, "CI/CD with GitLab"),
                  ("Chapter 2: SAST & DAST",             "chapter",    65,  "SonarQube lab upcoming")],
        "ICS":   [("Chapter 1: Threats landscape 2024",  "chapter",    100, ""),
                  ("Chapter 2: Risk assessment basics",  "chapter",    80,  "Case study: WannaCry"),
                  ("Competency: Threat modelling",       "competency", 70,  "STRIDE framework")],
        "CRYPT": [("Chapter 1: Symmetric encryption",   "chapter",    100, "AES, 3DES"),
                  ("Chapter 2: Asymmetric & PKI",        "chapter",    85,  "RSA lab"),
                  ("TP1: OpenSSL hands-on",              "tp",         75,  "")],
        "DFIM":  [("Chapter 1: Incident response lifecycle","chapter", 100, ""),
                  ("Chapter 2: Digital evidence collection","chapter", 70,  "Autopsy tool intro"),
                  ("TP1: Memory forensics — Volatility", "tp",         50,  "In progress")],
        "NDS":   [("Chapter 1: MongoDB security",        "chapter",    100, "Authentication & authorisation"),
                  ("Chapter 2: Redis & Cassandra sec.",  "chapter",    60,  "Injection attacks demo")],
    }

    for code, entries in PROGRESS_TEMPLATES.items():
        t_idx   = code_to_teacher[code]
        teacher = teacher_objs[t_idx]

        # Get teacher token
        t_email, t_pw, _ = TEACHERS[t_idx]
        t_token = login(t_email, t_pw)

        # Determine which groups this course applies to
        if code in [c for c, _ in YEAR1_COURSES]:
            groups = groups_y1
        else:
            groups = groups_y2

        for group in groups:
            for chapter, etype, pct, notes in entries:
                log_progress(
                    t_token,
                    course_map[code]["id"],
                    group["id"],
                    chapter, etype, pct, notes
                )

    # ── summary ───────────────────────────────────────────────
    print("\n" + "═" * 60)
    print("  Seed complete!")
    print("═" * 60)
    print("""
Credentials summary:
  Admin      : admin@campusops.com         / Admin1234
  Secretary  : fatima.benali@eidia.ma      / Secr1234
               khadija.elhassani@eidia.ma  / Secr1234

  Teachers:
    Youssef Alaoui      youssef.alaoui@eidia.ma        Teach1234   SWP, DA
    Rachid Benchekroun  rachid.benchekroun@eidia.ma     Teach1234   AN, NS
    Meriem Tazi         meriem.tazi@eidia.ma             Teach1234   ASOS, SSOS
    Hamid Ouahabi       hamid.ouahabi@eidia.ma           Teach1234   CC, DevSecOps
    Nadia Chraibi       nadia.chraibi@eidia.ma           Teach1234   ICS, Cryptology
    Omar Berrada        omar.berrada@eidia.ma            Teach1234   DFIM, NDS

  Students (password: Stud1234):
    CS1-A: Amine Belhaj, Zineb Moussaoui, Karim Ouazzani, Houda Benkirane, Yassine Filali
    CS1-B: Salma Idrissi, Mehdi Lahlou, Nour Hajjaj, Ilyas Benmoussa, Rania Berrada
    CS2-A: Soufiane Amrani, Hasnae Bouhali, Tariq Naciri, Imane Chafik, Adil Sebbahi
    CS2-B: Chaymae Ziani, Reda Bensouda, Loubna El Hilali, Othmane Tounsi, Samira Kabbaj
""")


if __name__ == "__main__":
    main()

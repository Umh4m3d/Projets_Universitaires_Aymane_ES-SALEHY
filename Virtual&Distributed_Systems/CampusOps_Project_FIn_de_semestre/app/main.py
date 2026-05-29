# /main.py
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging_config import logger, setup_logging
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.sessions import router as sessions_router
from app.routes.groups import router as groups_router
from app.routes.courses import router as courses_router
from app.routes.absences import router as absences_router
from app.routes.notifications import router as notifications_router
from app.routes.payments import router as payments_router
from app.routes.profile import router as profile_router
from app.routes.students import router as students_router
from app.routes.mail import router as mail_router
from app.routes.progress import router as progress_router
from app.routes.openclaw import router as openclaw_router   # ← NEW

setup_logging()

app = FastAPI(
    title="CampusOps API",
    description="Academic management platform — secure, AI-ready",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENVIRONMENT == "development" else None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,          prefix="/api/v1")
app.include_router(users_router,         prefix="/api/v1")
app.include_router(sessions_router,      prefix="/api/v1")
app.include_router(groups_router,        prefix="/api/v1")
app.include_router(courses_router,       prefix="/api/v1")
app.include_router(absences_router,      prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(payments_router,      prefix="/api/v1")
app.include_router(profile_router,       prefix="/api/v1")
app.include_router(students_router,      prefix="/api/v1")
app.include_router(mail_router,          prefix="/api/v1")
app.include_router(progress_router,      prefix="/api/v1")
app.include_router(openclaw_router,      prefix="/api/v1")   # ← NEW


@app.get("/health", tags=["System"])
def health_check():
    logger.info("Health check called")
    return {"status": "ok", "version": "1.0.0"}

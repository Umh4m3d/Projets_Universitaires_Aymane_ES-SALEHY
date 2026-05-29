import httpx
import os
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
BOT_HEADERS = (
    {"X-Telegram-Bot-Token": os.getenv("TELEGRAM_BOT_TOKEN", "")}
    if os.getenv("TELEGRAM_BOT_TOKEN")
    else {}
)


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def get_user_by_chat_id(chat_id: str) -> dict | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{API_BASE_URL}/api/v1/users/by-chat-id/{chat_id}",
                headers=BOT_HEADERS,
            )
            if response.status_code == 200:
                return response.json()
            return None
        except httpx.RequestError:
            return None


async def bot_login(chat_id: str) -> str | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{API_BASE_URL}/api/v1/auth/bot-login",
                json={"chat_id": str(chat_id)},
                headers=BOT_HEADERS,
            )
            if response.status_code == 200:
                return response.json()["access_token"]
            return None
        except httpx.RequestError:
            return None


async def link_telegram(chat_id: str, otp: str) -> dict:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{API_BASE_URL}/api/v1/auth/telegram-link",
            json={"chat_id": chat_id, "otp": otp}
        )
        return {"status": response.status_code, "data": response.json()}


async def get_sessions_today(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/sessions/today",
            headers=_auth_headers(token)
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_sessions_week(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/sessions/week",
            headers=_auth_headers(token)
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_my_absences(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/absences/mine",
            headers=_auth_headers(token)
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_my_payments(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/payments/mine",
            headers=_auth_headers(token)
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_my_notifications(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/notifications/mine",
            headers=_auth_headers(token),
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_pending_notifications(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/notifications/pending",
            headers=_auth_headers(token),
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_pending_sessions(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/sessions/pending",
            headers=_auth_headers(token),
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_pending_profile_requests(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/profile/pending-requests",
            headers=_auth_headers(token),
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_overdue_payments(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/payments/?status=overdue",
            headers=_auth_headers(token),
        )
        if response.status_code == 200:
            return response.json()
        return []


async def get_progress_entries(token: str) -> list:
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{API_BASE_URL}/api/v1/progress/",
            headers=_auth_headers(token),
        )
        if response.status_code == 200:
            return response.json()
        return []

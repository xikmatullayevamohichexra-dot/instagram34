import os
import socket
import logging
from typing import Dict, List, Optional
import aiohttp

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Sen Telegram botidagi xushmuomala, aqlli va yordamsevar sun'iy intellekt (AI) yordamchisisan. "
    "Foydalanuvchilarning barcha savollariga (matematika, dasturlash, ilm-fan, tarjima, maslahat va boshqalar) "
    "aniq, tushunarli va to'g'ri javob berasan. "
    "Asosan o'zbek tilida javob ber, lekin foydalanuvchi boshqa tilda yozsa, o'sha tilda javob ber."
)

user_histories: Dict[int, List[Dict[str, str]]] = {}
MAX_HISTORY_LENGTH = 10  # Oxirgi 10 ta xabar


def clear_history(user_id: int):
    """Foydalanuvchining suhbat tarixini tozalash"""
    if user_id in user_histories:
        user_histories[user_id] = []


def get_user_history(user_id: int) -> List[Dict[str, str]]:
    """Foydalanuvchi tarixini olish"""
    if user_id not in user_histories:
        user_histories[user_id] = []
    return user_histories[user_id]


async def _ask_gemini(api_key: str, messages: List[Dict[str, str]]) -> Optional[str]:
    """Google Gemini API orqali javob olish"""
    contents = []
    for m in messages:
        if m["role"] == "system":
            continue
        role = "user" if m["role"] == "user" else "model"
        contents.append({
            "role": role,
            "parts": [{"text": m["content"]}]
        })

    payload = {
        "contents": contents,
        "systemInstruction": {
            "parts": [{"text": SYSTEM_PROMPT}]
        }
    }

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent?key={api_key}"
    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    timeout = aiohttp.ClientTimeout(total=7)  # 7 soniya tezkor timeout

    try:
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            async with session.post(url, json=payload) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    return text
                else:
                    logger.warning(f"Gemini API status kodi: {resp.status}")
    except Exception as e:
        logger.warning(f"Gemini chaqirishda muammo: {e}")

    return None


async def _ask_pollinations(messages: List[Dict[str, str]]) -> str:
    """Tezkor (0.9s) zaxira AI dvigateli"""
    url = "https://text.pollinations.ai/"
    payload = {
        "messages": messages,
        "model": "openai",
        "jsonMode": False
    }

    connector = aiohttp.TCPConnector(family=socket.AF_INET)
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                text = await resp.text()
                return text.strip()
            else:
                return "Kechirasiz, javob olishda muammo yuz berdi. Iltimos, qayta urinib ko'ring."


async def ask_ai(user_id: int, question: str) -> str:
    """
    Foydalanuvchi savolini AI ga jo'natish.
    Avval Google Gemini API, u sekinlashsa yoki ishlamasa, darhol zaxiradagi tezkor AI dvigateliga o'tadi.
    """
    history = get_user_history(user_id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": question})

    gemini_key = os.getenv("GEMINI_API_KEY")
    answer = None

    if gemini_key and gemini_key.strip():
        answer = await _ask_gemini(gemini_key.strip(), messages)

    # Agar Gemini bo'lmasa yoki kechiksa, darhol zaxiraga murojaat qilish
    if not answer:
        try:
            answer = await _ask_pollinations(messages)
        except Exception as e:
            logger.error(f"Zaxira AI xatoligi: {e}")
            answer = "⚠️ Hozirda AI xizmatida vaqtinchalik uzilish yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring."

    # Tarixni yangilash
    history.append({"role": "user", "content": question})
    history.append({"role": "assistant", "content": answer})

    if len(history) > MAX_HISTORY_LENGTH:
        user_histories[user_id] = history[-MAX_HISTORY_LENGTH:]

    return answer

import os
import sys
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
    print("XATOLIK: .env faylida BOT_TOKEN ko'rsatilmagan!")
    print("Iltimos, .env faylini oching va @BotFather bergan tokenni kiriting.")

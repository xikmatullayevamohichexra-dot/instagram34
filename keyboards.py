from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasi"""
    kb = [
        [
            KeyboardButton(text="🤖 AI Suhbat"),
            KeyboardButton(text="📥 Video Yuklash")
        ],
        [
            KeyboardButton(text="ℹ️ Yordam")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Quyidagi tugmalardan birini tanlang yoki havola yuboring..."
    )


def get_ai_keyboard() -> ReplyKeyboardMarkup:
    """AI suhbat bo'limi klaviaturasi"""
    kb = [
        [
            KeyboardButton(text="🔄 Yangi suhbat"),
            KeyboardButton(text="🔙 Bosh menyu")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Savolingizni yozing..."
    )

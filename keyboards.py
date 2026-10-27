from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """Asosiy menyu klaviaturasi"""
    kb = [
        [
            KeyboardButton(text="🤖 AI Suhbat"),
            KeyboardButton(text="📥 Video Yuklash")
        ],
        [
            KeyboardButton(text="📚 Kitob Yuklash"),
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


def get_book_keyboard() -> ReplyKeyboardMarkup:
    """Kitob qidirish bo'limi klaviaturasi"""
    kb = [
        [
            KeyboardButton(text="🔙 Bosh menyu")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        input_field_placeholder="Kitob nomi yoki muallifini kiriting..."
    )


def get_book_actions_keyboard(
    short_id: str,
    has_pdf: bool = True,
    has_epub: bool = False,
    web_url: str = None
) -> InlineKeyboardMarkup:
    """Kitobni yuklab olish yoki onlayn o'qish inline tugmalari"""
    buttons = []
    download_row = []

    if has_pdf:
        download_row.append(
            InlineKeyboardButton(text="📥 PDF", callback_data=f"dl_book:pdf:{short_id}")
        )
    if has_epub:
        download_row.append(
            InlineKeyboardButton(text="📥 EPUB", callback_data=f"dl_book:epub:{short_id}")
        )

    if download_row:
        buttons.append(download_row)

    if web_url:
        buttons.append([
            InlineKeyboardButton(text="📖 Onlayn o'qish", url=web_url)
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


import os
import re
import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext

from downloader import download_instagram_video
from ai_service import ask_ai, clear_history
from keyboards import get_main_keyboard, get_ai_keyboard
from states import BotStates

logger = logging.getLogger(__name__)
router = Router()

# Instagram havolalarini aniqlash uchun regex
INSTAGRAM_REGEX = re.compile(
    r'(https?://(?:www\.)?instagram\.com/(?:p|reel|reels|tv)/[A-Za-z0-9_\-]+[^\s]*)'
)


def chunk_text(text: str, max_size: int = 4000) -> list[str]:
    """Uzun matnlarni Telegram chekloviga ko'ra (4096 belgi) bo'laklarga ajratish"""
    chunks = []
    while len(text) > max_size:
        split_idx = text.rfind("\n", 0, max_size)
        if split_idx == -1:
            split_idx = text.rfind(" ", 0, max_size)
        if split_idx == -1:
            split_idx = max_size
        chunks.append(text[:split_idx])
        text = text[split_idx:].lstrip()
    if text:
        chunks.append(text)
    return chunks


# ==================== BUYRUQLAR (COMMANDS) ====================

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    user_name = message.from_user.first_name if message.from_user else "Foydalanuvchi"
    text = (
        f"Assalomu alaykum, <b>{user_name}</b>! 👋\n\n"
        "Men sizning ko'p funksiyali yordamchingizman:\n"
        "🎬 <b>Instagram Video Yuklash:</b> Reels yoki Post havolasini yuboring.\n"
        "🤖 <b>AI Suhbat:</b> Istalgan savolingizni bering, sun'iy intellekt javob beradi.\n\n"
        "<i>Quyidagi menyudan kerakli bo'limni tanlang yoki to'g'ridan-to'g'ri havola/savol yuboring:</i>"
    )
    await message.answer(text, reply_markup=get_main_keyboard(), parse_mode="HTML")


@router.message(Command("help"))
@router.message(F.text == "ℹ️ Yordam")
async def cmd_help(message: Message):
    text = (
        "<b>📖 Botdan foydalanish bo'yicha qo'llanma:</b>\n\n"
        "1️⃣ <b>Instagram videolarni yuklash:</b>\n"
        "• Instagram'da videoni 'Ulashish' (Share) -> 'Havoladan nusxa olish' (Copy link) qiling.\n"
        "• Botga havolani yuboring va video bir necha soniyada tayyor bo'ladi.\n\n"
        "2️⃣ <b>AI Suhbat (Sun'iy intellekt):</b>\n"
        "• <b>🤖 AI Suhbat</b> tugmasini bosing yoki to'g'ridan-to'g'ri savolingizni yozing.\n"
        "• AI sizning savollaringizga (matematika, dasturlash, tarjima, maslahatlar) javob beradi.\n"
        "• Suhbatni tozalash uchun <b>🔄 Yangi suhbat</b> tugmasidan foydalaning."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📥 Video Yuklash")
async def btn_video_download(message: Message):
    text = (
        "📥 <b>Instagram Video Yuklash:</b>\n\n"
        "Iltimos, yuklamoqchi bo'lgan <b>Reels</b>, <b>Post</b> yoki <b>Video</b> havolasini yuboring.\n\n"
        "<i>Misol: https://www.instagram.com/reel/C.../</i>"
    )
    await message.answer(text, parse_mode="HTML")


# ==================== AI SUHBAT BO'LIMI ====================

@router.message(F.text == "🤖 AI Suhbat")
async def enter_ai_chat(message: Message, state: FSMContext):
    await state.set_state(BotStates.ai_chat)
    text = (
        "🤖 <b>AI Suhbat bo'limiga xush kelibsiz!</b>\n\n"
        "Menga istalgan savolingizni berishingiz mumkin:\n"
        "• Maslahat va tavsiyalar\n"
        "• Dasturlash va matematika masalalari\n"
        "• Matnlarni tarjima qilish va tahrirlash\n"
        "• Qiziqarli mavzularda suhbat\n\n"
        "<i>Savolingizni yozib qoldiring:</i>"
    )
    await message.answer(text, reply_markup=get_ai_keyboard(), parse_mode="HTML")


@router.message(BotStates.ai_chat, F.text == "🔙 Bosh menyu")
async def exit_ai_chat(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Asosiy menyuga qaytdingiz.",
        reply_markup=get_main_keyboard()
    )


@router.message(BotStates.ai_chat, F.text == "🔄 Yangi suhbat")
async def reset_ai_chat(message: Message):
    clear_history(message.from_user.id)
    await message.answer(
        "✅ <b>Suhbat tarixi tozalandi!</b>\nEndi yangi mavzuda savol berishingiz mumkin.",
        reply_markup=get_ai_keyboard(),
        parse_mode="HTML"
    )


# ==================== INSTAGRAM VIDEOLARINI YUKLASH ====================

@router.message(F.text.regexp(INSTAGRAM_REGEX))
async def handle_instagram_link(message: Message):
    match = INSTAGRAM_REGEX.search(message.text)
    if not match:
        return

    url = match.group(1)
    status_msg = await message.answer("⏳ Video yuklab olinmoqda, iltimos kuting...")

    file_path = None
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO)
        result = await download_instagram_video(url)

        if not result or not result.get("file_path"):
            await status_msg.edit_text("❌ Videoni yuklab bo'lmadi. Havolani qayta tekshirib ko'ring.")
            return

        file_path = result["file_path"]
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

        if file_size_mb > 50:
            await status_msg.edit_text(
                f"⚠️ Video hajmi juda katta ({file_size_mb:.1f} MB).\n"
                "Telegram botlari orqali faqat 50 MB gacha bo'lgan videolarni jo'natish mumkin."
            )
            return

        video_file = FSInputFile(file_path)
        caption = "✅ <b>Video tayyor!</b>\n\n🤖 @InstaLMX99bot orqali yuklab olindi."

        await message.answer_video(
            video=video_file,
            caption=caption,
            parse_mode="HTML",
            supports_streaming=True
        )
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Xatolik: {e}")
        error_text = (
            "❌ <b>Videoni yuklab olishda xatolik yuz berdi.</b>\n\n"
            "Sabablari:\n"
            "• Profil yopiq (private) bo'lishi mumkin\n"
            "• Video o'chirilgan yoki havola noto'g'ri\n"
            "• Instagram cheklovi yoki internet uzilishi"
        )
        await status_msg.edit_text(error_text, parse_mode="HTML")

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError as err:
                logger.warning(f"Faylni o'chirishda xatolik: {err}")


# ==================== AI MATNLI SAVOLLARGA JAVOB BERISH ====================

@router.message(BotStates.ai_chat, F.text)
@router.message(F.text)
async def handle_ai_question(message: Message, state: FSMContext):
    # Agar foydalanuvchi tugmalarni bosmagan bo'lsa va bu Instagram havolasi bo'lmasa
    user_id = message.from_user.id
    user_question = message.text.strip()

    if not user_question:
        return

    # Foydalanuvchiga AI yozayotganini ko'rsatish
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    # AI dan javob olish
    answer = await ask_ai(user_id, user_question)

    # Agar javob juda uzun bo'lsa, qismlarga bo'lib jo'natish
    chunks = chunk_text(answer)
    for chunk in chunks:
        # Markdown yoki oddiy matn sifatida xavfsiz yuborish
        try:
            await message.answer(chunk, parse_mode="Markdown")
        except Exception:
            # Agar Markdown belgilarida format xatosi bo'lsa, oddiy matn sifatida yuborish
            await message.answer(chunk, parse_mode=None)

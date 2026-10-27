import os
import re
import uuid
import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.enums import ChatAction
from aiogram.fsm.context import FSMContext

from downloader import download_instagram_video
from ai_service import ask_ai, clear_history
from book_service import (
    search_books,
    get_book_available_files,
    download_file_to_disk,
    get_cached_book,
    DOWNLOAD_DIR
)
from keyboards import (
    get_main_keyboard,
    get_ai_keyboard,
    get_book_keyboard,
    get_book_actions_keyboard
)
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
        "📚 <b>Kitob Yuklash:</b> Sevimli kitobingiz nomi yoki muallifini qidiring va yuklab oling (PDF, EPUB).\n"
        "🤖 <b>AI Suhbat:</b> Istalgan savolingizni bering, sun'iy intellekt javob beradi.\n\n"
        "<i>Quyidagi menyudan kerakli bo'limni tanlang:</i>"
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
        "2️⃣ <b>Kitob qidirish va yuklash:</b>\n"
        "• <b>📚 Kitob Yuklash</b> tugmasini bosing.\n"
        "• Kitob nomi yoki muallifini kiriting (masalan: <i>Alisher Navoiy</i> yoki <i>Sherlock Holmes</i>).\n"
        "• Chiqqan natijalardan <b>📥 PDF</b> yoki <b>📥 EPUB</b> tugmasini bosib to'g'ridan-to'g'ri Telegram'da yuklab oling.\n\n"
        "3️⃣ <b>AI Suhbat (Sun'iy intellekt):</b>\n"
        "• <b>🤖 AI Suhbat</b> tugmasini bosing yoki to'g'ridan-to'g'ri savolingizni yozing.\n"
        "• AI sizning savollaringizga (matematika, dasturlash, tarjima, maslahatlar) javob beradi.\n"
        "• Suhbatni tozalash uchun <b>🔄 Yangi suhbat</b> tugmasidan foydalaning."
    )
    await message.answer(text, parse_mode="HTML")


@router.message(F.text == "📥 Video Yuklash")
async def btn_video_download(message: Message, state: FSMContext):
    await state.clear()
    text = (
        "📥 <b>Instagram Video Yuklash:</b>\n\n"
        "Iltimos, yuklamoqchi bo'lgan <b>Reels</b>, <b>Post</b> yoki <b>Video</b> havolasini yuboring.\n\n"
        "<i>Misol: https://www.instagram.com/reel/C.../</i>"
    )
    await message.answer(text, parse_mode="HTML")


# ==================== KITOB QIDIRISH VA YUKLASH BO'LIMI ====================

@router.message(Command("book"))
@router.message(Command("kitob"))
@router.message(F.text == "📚 Kitob Yuklash")
async def enter_book_search(message: Message, state: FSMContext):
    await state.set_state(BotStates.book_search)
    text = (
        "📚 <b>Elektron kitoblar qidirish va yuklash bo'limi!</b>\n\n"
        "Istalgan kitob nomi yoki muallifini yozing (o'zbek, rus yoki ingliz tillarida).\n\n"
        "<i>Masalan:</i>\n"
        "• <code>Alisher Navoiy</code>\n"
        "• <code>O'tkan kunlar</code>\n"
        "• <code>Sherlock Holmes</code>\n"
        "• <code>Python programming</code>\n"
        "• <code>Dostoyevskiy</code>"
    )
    await message.answer(text, reply_markup=get_book_keyboard(), parse_mode="HTML")


@router.message(BotStates.book_search, F.text == "🔙 Bosh menyu")
async def exit_book_search(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "🏠 Asosiy menyuga qaytdingiz.",
        reply_markup=get_main_keyboard()
    )


@router.message(BotStates.book_search, F.text)
async def handle_book_search_query(message: Message, state: FSMContext):
    query = message.text.strip()
    if not query:
        return

    status_msg = await message.answer(f"🔍 <i>\"{query}\" bo'yicha kitoblar qidirilmoqda...</i>", parse_mode="HTML")
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    try:
        books = await search_books(query, limit=5)
        if not books:
            await status_msg.edit_text(
                f"❌ <b>\"{query}\"</b> bo'yicha hech qanday kitob topilmadi.\n\n"
                "💡 <i>Tavsiya:</i>\n"
                "• Kitob nomini yoki muallif familiyasini boshqacha yozib ko'ring\n"
                "• Lotin yoki Kirill yozuvida sinab ko'ring (masalan, <i>Navoiy</i> yoki <i>Навоий</i>)\n"
                "• Asosiy kalit so'zlarni qisqaroq yozing.",
                parse_mode="HTML"
            )
            return

        await status_msg.edit_text(
            f"📚 <b>\"{query}\"</b> bo'yicha topilgan kitoblar ({len(books)} ta):\n"
            f"<i>Kerakli kitob ostidagi tugmani bosib yuklab oling:</i>",
            parse_mode="HTML"
        )

        for idx, book in enumerate(books, 1):
            short_id = book.get("short_id")
            title = book.get("title")
            author = book.get("author")
            year = f" ({book['year']})" if book.get("year") else ""
            web_url = book.get("url")

            kb = get_book_actions_keyboard(
                short_id=short_id,
                has_pdf=True,
                has_epub=True,
                web_url=web_url
            )

            book_text = (
                f"📖 <b>{idx}. {title}</b>\n"
                f"✍️ Muallif: <i>{author}</i>{year}"
            )
            await message.answer(book_text, reply_markup=kb, parse_mode="HTML")

    except Exception as e:
        logger.error(f"Kitob qidirishda xatolik: {e}")
        await status_msg.edit_text(
            "❌ Kitob qidirishda kutilmagan xatolik yuz berdi. Iltimos, keyinroq qayta urinib ko'ring.",
            parse_mode="HTML"
        )


@router.callback_query(F.data.startswith("dl_book:"))
async def handle_book_download(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Xatolik yuz berdi.", show_alert=True)
        return

    _, fmt, short_id = parts
    book = get_cached_book(short_id)

    if not book:
        await callback.answer(
            "⚠️ Ushbu so'rov eskirgan. Iltimos, kitobni qaytadan qidiring.",
            show_alert=True
        )
        return

    await callback.answer("⏳ Kitob tayyorlanmoqda...")
    status_msg = await callback.message.reply(
        f"⏳ <b>{book['title']}</b> ({fmt.upper()}) yuklab olinmoqda, iltimos kuting...",
        parse_mode="HTML"
    )

    temp_file_path = None
    try:
        await callback.bot.send_chat_action(chat_id=callback.message.chat.id, action=ChatAction.UPLOAD_DOCUMENT)
        files = await get_book_available_files(book["identifier"])
        target_file = files.get(fmt)

        # Agar so'ralgan format bo'lmasa, muqobil formatni tekshirish
        if not target_file:
            alt_fmt = "epub" if fmt == "pdf" else "pdf"
            target_file = files.get(alt_fmt)
            if target_file:
                fmt = alt_fmt
            else:
                web_url = book.get("url")
                await status_msg.edit_text(
                    f"❌ Kechirasiz, ushbu kitobning to'g'ridan-to'g'ri fayli topilmadi.\n\n"
                    f"Uni quyidagi havola orqali onlayn o'qishingiz mumkin:\n"
                    f"🔗 <a href='{web_url}'>Kitobni onlayn o'qish</a>",
                    parse_mode="HTML",
                    disable_web_page_preview=True
                )
                return

        file_size_mb = (target_file.get("size") or 0) / (1024 * 1024)
        if file_size_mb > 50:
            await status_msg.edit_text(
                f"⚠️ <b>{book['title']}</b> hajmi {file_size_mb:.1f} MB (Telegram bot limiti 50 MB dan katta).\n\n"
                f"Siz uni quyidagi havola orqali bepul yuklab olishingiz mumkin:\n"
                f"🔗 <a href='{target_file['url']}'>Faylni yuklab olish</a>",
                parse_mode="HTML"
            )
            return

        # Faylni xavfsiz nom bilan vaqtinchalik saqlash
        safe_filename = re.sub(r'[^\w\.\-\(\)]', '_', target_file["name"])
        temp_file_path = os.path.join(DOWNLOAD_DIR, f"{uuid.uuid4().hex[:8]}_{safe_filename}")

        download_res = await download_file_to_disk(target_file["url"], temp_file_path, max_size_mb=50)

        if download_res is None:
            await status_msg.edit_text(
                f"❌ Kitob faylini yuklab olishda xatolik yuz berdi.\n"
                f"Havola orqali to'g'ridan-to'g'ri yuklab ko'rishingiz mumkin:\n"
                f"🔗 <a href='{target_file['url']}'>Fayl havolasi</a>",
                parse_mode="HTML"
            )
            return

        if download_res == -1:
            await status_msg.edit_text(
                f"⚠️ Kitob hajmi juda katta (Telegram 50 MB limiti).\n"
                f"Quyidagi havola orqali to'g'ridan-to'g'ri yuklab oling:\n"
                f"🔗 <a href='{target_file['url']}'>Fayl havolasi</a>",
                parse_mode="HTML"
            )
            return

        doc = FSInputFile(temp_file_path, filename=target_file["name"])
        caption = (
            f"📚 <b>{book['title']}</b>\n"
            f"✍️ Muallif: <i>{book['author']}</i>\n"
            f"📄 Format: {fmt.upper()}\n\n"
            "🤖 @InstaLMX99bot orqali yuklab olindi."
        )

        await callback.message.answer_document(
            document=doc,
            caption=caption,
            parse_mode="HTML"
        )
        await status_msg.delete()

    except Exception as e:
        logger.error(f"Kitobni yuborishda xatolik: {e}")
        await status_msg.edit_text(
            f"❌ Kitobni yuborishda xatolik yuz berdi.",
            parse_mode="HTML"
        )
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except OSError:
                pass


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
        try:
            await message.answer(chunk, parse_mode="Markdown")
        except Exception:
            await message.answer(chunk, parse_mode=None)

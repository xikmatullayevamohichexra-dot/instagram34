import asyncio
import logging
import os
import sys
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from handlers import router


async def start_health_check_server(logger):
    """
    Render, Railway yoki boshqa bulutli xizmatlar (Web Service) uchun port ochib beruvchi server.
    Render $PORT muhit o'zgaruvchisini avtomatik beradi (odatda 10000).
    """
    port = os.getenv("PORT")
    if not port:
        return None

    try:
        app = web.Application()

        async def health(request):
            return web.Response(text="Bot is running!")

        app.router.add_get("/", health)
        app.router.add_get("/health", health)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", int(port))
        await site.start()
        logger.info(f"Health-check web server {port}-portda muvaffaqiyatli ishga tushdi.")
        return runner
    except Exception as e:
        logger.warning(f"Health-check web serverini ochishda xatolik: {e}")
        return None


async def main():
    # Logging sozlamalari
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("BOT_TOKEN aniqlanmadi! .env faylida bot tokenini ko'rsating.")
        return

    # Web Service (Render) uchun portni tinglash
    web_runner = await start_health_check_server(logger)

    # Bot va Dispatcher obyektlarini yaratish
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Routerni ulash
    dp.include_router(router)

    logger.info("Bot ishga tushirilmoqda...")
    try:
        # Eski kutilayotgan yangilanishlarni tozalash va pollingni boshlash
        await bot.delete_webhook(drop_pending_updates=True)
        # Polling rejimida ishga tushirish
        await dp.start_polling(bot)
    finally:
        if web_runner:
            await web_runner.cleanup()
        await bot.session.close()
        logger.info("Bot to'xtatildi.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("\nBot to'xtatildi.")

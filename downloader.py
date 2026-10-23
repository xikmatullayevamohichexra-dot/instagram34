import os
import glob
import uuid
import asyncio
import logging
from typing import Optional, Dict, Any
import yt_dlp

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


def _sync_download(url: str) -> Optional[Dict[str, Any]]:
    """
    Instagram havolasidan videoni yuklab oluvchi sinxron funksiya.
    ffmpeg talab qilmaslik uchun to'g'ridan-to'g'ri 'best' formatidan foydalanadi.
    """
    unique_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{unique_id}_%(id)s.%(ext)s")

    ydl_opts = {
        'outtmpl': output_template,
        'format': 'best[ext=mp4]/best',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/124.0.0.0 Safari/537.36'
            ),
            'Accept-Language': 'en-US,en;q=0.9',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None

            # Qidirib ko'ramiz - yuklangan fayl yo'li
            pattern = os.path.join(DOWNLOAD_DIR, f"{unique_id}_*")
            matching_files = glob.glob(pattern)

            if not matching_files:
                return None

            filepath = matching_files[0]
            title = info.get("title") or "Instagram Video"
            duration = info.get("duration") or 0
            caption = info.get("description") or ""

            return {
                "file_path": filepath,
                "title": title,
                "duration": duration,
                "caption": caption[:1000] if caption else ""
            }
    except Exception as e:
        logger.error(f"Yuklab olishda xatolik: {e}")
        # Tozalash
        for f in glob.glob(os.path.join(DOWNLOAD_DIR, f"{unique_id}_*")):
            try:
                os.remove(f)
            except OSError:
                pass
        raise e


async def download_instagram_video(url: str) -> Optional[Dict[str, Any]]:
    return await asyncio.to_thread(_sync_download, url)

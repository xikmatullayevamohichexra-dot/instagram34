import os
import re
import uuid
import logging
import urllib.parse
from typing import List, Dict, Any, Optional
import aiohttp

logger = logging.getLogger(__name__)

DOWNLOAD_DIR = os.path.join(os.path.dirname(__file__), "downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Callback_data limitini (64 bayt) oshirmaslik uchun qisqa ID kesh
BOOK_CACHE: Dict[str, Dict[str, Any]] = {}


def cache_book(book_data: Dict[str, Any]) -> str:
    """Kitob ma'lumotlarini qisqa kalit ostida saqlash"""
    short_id = uuid.uuid4().hex[:12]
    BOOK_CACHE[short_id] = book_data
    # Kesh juda kattalashib ketmasligi uchun (oxirgi 500 ta kitob)
    if len(BOOK_CACHE) > 500:
        first_key = next(iter(BOOK_CACHE))
        BOOK_CACHE.pop(first_key, None)
    return short_id


def get_cached_book(short_id: str) -> Optional[Dict[str, Any]]:
    return BOOK_CACHE.get(short_id)


def clean_text(text: str) -> str:
    """HTML teglar va ortiqcha belgilarni tozalash"""
    if not text:
        return ""
    text = re.sub(r'<[^>]+>', '', str(text))
    return " ".join(text.split())


async def search_archive_org(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Archive.org orqali kitoblarni qidirish"""
    # Maxsus belgilarni tozalash va qidiruv so'rovini tayyorlash
    safe_query = re.sub(r'[^\w\s\-\']', ' ', query).strip()
    if not safe_query:
        return []

    q_encoded = urllib.parse.quote(f"({safe_query}) AND mediatype:(texts)")
    url = (
        f"https://archive.org/advancedsearch.php?q={q_encoded}"
        f"&fl[]=identifier,title,creator,year,downloads,description"
        f"&sort[]=downloads+desc&rows={limit}&output=json"
    )

    books = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BookBot/1.0"}

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
                docs = data.get("response", {}).get("docs", [])

                for doc in docs:
                    identifier = doc.get("identifier")
                    if not identifier:
                        continue

                    title = clean_text(doc.get("title") or identifier)
                    creator = doc.get("creator")
                    if isinstance(creator, list):
                        creator = ", ".join(creator)
                    author = clean_text(creator or "Noma'lum muallif")
                    year = doc.get("year", "")

                    book_info = {
                        "identifier": identifier,
                        "title": title[:100],
                        "author": author[:80],
                        "year": str(year) if year else "",
                        "url": f"https://archive.org/details/{identifier}"
                    }
                    books.append(book_info)
    except Exception as e:
        logger.warning(f"Archive.org qidiruvida xatolik: {e}")

    return books


async def search_open_library(query: str, limit: int = 4) -> List[Dict[str, Any]]:
    """Open Library orqali kitoblar va ularning Internet Archive ID larini qidirish"""
    safe_query = urllib.parse.quote(query)
    url = f"https://openlibrary.org/search.json?q={safe_query}&limit={limit}"
    headers = {"User-Agent": "TelegramBookBot/1.0 (contact@example.com)"}

    books = []
    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return []
                data = await resp.json(content_type=None)
                docs = data.get("docs", [])

                for doc in docs:
                    ia_list = doc.get("ia")
                    if not ia_list:
                        continue
                    identifier = ia_list[0]
                    title = clean_text(doc.get("title") or identifier)
                    authors = doc.get("author_name", [])
                    author = ", ".join(authors) if authors else "Noma'lum muallif"
                    year = doc.get("first_publish_year", "")

                    books.append({
                        "identifier": identifier,
                        "title": title[:100],
                        "author": clean_text(author)[:80],
                        "year": str(year) if year else "",
                        "url": f"https://archive.org/details/{identifier}"
                    })
    except Exception as e:
        logger.warning(f"OpenLibrary qidiruvida xatolik: {e}")

    return books


async def search_books(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Kombinatsiyalashgan kitob qidirish (Archive.org + OpenLibrary).
    Natijalar saralanadi va qisqa kesh ID lari biriktiriladi.
    """
    seen_ids = set()
    results = []

    # 1. Archive.org qidiruvi
    ia_books = await search_archive_org(query, limit=limit)
    for b in ia_books:
        ident = b["identifier"]
        if ident not in seen_ids:
            seen_ids.add(ident)
            b["short_id"] = cache_book(b)
            results.append(b)

    # 2. Agar natijalar yetarli bo'lmasa, Open Library dan ham to'ldirish
    if len(results) < limit:
        ol_books = await search_open_library(query, limit=limit - len(results) + 2)
        for b in ol_books:
            ident = b["identifier"]
            if ident not in seen_ids:
                seen_ids.add(ident)
                b["short_id"] = cache_book(b)
                results.append(b)
            if len(results) >= limit:
                break

    return results[:limit]


async def get_book_available_files(identifier: str) -> Dict[str, Any]:
    """
    Kitobning mavjud formatlarini (PDF, EPUB) va yuklab olish havolalarini aniqlash.
    """
    url = f"https://archive.org/metadata/{identifier}/files"
    headers = {"User-Agent": "Mozilla/5.0 BookBot/1.0"}

    best_pdf = None
    best_epub = None

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status != 200:
                    return {}
                data = await resp.json(content_type=None)
                files = data.get("result", [])

                for f in files:
                    name = f.get("name", "")
                    size = int(f.get("size") or 0)
                    fmt = (f.get("format") or "").lower()

                    # PDF fayllarni tekshirish (chunki bir nechta bo'lishi mumkin)
                    if name.lower().endswith(".pdf") and not name.lower().endswith("_thumb.pdf"):
                        # Hajmi 0 dan katta va 50MB dan kam bo'lgan eng yaxshi PDF
                        if not best_pdf or ("text pdf" in fmt and size > 0):
                            best_pdf = {
                                "name": name,
                                "size": size,
                                "url": f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}"
                            }

                    # EPUB fayllarni tekshirish
                    if name.lower().endswith(".epub"):
                        if not best_epub or size > (best_epub.get("size") or 0):
                            best_epub = {
                                "name": name,
                                "size": size,
                                "url": f"https://archive.org/download/{identifier}/{urllib.parse.quote(name)}"
                            }

    except Exception as e:
        logger.error(f"Fayllar ro'yxatini olishda xatolik: {e}")

    return {
        "pdf": best_pdf,
        "epub": best_epub
    }


async def download_file_to_disk(url: str, dest_path: str, max_size_mb: int = 50) -> Optional[int]:
    """
    Faylni belgilangan manzilga xavfsiz yuklab olish.
    Agar hajmi max_size_mb dan oshsa, yuklash to'xtatiladi.
    Haqiqiy hajm (baytlarda) qaytariladi yoki None.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) BookBot/1.0"}
    max_bytes = max_size_mb * 1024 * 1024
    total_downloaded = 0

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                if resp.status != 200:
                    logger.error(f"Faylni yuklab bo'lmadi, status: {resp.status}")
                    return None

                content_len = resp.headers.get("Content-Length")
                if content_len and int(content_len) > max_bytes:
                    logger.warning(f"Fayl hajmi {int(content_len)} bayt, limit: {max_bytes}")
                    return -1  # Hajm kattaligini bildiradi

                with open(dest_path, "wb") as f:
                    while True:
                        chunk = await resp.content.read(64 * 1024)
                        if not chunk:
                            break
                        total_downloaded += len(chunk)
                        if total_downloaded > max_bytes:
                            return -1
                        f.write(chunk)

                return total_downloaded
    except Exception as e:
        logger.error(f"Faylni yuklab olishda istisno: {e}")
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
            except OSError:
                pass
        return None

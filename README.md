# 📸 Instagram Video Downloader, 📚 Kitob Yuklash & 🤖 AI Chat Telegram Bot

Ushbu bot 3 ta asosiy kuchli funksiyani birlashtirgan ko'p funksiyali yordamchidir:
1. **Instagram Video Downloader**: Foydalanuvchi yuborgan Instagram havolalaridagi (Reels, Post, Video) videolarni yuklab beradi.
2. **📚 Kitob Yuklash**: Dunyo va o'zbek adabiyoti, darsliklar va ilmiy kitoblarni qidirish, PDF hamda EPUB formatlarida to'g'ridan-to'g'ri Telegram orqali yuklab olish.
3. **🤖 AI Chat (Sun'iy intellekt suhbati)**: Foydalanuvchilarning barcha savollariga (matematika, dasturlash, tarjima, maslahat va h.k.) o'zbek tilida aqlli javob beradi.

---

## 🚀 Asosiy imkoniyatlari
- **Instagram Reels, Post va Video** yuklash (ffmpeg talab qilmaydi, tezyurar).
- **Elektron kitoblar qidirish va yuklash (PDF va EPUB)**:
  - Muallif yoki kitob nomi orqali qidirish (o'zbek, rus va ingliz tillarida).
  - Telegram orqali to'g'ridan-to'g'ri PDF yoki EPUB fayl shaklida yuklab olish.
  - Onlayn o'qish havolasi.
- **Aqlli AI Suhbat bo'limi**: Suhbat kontekstini (tarixini) eslab qoladi.
- **Tugmali qulay menyu**:
  - `🤖 AI Suhbat` — Sun'iy intellekt rejimiga o'tish.
  - `📚 Kitob Yuklash` — Kitob qidirish va yuklash rejimiga o'tish.
  - `📥 Video Yuklash` — Instagram yuklash bo'limi.
  - `🔄 Yangi suhbat` — AI xotirasini tozalash.
  - `🔙 Bosh menyu` — Asosiy menyuga qaytish.
- **Render.com / Cloud qo'llab-quvvatlovi**:
  - Web Service sifatida deploy qilish uchun avtomatik health-check server mavjud.
  - Port scan xatosi bo'lmaydi.

---

## 🛠 O'rnatish va Ishga tushirish

### 1-qadam: Tokenni sozlash
[`.env`](file:///.env) faylida bot tokeningiz ko'rsatilgan:
```env
BOT_TOKEN=8674266370:AAGuZwMZPjFmt5b_YJRGYrSFzAQ9UTKsvEs
# (Ixtiyoriy) Google Gemini kaliti:
GEMINI_API_KEY=
```

### 2-qadam: Botni ishga tushirish
Papka ichidagi [`run.bat`](file:///run.bat) faylini **ikki marta bosing**.
Yoki terminal orqali:
```powershell
.\venv\Scripts\python.exe main.py
```

---

## 📂 Loyiha tuzilishi
```
bot papka/
│
├── .env                # Bot tokeni
├── config.py           # Sozlamalar
├── ai_service.py       # AI chat xizmati va kontekst boshqaruvi
├── book_service.py     # Kitob qidirish va yuklash moduli (Archive.org, OpenLibrary)
├── keyboards.py        # Menyular va inline tugmalar
├── states.py           # FSM holatlari (AI va Kitob qidirish)
├── downloader.py       # Instagram videolarni yuklovchi modul
├── handlers.py         # Bot komandalari va xabar ishlovchilari
├── main.py             # Asosiy ishga tushiruvchi fayl (web server + bot polling)
├── bot.py              # Render/serverlar uchun entrypoint
├── requirements.txt    # Kerakli kutubxonalar
├── run.bat             # 1 marta bosish bilan ishga tushirish
└── README.md           # Qo'llanma
```

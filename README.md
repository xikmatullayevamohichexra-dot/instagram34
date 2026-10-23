# 📸 Instagram Video Downloader & 🤖 AI Chat Telegram Bot

Ushbu bot 2 ta asosiy kuchli funksiyani birlashtirgan:
1. **Instagram Video Downloader**: Foydalanuvchi yuborgan Instagram havolalaridagi (Reels, Post, Video) videolarni yuklab beradi.
2. **AI Chat (Sun'iy intellekt suhbati)**: Foydalanuvchilarning barcha savollariga (matematika, dasturlash, tarjima, maslahat va h.k.) o'zbek tilida aqlli javob beradi.

---

## 🚀 Asosiy imkoniyatlari
- **Instagram Reels, Post va Video** yuklash (ffmpeg talab qilmaydi, tezyurar).
- **Aqlli AI Suhbat bo'limi**: Suhbat kontekstini (tarixini) eslab qoladi.
- **Tugmali qulay menyu**:
  - `🤖 AI Suhbat` — Sun'iy intellekt rejimiga o'tish.
  - `🔄 Yangi suhbat` — AI xotirasini tozalash.
  - `📥 Video Yuklash` — Instagram yuklash bo'limi.
  - `🔙 Bosh menyu` — Asosiy menyuga qaytish.
- Bepul AI dvigateli bilan to'g'ridan-to'g'ri ishlaydi (hech qanday API kalit talab qilmaydi).
- Ixtiyoriy ravishda Google Gemini API kalitini ham qo'llab-quvvatlaydi.

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
├── keyboards.py        # Menyular va tugmalar
├── states.py           # FSM holatlari (AI rejim)
├── downloader.py       # Instagram videolarni yuklovchi modul
├── handlers.py         # Bot komandalari va xabar ishlovchilari
├── main.py             # Asosiy ishga tushiruvchi fayl
├── requirements.txt    # Kerakli kutubxonalar
├── run.bat             # 1 marta bosish bilan ishga tushirish
└── README.md           # Qo'llanma
```

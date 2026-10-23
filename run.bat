@echo off
chcp 65001 > nul
title Instagram Video Downloader Bot
echo ========================================================
echo         Instagram Video Downloader Bot (Aiogram 3)
echo ========================================================

REM Agar virtual muhit allaqachon mavjud bo'lsa, to'g'ridan-to'g'ri ishga tushirish
if exist venv\Scripts\python.exe (
    echo [OK] Muhit tayyor. Bot ishga tushirilmoqda...
    echo To'xtatish uchun: Ctrl + C tugmalarini bosing.
    echo.
    venv\Scripts\python.exe main.py
    goto end
)

REM Python dasturini aniqlash
set "PYTHON_EXE="

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else (
    where py >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
    ) else (
        where python >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=python"
        )
    )
)

if "%PYTHON_EXE%"=="" (
    echo [XATOLIK] Python topilmadi!
    echo Iltimos, Python 3.10+ o'rnatilganligini tekshiring.
    pause
    exit /b 1
)

echo [1/3] Virtual muhit (venv) yaratilmoqda...
"%PYTHON_EXE%" -m venv venv

echo [2/3] Kerakli kutubxonalar o'rnatilmoqda...
venv\Scripts\python.exe -m pip install -r requirements.txt --quiet

echo [3/3] Bot ishga tushirilmoqda...
venv\Scripts\python.exe main.py

:end
pause

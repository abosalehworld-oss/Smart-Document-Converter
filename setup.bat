@echo off
chcp 65001 >nul
title تثبيت برنامج تحويل المستندات الذكي
echo ============================================
echo   تثبيت برنامج تحويل المستندات الذكي
echo   Smart Document Converter - Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python غير مثبت! يرجى تثبيت Python 3.11 أو أحدث
    echo [ERROR] Python is not installed! Please install Python 3.11+
    pause
    exit /b 1
)

echo [1/3] إنشاء بيئة افتراضية...
echo [1/3] Creating virtual environment...
python -m venv venv
if errorlevel 1 (
    echo [ERROR] فشل إنشاء البيئة الافتراضية
    pause
    exit /b 1
)

echo [2/3] تفعيل البيئة الافتراضية...
echo [2/3] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/3] تثبيت المكتبات المطلوبة...
echo [3/3] Installing required packages...
pip install --no-cache-dir -r requirements.txt
if errorlevel 1 (
    echo [ERROR] فشل تثبيت المكتبات
    pause
    exit /b 1
)

echo.
echo ============================================
echo   تم التثبيت بنجاح! ✓
echo   Installation completed successfully!
echo ============================================
echo.
echo لتشغيل البرنامج، استخدم: run.bat
echo To run the app, use: run.bat
echo.
pause

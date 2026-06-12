@echo off
chcp 65001 >nul
color 0A
title 🔨 بناء برنامج محوّل المستندات الذكي

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║    🔨 بناء محوّل المستندات الذكي               ║
echo  ║    Smart Document Converter - Full Build        ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM ============================================
REM الخطوة 0: التحقق من Python
REM ============================================
py --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        color 0C
        echo  ❌ Python غير مثبت! ثبته من python.org
        pause
        exit /b 1
    )
    set PYCMD=python
) else (
    set PYCMD=py
)

for /f "tokens=2" %%i in ('%PYCMD% --version 2^>^&1') do set PYVER=%%i
echo  ✅ Python %PYVER%
echo.

REM ============================================
REM الخطوة 1: البيئة الافتراضية (مرة واحدة فقط)
REM ============================================
if not exist "venv\Scripts\activate.bat" (
    echo  [1/5] إنشاء البيئة الافتراضية...
    %PYCMD% -m venv venv
    if errorlevel 1 (
        color 0C
        echo  ❌ فشل إنشاء البيئة
        pause
        exit /b 1
    )
    echo  ✅ تم إنشاء البيئة
) else (
    echo  [1/5] ✅ البيئة الافتراضية موجودة ^(تخطي^)
)

call venv\Scripts\activate.bat

REM ============================================
REM الخطوة 2: المكتبات (مرة واحدة فقط)
REM ============================================
pip show easyocr >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [2/5] تثبيت المكتبات... ⏳ ^(15-30 دقيقة أول مرة^)
    echo.
    pip install --no-cache-dir -r requirements.txt
    if errorlevel 1 (
        color 0C
        echo  ❌ فشل تثبيت المكتبات - تأكد من الإنترنت
        pause
        exit /b 1
    )
    pip install pyinstaller
    echo  ✅ تم تثبيت المكتبات
) else (
    echo  [2/5] ✅ المكتبات مثبتة بالفعل ^(تخطي^)
    pip show pyinstaller >nul 2>&1
    if errorlevel 1 pip install pyinstaller
)

REM ============================================
REM الخطوة 3: نماذج OCR (مرة واحدة فقط)
REM ============================================
if not exist "models\" mkdir models

REM نتحقق من وجود أي ملف .pth في مجلد models
dir /b models\*.pth >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [3/5] تحميل نماذج OCR... ⏳ ^(~250MB^)
    %PYCMD% -c "import easyocr; r=easyocr.Reader(['ar','en'],gpu=False,model_storage_directory='models',verbose=True); print('  ✅ تم تحميل النماذج')"
    if errorlevel 1 (
        color 0C
        echo  ❌ فشل تحميل النماذج
        pause
        exit /b 1
    )
) else (
    echo  [3/5] ✅ نماذج OCR موجودة ^(تخطي^)
)

REM ============================================
REM الخطوة 4: بناء الـ exe ⚡
REM ============================================
echo.
echo  [4/5] بناء الملف التنفيذي... ⏳ ^(3-10 دقائق^)
echo.

if exist "dist\SmartDocConverter" rmdir /s /q "dist\SmartDocConverter"
if exist "build\SmartDocConverter" rmdir /s /q "build\SmartDocConverter"

pyinstaller SmartDocConverter.spec --noconfirm --clean

if errorlevel 1 (
    color 0C
    echo  ❌ فشل البناء!
    pause
    exit /b 1
)

REM ============================================
REM الخطوة 5: نسخ النماذج للمجلد النهائي
REM ============================================
echo.
echo  [5/5] تجهيز الحزمة النهائية...

if exist "models" (
    if not exist "dist\SmartDocConverter\models" mkdir "dist\SmartDocConverter\models"
    xcopy /E /I /Q /Y "models\*" "dist\SmartDocConverter\models\" >nul 2>&1
)

REM ملف تشغيل سهل بالعربي
(
echo @echo off
echo start SmartDocConverter.exe
) > "dist\SmartDocConverter\تشغيل البرنامج.bat"

echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║                                                  ║
echo  ║   ✅ تم البناء بنجاح!                           ║
echo  ║                                                  ║
echo  ║   📁 المجلد: dist\SmartDocConverter\             ║
echo  ║   🖱️ شغّل:   SmartDocConverter.exe               ║
echo  ║                                                  ║
echo  ║   📤 انسخ المجلد كامل لجهاز الشغل              ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

explorer "dist\SmartDocConverter"
pause

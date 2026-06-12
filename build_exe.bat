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
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo  ❌ خطأ: Python غير مثبت!
    echo  ❌ Error: Python is not installed!
    echo.
    echo  يرجى تثبيت Python 3.11 من:
    echo  https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYVER=%%i
echo  ✅ Python %PYVER% موجود
echo.

REM ============================================
REM الخطوة 1: إنشاء البيئة الافتراضية
REM ============================================
echo  [1/5] إعداد البيئة الافتراضية...
if not exist "venv\" (
    python -m venv venv
    if errorlevel 1 (
        color 0C
        echo  ❌ فشل إنشاء البيئة الافتراضية
        pause
        exit /b 1
    )
    echo  ✅ تم إنشاء البيئة الافتراضية
) else (
    echo  ✅ البيئة الافتراضية موجودة بالفعل
)

call venv\Scripts\activate.bat

REM ============================================
REM الخطوة 2: تثبيت المكتبات
REM ============================================
echo.
echo  [2/5] تثبيت المكتبات المطلوبة...
echo  ⏳ قد يستغرق هذا 5-15 دقيقة...
echo.

pip install --no-cache-dir -r requirements.txt --quiet
if errorlevel 1 (
    color 0C
    echo  ❌ فشل تثبيت المكتبات
    echo  تأكد من وجود اتصال بالإنترنت للتثبيت الأول
    pause
    exit /b 1
)

echo  ✅ تم تثبيت المكتبات

REM ============================================
REM الخطوة 3: تحميل نماذج OCR
REM ============================================
echo.
echo  [3/5] تحميل نماذج التعرف على النصوص...
echo  ⏳ جاري تحميل نماذج العربي والإنجليزي (~250MB)...

if not exist "models\" mkdir models

python -c "
import os, sys
os.makedirs('models', exist_ok=True)
print('  جاري تحميل نماذج EasyOCR...')
try:
    import easyocr
    reader = easyocr.Reader(
        ['ar', 'en'],
        gpu=False,
        model_storage_directory='models',
        verbose=False
    )
    print('  ✅ تم تحميل النماذج بنجاح')
except Exception as e:
    print(f'  ❌ خطأ في تحميل النماذج: {e}')
    sys.exit(1)
"

if errorlevel 1 (
    color 0C
    echo  ❌ فشل تحميل نماذج OCR
    pause
    exit /b 1
)

echo  ✅ نماذج OCR جاهزة

REM ============================================
REM الخطوة 4: بناء الـ exe بـ PyInstaller
REM ============================================
echo.
echo  [4/5] بناء الملف التنفيذي...
echo  ⏳ قد يستغرق 5-10 دقائق...
echo.

REM تنظيف ملفات البناء السابقة
if exist "dist\SmartDocConverter" rmdir /s /q "dist\SmartDocConverter"
if exist "build\SmartDocConverter" rmdir /s /q "build\SmartDocConverter"

pyinstaller SmartDocConverter.spec --noconfirm --clean

if errorlevel 1 (
    color 0C
    echo.
    echo  ❌ فشل بناء الملف التنفيذي!
    echo  راجع الأخطاء بالأعلى
    pause
    exit /b 1
)

REM ============================================
REM الخطوة 5: نسخ نماذج OCR للمجلد الناتج
REM ============================================
echo.
echo  [5/5] إضافة نماذج OCR للحزمة النهائية...

if exist "models" (
    if not exist "dist\SmartDocConverter\models" mkdir "dist\SmartDocConverter\models"
    xcopy /E /I /Q "models\*" "dist\SmartDocConverter\models\" >nul 2>&1
    echo  ✅ تم نسخ النماذج
)

REM ============================================
REM إنشاء ملف تشغيل سهل للمستخدم
REM ============================================
echo @echo off > "dist\SmartDocConverter\تشغيل البرنامج.bat"
echo start SmartDocConverter.exe >> "dist\SmartDocConverter\تشغيل البرنامج.bat"

REM ============================================
REM حساب حجم المجلد الناتج
REM ============================================
for /f "tokens=3" %%a in ('dir "dist\SmartDocConverter" /s ^| findstr "File(s)"') do set FILECOUNT=%%a
echo.
echo  ╔══════════════════════════════════════════════════╗
echo  ║                                                  ║
echo  ║   ✅ تم البناء بنجاح تام!                       ║
echo  ║   ✅ Build completed successfully!               ║
echo  ║                                                  ║
echo  ║   📁 الملف الناتج في:                           ║
echo  ║   dist\SmartDocConverter\                        ║
echo  ║                                                  ║
echo  ║   🖱️ اضغط دبل كليك على:                         ║
echo  ║   SmartDocConverter.exe                          ║
echo  ║                                                  ║
echo  ║   📤 انسخ مجلد SmartDocConverter كاملاً         ║
echo  ║   لجهاز العمل وشغّل exe مباشرة                  ║
echo  ║                                                  ║
echo  ╚══════════════════════════════════════════════════╝
echo.

REM فتح المجلد الناتج تلقائياً
explorer "dist\SmartDocConverter"

pause

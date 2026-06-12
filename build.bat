@echo off
chcp 65001 >nul
title بناء البرنامج - Smart Document Converter Build
echo ============================================
echo   بناء ملف exe مستقل
echo   Building standalone executable
echo ============================================
echo.

call venv\Scripts\activate.bat

echo [1/2] تنظيف ملفات البناء السابقة...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo [2/2] بناء الملف التنفيذي...
pyinstaller ^
    --name "SmartDocConverter" ^
    --windowed ^
    --noconfirm ^
    --clean ^
    --add-data "app;app" ^
    --hidden-import easyocr ^
    --hidden-import torch ^
    --hidden-import torchvision ^
    --hidden-import cv2 ^
    --hidden-import fitz ^
    --hidden-import docx ^
    --hidden-import arabic_reshaper ^
    --hidden-import bidi ^
    --hidden-import PySide6 ^
    main.py

if errorlevel 1 (
    echo.
    echo [ERROR] فشل البناء!
    pause
    exit /b 1
)

echo.
echo ============================================
echo   تم البناء بنجاح! ✓
echo   Build completed successfully!
echo   الملف موجود في: dist\SmartDocConverter\
echo ============================================
echo.
pause

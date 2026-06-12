@echo off
chcp 65001 >nul 2>&1
color 0A
title Building Smart Document Converter...

echo.
echo  ============================================================
echo   Smart Document Converter - Full Build
echo  ============================================================
echo.

REM ============================================
REM Step 0: Check Python
REM ============================================
py --version >nul 2>&1
if errorlevel 1 (
    python --version >nul 2>&1
    if errorlevel 1 (
        color 0C
        echo  [ERROR] Python is not installed! Install from python.org
        pause
        exit /b 1
    )
    set PYCMD=python
) else (
    set PYCMD=py
)

for /f "tokens=2" %%i in ('%PYCMD% --version 2^>^&1') do set PYVER=%%i
echo  [OK] Python %PYVER% found
echo.

REM ============================================
REM Step 1: Virtual Environment
REM ============================================
if not exist "venv\Scripts\activate.bat" (
    echo  [1/5] Creating virtual environment...
    %PYCMD% -m venv venv
    if errorlevel 1 (
        color 0C
        echo  [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo  [OK] Virtual environment created
) else (
    echo  [1/5] Virtual environment already exists (skip)
)

call venv\Scripts\activate.bat

REM ============================================
REM Step 2: Install libraries
REM ============================================
pip show easyocr >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [2/5] Installing libraries... (15-30 min first time)
    echo.
    pip install --no-cache-dir -r requirements.txt
    if errorlevel 1 (
        color 0C
        echo  [ERROR] Failed to install libraries - check internet connection
        pause
        exit /b 1
    )
    pip install pyinstaller
    echo  [OK] Libraries installed
) else (
    echo  [2/5] Libraries already installed (skip)
    pip show pyinstaller >nul 2>&1
    if errorlevel 1 pip install pyinstaller
)

REM ============================================
REM Step 3: OCR Models
REM ============================================
if not exist "models\" mkdir models

dir /b models\*.pth >nul 2>&1
if errorlevel 1 (
    echo.
    echo  [3/5] Downloading OCR models... (~250MB)
    %PYCMD% -c "import easyocr; r=easyocr.Reader(['ar','en'],gpu=False,model_storage_directory='models',verbose=True); print('  [OK] Models downloaded')"
    if errorlevel 1 (
        color 0C
        echo  [ERROR] Failed to download models
        pause
        exit /b 1
    )
) else (
    echo  [3/5] OCR models already exist (skip)
)

REM ============================================
REM Step 4: Build EXE
REM ============================================
echo.
echo  [4/5] Building executable... (3-10 minutes)
echo.

if exist "dist\SmartDocConverter" rmdir /s /q "dist\SmartDocConverter"
if exist "build\SmartDocConverter" rmdir /s /q "build\SmartDocConverter"

pyinstaller SmartDocConverter.spec --noconfirm --clean

if errorlevel 1 (
    color 0C
    echo  [ERROR] Build failed!
    pause
    exit /b 1
)

REM ============================================
REM Step 5: Copy models to output folder
REM ============================================
echo.
echo  [5/5] Preparing final package...

if exist "models" (
    if not exist "dist\SmartDocConverter\models" mkdir "dist\SmartDocConverter\models"
    xcopy /E /I /Q /Y "models\*" "dist\SmartDocConverter\models\" >nul 2>&1
)

REM Create a simple launcher bat file
(
echo @echo off
echo start SmartDocConverter.exe
) > "dist\SmartDocConverter\Run_Program.bat"

echo.
echo  ============================================================
echo.
echo   [SUCCESS] Build completed successfully!
echo.
echo   Folder : dist\SmartDocConverter\
echo   Run    : SmartDocConverter.exe
echo.
echo   Copy the entire folder to target machine
echo  ============================================================
echo.

explorer "dist\SmartDocConverter"
pause

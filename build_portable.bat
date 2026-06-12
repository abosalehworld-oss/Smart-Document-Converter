@echo off
chcp 65001 >nul 2>&1
color 0A
title Building Portable Smart Document Converter...

set OUTDIR=dist\Portable_SmartDocConverter
set PYDIR=%OUTDIR%\python
set TESSDIR=%OUTDIR%\tesseract

echo.
echo  ============================================================
echo   Building Portable Standalone Package (v2.0 - Tesseract)
echo  ============================================================
echo.

echo  [1/7] Cleaning old portable build...
if exist "%OUTDIR%" rmdir /s /q "%OUTDIR%"
mkdir "%OUTDIR%"
mkdir "%PYDIR%"
mkdir "%PYDIR%\Lib\site-packages"

echo  [2/7] Downloading Python 3.13 Embeddable Package...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.1/python-3.13.1-embed-amd64.zip' -OutFile 'python-embed.zip'"
if errorlevel 1 (
    color 0C
    echo  [ERROR] Failed to download Python!
    pause
    exit /b 1
)

echo  [3/7] Extracting Python...
powershell -Command "Expand-Archive -Path 'python-embed.zip' -DestinationPath '%PYDIR%' -Force"
del python-embed.zip

echo  [4/7] Configuring Python (Enabling site-packages)...
powershell -Command "(Get-Content '%PYDIR%\python313._pth') -replace '#import site', 'import site' | Set-Content '%PYDIR%\python313._pth'"
echo Lib\site-packages >> "%PYDIR%\python313._pth"

echo  [5/7] Copying Tesseract OCR Engine...
if exist "C:\Program Files\Tesseract-OCR" (
    xcopy /E /I /Q /Y "C:\Program Files\Tesseract-OCR\*" "%TESSDIR%\" >nul
    echo  [OK] Tesseract copied from Program Files
) else (
    color 0C
    echo  [ERROR] Tesseract not found! Install it first.
    echo  Download: https://github.com/UB-Mannheim/tesseract/wiki
    pause
    exit /b 1
)

echo  [6/7] Copying Libraries and App Files...
REM Copy site-packages from venv to portable python
xcopy /E /I /Q /Y "venv\Lib\site-packages\*" "%PYDIR%\Lib\site-packages\" >nul

REM Copy app files
copy /Y "main.py" "%OUTDIR%\" >nul
xcopy /E /I /Q /Y "app\*" "%OUTDIR%\app\" >nul

REM Copy models if they exist
if exist "models" (
    xcopy /E /I /Q /Y "models\*" "%OUTDIR%\models\" >nul
)

echo  [7/7] Creating Run Program Script...
(
echo @echo off
echo title Smart Document Converter
echo cd /d "%%~dp0"
echo set PYTHONUTF8=1
echo start "" "python\pythonw.exe" main.py
) > "%OUTDIR%\Run_Program.bat"

echo.
echo  ============================================================
echo   [SUCCESS] Portable Package Created!
echo.
echo   Folder : %OUTDIR%
echo   Run    : Run_Program.bat
echo  ============================================================
echo.
explorer "%OUTDIR%"
pause

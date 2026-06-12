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

echo  [2/7] Preparing Python 3.13 Embeddable Package...
if not exist "python-embed.zip" (
    echo  Downloading Python from internet...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.1/python-3.13.1-embed-amd64.zip' -OutFile 'python-embed.zip'"
    if errorlevel 1 (
        color 0C
        echo  [ERROR] Failed to download Python!
        pause
        exit /b 1
    )
) else (
    echo  [OK] Using existing python-embed.zip file!
)

echo  [3/7] Extracting Python...
powershell -Command "Expand-Archive -Path 'python-embed.zip' -DestinationPath '%PYDIR%' -Force"
REM del python-embed.zip (Removed to allow offline builds)

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

echo  [7/7] Creating Run Program Script and Shortcut...
(
echo @echo off
echo title Smart Document Converter
echo cd /d "%%~dp0"
echo set PYTHONUTF8=1
echo start "" "python\pythonw.exe" main.py
) > "%OUTDIR%\Run_Program.bat"

REM Convert PNG to ICO if it doesn't exist
if exist "app\assets\icon.png" (
    if not exist "%OUTDIR%\app\assets\icon.ico" (
        venv\Scripts\python.exe -c "from PIL import Image; img=Image.open('app\assets\icon.png'); img.save(r'%OUTDIR%\app\assets\icon.ico', format='ICO', sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])"
    )
)

REM Create a desktop shortcut with the correct icon using VBScript
set VBS_FILE="%OUTDIR%\create_shortcut.vbs"
(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo Set fso = CreateObject^("Scripting.FileSystemObject"^)
echo currentDir = fso.GetAbsolutePathName^("."^)
echo sLinkFile = currentDir ^& "\Smart Document Converter.lnk"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = currentDir ^& "\Run_Program.bat"
echo oLink.WorkingDirectory = currentDir
echo oLink.IconLocation = currentDir ^& "\app\assets\icon.ico"
echo oLink.Save
) > %VBS_FILE%
cscript //nologo %VBS_FILE%
del %VBS_FILE%

echo.
echo  ============================================================
echo   [SUCCESS] Portable Package Created!
echo.
echo   Folder : %OUTDIR%
echo   Run    : Smart Document Converter.lnk (Shortcut)
echo  ============================================================
echo.
explorer "%OUTDIR%"
pause

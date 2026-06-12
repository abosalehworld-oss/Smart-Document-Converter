@echo off
chcp 65001 >nul 2>&1
color 0A
title Building Portable Smart Document Converter...

set OUTDIR=dist\Portable_SmartDocConverter
set PYDIR=%OUTDIR%\python

echo.
echo  ============================================================
echo   Building Portable Standalone Package
echo  ============================================================
echo.

echo  [1/6] Cleaning old portable build...
if exist "%OUTDIR%" rmdir /s /q "%OUTDIR%"
mkdir "%OUTDIR%"
mkdir "%PYDIR%"
mkdir "%PYDIR%\Lib\site-packages"

echo  [2/6] Downloading Python 3.13 Embeddable Package...
powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.13.1/python-3.13.1-embed-amd64.zip' -OutFile 'python-embed.zip'"
if errorlevel 1 (
    color 0C
    echo  [ERROR] Failed to download Python!
    pause
    exit /b 1
)

echo  [3/6] Extracting Python...
powershell -Command "Expand-Archive -Path 'python-embed.zip' -DestinationPath '%PYDIR%' -Force"
del python-embed.zip

echo  [4/6] Configuring Python (Enabling site-packages)...
REM Enable site-packages in the .pth file
powershell -Command "(Get-Content '%PYDIR%\python313._pth') -replace '#import site', 'import site' | Set-Content '%PYDIR%\python313._pth'"
echo Lib\site-packages >> "%PYDIR%\python313._pth"

echo  [5/6] Copying Libraries and App Files (This may take a minute)...
REM Copy site-packages from venv to portable python
xcopy /E /I /Q /Y "venv\Lib\site-packages\*" "%PYDIR%\Lib\site-packages\" >nul

REM Copy app files
copy /Y "main.py" "%OUTDIR%\" >nul
xcopy /E /I /Q /Y "app\*" "%OUTDIR%\app\" >nul

REM Copy models if they exist
if exist "models" (
    xcopy /E /I /Q /Y "models\*" "%OUTDIR%\models\" >nul
)

echo  [6/6] Creating Run Program Script...
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
echo ============================================================
echo.
explorer "%OUTDIR%"
pause

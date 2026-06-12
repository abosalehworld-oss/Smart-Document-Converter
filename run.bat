@echo off
chcp 65001 >nul
title محول المستندات الذكي
call venv\Scripts\activate.bat
python main.py

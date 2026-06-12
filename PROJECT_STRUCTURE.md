# 🔒 Smart Document Converter - محوّل المستندات الذكي

## Project Architecture / هيكل المشروع

> ⚠️ **IMPORTANT FOR AI AGENTS**: This document describes the full architecture of this project.
> Read this file FIRST before making any changes to understand the codebase structure,
> design decisions, security constraints, and component relationships.

---

## 📋 Overview / نظرة عامة

**Purpose**: Offline, secure desktop application for converting PDF files and images to Word documents
with full Arabic (RTL) and English support. Built specifically for use in **sensitive government environments**
where internet access is unavailable and data security is paramount.

**Key Constraints**:
- 🚫 **ZERO network access** - No HTTP calls, no sockets, no telemetry, no update checks
- 🔒 **No data persistence** - No logs containing document content, no analytics, no tracking
- 💻 **CPU-only** - Must work on the weakest machines (no GPU required)
- 🌐 **Bilingual UI** - Arabic (RTL) + English (LTR) with runtime switching
- ♾️ **Unlimited free use** - No file limits, no watermarks, no license keys
- 📦 **Self-contained** - All dependencies pinned, no runtime downloads

---

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        main.py (Entry Point)                     │
│                  Setup logging, security checks,                 │
│                  create QApplication, launch GUI                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     app/gui/ (Presentation Layer)                │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ main_window  │  │   styles     │  │      workers         │   │
│  │   .py        │  │   .py        │  │       .py            │   │
│  │              │  │              │  │  (QThread workers     │   │
│  │ - Sidebar    │  │ - Dark theme │  │   for background     │   │
│  │ - Navigation │  │ - QSS styles │  │   OCR processing)    │   │
│  │ - RTL/LTR   │  │ - Colors     │  │                      │   │
│  │ - Lang switch│  │              │  │  - OCRLoadWorker     │   │
│  └──────┬───────┘  └──────────────┘  │  - PDFConversionWkr  │   │
│         │                            │  - ImageConversionWkr│   │
│         ▼                            └──────────────────────┘   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │  pdf_tab.py  │  │ image_tab.py │  │  settings_tab.py     │   │
│  │              │  │              │  │                      │   │
│  │ - Select PDF │  │ - Drag&Drop  │  │  - Language          │   │
│  │ - Page range │  │ - Browse img │  │  - OCR languages     │   │
│  │ - Convert    │  │ - Browse dir │  │  - Font settings     │   │
│  │ - Save as    │  │ - Convert    │  │  - Quality           │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    widgets.py                             │   │
│  │  DragDropArea | ProgressCard | FileListWidget             │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Uses
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     app/core/ (Business Logic Layer)             │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────────────────────┐     │
│  │  ocr_engine.py   │  │     image_processor.py           │     │
│  │                  │  │                                  │     │
│  │  - Tesseract wrap  │  │  - CLAHE contrast enhancement   │     │
│  │  - ar + en       │  │  - Gentle denoising (Arabic!)   │     │
│  │  - Text sorting  │  │  - Adaptive binarization        │     │
│  │  - Portable tess │  │  - Shadow removal (phone pics)  │     │
│  │  - Win Monkey Ptc│  │  - Upscaling small images       │     │
│  └──────────────────┘  │  - Deskewing                    │     │
│                        └──────────────────────────────────┘     │
│  ┌──────────────────┐  ┌──────────────────────────────────┐     │
│  │ pdf_processor.py │  │     word_generator.py            │     │
│  │                  │  │                                  │     │
│  │  - PyMuPDF/fitz  │  │  - python-docx                  │     │
│  │  - Smart detect: │  │  - Native RTL & LTR Auto-switch │     │
│  │    digital text  │  │  - Arabic CS fonts              │     │
│  │    vs scanned    │  │  - Exact Layout Preservation    │     │
│  │  - 300 DPI render│  │    (Line-by-Line mapping)       │     │
│  │  - Page-by-page  │  │  - .docx output                 │     │
│  └──────────────────┘  └──────────────────────────────────┘     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ Uses
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                     app/utils/ (Utilities Layer)                  │
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │   security.py    │  │ file_handler.py  │  │arabic_utils.py│  │
│  │                  │  │                  │  │              │  │
│  │  - Magic bytes   │  │  - TempFileManager│  │ - RTL reshape│  │
│  │  - File size     │  │  - Secure delete │  │ - Lang detect│  │
│  │  - Extension     │  │  - Auto cleanup  │  │ - i18n trans │  │
│  │  - Integrity     │  │  - File dialogs  │  │ - Normalize  │  │
│  │  - Error masking │  │                  │  │              │  │
│  │  - No network    │  │                  │  │              │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📂 File Tree / شجرة الملفات

```
بروجكت برنامج OCR/
│
├── main.py                          # 🚀 Entry point - app startup & security checks
├── requirements.txt                 # 📦 Pinned dependencies (NEVER use floating versions)
├── settings.json                    # ⚙️ User settings (auto-generated, no sensitive data)
├── setup.bat                        # 🔧 One-click environment setup
├── run.bat                          # ▶️ One-click app launcher
├── build.bat                        # 📦 PyInstaller build script
├── .gitignore                       # 🚫 Git ignore rules
├── README.md                        # 📖 Project overview
├── PROJECT_STRUCTURE.md             # 🏗️ THIS FILE - Architecture docs
├── SECURITY.md                      # 🔒 Security policy & guidelines
├── USER_GUIDE.md                    # 📚 Complete user manual
│
├── app/                             # 📁 Application source code
│   ├── __init__.py
│   │
│   ├── core/                        # ⚙️ Business logic (no UI dependencies)
│   │   ├── __init__.py
│   │   ├── ocr_engine.py           # Tesseract wrapper (CPU, offline)
│   │   ├── image_processor.py      # OpenCV image enhancement
│   │   ├── pdf_processor.py        # PyMuPDF PDF handling
│   │   └── word_generator.py       # python-docx Word creation
│   │
│   ├── gui/                         # 🎨 PySide6 GUI components
│   │   ├── __init__.py
│   │   ├── main_window.py          # Main window + sidebar navigation
│   │   ├── pdf_tab.py              # PDF → Word conversion tab
│   │   ├── image_tab.py            # Images → Word conversion tab
│   │   ├── settings_tab.py         # Settings + language switcher
│   │   ├── widgets.py              # Reusable widgets (DragDrop, Progress)
│   │   ├── workers.py              # QThread background workers
│   │   └── styles.py               # Dark theme QSS stylesheet
│   │
│   ├── utils/                       # 🔧 Utility modules
│   │   ├── __init__.py
│   │   ├── security.py             # File validation, no-network enforcement
│   │   ├── file_handler.py         # Temp files, secure delete, dialogs
│   │   └── arabic_utils.py         # RTL text, language detection, i18n
│   │
│   └── assets/                      # 🎨 Static resources
│       └── (icons, fonts)
│
└── tesseract/                         # 🧠 Tesseract OCR engine and data (bundled)
    ├── tesseract.exe                # OCR executable
    └── tessdata/                    # Language files (ara.traineddata)
```

---

## 🔗 Component Dependencies / ترتيب الاعتماديات

```
main.py
  └── app.gui.main_window
        ├── app.gui.pdf_tab
        │     ├── app.gui.widgets
        │     ├── app.gui.workers ──────┐
        │     ├── app.utils.security    │
        │     ├── app.utils.file_handler│
        │     └── app.utils.arabic_utils│
        │                              │
        ├── app.gui.image_tab          │
        │     ├── (same as pdf_tab)    │
        │     └── ...                  │
        │                              │
        ├── app.gui.settings_tab       │
        │     └── app.utils.arabic_utils│
        │                              ▼
        ├── app.core.ocr_engine ◄──── workers.py calls these
        ├── app.core.image_processor ◄─┘
        └── app.gui.styles

  app.core.pdf_processor
    ├── app.core.ocr_engine
    └── app.core.image_processor

  app.core.word_generator
    └── app.utils.arabic_utils
```

**Rule**: `utils/` has NO dependencies on `core/` or `gui/`.
`core/` has NO dependencies on `gui/`. Only `gui/` depends on both.

---

## 🛠️ Technology Stack / المكتبات

| Component | Library | Version | License | Purpose |
|-----------|---------|---------|---------|---------|
| OCR Engine | Tesseract | 5.x | Apache 2.0 | Text recognition (Arabic+English) |
| Deep Learning | pytesseract | 0.3.13 | GPL | Python wrapper for Tesseract |
| PDF Reading | PyMuPDF | 1.25.5 | AGPL | PDF → image conversion |
| Word Writing | python-docx | 1.1.2 | MIT | .docx file creation |
| Image Processing | OpenCV | 4.10.0 | Apache 2.0 | Image enhancement for OCR |
| GUI Framework | PySide6 | 6.8.3 | LGPL | Desktop UI with native RTL |
| Arabic RTL | arabic-reshaper | 3.0.0 | MIT | Arabic character joining (UI only) |
| BiDi Text | python-bidi | 0.6.6 | LGPL | RTL text ordering (UI only) |
| Image Utils | Pillow | 11.2.1 | HPND | Image format conversion |

---

## 🔒 Security Design / تصميم الأمان

See [SECURITY.md](SECURITY.md) for the complete security policy.

**Core Principles**:
1. **Air-gapped by design** - Zero network imports, zero HTTP calls
2. **Input paranoia** - Every file is validated (magic bytes, size, extension)
3. **Secure cleanup** - 3-pass zero-overwrite before deletion of temp files
4. **Error masking** - No stack traces or system paths in user-facing errors
5. **Least privilege** - No admin rights, no Registry writes
6. **Pinned deps** - All library versions frozen to prevent supply-chain attacks
7. **No telemetry** - No analytics, no crash reporting, no usage tracking
8. **RAM Protection** - Giant images (>4000px) are downscaled to prevent OOM DOS attacks
9. **PDF Size Limits** - PDFs > 500MB are rejected to prevent system freezes

---

## 🌐 i18n Design / نظام الترجمة

The app uses a dictionary-based translation system in `arabic_utils.py`:

```python
from app.utils.arabic_utils import tr

# Usage:
label.setText(tr('start_conversion', 'ar'))  # → "بدء التحويل"
label.setText(tr('start_conversion', 'en'))  # → "Start Conversion"
```

**Adding new translations**: Add keys to `TRANSLATIONS` dict in `arabic_utils.py`.

**RTL Layout**: Handled by PySide6's native `setLayoutDirection(Qt.RightToLeft)`.

---

## 📊 Data Flow / تدفق البيانات

### PDF → Word Flow:
```
User selects PDF → security.validate_file_integrity()
                 → PDFProcessor.open_pdf()
                 → For each page:
                     → has_text_layer()? → extract_digital_text() (fast, no OCR)
                     → No text layer?    → page_to_image(300 DPI)
                                         → ImageProcessor.enhance_for_ocr()
                                         → OCREngine.extract_text_simple()
                 → WordGenerator.add_page_text() (auto RTL detection)
                 → WordGenerator.save() → User picks save location
                 → TempFileManager.cleanup() (secure delete)
```

### Image → Word Flow:
```
User drops images → security.validate_file_integrity() for each
                  → ImageProcessor.load_and_preprocess()
                  → OCREngine.extract_text_simple()
                  → WordGenerator.add_page_text()
                  → WordGenerator.save()
                  → TempFileManager.cleanup()
```

---

## 📦 Portable Build System / نظام بناء النسخة المحمولة

The `build_portable.bat` script generates a 100% self-contained standalone folder (`dist/Portable_SmartDocConverter`) that can be executed on any offline machine without installation.

**Build Workflow**:
1. **Offline-First Python**: Checks for `python-embed.zip` locally. Downloads it only if missing, then caches it for future offline builds.
2. **Tesseract Bundling**: Copies the full `Tesseract-OCR` engine and Arabic language packs from the developer's machine to the portable folder.
3. **App Code & Assets**: Copies the `app/` directory, `main.py`, and custom icons.
4. **VBScript Shortcut Gen**: Automatically generates an `.ico` file using PIL and runs a VBScript to create a Windows Shortcut (`Smart Document Converter.lnk`) with the custom golden logo, pointing to `Run_Program.bat`.

**Execution Constraints (Pythonw Bug Fix)**:
- Windows `pythonw.exe` lacks standard console handles (`stdin`), causing `pytesseract.get_languages()` to crash with `WinError 6`.
- We bypass this bug in `ocr_engine.py` by manually scanning the `tessdata` directory instead of using `pytesseract`'s broken internal subprocess checks.
- The taskbar icon is forced by combining `AppUserModelID` and explicit `setWindowIcon` on `MainWindow`.

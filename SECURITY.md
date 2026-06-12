# 🔒 Security Policy - سياسة الأمان

## ⚠️ CRITICAL: This application handles SENSITIVE GOVERNMENT DATA

This document defines the security requirements, constraints, and guidelines
for the Smart Document Converter. **ALL contributors MUST read and follow this policy.**

---

## 1. Core Security Principles / المبادئ الأساسية

### 1.1 🚫 ZERO Network Access (عدم الاتصال بالشبكة مطلقاً)

**Rule**: The application MUST NEVER make any network connection of any kind.

**Enforcement**:
- No `import requests`, `urllib`, `http`, `socket`, `ssl`, `ftplib`, `smtplib`
- No `pip install` at runtime
- No update checking mechanisms
- No telemetry, analytics, or crash reporting
- No cloud API calls (no Google, no Azure, no AWS)
- `security.verify_no_network_imports()` runs at startup to detect violations
- Tesseract OCR engine and language data must be bundled with the portable app
- No EasyOCR or PyTorch dependencies (removed for security and size reduction)

**Verification**: Run Wireshark or `netstat` while the app is running — zero traffic expected.

### 1.2 🔐 No Data Persistence (عدم تخزين البيانات)

**Rule**: The application MUST NOT store any content from processed documents.

- No database (SQLite, etc.)
- No log files containing document text
- No cache files with extracted content
- No "recent files" history with file contents
- Settings file (`settings.json`) stores ONLY UI preferences, never document data
- Console logging shows only operation status, never document content

### 1.3 🗑️ Secure Temporary File Handling (إدارة آمنة للملفات المؤقتة)

**Rule**: All temporary files MUST be securely deleted after processing.

- `TempFileManager` creates temp files in system `%TEMP%` directory
- After processing, files are overwritten with zeros (3 passes)
- `atexit` handler ensures cleanup even on crash
- `MainWindow.closeEvent()` triggers cleanup on normal exit

### 1.4 🛡️ Input Validation (التحقق من المدخلات)

**Rule**: Every file MUST be validated before processing.

Validation chain (`security.validate_file_integrity()`):
1. **Existence check** — File must exist and be a file (not directory)
2. **Extension check** — Must be in allowed list (.pdf, .png, .jpg, etc.)
3. **Size check** — Must be < 500MB (prevents decompression bombs)
4. **Magic bytes check** — File header must match expected type
5. **Cross-validation** — Extension must match actual content type

**If any check fails**: Processing is REJECTED with a safe error message.

### 1.5 🔇 Error Masking (إخفاء تفاصيل الأخطاء)

**Rule**: User-facing errors MUST NOT contain system information.

- No stack traces shown to user
- No file paths from system directories
- No Python version or OS details
- `security.sanitize_error_message()` converts exceptions to safe messages
- Internal errors logged to console only (for developer debugging)

### 1.6 ⚡ Least Privilege (أقل صلاحيات)

**Rule**: The application runs with minimal permissions.

- Does NOT require Administrator/root privileges
- Does NOT write to Windows Registry
- Does NOT modify system files
- Does NOT install system-wide services
- Does NOT auto-start with Windows
- Only accesses files the user explicitly selects

---

## 2. Dependency Security / أمان المكتبات

### 2.1 Version Pinning (تثبيت الإصدارات)

**Rule**: ALL dependency versions MUST be pinned exactly in `requirements.txt`.

```
# ✅ CORRECT - pinned version
pytesseract==0.3.13
PyMuPDF==1.25.5

# ❌ WRONG - floating version (NEVER do this)
easyocr>=1.7
torch
```

### 2.2 No Runtime Downloads (عدم التحميل أثناء التشغيل)

- All pip packages bundled inside the portable Python environment
- Tesseract OCR engine (`tesseract.exe` and `tessdata/`) bundled in the portable app

### 2.3 Dependency Audit (فحص المكتبات)

Before deployment, run:
```bash
pip-audit                    # Check for known vulnerabilities
pip list --outdated          # Review (but don't auto-update!)
```

### 2.4 Allowed Libraries Only (المكتبات المسموح بها فقط)

| Status | Library | Reason |
|--------|---------|--------|
| ✅ Allowed | pytesseract, OpenCV | OCR wrapper & image processing |
| ✅ Allowed | PyMuPDF | PDF processing |
| ✅ Allowed | python-docx | Word generation |
| ✅ Allowed | opencv-python-headless | Image processing |
| ✅ Allowed | PySide6 | GUI framework |
| ✅ Allowed | arabic-reshaper, python-bidi | Arabic text |
| ✅ Allowed | Pillow | Image utilities |
| ❌ BANNED | requests, urllib3, httpx | Network libraries |
| ❌ BANNED | flask, django, fastapi | Web frameworks |
| ❌ BANNED | boto3, azure-*, google-cloud-* | Cloud SDKs |
| ❌ BANNED | sentry-sdk, bugsnag | Error reporting |
| ❌ BANNED | analytics-python, mixpanel | Analytics |



---

## 4. Threat Model / نموذج التهديدات

| Threat | Mitigation |
|--------|------------|
| Malicious file upload | Magic bytes validation, size limits |
| Data exfiltration | Zero network access, no telemetry |
| Temp file recovery | 3-pass zero overwrite before deletion |
| Code reverse engineering | PyInstaller bundling (optional: PyArmor) |
| Supply chain attack | Pinned versions, no runtime downloads |
| Memory dump | No persistent sensitive data in memory |
| Privilege escalation | Runs as standard user, no admin rights |
| Error info leak | Sanitized error messages, no stack traces |

---

## 5. Deployment Checklist / قائمة التحقق للنشر

Before deploying to sensitive machines:

- [ ] Verify `requirements.txt` has all versions pinned
- [ ] Run `pip-audit` — zero vulnerabilities
- [ ] Test with network cable unplugged — app works fully
- [ ] Monitor with Task Manager → Network tab — zero traffic
- [ ] Verify temp files are deleted after conversion
- [ ] Verify `settings.json` contains no document content
- [ ] Test with malicious file (wrong extension) — rejected
- [ ] Test with large file (>500MB) — rejected
- [ ] Verify no admin prompt appears on launch
- [ ] Build with PyInstaller and test the .exe

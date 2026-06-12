"""
Security Module - وحدة الأمان
=============================
فحوصات أمان شاملة لحماية البيانات الحساسة.
لا يوجد أي اتصال بالإنترنت - كل شيء يعمل محلياً.
"""

import os
import struct
import tempfile
import logging

logger = logging.getLogger(__name__)

# ============================================
# Magic Bytes للتحقق من نوع الملف الحقيقي
# ============================================
MAGIC_BYTES = {
    # PDF
    b'%PDF': 'pdf',
    # PNG
    b'\x89PNG': 'png',
    # JPEG
    b'\xff\xd8\xff': 'jpeg',
    # BMP
    b'BM': 'bmp',
    # TIFF (Little Endian)
    b'II\x2a\x00': 'tiff',
    # TIFF (Big Endian)
    b'MM\x00\x2a': 'tiff',
    # WebP
    b'RIFF': 'webp',  # followed by ....WEBP
}

# الامتدادات المسموح بها
ALLOWED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp'}
ALLOWED_PDF_EXTENSIONS = {'.pdf'}
ALLOWED_ALL_EXTENSIONS = ALLOWED_IMAGE_EXTENSIONS | ALLOWED_PDF_EXTENSIONS

# الحد الأقصى لحجم الملف (500 ميجابايت)
MAX_FILE_SIZE_MB = 500
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


def validate_file_exists(file_path: str) -> tuple:
    """
    التحقق من وجود الملف.
    Returns: (is_valid: bool, message: str)
    """
    if not file_path:
        return False, "لم يتم تحديد ملف / No file specified"
    
    if not os.path.exists(file_path):
        return False, "الملف غير موجود / File not found"
    
    if not os.path.isfile(file_path):
        return False, "المسار ليس ملفاً / Path is not a file"
    
    return True, "OK"


def validate_file_extension(file_path: str, allowed_extensions: set = None) -> tuple:
    """
    التحقق من امتداد الملف.
    Returns: (is_valid: bool, message: str)
    """
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_ALL_EXTENSIONS
    
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    if ext not in allowed_extensions:
        allowed = ', '.join(sorted(allowed_extensions))
        return False, f"نوع الملف غير مدعوم. الأنواع المسموحة: {allowed}"
    
    return True, "OK"


def validate_file_size(file_path: str, max_size_mb: int = MAX_FILE_SIZE_MB) -> tuple:
    """
    التحقق من حجم الملف لمنع ملفات مفخخة (decompression bombs).
    Returns: (is_valid: bool, message: str)
    """
    try:
        file_size = os.path.getsize(file_path)
        max_bytes = max_size_mb * 1024 * 1024
        
        if file_size == 0:
            return False, "الملف فارغ / File is empty"
        
        if file_size > max_bytes:
            size_mb = file_size / (1024 * 1024)
            return False, f"حجم الملف ({size_mb:.1f}MB) يتجاوز الحد المسموح ({max_size_mb}MB)"
        
        return True, "OK"
    except OSError:
        return False, "لا يمكن قراءة حجم الملف / Cannot read file size"


def check_magic_bytes(file_path: str) -> tuple:
    """
    التحقق من نوع الملف الحقيقي عبر Magic Bytes (وليس الامتداد فقط).
    هذا يمنع الملفات الخبيثة المتنكرة بامتداد مزيف.
    Returns: (detected_type: str or None, message: str)
    """
    try:
        with open(file_path, 'rb') as f:
            header = f.read(16)  # قراءة أول 16 بايت
        
        if len(header) < 2:
            return None, "الملف صغير جداً / File too small"
        
        # فحص Magic Bytes
        for magic, file_type in MAGIC_BYTES.items():
            if header.startswith(magic):
                # فحص إضافي لـ WebP
                if file_type == 'webp' and len(header) >= 12:
                    if header[8:12] != b'WEBP':
                        continue
                return file_type, "OK"
        
        return None, "نوع الملف غير معروف / Unknown file type"
    except OSError:
        return None, "لا يمكن قراءة الملف / Cannot read file"


def validate_file_integrity(file_path: str, expected_type: str = None) -> tuple:
    """
    فحص شامل لسلامة الملف:
    1. التحقق من الوجود
    2. التحقق من الامتداد
    3. التحقق من الحجم
    4. التحقق من Magic Bytes
    5. التحقق من تطابق الامتداد مع المحتوى الحقيقي
    
    Returns: (is_valid: bool, message: str)
    """
    # 1. وجود الملف
    valid, msg = validate_file_exists(file_path)
    if not valid:
        return False, msg
    
    # 2. الامتداد
    if expected_type == 'pdf':
        allowed = ALLOWED_PDF_EXTENSIONS
    elif expected_type == 'image':
        allowed = ALLOWED_IMAGE_EXTENSIONS
    else:
        allowed = ALLOWED_ALL_EXTENSIONS
    
    valid, msg = validate_file_extension(file_path, allowed)
    if not valid:
        return False, msg
    
    # 3. الحجم
    valid, msg = validate_file_size(file_path)
    if not valid:
        return False, msg
    
    # 4. Magic Bytes
    detected_type, msg = check_magic_bytes(file_path)
    if detected_type is None:
        return False, f"فشل فحص محتوى الملف: {msg}"
    
    # 5. تطابق الامتداد مع المحتوى
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()
    
    ext_to_type = {
        '.pdf': 'pdf',
        '.png': 'png',
        '.jpg': 'jpeg', '.jpeg': 'jpeg',
        '.bmp': 'bmp',
        '.tiff': 'tiff', '.tif': 'tiff',
        '.webp': 'webp',
    }
    
    expected_content_type = ext_to_type.get(ext)
    if expected_content_type and expected_content_type != detected_type:
        return False, (
            f"تحذير أمني: امتداد الملف ({ext}) لا يتطابق مع محتواه الحقيقي ({detected_type}). "
            f"قد يكون ملف خبيث!"
        )
    
    return True, "OK"


def secure_delete_file(file_path: str) -> bool:
    """
    حذف آمن للملف: الكتابة فوقه بأصفار قبل الحذف.
    هذا يمنع استعادة البيانات من القرص.
    """
    try:
        if not os.path.exists(file_path):
            return True
        
        # الكتابة فوق الملف بأصفار
        file_size = os.path.getsize(file_path)
        if file_size > 0:
            with open(file_path, 'wb') as f:
                # كتابة أصفار على 3 مراحل
                chunk_size = min(file_size, 1024 * 1024)  # 1MB chunks
                zeros = b'\x00' * chunk_size
                
                for _pass in range(3):  # 3 passes للأمان
                    f.seek(0)
                    remaining = file_size
                    while remaining > 0:
                        write_size = min(remaining, chunk_size)
                        f.write(zeros[:write_size])
                        remaining -= write_size
                    f.flush()
                    os.fsync(f.fileno())
        
        # حذف الملف
        os.remove(file_path)
        return True
    except OSError as e:
        logger.error(f"فشل الحذف الآمن: {type(e).__name__}")
        # محاولة حذف عادي كحل أخير
        try:
            os.remove(file_path)
        except OSError:
            pass
        return False


def secure_delete_directory(dir_path: str) -> bool:
    """
    حذف آمن لمجلد كامل ومحتوياته.
    """
    try:
        if not os.path.exists(dir_path):
            return True
        
        # حذف كل الملفات أولاً
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for name in files:
                secure_delete_file(os.path.join(root, name))
            for name in dirs:
                try:
                    os.rmdir(os.path.join(root, name))
                except OSError:
                    pass
        
        # حذف المجلد الرئيسي
        try:
            os.rmdir(dir_path)
        except OSError:
            pass
        
        return True
    except OSError as e:
        logger.error(f"فشل حذف المجلد: {type(e).__name__}")
        return False


def sanitize_error_message(error: Exception) -> str:
    """
    تنظيف رسائل الخطأ لإخفاء تفاصيل النظام الحساسة.
    لا نعرض stack traces أو مسارات نظامية.
    """
    error_type = type(error).__name__
    
    # رسائل آمنة عامة
    safe_messages = {
        'FileNotFoundError': 'الملف غير موجود / File not found',
        'PermissionError': 'لا توجد صلاحيات كافية / Insufficient permissions',
        'IsADirectoryError': 'المسار مجلد وليس ملف / Path is a directory',
        'OSError': 'خطأ في الوصول للملف / File access error',
        'MemoryError': 'الذاكرة غير كافية / Insufficient memory',
        'ValueError': 'قيمة غير صالحة / Invalid value',
    }
    
    return safe_messages.get(error_type, 'حدث خطأ غير متوقع / An unexpected error occurred')


def verify_no_network_imports():
    """
    التحقق من أن البرنامج لا يستورد مكتبات شبكية.
    يُستدعى عند بدء التشغيل.
    """
    import sys
    network_modules = [
        'http', 'urllib', 'requests', 'socket', 
        'ftplib', 'smtplib', 'xmlrpc', 'httplib2',
        'aiohttp', 'websocket', 'ssl'
    ]
    
    warnings = []
    for mod_name in network_modules:
        if mod_name in sys.modules:
            warnings.append(mod_name)
    
    if warnings:
        logger.warning(
            f"تحذير أمني: تم رصد مكتبات شبكية محملة: {', '.join(warnings)}"
        )
    
    return len(warnings) == 0

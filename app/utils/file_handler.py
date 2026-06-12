"""
File Handler - إدارة الملفات الآمنة
====================================
إدارة الملفات المؤقتة والحذف الآمن.
"""

import os
import tempfile
import atexit
import logging

from app.utils.security import secure_delete_file, secure_delete_directory

logger = logging.getLogger(__name__)


class TempFileManager:
    """
    مدير الملفات المؤقتة - يضمن حذفها الآمن عند الانتهاء.
    يُنشئ مجلد مؤقت خاص بالبرنامج ويحذفه تلقائياً.
    """
    
    def __init__(self):
        self._temp_dir = None
        self._temp_files = []
        # تسجيل الحذف التلقائي عند إغلاق البرنامج
        atexit.register(self.cleanup)
    
    @property
    def temp_dir(self) -> str:
        """إنشاء وإرجاع مسار المجلد المؤقت."""
        if self._temp_dir is None or not os.path.exists(self._temp_dir):
            self._temp_dir = tempfile.mkdtemp(prefix='sdc_')
            logger.debug(f"تم إنشاء مجلد مؤقت")
        return self._temp_dir
    
    def get_temp_path(self, suffix: str = '.tmp') -> str:
        """إنشاء مسار ملف مؤقت جديد."""
        fd, path = tempfile.mkstemp(suffix=suffix, dir=self.temp_dir)
        os.close(fd)
        self._temp_files.append(path)
        return path
    
    def register_temp_file(self, file_path: str):
        """تسجيل ملف مؤقت للحذف لاحقاً."""
        if file_path not in self._temp_files:
            self._temp_files.append(file_path)
    
    def delete_temp_file(self, file_path: str) -> bool:
        """حذف ملف مؤقت بشكل آمن."""
        result = secure_delete_file(file_path)
        if file_path in self._temp_files:
            self._temp_files.remove(file_path)
        return result
    
    def cleanup(self):
        """حذف جميع الملفات المؤقتة والمجلد المؤقت بشكل آمن."""
        logger.debug("تنظيف الملفات المؤقتة...")
        
        # حذف الملفات المسجلة
        for f in list(self._temp_files):
            secure_delete_file(f)
        self._temp_files.clear()
        
        # حذف المجلد المؤقت
        if self._temp_dir and os.path.exists(self._temp_dir):
            secure_delete_directory(self._temp_dir)
            self._temp_dir = None
        
        logger.debug("تم تنظيف الملفات المؤقتة بنجاح")


# مدير ملفات مؤقتة عام (singleton)
_global_temp_manager = None


def get_temp_manager() -> TempFileManager:
    """الحصول على مدير الملفات المؤقتة العام."""
    global _global_temp_manager
    if _global_temp_manager is None:
        _global_temp_manager = TempFileManager()
    return _global_temp_manager


def get_supported_image_filters(language: str = 'ar') -> str:
    """إرجاع فلاتر الصور لـ QFileDialog."""
    if language == 'ar':
        return (
            "كل الصور المدعومة (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp);;"
            "PNG (*.png);;"
            "JPEG (*.jpg *.jpeg);;"
            "BMP (*.bmp);;"
            "TIFF (*.tiff *.tif);;"
            "WebP (*.webp);;"
            "كل الملفات (*.*)"
        )
    else:
        return (
            "All Supported Images (*.png *.jpg *.jpeg *.bmp *.tiff *.tif *.webp);;"
            "PNG (*.png);;"
            "JPEG (*.jpg *.jpeg);;"
            "BMP (*.bmp);;"
            "TIFF (*.tiff *.tif);;"
            "WebP (*.webp);;"
            "All Files (*.*)"
        )


def get_supported_pdf_filters(language: str = 'ar') -> str:
    """إرجاع فلاتر PDF لـ QFileDialog."""
    if language == 'ar':
        return "ملفات PDF (*.pdf);;كل الملفات (*.*)"
    else:
        return "PDF Files (*.pdf);;All Files (*.*)"


def get_word_save_filter(language: str = 'ar') -> str:
    """إرجاع فلتر حفظ Word لـ QFileDialog."""
    if language == 'ar':
        return "مستند Word (*.docx)"
    else:
        return "Word Document (*.docx)"


def ensure_docx_extension(file_path: str) -> str:
    """التأكد من أن الملف ينتهي بـ .docx"""
    if not file_path.lower().endswith('.docx'):
        file_path += '.docx'
    return file_path

"""
Smart Document Converter - محوّل المستندات الذكي
==================================================
نقطة البدء الرئيسية للبرنامج.

🔒 آمن بالكامل - يعمل أوفلاين بدون إنترنت
📄 تحويل PDF إلى Word
🖼️ تحويل الصور إلى Word
🌐 يدعم العربي والإنجليزي
"""

import sys
import os
import logging

# ============================================
# إعداد المسارات
# ============================================
# التأكد من أن مسار المشروع في Python path
APP_DIR = os.path.dirname(os.path.abspath(__file__))
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)


# ============================================
# إعداد التسجيل (Logging)
# ============================================
def setup_logging():
    """إعداد نظام التسجيل - بدون تخزين محتوى الملفات."""
    log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    
    # تسجيل في الكونسول فقط (لا ملفات log لأسباب أمنية)
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[logging.StreamHandler()]
    )
    
    # تقليل ضوضاء المكتبات
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('easyocr').setLevel(logging.WARNING)
    logging.getLogger('torch').setLevel(logging.WARNING)


# ============================================
# نقطة البدء
# ============================================
def main():
    """تشغيل البرنامج."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 50)
    logger.info("محوّل المستندات الذكي - Smart Document Converter")
    logger.info("الإصدار: 1.0.0")
    logger.info("الوضع: آمن - أوفلاين")
    logger.info("=" * 50)
    
    # ============================================
    # فحص الأمان عند البدء
    # ============================================
    from app.utils.security import verify_no_network_imports
    
    # ============================================
    # إنشاء تطبيق Qt
    # ============================================
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    
    # منع تكرار التطبيق
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # إعدادات عامة
    app.setApplicationName("Smart Document Converter")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SDC")
    
    # خط افتراضي
    default_font = QFont("Segoe UI", 11)
    app.setFont(default_font)
    
    # ============================================
    # إنشاء وعرض النافذة الرئيسية
    # ============================================
    from app.gui.main_window import MainWindow
    
    window = MainWindow()
    window.show()
    
    logger.info("البرنامج يعمل بنجاح ✓")
    
    # ============================================
    # حلقة الأحداث الرئيسية
    # ============================================
    exit_code = app.exec()
    
    # ============================================
    # تنظيف عند الإغلاق
    # ============================================
    logger.info("جاري الإغلاق...")
    
    # تنظيف الملفات المؤقتة
    from app.utils.file_handler import get_temp_manager
    get_temp_manager().cleanup()
    
    # فحص أمان نهائي
    verify_no_network_imports()
    
    logger.info("تم الإغلاق بنجاح ✓")
    sys.exit(exit_code)


if __name__ == '__main__':
    main()

"""
Arabic Utilities - أدوات اللغة العربية
=======================================
أدوات لمعالجة النص العربي RTL والكشف عن اللغة.
arabic-reshaper و python-bidi تُستخدم فقط لعرض النص في واجهة البرنامج.
ملفات Word تستخدم RTL المدمج أصلاً في python-docx.
"""

import re
import unicodedata

# محاولة استيراد مكتبات RTL
try:
    import arabic_reshaper
    HAS_RESHAPER = True
except ImportError:
    HAS_RESHAPER = False

try:
    from bidi.algorithm import get_display
    HAS_BIDI = True
except ImportError:
    HAS_BIDI = False


# نطاقات Unicode للحروف العربية
ARABIC_RANGE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
ENGLISH_RANGE = re.compile(r'[a-zA-Z]')
DIGIT_RANGE = re.compile(r'[0-9\u0660-\u0669\u06F0-\u06F9]')


def reshape_for_display(text: str) -> str:
    """
    تشكيل النص العربي للعرض في واجهة البرنامج.
    هذا ضروري لأن بعض widgets لا تدعم RTL أصلاً.
    
    ⚠️ لا تستخدم هذا لملفات Word - Word يدعم RTL أصلاً.
    """
    if not text or not text.strip():
        return text
    
    if not is_arabic(text):
        return text
    
    try:
        if HAS_RESHAPER:
            reshaped = arabic_reshaper.reshape(text)
            if HAS_BIDI:
                return get_display(reshaped)
            return reshaped
    except Exception:
        pass
    
    return text


def detect_language(text: str) -> str:
    """
    كشف اللغة الرئيسية في النص.
    
    Returns:
        'ar' - عربي
        'en' - إنجليزي
        'mixed' - مختلط
        'unknown' - غير معروف
    """
    if not text or not text.strip():
        return 'unknown'
    
    # إزالة المسافات والأرقام وعلامات الترقيم
    clean_text = re.sub(r'[\s\d\W]', '', text)
    
    if not clean_text:
        return 'unknown'
    
    arabic_count = len(ARABIC_RANGE.findall(clean_text))
    english_count = len(ENGLISH_RANGE.findall(clean_text))
    total = arabic_count + english_count
    
    if total == 0:
        return 'unknown'
    
    arabic_ratio = arabic_count / total
    english_ratio = english_count / total
    
    if arabic_ratio > 0.7:
        return 'ar'
    elif english_ratio > 0.7:
        return 'en'
    elif arabic_count > 0 and english_count > 0:
        return 'mixed'
    elif arabic_count > 0:
        return 'ar'
    elif english_count > 0:
        return 'en'
    else:
        return 'unknown'


def is_arabic(text: str) -> bool:
    """التحقق من احتواء النص على حروف عربية."""
    return bool(ARABIC_RANGE.search(text)) if text else False


def is_english(text: str) -> bool:
    """التحقق من احتواء النص على حروف إنجليزية."""
    return bool(ENGLISH_RANGE.search(text)) if text else False


def normalize_arabic_text(text: str) -> str:
    """
    تنظيف وتطبيع النص العربي المستخرج من OCR.
    - إزالة أحرف التحكم غير المرئية
    - تصحيح المسافات الزائدة
    - تطبيع الأحرف العربية الشائعة
    """
    if not text:
        return text
    
    # إزالة أحرف التحكم (لكن ليس السطر الجديد والتاب)
    text = ''.join(
        char for char in text
        if not unicodedata.category(char).startswith('C')
        or char in '\n\r\t'
    )
    
    # تصحيح المسافات الزائدة
    text = re.sub(r' +', ' ', text)
    
    # تصحيح أسطر فارغة زائدة
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # إزالة مسافات في بداية ونهاية كل سطر
    lines = text.split('\n')
    lines = [line.strip() for line in lines]
    text = '\n'.join(lines)
    
    # توحيد الأرقام المشرقية (٠١٢٣) إلى أرقام قياسية (0123) للحفاظ على تنسيق التواريخ والقوائم
    text = convert_arabic_numerals(text)
    
    return text.strip()


def convert_arabic_numerals(text: str) -> str:
    """
    تحويل الأرقام العربية الشرقية (٠١٢...) إلى غربية (012...).
    """
    arabic_to_western = {
        '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
        '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9',
        '۰': '0', '۱': '1', '۲': '2', '۳': '3', '۴': '4',
        '۵': '5', '۶': '6', '۷': '7', '۸': '8', '۹': '9',
    }
    
    for ar_digit, en_digit in arabic_to_western.items():
        text = text.replace(ar_digit, en_digit)
    
    return text


def get_text_direction(text: str) -> str:
    """
    تحديد اتجاه النص (RTL أو LTR).
    مفيد لضبط محاذاة الفقرات في Word.
    """
    lang = detect_language(text)
    if lang in ('ar', 'mixed'):
        return 'rtl'
    return 'ltr'


# ============================================
# نظام الترجمة (i18n) - ثنائي اللغة
# ============================================
TRANSLATIONS = {
    'ar': {
        # العنوان
        'app_title': 'محوّل المستندات الذكي',
        'app_subtitle': 'تحويل PDF والصور إلى Word بدقة عالية',
        
        # التبويبات
        'tab_pdf': 'تحويل PDF',
        'tab_images': 'تحويل الصور',
        'tab_settings': 'الإعدادات',
        
        # تبويب PDF
        'select_pdf': 'اختيار ملف PDF',
        'select_pdfs': 'اختيار ملفات PDF',
        'pdf_pages': 'عدد الصفحات',
        'convert_all': 'تحويل الكل',
        'select_pages': 'اختيار صفحات',
        'start_conversion': 'بدء التحويل',
        'stop_conversion': 'إيقاف التحويل',
        
        # تبويب الصور
        'select_images': 'اختيار صور',
        'select_folder': 'اختيار مجلد',
        'drag_drop': 'اسحب وأفلت الصور هنا\nأو اضغط لاختيار الملفات',
        'images_count': 'عدد الصور',
        
        # مشترك
        'save_as': 'حفظ باسم',
        'save_location': 'مكان الحفظ',
        'browse': 'تصفح...',
        'converting': 'جاري التحويل...',
        'progress': 'التقدم',
        'completed': 'تم بنجاح!',
        'failed': 'فشل التحويل',
        'cancel': 'إلغاء',
        'close': 'إغلاق',
        'open_file': 'فتح الملف',
        'open_folder': 'فتح المجلد',
        'page': 'صفحة',
        'of': 'من',
        'processing_page': 'جاري معالجة الصفحة',
        
        # الإعدادات
        'language': 'اللغة',
        'ocr_language': 'لغة التعرف (OCR)',
        'arabic_only': 'عربي فقط',
        'english_only': 'إنجليزي فقط',
        'both_languages': 'عربي وإنجليزي',
        'ocr_quality': 'جودة التعرف',
        'quality_fast': 'سريع',
        'quality_balanced': 'متوازن',
        'quality_high': 'عالي الدقة',
        'default_save_path': 'مسار الحفظ الافتراضي',
        'font_name': 'نوع الخط',
        'font_size': 'حجم الخط',
        'handwriting_mode': 'وضع الخط اليدوي',
        'preprocessing': 'معالجة الصور المسبقة',
        'reset_settings': 'إعادة تعيين',
        'settings_saved': 'تم حفظ الإعدادات',
        'interface_language': 'لغة الواجهة',
        
        # الحالة
        'ready': 'جاهز',
        'loading_ocr': 'جاري تحميل محرك التعرف...',
        'ocr_loaded': 'محرك التعرف جاهز',
        'no_file_selected': 'لم يتم اختيار ملف',
        'file_saved': 'تم حفظ الملف بنجاح',
        'security_warning': 'تحذير أمني',
        'invalid_file': 'ملف غير صالح',
    },
    'en': {
        # Title
        'app_title': 'Smart Document Converter',
        'app_subtitle': 'Convert PDF & Images to Word with high accuracy',
        
        # Tabs
        'tab_pdf': 'PDF Conversion',
        'tab_images': 'Image Conversion',
        'tab_settings': 'Settings',
        
        # PDF Tab
        'select_pdf': 'Select PDF File',
        'select_pdfs': 'Select PDF Files',
        'pdf_pages': 'Number of Pages',
        'convert_all': 'Convert All',
        'select_pages': 'Select Pages',
        'start_conversion': 'Start Conversion',
        'stop_conversion': 'Stop Conversion',
        
        # Image Tab
        'select_images': 'Select Images',
        'select_folder': 'Select Folder',
        'drag_drop': 'Drag & Drop images here\nor click to select files',
        'images_count': 'Number of Images',
        
        # Common
        'save_as': 'Save As',
        'save_location': 'Save Location',
        'browse': 'Browse...',
        'converting': 'Converting...',
        'progress': 'Progress',
        'completed': 'Completed Successfully!',
        'failed': 'Conversion Failed',
        'cancel': 'Cancel',
        'close': 'Close',
        'open_file': 'Open File',
        'open_folder': 'Open Folder',
        'page': 'Page',
        'of': 'of',
        'processing_page': 'Processing page',
        
        # Settings
        'language': 'Language',
        'ocr_language': 'OCR Language',
        'arabic_only': 'Arabic Only',
        'english_only': 'English Only',
        'both_languages': 'Arabic & English',
        'ocr_quality': 'OCR Quality',
        'quality_fast': 'Fast',
        'quality_balanced': 'Balanced',
        'quality_high': 'High Accuracy',
        'default_save_path': 'Default Save Path',
        'font_name': 'Font Name',
        'font_size': 'Font Size',
        'handwriting_mode': 'Handwriting Mode',
        'preprocessing': 'Image Preprocessing',
        'reset_settings': 'Reset Settings',
        'settings_saved': 'Settings Saved',
        'interface_language': 'Interface Language',
        
        # Status
        'ready': 'Ready',
        'loading_ocr': 'Loading OCR engine...',
        'ocr_loaded': 'OCR engine ready',
        'no_file_selected': 'No file selected',
        'file_saved': 'File saved successfully',
        'security_warning': 'Security Warning',
        'invalid_file': 'Invalid file',
    }
}


def tr(key: str, language: str = 'ar') -> str:
    """
    ترجمة مفتاح نصي حسب اللغة المختارة.
    """
    translations = TRANSLATIONS.get(language, TRANSLATIONS['ar'])
    return translations.get(key, key)

"""
OCR Engine - محرك التعرف على النصوص
=====================================
يستخدم Tesseract OCR مع دعم كامل للعربي والإنجليزي.
يعمل أوفلاين بالكامل - لا يتصل بالإنترنت أبداً.
أسرع وأدق بكثير من EasyOCR للنصوص العربية المطبوعة.
"""

import logging
import os
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class TesseractOCREngine:
    """
    محرك OCR الرئيسي - يستخدم Tesseract.
    يعمل أوفلاين بالكامل، أسرع وأدق للعربي.
    """
    
    def __init__(
        self,
        languages: list = None,
        gpu: bool = False,
        model_dir: str = None
    ):
        """
        تهيئة محرك OCR.
        
        Args:
            languages: قائمة اللغات ['ar', 'en']
            gpu: غير مستخدم (Tesseract يعمل على CPU دائماً وبسرعة عالية)
            model_dir: مسار Tesseract (يُكتشف تلقائياً)
        """
        self.languages = languages or ['ar', 'en']
        self.model_dir = model_dir
        self._tesseract_cmd = None
        self._is_loaded = False
    
    def _find_tesseract(self) -> str:
        """
        البحث عن Tesseract في المواقع المعروفة.
        يبحث أولاً في المجلد المحمول بجانب البرنامج، ثم في مواقع التثبيت.
        """
        import sys
        
        # 1. البحث في المجلد المحمول (بجانب البرنامج)
        base_dirs = [
            os.path.dirname(os.path.abspath(sys.argv[0])),  # مجلد البرنامج
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),  # مجلد app/.
            os.getcwd(),
        ]
        
        for base in base_dirs:
            portable_path = os.path.join(base, 'tesseract', 'tesseract.exe')
            if os.path.isfile(portable_path):
                logger.info(f"Tesseract found (portable): {portable_path}")
                return portable_path
        
        # 2. البحث في مسارات التثبيت المعروفة على Windows
        program_files = [
            os.environ.get('ProgramFiles', r'C:\Program Files'),
            os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)'),
            os.environ.get('LOCALAPPDATA', ''),
        ]
        
        for pf in program_files:
            if not pf:
                continue
            tesseract_path = os.path.join(pf, 'Tesseract-OCR', 'tesseract.exe')
            if os.path.isfile(tesseract_path):
                logger.info(f"Tesseract found (installed): {tesseract_path}")
                return tesseract_path
        
        # 3. البحث في PATH
        import shutil
        path_tesseract = shutil.which('tesseract')
        if path_tesseract:
            logger.info(f"Tesseract found (PATH): {path_tesseract}")
            return path_tesseract
        
        return None
    
    def load(self, progress_callback=None):
        """
        تحميل محرك Tesseract OCR.
        يتم استدعاؤها مرة واحدة عند بدء التشغيل.
        """
        if self._is_loaded:
            return
        
        try:
            if progress_callback:
                progress_callback("جاري تحميل محرك التعرف...")
            
            import pytesseract
            
            # البحث عن Tesseract
            tesseract_path = self._find_tesseract()
            if tesseract_path is None:
                raise FileNotFoundError(
                    "لم يتم العثور على Tesseract OCR. "
                    "يرجى تثبيته أو وضعه في مجلد 'tesseract' بجانب البرنامج."
                )
            
            # حل مشاكل النسخة المحمولة (TESSDATA_PREFIX و PATH)
            tesseract_dir = os.path.dirname(tesseract_path)
            self._tessdata_prefix = os.path.join(tesseract_dir, 'tessdata')
            
            # تحديد TESSDATA_PREFIX في بيئة النظام مباشرة لتجنب مشاكل المسارات العربية في Tesseract
            os.environ['TESSDATA_PREFIX'] = self._tessdata_prefix
            
            # إضافة لمسار النظام لتجاوز مشاكل المسارات العربية في Windows
            if tesseract_dir not in os.environ.get('PATH', ''):
                os.environ['PATH'] = tesseract_dir + os.pathsep + os.environ.get('PATH', '')
            
            # استخدام المسار المباشر، وتخطي مشاكل ترميز Windows
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            self._tesseract_cmd = tesseract_path
            
            # بدلاً من استخدام pytesseract.get_languages() الذي به خطأ (Bug)
            # عند تشغيله من واجهة رسومية (pythonw.exe) بسبب عدم توجيه stdin،
            # نقوم بفحص اللغات المتاحة يدوياً من مجلد tessdata
            available_langs = []
            if os.path.isdir(self._tessdata_prefix):
                for f in os.listdir(self._tessdata_prefix):
                    if f.endswith('.traineddata'):
                        available_langs.append(f.replace('.traineddata', ''))
            
            if not available_langs:
                available_langs = ['ara', 'eng', 'osd'] # اللغات الافتراضية للنسخة المحمولة
                
            logger.info(f"Tesseract languages available: {available_langs}")
            
            # بناء سلسلة اللغات لـ Tesseract
            tess_langs_set = set()
            for lang in self.languages:
                if lang == 'ar':
                    tess_langs_set.add('ara')
                elif lang == 'en':
                    tess_langs_set.add('eng')
                else:
                    tess_langs_set.add(lang)
            
            # ترتيب اللغات: ara ثم eng
            sorted_langs = []
            if 'ara' in tess_langs_set: sorted_langs.append('ara')
            if 'eng' in tess_langs_set: sorted_langs.append('eng')
            for l in tess_langs_set:
                if l not in ['ara', 'eng']: sorted_langs.append(l)
                
            self._tess_lang = '+'.join(sorted_langs)
            
            # التحقق من توفر اللغات المطلوبة
            lang_map = {'ar': 'ara', 'en': 'eng'}
            for lang in self.languages:
                tess_lang = lang_map.get(lang, lang)
                if tess_lang not in available_langs:
                    raise RuntimeError(
                        f"لغة '{tess_lang}' غير متوفرة في Tesseract. "
                        f"اللغات المتاحة: {available_langs}"
                    )
            
            # إصلاح مشكلة pytesseract مع المسارات التي تحتوي على مسافات وحروف عربية على ويندوز
            # pytesseract يستخدم shlex.split مع posix=False مما يبقي علامات التنصيص
            import subprocess
            if not hasattr(pytesseract.pytesseract, '_original_popen'):
                pytesseract.pytesseract._original_popen = pytesseract.pytesseract.subprocess.Popen
                
                def popen_wrapper(*args, **kwargs):
                    cmd_list = list(args[0])
                    for i in range(len(cmd_list)):
                        if cmd_list[i].startswith('"') and cmd_list[i].endswith('"'):
                            cmd_list[i] = cmd_list[i][1:-1]
                    new_args = (cmd_list,) + args[1:]
                    return pytesseract.pytesseract._original_popen(*new_args, **kwargs)
                
                pytesseract.pytesseract.subprocess.Popen = popen_wrapper
            
            # إصلاح جذري لمشكلة UnicodeDecodeError التي تتسبب في توقف البرنامج
            # عندما يقوم Tesseract بطباعة تحذيرات بالعربية في نظام ويندوز
            if not hasattr(pytesseract.pytesseract, '_original_get_errors'):
                pytesseract.pytesseract._original_get_errors = pytesseract.pytesseract.get_errors
                
                def get_errors_wrapper(error_string):
                    try:
                        return pytesseract.pytesseract._original_get_errors(error_string)
                    except UnicodeDecodeError:
                        # في حالة فشل فك التشفير بصيغة utf-8، نستخدم الترميز الافتراضي لويندوز أو نتجاهل الأخطاء
                        return [line for line in error_string.decode('mbcs', errors='replace').splitlines()]
                
                pytesseract.pytesseract.get_errors = get_errors_wrapper
            
            self._is_loaded = True
            
            if progress_callback:
                progress_callback("محرك التعرف جاهز")
            
            logger.info(f"تم تحميل Tesseract بنجاح - اللغات: {self._tess_lang}")
        except Exception as e:
            logger.error(f"فشل تحميل Tesseract: {type(e).__name__}: {e}")
            raise RuntimeError(f"فشل تحميل محرك التعرف على النصوص: {e}") from e
    
    @property
    def is_loaded(self) -> bool:
        """هل تم تحميل المحرك؟"""
        return self._is_loaded
    
    def extract_text(
        self,
        image: np.ndarray,
        detail: int = 1,
        paragraph: bool = True
    ) -> list:
        """
        استخراج النصوص من صورة.
        
        Args:
            image: صورة كمصفوفة NumPy
            detail: مستوى التفاصيل (0=نص فقط، 1=مع إحداثيات)
            paragraph: دمج النصوص في فقرات
        
        Returns:
            قائمة بالنتائج: [{'text', 'bbox', 'confidence'}]
        """
        if not self._is_loaded:
            self.load()
        
        try:
            import pytesseract
            
            # تحويل الصورة لـ PIL إذا لزم الأمر
            if isinstance(image, np.ndarray):
                if len(image.shape) == 2:
                    pil_image = Image.fromarray(image, mode='L')
                else:
                    pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            # إعدادات Tesseract المحسنة للعربي مع دعم المسارات العربية لملفات tessdata
            # تم تعديل psm إلى 6 لمنع تداخل الأرقام والتواريخ العشوائي
            # تم إضافة --dpi 300 لضمان دقة التعرف، وتخطي عكس الألوان (invert=0) لمنع تشوه الأرقام
            tessdata_dir = getattr(self, '_tessdata_prefix', '').replace('\\', '/')
            base_config = r'--dpi 300 --oem 3 --psm 6 -c tessedit_do_invert=0'
            custom_config = f'--tessdata-dir "{tessdata_dir}" {base_config}' if tessdata_dir else base_config
            
            if detail == 0:
                # نص فقط - أبسط وأسرع
                text = pytesseract.image_to_string(
                    pil_image,
                    lang=self._tess_lang,
                    config=custom_config,
                    timeout=180  # 3 دقائق حد أقصى للورقة لمنع التعليق
                )
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                return [{'text': line, 'confidence': 1.0} for line in lines]
            
            # استخراج مع التفاصيل (إحداثيات + ثقة)
            data = pytesseract.image_to_data(
                pil_image,
                lang=self._tess_lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT,
                timeout=180  # 3 دقائق حد أقصى للورقة لمنع التعليق
            )
            
            extracted = []
            n_boxes = len(data['text'])
            
            # تجميع الكلمات في سطور
            current_line = []
            current_line_num = -1
            current_block = -1
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
                # تنظيف الأرقام والحروف المتداخلة
                text = self._post_process_arabic_text(text)
                conf = int(data['conf'][i])
                line_num = data['line_num'][i]
                block_num = data['block_num'][i]
                
                if conf < 0 or not text:
                    # نهاية سطر أو block
                    if current_line:
                        line_text = ' '.join(current_line)
                        extracted.append({
                            'text': line_text,
                            'bbox': [[0, 0], [0, 0], [0, 0], [0, 0]],
                            'confidence': 0.9,
                        })
                        current_line = []
                    continue
                
                if line_num != current_line_num or block_num != current_block:
                    # بداية سطر جديد
                    if current_line:
                        line_text = ' '.join(current_line)
                        extracted.append({
                            'text': line_text,
                            'bbox': [[0, 0], [0, 0], [0, 0], [0, 0]],
                            'confidence': 0.9,
                        })
                        current_line = []
                    current_line_num = line_num
                    current_block = block_num
                
                current_line.append(text)
            
            # آخر سطر
            if current_line:
                line_text = ' '.join(current_line)
                extracted.append({
                    'text': line_text,
                    'bbox': [[0, 0], [0, 0], [0, 0], [0, 0]],
                    'confidence': 0.9,
                })
            
            return extracted
        except Exception as e:
            logger.error(f"فشل استخراج النص: {type(e).__name__}: {e}")
            return []
    
    def extract_text_simple(self, image: np.ndarray) -> str:
        """
        استخراج النص كسلسلة نصية بسيطة.
        الأسهل للاستخدام المباشر.
        """
        if not self._is_loaded:
            self.load()
        
        try:
            import pytesseract
            
            # تحويل الصورة لـ PIL
            if isinstance(image, np.ndarray):
                if len(image.shape) == 2:
                    pil_image = Image.fromarray(image, mode='L')
                else:
                    pil_image = Image.fromarray(image)
            else:
                pil_image = image
            
            # إعدادات Tesseract المحسنة للعربي مع دعم المسارات العربية لملفات tessdata
            # تم تعديل psm إلى 6 لمنع تداخل التواريخ وتكسر الأرقام، وإضافة dpi=300
            tessdata_dir = getattr(self, '_tessdata_prefix', '').replace('\\', '/')
            base_config = r'--dpi 300 --oem 3 --psm 6 -c tessedit_do_invert=0'
            custom_config = f'--tessdata-dir "{tessdata_dir}" {base_config}' if tessdata_dir else base_config
            
            text = pytesseract.image_to_string(
                pil_image,
                lang=self._tess_lang,
                config=custom_config,
                timeout=180  # 3 دقائق حد أقصى للورقة لمنع التعليق
            )
            
            # تنظيف النص مع الحفاظ على الفقرات
            import re
            
            # تنظيف الحروف والأرقام العربية
            text = self._post_process_arabic_text(text)
            
            # إزالة المسافات من أطراف كل سطر
            lines = text.split('\n')
            cleaned_lines = [line.strip() for line in lines]
            text = '\n'.join(cleaned_lines)
            
            # تقليص الأسطر الفارغة المتعددة إلى سطرين (فقرة جديدة)
            text = re.sub(r'\n{3,}', '\n\n', text)
            
            return text.strip()
        except Exception as e:
            logger.error(f"فشل استخراج النص: {type(e).__name__}: {e}")
            return ""
    
    def _sort_by_position(self, results: list) -> list:
        """
        ترتيب النتائج حسب موقعها في الصفحة.
        من أعلى لأسفل، ثم من يمين لشمال (للعربي).
        """
        def sort_key(item):
            bbox = item.get('bbox', [[0, 0]])
            if isinstance(bbox, list) and len(bbox) > 0:
                if isinstance(bbox[0], list):
                    y = bbox[0][1]
                    x = bbox[0][0]
                else:
                    y = bbox[1] if len(bbox) > 1 else 0
                    x = bbox[0]
            else:
                y = 0
                x = 0
            # ترتيب أساسي بالسطر (y) ثم بالعمود (x)
            return (y // 30, x)  # تجميع بنطاق 30 بكسل كسطر واحد
        
        try:
            return sorted(results, key=sort_key)
        except Exception:
            return results
            
    def _post_process_arabic_text(self, text: str) -> str:
        """
        تنظيف ومعالجة النص العربي لإصلاح أخطاء Tesseract الشائعة في الأرقام والحروف.
        """
        if not text:
            return text
            
        import re
        
        # 1. إصلاح التباعد العشوائي بين الحروف
        text = re.sub(r' +', ' ', text)
        
        # 2. إصلاح الخلط الشائع للأرقام الهندية (العربية) مع الحروف
        # رموز غريبة يهذي بها Tesseract للأرقام
        text = text.replace('©', '٥')
        text = text.replace('¥', '٢')
        
        # إذا جاء حرف 'ا' (ألف) بجوار أرقام فهو بنسبة كبيرة رقم '١'
        text = re.sub(r'(?<=[٠-٩])ا', '١', text)
        text = re.sub(r'ا(?=[٠-٩])', '١', text)
        
        # إذا جاء حرف 'ه' أو 'هـ' بجوار أرقام فهو رقم '٥'
        text = re.sub(r'(?<=[٠-٩])ه(?=[٠-٩]|\s)', '٥', text)
        text = re.sub(r'(?<=[٠-٩])هـ(?=[٠-٩]|\s)', '٥', text)
        
        # حرف 'ع' وسط الأرقام قد يكون '٤'
        text = re.sub(r'(?<=[٠-٩])ع(?=[٠-٩]|\s)', '٤', text)
        
        # الخلط بين الصفر الإنجليزي '0' والنقطة أو حرف 'o' أو 'O' وسط الأرقام العربية
        text = re.sub(r'(?<=[0-9])o(?=[0-9]|\s)', '0', text, flags=re.IGNORECASE)
        
        return text
    
    def change_languages(self, languages: list):
        """تغيير اللغات وإعادة تحميل المحرك."""
        if set(languages) != set(self.languages):
            self.languages = languages
            self._is_loaded = False
            self._tesseract_cmd = None
            self.load()
    
    def get_supported_languages(self) -> list:
        """إرجاع قائمة اللغات المدعومة."""
        return ['ar', 'en']


from app.core.windows_ocr import WindowsOCREngine

class OCREngine:
    """
    محرك التوجيه (Router Engine)
    يحاول استخدام محرك الويندوز أولاً لسرعته ودقته الفائقة، 
    وإذا لم يتوفر يعود إلى Tesseract.
    """
    
    def __init__(
        self,
        languages: list = None,
        gpu: bool = False,
        model_dir: str = None
    ):
        self.languages = languages or ['ar', 'en']
        self._is_loaded = False
        self._active_engine = None
        
        # تهيئة المحركات
        self._windows_engine = WindowsOCREngine(languages)
        self._tesseract_engine = TesseractOCREngine(languages, gpu, model_dir)
        
    def load(self, progress_callback=None):
        if self._is_loaded:
            return
            
        # محاولة تحميل Windows OCR أولاً
        try:
            if progress_callback:
                progress_callback("جاري فحص محرك الويندوز الذكي...")
            self._windows_engine.load(progress_callback)
            self._active_engine = self._windows_engine
            self._is_loaded = True
            import logging
            logger = logging.getLogger(__name__)
            logger.info("تم تفعيل محرك الويندوز بنجاح كخيار أساسي.")
            return
        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            error_msg = f"لم يتم تشغيل محرك الويندوز (سيتم استخدام Tesseract بدلاً منه): {e}\n{traceback.format_exc()}"
            logger.warning(error_msg)
            try:
                with open("debug_ocr.txt", "a", encoding="utf-8") as f:
                    f.write(error_msg + "\n")
            except:
                pass
        # إذا فشل الويندوز، استخدم Tesseract
        if progress_callback:
            progress_callback("جاري تحميل محرك Tesseract كبديل...")
        
        self._tesseract_engine.load(progress_callback)
        self._active_engine = self._tesseract_engine
        self._is_loaded = True
        
    @property
    def is_loaded(self) -> bool:
        return self._is_loaded
        
    def extract_text(self, image, detail: int = 1, paragraph: bool = True) -> list:
        if not self._is_loaded:
            self.load()
        return self._active_engine.extract_text(image, detail, paragraph)

    def extract_text_simple(self, image) -> str:
        if not self._is_loaded:
            self.load()
        return self._active_engine.extract_text_simple(image)
        
    def change_languages(self, languages: list):
        self.languages = languages
        self._is_loaded = False
        self._windows_engine.change_languages(languages)
        self._tesseract_engine.change_languages(languages)
        self.load()
        
    def get_supported_languages(self) -> list:
        return ['ar', 'en']

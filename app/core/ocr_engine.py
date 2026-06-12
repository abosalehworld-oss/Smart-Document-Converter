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


class OCREngine:
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
            os.environ['TESSDATA_PREFIX'] = os.path.join(tesseract_dir, 'tessdata')
            
            # إضافة لمسار النظام لتجاوز مشاكل المسارات العربية في Windows
            if tesseract_dir not in os.environ.get('PATH', ''):
                os.environ['PATH'] = tesseract_dir + os.pathsep + os.environ.get('PATH', '')
            
            # استخدام المسار المباشر، وتخطي مشاكل ترميز Windows
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
            self._tesseract_cmd = tesseract_path
            
            # التحقق من أن Tesseract يعمل واللغات متاحة
            available_langs = pytesseract.get_languages()
            logger.info(f"Tesseract languages available: {available_langs}")
            
            # بناء سلسلة اللغات لـ Tesseract
            lang_map = {'ar': 'ara', 'en': 'eng'}
            self._tess_lang = '+'.join(
                lang_map.get(lang, lang) for lang in self.languages
            )
            
            # التحقق من توفر اللغات المطلوبة
            for lang in self.languages:
                tess_lang = lang_map.get(lang, lang)
                if tess_lang not in available_langs:
                    raise RuntimeError(
                        f"لغة '{tess_lang}' غير متوفرة في Tesseract. "
                        f"اللغات المتاحة: {available_langs}"
                    )
            
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
            
            # إعدادات Tesseract المحسنة للعربي
            custom_config = r'--oem 3 --psm 6'
            
            if detail == 0:
                # نص فقط - أبسط وأسرع
                text = pytesseract.image_to_string(
                    pil_image,
                    lang=self._tess_lang,
                    config=custom_config
                )
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                return [{'text': line, 'confidence': 1.0} for line in lines]
            
            # استخراج مع التفاصيل (إحداثيات + ثقة)
            data = pytesseract.image_to_data(
                pil_image,
                lang=self._tess_lang,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            extracted = []
            n_boxes = len(data['text'])
            
            # تجميع الكلمات في سطور
            current_line = []
            current_line_num = -1
            current_block = -1
            
            for i in range(n_boxes):
                text = data['text'][i].strip()
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
            
            # إعدادات Tesseract المحسنة للعربي
            custom_config = r'--oem 3 --psm 6'
            
            text = pytesseract.image_to_string(
                pil_image,
                lang=self._tess_lang,
                config=custom_config
            )
            
            # تنظيف النص
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            return '\n'.join(lines)
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

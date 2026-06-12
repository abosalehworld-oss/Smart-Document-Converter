"""
OCR Engine - محرك التعرف على النصوص
=====================================
يغلف EasyOCR مع دعم كامل للعربي والإنجليزي.
يعمل أوفلاين بالكامل - CPU فقط.
"""

import logging
import os
import numpy as np

logger = logging.getLogger(__name__)


class OCREngine:
    """
    محرك OCR الرئيسي - يستخدم EasyOCR.
    يعمل على CPU فقط، أوفلاين بالكامل.
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
            gpu: استخدام GPU (False دائماً للأمان والتوافق)
            model_dir: مسار النماذج المحلية
        """
        self.languages = languages or ['ar', 'en']
        self.gpu = False  # إجباري CPU فقط
        self.model_dir = model_dir
        self._reader = None
        self._is_loaded = False
    
    def load(self, progress_callback=None):
        """
        تحميل محرك OCR والنماذج.
        يتم استدعاؤها مرة واحدة عند بدء التشغيل.
        """
        if self._is_loaded:
            return
        
        try:
            if progress_callback:
                progress_callback("جاري تحميل محرك التعرف...")
            
            import easyocr
            
            kwargs = {
                'lang_list': self.languages,
                'gpu': False,
                'verbose': False,
            }
            
            # استخدام مجلد نماذج محلي إذا وُجد
            if self.model_dir and os.path.exists(self.model_dir):
                kwargs['model_storage_directory'] = self.model_dir
                kwargs['download_enabled'] = False
            
            self._reader = easyocr.Reader(**kwargs)
            self._is_loaded = True
            
            if progress_callback:
                progress_callback("محرك التعرف جاهز")
            
            logger.info(f"تم تحميل OCR بنجاح - اللغات: {self.languages}")
        except Exception as e:
            logger.error(f"فشل تحميل OCR: {type(e).__name__}")
            raise RuntimeError(f"فشل تحميل محرك التعرف على النصوص") from e
    
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
            results = self._reader.readtext(
                image,
                detail=detail,
                paragraph=paragraph,
            )
            
            if detail == 0:
                # إرجاع نص فقط
                return [{'text': text, 'confidence': 1.0} for text in results]
            
            # تحويل النتائج لتنسيق موحد
            extracted = []
            for item in results:
                if len(item) == 3:
                    bbox, text, confidence = item
                elif len(item) == 2:
                    bbox, text = item
                    confidence = 1.0
                else:
                    continue
                
                extracted.append({
                    'text': text,
                    'bbox': bbox,
                    'confidence': confidence,
                })
            
            return extracted
        except Exception as e:
            logger.error(f"فشل استخراج النص: {type(e).__name__}")
            return []
    
    def extract_text_simple(self, image: np.ndarray) -> str:
        """
        استخراج النص كسلسلة نصية بسيطة.
        الأسهل للاستخدام المباشر.
        """
        results = self.extract_text(image, detail=1, paragraph=True)
        
        if not results:
            return ""
        
        # ترتيب حسب الموقع (أعلى لأسفل)
        sorted_results = self._sort_by_position(results)
        
        # دمج النصوص
        lines = [r['text'] for r in sorted_results if r['text'].strip()]
        return '\n'.join(lines)
    
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
            self._reader = None
            self.load()
    
    def get_supported_languages(self) -> list:
        """إرجاع قائمة اللغات المدعومة."""
        return ['ar', 'en']

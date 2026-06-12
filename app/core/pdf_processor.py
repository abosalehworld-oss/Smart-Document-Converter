"""
PDF Processor - معالجة ملفات PDF
=================================
استخراج النصوص من PDF باستخدام PyMuPDF + OCR.
ذكي: يكتشف هل PDF فيه نص رقمي ويستخدمه مباشرة.
"""

import fitz  # PyMuPDF
import numpy as np
from PIL import Image
import io
import logging

from app.core.ocr_engine import OCREngine
from app.core.image_processor import ImageProcessor

logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    معالج PDF - يحول صفحات PDF إلى نصوص.
    يستخدم OCR للصفحات الممسوحة ضوئياً.
    يستخرج النص مباشرة من PDF الرقمي.
    """
    
    def __init__(
        self,
        ocr_engine: OCREngine,
        image_processor: ImageProcessor,
        dpi: int = 300
    ):
        self.ocr_engine = ocr_engine
        self.image_processor = image_processor
        self.dpi = dpi
        self._doc = None
        self._current_path = None
    
    def open_pdf(self, file_path: str, password: str = None) -> int:
        """
        فتح ملف PDF.
        
        Args:
            file_path: مسار الملف
            password: كلمة المرور (للملفات المحمية)
        
        Returns:
            عدد الصفحات
        """
        try:
            self.close()  # إغلاق أي ملف مفتوح
            
            self._doc = fitz.open(file_path)
            
            # فتح ملف محمي بكلمة مرور
            if self._doc.is_encrypted:
                if password:
                    if not self._doc.authenticate(password):
                        raise ValueError("كلمة المرور غير صحيحة")
                else:
                    raise ValueError("الملف محمي بكلمة مرور")
            
            self._current_path = file_path
            page_count = len(self._doc)
            logger.info(f"تم فتح PDF: {page_count} صفحة")
            return page_count
        except fitz.FileDataError:
            raise ValueError("ملف PDF تالف أو غير صالح")
        except Exception as e:
            if "كلمة المرور" in str(e) or "محمي" in str(e):
                raise
            logger.error(f"فشل فتح PDF: {type(e).__name__}")
            raise ValueError("فشل فتح ملف PDF") from e
    
    def get_page_count(self) -> int:
        """إرجاع عدد الصفحات."""
        if self._doc is None:
            return 0
        return len(self._doc)
    
    def has_text_layer(self, page_num: int) -> bool:
        """
        فحص هل الصفحة تحتوي على نص رقمي مضمن.
        إذا كان هناك نص، لا نحتاج OCR.
        """
        if self._doc is None:
            return False
        
        try:
            page = self._doc[page_num]
            text = page.get_text("text").strip()
            # نعتبر الصفحة فيها نص إذا كان أكثر من 20 حرف
            return len(text) > 20
        except Exception:
            return False
    
    def extract_digital_text(self, page_num: int) -> str:
        """
        استخراج النص الرقمي المضمن في PDF مباشرة (بدون OCR).
        أسرع وأدق بكتير من OCR للملفات الرقمية.
        """
        if self._doc is None:
            return ""
        
        try:
            page = self._doc[page_num]
            text = page.get_text("text")
            return text.strip()
        except Exception as e:
            logger.error(f"فشل استخراج النص الرقمي: {type(e).__name__}")
            return ""
    
    def page_to_image(self, page_num: int) -> np.ndarray:
        """
        تحويل صفحة PDF إلى صورة عالية الدقة.
        
        Args:
            page_num: رقم الصفحة (يبدأ من 0)
        
        Returns:
            صورة كمصفوفة NumPy
        """
        if self._doc is None:
            raise ValueError("لم يتم فتح ملف PDF")
        
        try:
            page = self._doc[page_num]
            
            # تحويل لصورة بدقة عالية
            zoom = self.dpi / 72  # 72 هو الدقة الافتراضية لـ PDF
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat)
            
            # تحويل لـ NumPy array
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            img_array = np.array(img)
            
            return img_array
        except Exception as e:
            logger.error(f"فشل تحويل الصفحة لصورة: {type(e).__name__}")
            raise
    
    def process_page(self, page_num: int, mode: str = 'printed') -> str:
        """
        معالجة صفحة واحدة واستخراج نصها.
        ذكي: يستخدم النص الرقمي إذا وُجد، وإلا يستخدم OCR.
        
        Args:
            page_num: رقم الصفحة
            mode: وضع المعالجة (printed/handwritten/photo)
        
        Returns:
            النص المستخرج
        """
        # تم إيقاف استخراج النص الرقمي المباشر لأن مكتبة PyMuPDF 
        # تقوم بعكس الحروف العربية المركبة (مثل مح، مج) في بعض الخطوط.
        # بدلاً من ذلك، سنجبر البرنامج على تحويل الصفحة لصورة عالية الدقة
        # واستخدام محرك Tesseract OCR الذي يقرأ الكلمات العربية بشكل مثالي بالنظر.
        
        # if self.has_text_layer(page_num):
        #     text = self.extract_digital_text(page_num)
        #     if text:
        #         logger.debug(f"صفحة {page_num + 1}: نص رقمي ({len(text)} حرف)")
        #         return text
        
        # 2. استخدام OCR للصفحات الممسوحة ضوئياً
        logger.debug(f"صفحة {page_num + 1}: استخدام OCR")
        
        # تحويل الصفحة لصورة
        image = self.page_to_image(page_num)
        
        # معالجة الصورة
        import cv2
        if len(image.shape) == 3:
            bgr_image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        else:
            bgr_image = image
        
        processed = self.image_processor.enhance_for_ocr(bgr_image, mode)
        
        # استخراج النص
        text = self.ocr_engine.extract_text_simple(processed)
        logger.debug(f"صفحة {page_num + 1}: OCR ({len(text)} حرف)")
        
        return text
    
    def process_all_pages(
        self,
        pages: list = None,
        mode: str = 'printed',
        progress_callback=None,
        cancel_check=None
    ) -> list:
        """
        معالجة عدة صفحات.
        
        Args:
            pages: قائمة أرقام الصفحات (None = كل الصفحات)
            mode: وضع المعالجة
            progress_callback: دالة لإرسال التقدم (page_num, total, text)
            cancel_check: دالة للتحقق من طلب الإلغاء
        
        Returns:
            قائمة بالنصوص المستخرجة (نص لكل صفحة)
        """
        if self._doc is None:
            raise ValueError("لم يتم فتح ملف PDF")
        
        total_pages = len(self._doc)
        
        if pages is None:
            pages = list(range(total_pages))
        
        results = []
        
        for i, page_num in enumerate(pages):
            # فحص الإلغاء
            if cancel_check and cancel_check():
                logger.info("تم إلغاء المعالجة بواسطة المستخدم")
                break
            
            # إرسال التقدم
            if progress_callback:
                progress_callback(i + 1, len(pages), f"صفحة {page_num + 1}")
            
            try:
                text = self.process_page(page_num, mode)
                results.append(text)
            except Exception as e:
                logger.error(f"خطأ في صفحة {page_num + 1}: {type(e).__name__}")
                results.append(f"[خطأ في معالجة الصفحة {page_num + 1}]")
        
        return results
    
    def get_page_thumbnail(self, page_num: int, max_size: int = 200) -> Image.Image:
        """إنشاء صورة مصغرة للصفحة (للمعاينة في الواجهة)."""
        if self._doc is None:
            return None
        
        try:
            page = self._doc[page_num]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
            img_data = pix.tobytes("ppm")
            img = Image.open(io.BytesIO(img_data))
            img.thumbnail((max_size, max_size))
            return img
        except Exception:
            return None
    
    def close(self):
        """إغلاق ملف PDF وتحرير الذاكرة."""
        if self._doc is not None:
            try:
                self._doc.close()
            except Exception:
                pass
            self._doc = None
            self._current_path = None
    
    def __del__(self):
        """تنظيف عند الحذف."""
        self.close()

"""
Workers - خيوط المعالجة الخلفية
=================================
QThread workers لتشغيل OCR في الخلفية بدون تجميد الواجهة.
"""

from PySide6.QtCore import QThread, Signal, QMutex
import logging
import traceback

from app.core.ocr_engine import OCREngine
from app.core.image_processor import ImageProcessor
from app.core.pdf_processor import PDFProcessor
from app.core.word_generator import WordGenerator
from app.utils.arabic_utils import normalize_arabic_text

logger = logging.getLogger(__name__)


class OCRLoadWorker(QThread):
    """تحميل محرك OCR في الخلفية."""
    progress = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, ocr_engine: OCREngine):
        super().__init__()
        self.ocr_engine = ocr_engine
    
    def run(self):
        try:
            self.ocr_engine.load(progress_callback=lambda msg: self.progress.emit(msg))
            self.finished.emit(True, "تم تحميل محرك التعرف بنجاح")
        except Exception as e:
            self.finished.emit(False, f"فشل تحميل محرك التعرف: {str(e)}")


class PDFConversionWorker(QThread):
    """تحويل PDF إلى Word في الخلفية."""
    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(bool, str)  # success, message/path
    
    def __init__(
        self,
        pdf_path: str,
        output_path: str,
        ocr_engine: OCREngine,
        image_processor: ImageProcessor,
        pages: list = None,
        mode: str = 'printed',
        font_name: str = 'Simplified Arabic',
        font_size: int = 14
    ):
        super().__init__()
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.ocr_engine = ocr_engine
        self.image_processor = image_processor
        self.pages = pages
        self.mode = mode
        self.font_name = font_name
        self.font_size = font_size
        self._cancelled = False
        self._mutex = QMutex()
    
    def cancel(self):
        """طلب إلغاء المعالجة."""
        self._mutex.lock()
        self._cancelled = True
        self._mutex.unlock()
    
    def _is_cancelled(self) -> bool:
        self._mutex.lock()
        val = self._cancelled
        self._mutex.unlock()
        return val
    
    def run(self):
        try:
            # إنشاء معالج PDF
            pdf_proc = PDFProcessor(self.ocr_engine, self.image_processor)
            
            # فتح الملف
            self.progress.emit(0, 1, "جاري فتح ملف PDF...")
            page_count = pdf_proc.open_pdf(self.pdf_path)
            
            # تحديد الصفحات
            pages = self.pages or list(range(page_count))
            total = len(pages)
            
            # إنشاء مولد Word
            word_gen = WordGenerator(
                font_name=self.font_name,
                font_size=self.font_size
            )
            word_gen.create_document()
            
            # معالجة كل صفحة
            for i, page_num in enumerate(pages):
                if self._is_cancelled():
                    pdf_proc.close()
                    self.finished.emit(False, "تم إلغاء التحويل")
                    return
                
                self.progress.emit(i + 1, total, f"صفحة {page_num + 1} من {page_count}")
                
                try:
                    text = pdf_proc.process_page(page_num, self.mode)
                    word_gen.add_page_text(text, page_number=page_num + 1)
                except Exception as e:
                    logger.error(f"خطأ في صفحة {page_num + 1}: {e}")
                    word_gen.add_page_text(
                        f"[خطأ في معالجة الصفحة {page_num + 1}]"
                    )
            
            # حفظ الملف
            self.progress.emit(total, total, "جاري حفظ الملف...")
            saved_path = word_gen.save(self.output_path)
            
            # تنظيف
            pdf_proc.close()
            
            self.finished.emit(True, saved_path)
        except Exception as e:
            logger.error(f"فشل تحويل PDF: {e}")
            self.finished.emit(False, f"فشل التحويل: {str(e)}")


class ImageConversionWorker(QThread):
    """تحويل صور إلى Word في الخلفية."""
    progress = Signal(int, int, str)  # current, total, message
    finished = Signal(bool, str)  # success, message/path
    
    def __init__(
        self,
        image_paths: list,
        output_path: str,
        ocr_engine: OCREngine,
        image_processor: ImageProcessor,
        mode: str = 'printed',
        font_name: str = 'Simplified Arabic',
        font_size: int = 14
    ):
        super().__init__()
        self.image_paths = image_paths
        self.output_path = output_path
        self.ocr_engine = ocr_engine
        self.image_processor = image_processor
        self.mode = mode
        self.font_name = font_name
        self.font_size = font_size
        self._cancelled = False
        self._mutex = QMutex()
    
    def cancel(self):
        self._mutex.lock()
        self._cancelled = True
        self._mutex.unlock()
    
    def _is_cancelled(self) -> bool:
        self._mutex.lock()
        val = self._cancelled
        self._mutex.unlock()
        return val
    
    def run(self):
        try:
            total = len(self.image_paths)
            
            # إنشاء مولد Word
            word_gen = WordGenerator(
                font_name=self.font_name,
                font_size=self.font_size
            )
            word_gen.create_document()
            
            # معالجة كل صورة
            for i, img_path in enumerate(self.image_paths):
                if self._is_cancelled():
                    self.finished.emit(False, "تم إلغاء التحويل")
                    return
                
                filename = img_path.split('\\')[-1].split('/')[-1]
                self.progress.emit(i + 1, total, f"صورة {i + 1}: {filename}")
                
                try:
                    # معالجة الصورة
                    processed = self.image_processor.load_and_preprocess(
                        img_path, self.mode
                    )
                    
                    # استخراج النص
                    text = self.ocr_engine.extract_text_simple(processed)
                    
                    # إضافة للمستند
                    word_gen.add_page_text(text, page_number=i + 1)
                except Exception as e:
                    logger.error(f"خطأ في صورة {filename}: {e}")
                    word_gen.add_page_text(
                        f"[خطأ في معالجة الصورة: {filename}]"
                    )
            
            # حفظ الملف
            self.progress.emit(total, total, "جاري حفظ الملف...")
            saved_path = word_gen.save(self.output_path)
            
            self.finished.emit(True, saved_path)
        except Exception as e:
            logger.error(f"فشل تحويل الصور: {e}")
            self.finished.emit(False, f"فشل التحويل: {str(e)}")

"""
Image Processor - معالجة وتحسين الصور
======================================
تحسين جودة الصور قبل OCR مع الحفاظ على النقاط والتشكيل العربي.
⚠️ التنظيف لطيف جداً حتى لا نفقد النقاط العربية (فاء، قاف، جيم...).
"""

import cv2
import numpy as np
from PIL import Image
import logging
import os

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    معالج الصور - يحسّن جودة الصور لأفضل نتيجة OCR ممكنة.
    """
    
    # أوضاع المعالجة
    MODE_PRINTED = 'printed'      # نصوص مطبوعة
    MODE_HANDWRITTEN = 'handwritten'  # خط يدوي
    MODE_PHOTO = 'photo'          # صور موبايل
    
    def __init__(self, target_dpi: int = 300):
        self.target_dpi = target_dpi
    
    def enhance_for_ocr(self, image, mode: str = MODE_PRINTED) -> np.ndarray:
        """
        المعالجة الكاملة للصورة حسب النوع.
        
        Args:
            image: مصفوفة NumPy أو مسار الملف
            mode: نوع المعالجة (printed/handwritten/photo)
        
        Returns:
            صورة محسّنة كمصفوفة NumPy
        """
        # تحديد أقصى بكسلات للحماية من انهيار الذاكرة (Zip bombs / Massive images)
        Image.MAX_IMAGE_PIXELS = 100000000  # 100 ميجابكسل كحد أقصى (مثلاً 10000x10000)
        
        # تحميل الصورة إذا كانت مسار
        if isinstance(image, str):
            image = self._load_image(image)
        
        if image is None:
            raise ValueError("فشل تحميل الصورة")
        
        # نسخة للعمل عليها
        processed = image.copy()
        
        # 0. حماية الرامات من الصور العملاقة (Downscale if too large)
        h, w = processed.shape[:2]
        max_dim = 4000
        if h > max_dim or w > max_dim:
            scale = max_dim / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            processed = cv2.resize(processed, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.info(f"تم تصغير الصورة العملاقة لحماية الذاكرة: {w}x{h} -> {new_w}x{new_h}")
        
        # 1. تكبير الصور الصغيرة
        processed = self._upscale_if_needed(processed)
        
        # 2. تحويل للرمادي
        if len(processed.shape) == 3:
            gray = cv2.cvtColor(processed, cv2.COLOR_BGR2GRAY)
        else:
            gray = processed
        
        # 3. تصحيح الميل
        gray = self._deskew(gray)
        
        # 4. معالجة حسب النوع
        if mode == self.MODE_PHOTO:
            # صور الموبايل تحتاج معالجة إضافية
            gray = self._remove_shadows(gray)
            gray = self._enhance_contrast(gray)
            gray = self._gentle_denoise(gray, strength=8)
            gray = self._adaptive_binarize(gray)
        elif mode == self.MODE_HANDWRITTEN:
            # الخط اليدوي يحتاج تباين عالي وتنظيف أقل
            gray = self._enhance_contrast(gray, clip_limit=3.0)
            gray = self._gentle_denoise(gray, strength=5)
            gray = self._adaptive_binarize(gray, block_size=15)
        else:
            # النصوص المطبوعة - معالجة قياسية
            gray = self._enhance_contrast(gray)
            gray = self._gentle_denoise(gray, strength=8)
            gray = self._adaptive_binarize(gray)
        
        return gray
    
    def load_and_preprocess(self, image_path: str, mode: str = MODE_PRINTED) -> np.ndarray:
        """تحميل ومعالجة صورة من ملف."""
        image = self._load_image(image_path)
        if image is None:
            raise ValueError(f"فشل تحميل الصورة")
        return self.enhance_for_ocr(image, mode)
    
    def _load_image(self, image_path: str) -> np.ndarray:
        """تحميل صورة مع دعم المسارات العربية."""
        try:
            # استخدام PIL للدعم الأفضل للمسارات
            pil_img = Image.open(image_path)
            # تحويل لـ RGB إذا لزم الأمر
            if pil_img.mode == 'RGBA':
                # تحويل الشفافية لأبيض
                background = Image.new('RGB', pil_img.size, (255, 255, 255))
                background.paste(pil_img, mask=pil_img.split()[3])
                pil_img = background
            elif pil_img.mode != 'RGB':
                pil_img = pil_img.convert('RGB')
            
            # تحويل لـ OpenCV format
            img_array = np.array(pil_img)
            return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        except Exception as e:
            logger.error(f"فشل تحميل الصورة: {type(e).__name__}")
            return None
    
    def _upscale_if_needed(self, image: np.ndarray, min_height: int = 1000) -> np.ndarray:
        """تكبير الصور الصغيرة لتحسين دقة OCR."""
        h, w = image.shape[:2]
        
        if h < min_height:
            scale = min_height / h
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
            logger.debug(f"تم تكبير الصورة: {w}x{h} -> {new_w}x{new_h}")
        
        return image
    
    def _deskew(self, gray: np.ndarray) -> np.ndarray:
        """تصحيح ميل الصورة."""
        try:
            # كشف الحواف
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            
            # كشف الخطوط
            lines = cv2.HoughLinesP(
                edges, 1, np.pi / 180, 
                threshold=100,
                minLineLength=gray.shape[1] // 4,
                maxLineGap=20
            )
            
            if lines is None or len(lines) == 0:
                return gray
            
            # حساب متوسط الزاوية
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                if abs(angle) < 30:  # تجاهل الخطوط العمودية
                    angles.append(angle)
            
            if not angles:
                return gray
            
            median_angle = np.median(angles)
            
            # تجاهل الزوايا الصغيرة جداً
            if abs(median_angle) < 0.5:
                return gray
            
            # تدوير الصورة
            h, w = gray.shape[:2]
            center = (w // 2, h // 2)
            matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
            rotated = cv2.warpAffine(
                gray, matrix, (w, h),
                flags=cv2.INTER_CUBIC,
                borderMode=cv2.BORDER_REPLICATE
            )
            
            logger.debug(f"تم تصحيح الميل: {median_angle:.1f}°")
            return rotated
        except Exception:
            return gray
    
    def _enhance_contrast(self, gray: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
        """تحسين التباين باستخدام CLAHE."""
        clahe = cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=(8, 8)
        )
        return clahe.apply(gray)
    
    def _gentle_denoise(self, gray: np.ndarray, strength: int = 8) -> np.ndarray:
        """
        إزالة شوائب لطيفة - مهم جداً!
        ⚠️ القيمة h يجب أن تكون منخفضة (5-10) حتى لا نفقد النقاط العربية.
        النقاط (فاء ف، قاف ق، جيم ج) والتشكيل تبدو مثل الشوائب للخوارزمية!
        """
        return cv2.fastNlMeansDenoising(gray, h=strength)
    
    def _adaptive_binarize(self, gray: np.ndarray, block_size: int = 11) -> np.ndarray:
        """
        تحويل ثنائي تكيفي - يحافظ على التشكيل.
        Adaptive threshold أفضل من Otsu للنصوص العربية لأنه يتعامل
        مع الإضاءة غير المتساوية بشكل أفضل.
        """
        binary = cv2.adaptiveThreshold(
            gray, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY,
            block_size, 2
        )
        return binary
    
    def _remove_shadows(self, gray: np.ndarray) -> np.ndarray:
        """إزالة الظلال من صور الموبايل."""
        try:
            # تمويه كبير لالتقاط الخلفية
            dilated = cv2.dilate(gray, np.ones((7, 7), np.uint8))
            bg = cv2.medianBlur(dilated, 21)
            
            # طرح الخلفية
            diff = 255 - cv2.absdiff(gray, bg)
            
            # تطبيع
            norm = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
            return norm
        except Exception:
            return gray
    
    def numpy_to_pil(self, image: np.ndarray) -> Image.Image:
        """تحويل من NumPy إلى PIL Image."""
        if len(image.shape) == 2:
            return Image.fromarray(image, mode='L')
        else:
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            return Image.fromarray(rgb)
    
    def pil_to_numpy(self, pil_image: Image.Image) -> np.ndarray:
        """تحويل من PIL Image إلى NumPy."""
        return np.array(pil_image)

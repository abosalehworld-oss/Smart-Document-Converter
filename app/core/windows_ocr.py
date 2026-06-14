import asyncio
import io
import logging
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

class WindowsOCREngine:
    """
    محرك OCR يعتمد على Windows Media OCR (WinRT).
    دقيق جداً للغة العربية وأسرع من Tesseract ولا يتطلب مساحة إضافية.
    """
    
    def __init__(self, languages: list = None):
        self.languages = languages or ['ar', 'en']
        self._engine = None
        self._is_loaded = False
        
    def load(self, progress_callback=None):
        if self._is_loaded:
            return
            
        try:
            from winrt.windows.media.ocr import OcrEngine
            from winrt.windows.globalization import Language
            
            available_langs = OcrEngine.get_available_recognizer_languages()
            
            lang = None
            if 'ar' in self.languages:
                # Find any available Arabic language pack (ar-SA, ar-EG, ar-AE, etc.)
                for l in available_langs:
                    if l.language_tag.startswith('ar'):
                        lang = l
                        break
            
            if not lang and 'en' in self.languages:
                for l in available_langs:
                    if l.language_tag.startswith('en'):
                        lang = l
                        break
                        
            if not lang:
                # Fallback to creating Language object to trigger native error if missing
                lang_tag = 'ar-SA' if 'ar' in self.languages else 'en-US'
                lang = Language(lang_tag)
                if not OcrEngine.is_language_supported(lang):
                    raise RuntimeError(f"اللغة {lang_tag} غير مدعومة في نظام ويندوز الحالي. يرجى تثبيت حزمة اللغة.")
                
            self._engine = OcrEngine.try_create_from_language(lang)
            if not self._engine:
                raise RuntimeError("فشل تهيئة محرك ويندوز للتعرف على النصوص.")
                
            self._is_loaded = True
            if progress_callback:
                progress_callback(f"تم تحميل محرك ويندوز للغة: {lang.display_name}")
            logger.info(f"Windows OCR Engine loaded for {lang_tag}.")
        except ImportError as e:
            raise RuntimeError("مكتبة winsdk/winrt غير مثبتة.") from e
        except Exception as e:
            raise RuntimeError(f"فشل تحميل Windows OCR: {e}") from e

    @property
    def is_loaded(self) -> bool:
        return self._is_loaded

    def change_languages(self, languages: list):
        if set(languages) != set(self.languages):
            self.languages = languages
            self._is_loaded = False
            self.load()

    def get_supported_languages(self) -> list:
        return ['ar', 'en']

    async def _recognize_async(self, pil_image: Image.Image):
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.graphics.imaging import BitmapDecoder, SoftwareBitmap
        from winrt.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

        # Convert PIL Image to BMP bytes
        stream = io.BytesIO()
        pil_image.save(stream, format="BMP")
        image_bytes = stream.getvalue()

        # Write to WinRT RandomAccessStream
        random_access_stream = InMemoryRandomAccessStream()
        writer = DataWriter(random_access_stream)
        writer.write_bytes(image_bytes)
        await writer.store_async()
        writer.detach_stream()
        random_access_stream.seek(0)

        # Create SoftwareBitmap
        decoder = await BitmapDecoder.create_async(random_access_stream)
        software_bitmap = await decoder.get_software_bitmap_async()

        # Recognize Text
        result = await self._engine.recognize_async(software_bitmap)
        return result

    def extract_text_simple(self, image: np.ndarray) -> str:
        if not self._is_loaded:
            self.load()

        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:
                pil_image = Image.fromarray(image, mode='L')
            else:
                pil_image = Image.fromarray(image)
        else:
            pil_image = image

        try:
            result = asyncio.run(self._recognize_async(pil_image))
            
            # Reconstruct text fixing RTL order
            # Windows OCR often returns words in visual LTR order
            # For Arabic, we reverse the words array to get logical RTL order
            lines = []
            for line in result.lines:
                words = [w.text for w in line.words]
                # Reverse words to match Arabic reading direction
                lines.append(" ".join(words[::-1]))
                
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Windows OCR extraction failed: {e}")
            return ""

    def extract_text(self, image: np.ndarray, detail: int = 1, paragraph: bool = True) -> list:
        if not self._is_loaded:
            self.load()

        if isinstance(image, np.ndarray):
            if len(image.shape) == 2:
                pil_image = Image.fromarray(image, mode='L')
            else:
                pil_image = Image.fromarray(image)
        else:
            pil_image = image

        extracted = []
        try:
            result = asyncio.run(self._recognize_async(pil_image))
            
            for line in result.lines:
                words = [w.text for w in line.words]
                # Reverse words for Arabic RTL
                text = " ".join(words[::-1])
                
                # Get bounding box if available
                bbox = [[0, 0], [0, 0], [0, 0], [0, 0]]
                if hasattr(line, 'bounding_rect'):
                    rect = line.bounding_rect
                    bbox = [
                        [rect.x, rect.y],
                        [rect.x + rect.width, rect.y],
                        [rect.x + rect.width, rect.y + rect.height],
                        [rect.x, rect.y + rect.height]
                    ]
                
                confidence = 0.99  # Windows OCR does not return confidence, assume very high

                extracted.append({
                    'text': text,
                    'bbox': bbox,
                    'confidence': confidence
                })
            
            return extracted
        except Exception as e:
            logger.error(f"Windows OCR extraction failed: {e}")
            return []

import asyncio
import io
import logging
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

def is_arabic(text: str) -> bool:
    """تحقق مما إذا كان النص يحتوي على حروف عربية أو أرقام عربية-شرقية."""
    for char in text:
        cp = ord(char)
        if (0x0600 <= cp <= 0x06FF) or (0x0750 <= cp <= 0x077F) or (0x08A0 <= cp <= 0x08FF) or (0xFB50 <= cp <= 0xFDFF) or (0xFE70 <= cp <= 0xFEFF):
            return True
    return False

class WindowsOCREngine:
    """
    محرك OCR يعتمد على Windows Media OCR (WinRT).
    دقيق جداً للغة العربية وأسرع من Tesseract ولا يتطلب مساحة إضافية.
    """
    
    def __init__(self, languages: list = None):
        self.languages = languages or ['ar', 'en']
        self._engine = None
        self._engine_ar = None
        self._engine_en = None
        self._is_loaded = False
        
    def load(self, progress_callback=None):
        if self._is_loaded:
            return
            
        try:
            from winrt.windows.media.ocr import OcrEngine
            from winrt.windows.globalization import Language
            
            available_langs = OcrEngine.available_recognizer_languages
            
            self._engine_ar = None
            self._engine_en = None
            
            lang_ar = None
            lang_en = None
            
            for l in available_langs:
                if l.language_tag.startswith('ar'):
                    lang_ar = l
                elif l.language_tag.startswith('en'):
                    lang_en = l
            
            # Load Arabic if requested
            if 'ar' in self.languages:
                if lang_ar:
                    self._engine_ar = OcrEngine.try_create_from_language(lang_ar)
                else:
                    try:
                        fallback_ar = Language('ar-SA')
                        if OcrEngine.is_language_supported(fallback_ar):
                            self._engine_ar = OcrEngine.try_create_from_language(fallback_ar)
                            lang_ar = fallback_ar
                    except Exception:
                        pass
            
            # Load English if requested
            if 'en' in self.languages:
                if lang_en:
                    self._engine_en = OcrEngine.try_create_from_language(lang_en)
                else:
                    try:
                        fallback_en = Language('en-US')
                        if OcrEngine.is_language_supported(fallback_en):
                            self._engine_en = OcrEngine.try_create_from_language(fallback_en)
                            lang_en = fallback_en
                    except Exception:
                        pass
            
            # Fallback if both requested but neither loaded
            if ('ar' in self.languages or 'en' in self.languages) and not self._engine_ar and not self._engine_en:
                lang_tag = 'ar-SA' if 'ar' in self.languages else 'en-US'
                lang = Language(lang_tag)
                if not OcrEngine.is_language_supported(lang):
                    raise RuntimeError(f"اللغة {lang_tag} غير مدعومة في نظام ويندوز الحالي. يرجى تثبيت حزمة اللغة.")
                self._engine = OcrEngine.try_create_from_language(lang)
            
            self._is_loaded = True
            
            loaded_names = []
            if self._engine_ar:
                loaded_names.append(lang_ar.display_name if lang_ar else "العربية")
            if self._engine_en:
                loaded_names.append(lang_en.display_name if lang_en else "الإنجليزية")
            if self._engine:
                loaded_names.append("الافتراضي")
                
            if progress_callback:
                progress_callback(f"تم تحميل محرك ويندوز للغة: {' و '.join(loaded_names)}")
            logger.info(f"Windows OCR Engines loaded: {', '.join(loaded_names)}.")
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
        if self._engine_ar and self._engine_en:
            result_ar = await self._engine_ar.recognize_async(software_bitmap)
            ar_text = "".join(w.text for line in result_ar.lines for w in line.words)
            if is_arabic(ar_text):
                return result_ar
            else:
                try:
                    result_en = await self._engine_en.recognize_async(software_bitmap)
                    return result_en
                except Exception as e:
                    logger.warning(f"Failed English OCR, using Arabic: {e}")
                    return result_ar
        elif self._engine_ar:
            return await self._engine_ar.recognize_async(software_bitmap)
        elif self._engine_en:
            return await self._engine_en.recognize_async(software_bitmap)
        elif self._engine:
            return await self._engine.recognize_async(software_bitmap)
        else:
            raise RuntimeError("لم يتم تحميل محرك التعرف لويندوز.")

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
            # Windows OCR returns words in visual LTR order (left-to-right).
            # For lines containing Arabic, we sort words by their bounding box X-coordinate in descending order.
            lines = []
            for line in result.lines:
                line_words = list(line.words)
                if line_words:
                    combined_text = "".join(w.text for w in line_words)
                    if is_arabic(combined_text):
                        try:
                            line_words = sorted(line_words, key=lambda w: w.bounding_rect.x, reverse=True)
                        except Exception as e:
                            logger.warning(f"Failed to sort words by bounding_rect: {e}")
                            line_words = line_words[::-1]
                words = [w.text for w in line_words]
                lines.append(" ".join(words))
                
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
                line_words = list(line.words)
                if line_words:
                    combined_text = "".join(w.text for w in line_words)
                    if is_arabic(combined_text):
                        try:
                            line_words = sorted(line_words, key=lambda w: w.bounding_rect.x, reverse=True)
                        except Exception as e:
                            logger.warning(f"Failed to sort words by bounding_rect: {e}")
                            line_words = line_words[::-1]
                
                words = [w.text for w in line_words]
                text = " ".join(words)
                
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

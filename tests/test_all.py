"""
Test: OCR Engine
اختبارات محرك التعرف على النصوص
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
from PIL import Image, ImageDraw, ImageFont


def create_test_image_arabic(text: str = "مرحباً بالعالم 123") -> np.ndarray:
    """إنشاء صورة اختبار بنص عربي."""
    img = Image.new('RGB', (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), text, fill=(0, 0, 0))
    return np.array(img)


def create_test_image_english(text: str = "Hello World 123") -> np.ndarray:
    """إنشاء صورة اختبار بنص إنجليزي."""
    img = Image.new('RGB', (400, 100), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.text((10, 30), text, fill=(0, 0, 0))
    return np.array(img)


def test_ocr_engine_loads():
    """اختبار تحميل محرك OCR."""
    from app.core.ocr_engine import OCREngine
    engine = OCREngine(languages=['ar', 'en'], gpu=False)
    assert engine is not None
    assert engine.gpu == False
    print("✅ OCR Engine creates successfully")


def test_ocr_cpu_only():
    """التأكد من أن GPU دائماً False."""
    from app.core.ocr_engine import OCREngine
    # حتى لو طلبنا GPU، لازم يبقى False
    engine = OCREngine(languages=['en'], gpu=True)
    assert engine.gpu == False
    print("✅ GPU is always False (CPU-only mode enforced)")


def test_security_magic_bytes():
    """اختبار فحص Magic Bytes."""
    from app.utils.security import check_magic_bytes
    import tempfile

    # إنشاء ملف PNG وهمي
    png_header = b'\x89PNG\r\n\x1a\n' + b'\x00' * 8
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        f.write(png_header)
        tmp_path = f.name

    detected, msg = check_magic_bytes(tmp_path)
    os.unlink(tmp_path)

    assert detected == 'png', f"Expected 'png', got '{detected}'"
    print("✅ Magic bytes detection works correctly")


def test_security_malicious_file():
    """اختبار رفض الملفات الخبيثة."""
    from app.utils.security import validate_file_integrity
    import tempfile

    # ملف exe متنكر كـ PDF
    exe_header = b'MZ\x90\x00' + b'\x00' * 100  # Windows EXE header
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
        f.write(exe_header)
        tmp_path = f.name

    valid, msg = validate_file_integrity(tmp_path, 'pdf')
    os.unlink(tmp_path)

    assert not valid, "يجب رفض الملف الخبيث!"
    print(f"✅ Malicious file rejected: {msg}")


def test_arabic_language_detection():
    """اختبار كشف اللغة العربية."""
    from app.utils.arabic_utils import detect_language

    assert detect_language("مرحباً بالعالم") == 'ar'
    assert detect_language("Hello World") == 'en'
    assert detect_language("مرحبا Hello") == 'mixed'
    assert detect_language("12345") == 'unknown'
    print("✅ Language detection works correctly")


def test_arabic_numeral_conversion():
    """اختبار تحويل الأرقام العربية."""
    from app.utils.arabic_utils import convert_arabic_numerals

    result = convert_arabic_numerals("٢٠٢٤")
    assert result == "2024", f"Expected '2024', got '{result}'"
    print("✅ Arabic numeral conversion works")


def test_translations():
    """اختبار نظام الترجمة."""
    from app.utils.arabic_utils import tr

    ar_text = tr('start_conversion', 'ar')
    en_text = tr('start_conversion', 'en')

    assert ar_text != en_text
    assert 'التحويل' in ar_text or 'بدء' in ar_text
    assert 'Conversion' in en_text or 'Start' in en_text
    print(f"✅ Translation works: AR='{ar_text}' EN='{en_text}'")


def test_secure_delete():
    """اختبار الحذف الآمن."""
    from app.utils.security import secure_delete_file
    import tempfile

    # إنشاء ملف مؤقت
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"sensitive data " * 100)
        tmp_path = f.name

    assert os.path.exists(tmp_path)
    result = secure_delete_file(tmp_path)
    assert result == True
    assert not os.path.exists(tmp_path)
    print("✅ Secure file deletion works")


def test_word_generator_creates():
    """اختبار إنشاء مستند Word."""
    from app.core.word_generator import WordGenerator
    import tempfile

    gen = WordGenerator()
    gen.create_document()
    gen.add_page_text("مرحباً بالعالم\nHello World")

    with tempfile.NamedTemporaryFile(suffix='.docx', delete=False) as f:
        tmp_path = f.name

    saved = gen.save(tmp_path)
    assert os.path.exists(saved)
    assert os.path.getsize(saved) > 0

    os.unlink(saved)
    print("✅ Word document created successfully")


def test_image_processor():
    """اختبار معالجة الصور."""
    from app.core.image_processor import ImageProcessor
    import tempfile

    processor = ImageProcessor()

    # إنشاء صورة اختبار
    img = Image.new('RGB', (400, 200), color=(240, 240, 240))
    draw = ImageDraw.Draw(img)
    draw.text((10, 80), "Test Arabic OCR", fill=(0, 0, 0))

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as f:
        img.save(f.name)
        tmp_path = f.name

    result = processor.load_and_preprocess(tmp_path)
    assert result is not None
    assert result.shape[0] > 0

    os.unlink(tmp_path)
    print("✅ Image processor works correctly")


if __name__ == '__main__':
    print("\n" + "="*50)
    print("  اختبارات مشروع محوّل المستندات الذكي")
    print("  Smart Document Converter - Tests")
    print("="*50 + "\n")

    tests = [
        test_ocr_cpu_only,
        test_security_magic_bytes,
        test_security_malicious_file,
        test_arabic_language_detection,
        test_arabic_numeral_conversion,
        test_translations,
        test_secure_delete,
        test_word_generator_creates,
        test_image_processor,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} FAILED: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"النتيجة: {passed} نجح | {failed} فشل")
    print(f"{'='*50}\n")

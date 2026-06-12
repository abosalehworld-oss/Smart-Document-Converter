import sys
import os
import io

# Ensure app path is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import arabic_reshaper
from bidi.algorithm import get_display

from app.core.ocr_engine import OCREngine
from app.core.pdf_processor import PDFProcessor
from app.core.image_processor import ImageProcessor
from app.core.word_generator import WordGenerator

def get_arabic_font(size=40):
    try:
        return ImageFont.truetype("C:\\Windows\\Fonts\\arial.ttf", size)
    except IOError:
        try:
            return ImageFont.truetype("C:\\Windows\\Fonts\\tahoma.ttf", size)
        except IOError:
            return ImageFont.load_default()

def get_english_font(size=40):
    try:
        return ImageFont.truetype("C:\\Windows\\Fonts\\times.ttf", size)
    except IOError:
        return ImageFont.load_default()

def draw_arabic_text(draw, x, y, text, font, fill="black"):
    reshaped_text = arabic_reshaper.reshape(text)
    bidi_text = get_display(reshaped_text)
    draw.text((x, y), bidi_text, font=font, fill=fill)

def create_arabic_memo_pdf(filepath):
    img = Image.new('RGB', (1600, 1200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = get_arabic_font(80)
    font_body = get_arabic_font(50)
    
    draw_arabic_text(draw, 600, 100, "مذكرة قانونية", font_title)
    draw_arabic_text(draw, 100, 300, "إنه في يوم الإثنين الموافق 12 يونيو 2026", font_body)
    draw_arabic_text(draw, 100, 400, "بناء على طلب السيد / أحمد محمود", font_body)
    draw_arabic_text(draw, 100, 500, "ضد السيد / مصطفى كمال", font_body)
    draw_arabic_text(draw, 100, 700, "نلتمس من المحكمة الموقرة الحكم بالآتي:", font_body)
    draw_arabic_text(draw, 100, 800, "أولا: قبول الدعوى شكلا.", font_body)
    
    img.save(filepath, "PDF", resolution=300.0)
    print(f"[OK] Created: {filepath}")

def create_english_story_image(filepath):
    img = Image.new('RGB', (1600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = get_english_font(80)
    font_body = get_english_font(50)
    
    draw.text((100, 100), "The Silent Forest", font=font_title, fill="black")
    draw.text((100, 300), "Once upon a time in a digital world,", font=font_body, fill="black")
    draw.text((100, 400), "an OCR program was born to bridge the gap", font=font_body, fill="black")
    draw.text((100, 500), "between pixels and meaning. It processed", font=font_body, fill="black")
    draw.text((100, 600), "thousands of documents swiftly.", font=font_body, fill="black")
    
    img.save(filepath, "PNG")
    print(f"[OK] Created: {filepath}")

def create_mixed_judgment_image(filepath):
    img = Image.new('RGB', (1600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    font_title = get_arabic_font(70)
    font_body = get_arabic_font(50)
    
    draw_arabic_text(draw, 400, 100, "حكم محكمة النقض رقم 4589 لسنة 2025", font_title)
    draw_arabic_text(draw, 100, 300, "المادة 15 من قانون العقوبات تنص على...", font_body)
    draw_arabic_text(draw, 100, 400, "غرامة قدرها 50000 جنيه مصري", font_body)
    draw_arabic_text(draw, 100, 500, "تاريخ الجلسة: 15 / 10 / 2026", font_body)
    
    img.save(filepath, "PNG")
    print(f"[OK] Created: {filepath}")

def main():
    print("=" * 50)
    print("بدء الاختبار الحي - Smart Document Converter")
    print("=" * 50)
    
    pdf_path = "test_arabic_memo.pdf"
    eng_path = "test_english_story.png"
    mixed_path = "test_mixed_judgment.png"
    
    create_arabic_memo_pdf(pdf_path)
    create_english_story_image(eng_path)
    create_mixed_judgment_image(mixed_path)
    
    print("\n[1] تهيئة المحركات (OCR Engine & Image Processor)...")
    try:
        ocr_engine = OCREngine(languages=['ar', 'en'], gpu=False)
        ocr_engine.load()
        img_processor = ImageProcessor()
        pdf_processor = PDFProcessor(ocr_engine, img_processor)
    except Exception as e:
        print(f"[FAIL] فشل تهيئة المحركات: {e}")
        return

    print("\n[2] معالجة مذكرة قانونية (PDF بالعربية)...")
    try:
        pdf_processor.open_pdf(pdf_path)
        result_pdf = pdf_processor.process_all_pages()
        print("-" * 30)
        for i, text in enumerate(result_pdf):
            print(f"--- صفحة {i+1} ---")
            print(text)
        print("-" * 30)
        
        # حفظ كمستند Word
        word_gen = WordGenerator()
        word_gen.create_document()
        for text in result_pdf:
            word_gen.add_page_text(text)
        out_word_1 = "output_arabic_memo.docx"
        word_gen.save(out_word_1)
        print(f"[OK] تم حفظ المستند بنجاح: {out_word_1}")
        
    except Exception as e:
        print(f"[FAIL] خطأ في معالجة PDF: {e}")

    print("\n[3] معالجة قصة بالإنجليزية (صورة / Word Output)...")
    try:
        img_eng = np.array(Image.open(eng_path))
        processed_eng = img_processor.enhance_for_ocr(img_eng, mode='printed')
        text_eng = ocr_engine.extract_text_simple(processed_eng)
        print("-" * 30)
        print(text_eng)
        print("-" * 30)
        
        # حفظ كمستند Word
        word_gen2 = WordGenerator()
        word_gen2.create_document()
        word_gen2.add_page_text(text_eng)
        out_word_2 = "output_english_story.docx"
        word_gen2.save(out_word_2)
        print(f"[OK] تم حفظ المستند بنجاح: {out_word_2}")
    except Exception as e:
        print(f"[FAIL] خطأ في معالجة الإنجليزية: {e}")

    print("\n[4] معالجة حكم قضائي (مزيج عربي وأرقام)...")
    try:
        img_mixed = np.array(Image.open(mixed_path))
        processed_mixed = img_processor.enhance_for_ocr(img_mixed, mode='printed')
        text_mixed = ocr_engine.extract_text_simple(processed_mixed)
        print("-" * 30)
        print(text_mixed)
        print("-" * 30)
        
        # حفظ كمستند Word
        word_gen3 = WordGenerator()
        word_gen3.create_document()
        word_gen3.add_page_text(text_mixed)
        out_word_3 = "output_mixed_judgment.docx"
        word_gen3.save(out_word_3)
        print(f"[OK] تم حفظ المستند بنجاح: {out_word_3}")
    except Exception as e:
        print(f"[FAIL] خطأ في معالجة المزيج: {e}")
        
    print("\n" + "=" * 50)
    print("تم الانتهاء من الاختبار الحي بنجاح!")
    print("=" * 50)

if __name__ == "__main__":
    main()

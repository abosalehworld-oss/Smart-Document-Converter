import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import sys

# إضافة مسار المشروع
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.ocr_engine import OCREngine
from app.core.image_processor import ImageProcessor

def create_synthetic_ad():
    """إنشاء صورة إعلانية معقدة (خلفية متدرجة + نص)"""
    width, height = 800, 400
    # خلفية متدرجة (Gradient) تحاكي الإعلانات
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        r = int(255 * (y / height))
        g = 50
        b = int(255 * (1 - y / height))
        img[y, :] = (b, g, r)
    
    pil_img = Image.fromarray(img)
    draw = ImageDraw.Draw(pil_img)
    
    # إضافة نصوص بخطوط وألوان مختلفة
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
        
    # إضافة نصوص إنجليزية محاكية لإعلان
    draw.text((50, 50), "SPECIAL OFFER 2026", fill=(255, 255, 255), font=font)
    draw.text((50, 150), "Buy 1 Get 1 FREE!", fill=(255, 200, 0), font=font)
    draw.text((50, 250), "Limited Time Only.", fill=(200, 255, 255), font=font)
    
    # إضافة "علامة مائية" خفيفة كضوضاء
    draw.text((200, 100), "WATERMARK WATERMARK", fill=(150, 50, 150), font=font)
    
    test_path = "test_ad.jpg"
    pil_img.save(test_path)
    return test_path

def test_ocr():
    print("=== بدء اختبار OCR على الصور الإعلانية ===")
    img_path = create_synthetic_ad()
    print(f"تم إنشاء صورة إعلانية تجريبية: {img_path}")
    
    engine = OCREngine(languages=['en'])
    processor = ImageProcessor()
    
    # اختبار 1: الوضع التقليدي (المعالجة المسبقة مفعلة)
    print("\n[1] الاختبار مع (تفعيل معالجة الصور) - الوضع التقليدي...")
    processed_printed = processor.load_and_preprocess(img_path, mode='printed')
    text_printed = engine.extract_text_simple(processed_printed)
    print("النتيجة:\n", text_printed)
    print("-" * 40)
    
    # اختبار 2: وضع الجرافيك الجديد (المعالجة المسبقة معطلة)
    print("\n[2] الاختبار مع (إيقاف معالجة الصور) - الوضع الجرافيكي الجديد...")
    processed_graphic = processor.load_and_preprocess(img_path, mode='graphic')
    text_graphic = engine.extract_text_simple(processed_graphic)
    print("النتيجة:\n", text_graphic)
    print("-" * 40)

if __name__ == "__main__":
    test_ocr()

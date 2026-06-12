import sys
sys.stdout.reconfigure(encoding='utf-8')
import fitz
import cv2
import numpy as np
import pytesseract
from PIL import Image
import os
import shutil

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def page_to_image(doc, page_num):
    page = doc[page_num]
    zoom = 300 / 72
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes('ppm')
    import io
    img = Image.open(io.BytesIO(img_data))
    img_array = np.array(img)
    if len(img_array.shape) == 3:
        return cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    return img_array

pdfs = [
    r'dist\Portable_SmartDocConverter\قرار رقم 12-2026 نقل.pdf'
]

tessdata_dir = os.path.abspath('tessdata_temp')
os.makedirs(tessdata_dir, exist_ok=True)
shutil.copy('ara_best.traineddata', os.path.join(tessdata_dir, 'ara.traineddata'))

for pdf_path in pdfs:
    print(f'\n--- Testing BEST model on {os.path.basename(pdf_path)} ---')
    try:
        doc = fitz.open(pdf_path)
        img = page_to_image(doc, 0)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=1.5, tileGridSize=(8, 8))
        after_img = clahe.apply(gray)
        after_img = cv2.fastNlMeansDenoising(after_img, h=3)
        
        config = f'--tessdata-dir "{tessdata_dir}" --oem 3 --psm 3'
        txt_after = pytesseract.image_to_string(after_img, lang='ara', config=config)
        print(txt_after.strip()[:1000])
        doc.close()
    except Exception as e:
        print('Error:', e)

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextEdit, QApplication, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QClipboard

import numpy as np
import cv2

from app.gui.styles import COLORS
from app.utils.arabic_utils import tr
from app.core.ocr_engine import OCREngine
from app.core.image_processor import ImageProcessor
from app.gui.snippet_overlay import SnippetOverlay
from app.gui.workers import SnippetWorker

class SnippingTab(QWidget):
    """تبويب اللقطات السريعة (Snipping Tool)."""
    
    def __init__(self, ocr_engine: OCREngine, image_processor: ImageProcessor, settings: dict):
        super().__init__()
        self.ocr_engine = ocr_engine
        self.image_processor = image_processor
        self.settings = settings
        self._current_lang = settings.get('language', 'ar')
        
        self.overlay = None
        self.worker = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)
        
        # العنوان والشرح
        header_layout = QVBoxLayout()
        header_layout.setSpacing(10)
        
        self._title_label = QLabel(tr('tab_snipping', self._current_lang))
        self._title_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 24px; font-weight: bold;")
        header_layout.addWidget(self._title_label)
        
        self._desc_label = QLabel(tr('snip_desc', self._current_lang))
        self._desc_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 14px;")
        self._desc_label.setWordWrap(True)
        header_layout.addWidget(self._desc_label)
        
        layout.addLayout(header_layout)
        
        # زر التقاط الشاشة
        self._btn_snip = QPushButton(tr('take_snip', self._current_lang))
        self._btn_snip.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_snip.setFixedHeight(60)
        self._btn_snip.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        self._btn_snip.clicked.connect(self._start_snipping)
        layout.addWidget(self._btn_snip)
        
        # مربع النص
        self._text_edit = QTextEdit()
        self._text_edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: {COLORS['bg_input']};
                color: {COLORS['text_primary']};
                border: 2px solid {COLORS['border']};
                border-radius: 8px;
                padding: 15px;
                font-size: 16px;
            }}
            QTextEdit:focus {{
                border-color: {COLORS['primary']};
            }}
        """)
        # ضبط الاتجاه الافتراضي
        self._text_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft if self._current_lang == 'ar' else Qt.LayoutDirection.LeftToRight)
        layout.addWidget(self._text_edit)
        
        # أزرار أسفل المربع
        bottom_layout = QHBoxLayout()
        
        self._btn_copy = QPushButton("📋 " + tr('copy_text', self._current_lang))
        self._btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_copy.setFixedSize(200, 45)
        self._btn_copy.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['bg_card']};
                color: {COLORS['text_primary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['bg_card_hover']};
                border-color: {COLORS['primary']};
            }}
        """)
        self._btn_copy.clicked.connect(self._copy_to_clipboard)
        bottom_layout.addWidget(self._btn_copy, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addLayout(bottom_layout)
        
    def update_language(self, lang: str):
        self._current_lang = lang
        self._title_label.setText(tr('tab_snipping', lang))
        self._desc_label.setText(tr('snip_desc', lang))
        self._btn_snip.setText(tr('take_snip', lang))
        self._btn_copy.setText("📋 " + tr('copy_text', lang))
        self._text_edit.setLayoutDirection(Qt.LayoutDirection.RightToLeft if lang == 'ar' else Qt.LayoutDirection.LeftToRight)
        
    def _start_snipping(self):
        # 1. إخفاء النافذة الرئيسية
        self.window().hide()
        
        # 2. الانتظار قليلاً لتختفي النافذة تماماً قبل التصوير
        QTimer.singleShot(300, self._show_overlay)
        
    def _show_overlay(self):
        self.overlay = SnippetOverlay()
        self.overlay.on_snippet_taken.connect(self._process_snippet)
        self.overlay.on_cancelled.connect(self._restore_window)
        self.overlay.show()
        
    def _restore_window(self):
        self.window().showNormal()
        self.window().activateWindow()
        
    def _process_snippet(self, qimage):
        # استعادة النافذة
        self._restore_window()
        
        # مسح النص القديم وعرض رسالة تحميل
        self._text_edit.clear()
        self._text_edit.setText("⏳ " + tr('converting', self._current_lang))
        self._btn_snip.setEnabled(False)
        
        # تحويل QImage إلى Numpy Array
        qimage = qimage.convertToFormat(qimage.Format.Format_RGB32)
        width = qimage.width()
        height = qimage.height()
        
        ptr = qimage.constBits()
        arr = np.frombuffer(ptr, np.uint8).reshape((height, width, 4))
        # تحويل BGRA إلى BGR ليتوافق مع OpenCV
        img_bgr = cv2.cvtColor(arr, cv2.COLOR_BGRA2BGR)
        
        # معالجة في الخلفية
        self.worker = SnippetWorker(img_bgr, self.ocr_engine, self.image_processor)
        self.worker.finished.connect(self._on_extraction_finished)
        self.worker.start()
        
    def _on_extraction_finished(self, success, text):
        self._btn_snip.setEnabled(True)
        if success:
            self._text_edit.setText(text)
        else:
            self._text_edit.setText("❌ " + text)
            
    def _copy_to_clipboard(self):
        text = self._text_edit.toPlainText()
        if text and not text.startswith("⏳"):
            QApplication.clipboard().setText(text)
            
            # تغيير النص لفترة قصيرة كدليل مرئي
            original_text = self._btn_copy.text()
            self._btn_copy.setText("✅ " + tr('text_copied', self._current_lang))
            QTimer.singleShot(2000, lambda: self._btn_copy.setText(original_text))

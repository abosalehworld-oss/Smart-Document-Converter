"""
PDF Tab - تبويب تحويل PDF إلى Word
=====================================
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QFrame, QSpinBox,
    QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt
import os

from app.gui.styles import COLORS
from app.gui.widgets import ProgressCard
from app.gui.workers import PDFConversionWorker
from app.utils.arabic_utils import tr
from app.utils.file_handler import get_supported_pdf_filters, get_word_save_filter, ensure_docx_extension
from app.utils.security import validate_file_integrity


class PDFTab(QWidget):
    """تبويب تحويل PDF إلى Word."""
    
    def __init__(self, ocr_engine, image_processor, settings, parent=None):
        super().__init__(parent)
        self.ocr_engine = ocr_engine
        self.image_processor = image_processor
        self.settings = settings
        self._worker = None
        self._pdf_path = None
        self._page_count = 0
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        # ===== العنوان =====
        title = QLabel(tr('tab_pdf', self.settings.get('language', 'ar')))
        title.setObjectName("title")
        layout.addWidget(title)
        
        # ===== بطاقة اختيار الملف =====
        file_card = QFrame()
        file_card.setObjectName("card")
        file_card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        file_layout = QVBoxLayout(file_card)
        file_layout.setSpacing(12)
        
        # زر اختيار الملف
        btn_row = QHBoxLayout()
        
        self._select_btn = QPushButton("📄  " + tr('select_pdf', self.settings.get('language', 'ar')))
        self._select_btn.setMinimumHeight(45)
        self._select_btn.clicked.connect(self._select_pdf)
        btn_row.addWidget(self._select_btn)
        
        file_layout.addLayout(btn_row)
        
        # معلومات الملف
        self._file_info = QLabel(tr('no_file_selected', self.settings.get('language', 'ar')))
        self._file_info.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px; padding: 8px;")
        self._file_info.setWordWrap(True)
        file_layout.addWidget(self._file_info)
        
        # خيارات الصفحات
        pages_row = QHBoxLayout()
        
        self._all_pages_check = QCheckBox(tr('convert_all', self.settings.get('language', 'ar')))
        self._all_pages_check.setChecked(True)
        self._all_pages_check.toggled.connect(self._toggle_page_selection)
        pages_row.addWidget(self._all_pages_check)
        
        pages_row.addSpacing(20)
        
        from_label = QLabel("من:")
        from_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        pages_row.addWidget(from_label)
        
        self._from_page = QSpinBox()
        self._from_page.setMinimum(1)
        self._from_page.setMaximum(1)
        self._from_page.setEnabled(False)
        self._from_page.setFixedWidth(80)
        pages_row.addWidget(self._from_page)
        
        to_label = QLabel("إلى:")
        to_label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        pages_row.addWidget(to_label)
        
        self._to_page = QSpinBox()
        self._to_page.setMinimum(1)
        self._to_page.setMaximum(1)
        self._to_page.setEnabled(False)
        self._to_page.setFixedWidth(80)
        pages_row.addWidget(self._to_page)
        
        pages_row.addStretch()
        file_layout.addLayout(pages_row)
        
        layout.addWidget(file_card)
        
        # ===== بطاقة الحفظ =====
        save_card = QFrame()
        save_card.setObjectName("card")
        save_card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        save_layout = QHBoxLayout(save_card)
        
        save_label = QLabel("💾  " + tr('save_location', self.settings.get('language', 'ar')) + ":")
        save_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        save_layout.addWidget(save_label)
        
        self._save_path_label = QLabel(self.settings.get('default_save_path', os.path.expanduser('~\\Documents')))
        self._save_path_label.setStyleSheet(f"color: {COLORS['text_primary']}; font-size: 13px;")
        self._save_path_label.setWordWrap(True)
        save_layout.addWidget(self._save_path_label, 1)
        
        browse_btn = QPushButton(tr('browse', self.settings.get('language', 'ar')))
        browse_btn.setObjectName("btn_secondary")
        browse_btn.setFixedWidth(100)
        browse_btn.clicked.connect(self._browse_save_location)
        save_layout.addWidget(browse_btn)
        
        layout.addWidget(save_card)
        
        # ===== شريط التقدم =====
        self._progress_card = ProgressCard()
        self._progress_card.cancel_clicked.connect(self._cancel_conversion)
        layout.addWidget(self._progress_card)
        
        # ===== أزرار التحويل =====
        btn_row2 = QHBoxLayout()
        btn_row2.addStretch()
        
        self._convert_btn = QPushButton("🚀  " + tr('start_conversion', self.settings.get('language', 'ar')))
        self._convert_btn.setMinimumHeight(50)
        self._convert_btn.setMinimumWidth(200)
        self._convert_btn.setStyleSheet(f"""
            QPushButton {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary']},
                    stop:1 {COLORS['accent']}
                );
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 32px;
            }}
            QPushButton:hover {{
                background: qlineargradient(
                    x1:0, y1:0, x2:1, y2:0,
                    stop:0 {COLORS['primary_hover']},
                    stop:1 {COLORS['accent_hover']}
                );
            }}
            QPushButton:disabled {{
                background: {COLORS['bg_card']};
                color: {COLORS['text_muted']};
            }}
        """)
        self._convert_btn.setEnabled(False)
        self._convert_btn.clicked.connect(self._start_conversion)
        btn_row2.addWidget(self._convert_btn)
        
        btn_row2.addStretch()
        layout.addLayout(btn_row2)
        
        # ===== نتيجة =====
        self._result_frame = QFrame()
        self._result_frame.hide()
        result_layout = QHBoxLayout(self._result_frame)
        
        self._open_file_btn = QPushButton("📂  " + tr('open_file', self.settings.get('language', 'ar')))
        self._open_file_btn.setObjectName("btn_success")
        self._open_file_btn.clicked.connect(self._open_result_file)
        result_layout.addWidget(self._open_file_btn)
        
        self._open_folder_btn = QPushButton("📁  " + tr('open_folder', self.settings.get('language', 'ar')))
        self._open_folder_btn.setObjectName("btn_secondary")
        self._open_folder_btn.clicked.connect(self._open_result_folder)
        result_layout.addWidget(self._open_folder_btn)
        
        result_layout.addStretch()
        layout.addWidget(self._result_frame)
        
        layout.addStretch()
    
    def _select_pdf(self):
        lang = self.settings.get('language', 'ar')
        path, _ = QFileDialog.getOpenFileName(
            self,
            tr('select_pdf', lang),
            self.settings.get('last_open_path', ''),
            get_supported_pdf_filters(lang)
        )
        
        if path:
            # فحص أمان الملف
            valid, msg = validate_file_integrity(path, 'pdf')
            if not valid:
                QMessageBox.warning(self, tr('security_warning', lang), msg)
                return
            
            self._pdf_path = path
            self.settings['last_open_path'] = os.path.dirname(path)
            
            # الحصول على عدد الصفحات
            try:
                import fitz
                doc = fitz.open(path)
                self._page_count = len(doc)
                doc.close()
                
                filename = os.path.basename(path)
                self._file_info.setText(
                    f"📄 {filename}\n"
                    f"📝 {self._page_count} {tr('page', lang)}"
                )
                self._file_info.setStyleSheet(f"color: {COLORS['accent']}; font-size: 13px; padding: 8px;")
                
                # تحديث range الصفحات
                self._from_page.setMaximum(self._page_count)
                self._to_page.setMaximum(self._page_count)
                self._to_page.setValue(self._page_count)
                
                self._convert_btn.setEnabled(True)
                
                # اقتراح اسم ملف الحفظ
                base_name = os.path.splitext(filename)[0]
                save_dir = self._save_path_label.text()
                self._output_path = os.path.join(save_dir, f"{base_name}_converted.docx")
                
            except Exception as e:
                self._file_info.setText(f"❌ فشل قراءة الملف")
                self._file_info.setStyleSheet(f"color: {COLORS['danger']}; font-size: 13px; padding: 8px;")
                self._convert_btn.setEnabled(False)
    
    def _toggle_page_selection(self, checked):
        self._from_page.setEnabled(not checked)
        self._to_page.setEnabled(not checked)
    
    def _browse_save_location(self):
        lang = self.settings.get('language', 'ar')
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr('save_as', lang),
            getattr(self, '_output_path', os.path.expanduser('~\\Documents\\output.docx')),
            get_word_save_filter(lang)
        )
        if path:
            path = ensure_docx_extension(path)
            self._output_path = path
            self._save_path_label.setText(os.path.dirname(path))
    
    def _start_conversion(self):
        if not self._pdf_path:
            return
        
        lang = self.settings.get('language', 'ar')
        
        # تحديد مكان الحفظ
        if not hasattr(self, '_output_path'):
            path, _ = QFileDialog.getSaveFileName(
                self, tr('save_as', lang), '', get_word_save_filter(lang)
            )
            if not path:
                return
            self._output_path = ensure_docx_extension(path)
        
        # تحديد الصفحات
        pages = None
        if not self._all_pages_check.isChecked():
            from_p = self._from_page.value() - 1
            to_p = self._to_page.value()
            pages = list(range(from_p, to_p))
        
        # تحديد الوضع
        mode = 'handwritten' if self.settings.get('handwriting_mode', False) else 'printed'
        
        # إعداد الواجهة
        self._convert_btn.setEnabled(False)
        self._select_btn.setEnabled(False)
        self._progress_card.start(tr('converting', lang))
        self._result_frame.hide()
        
        # بدء التحويل
        self._worker = PDFConversionWorker(
            pdf_path=self._pdf_path,
            output_path=self._output_path,
            ocr_engine=self.ocr_engine,
            image_processor=self.image_processor,
            pages=pages,
            mode=mode,
            font_name=self.settings.get('font_name', 'Simplified Arabic'),
            font_size=self.settings.get('font_size', 14)
        )
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.start()
    
    def _cancel_conversion(self):
        if self._worker and self._worker.isRunning():
            self._worker.cancel()
    
    def _on_progress(self, current, total, message):
        self._progress_card.update_progress(current, total, message)
    
    def _on_finished(self, success, message):
        lang = self.settings.get('language', 'ar')
        
        if success:
            self._progress_card.finish_success(tr('completed', lang))
            self._result_path = message
            self._result_frame.show()
        else:
            self._progress_card.finish_error(message)
        
        self._convert_btn.setEnabled(True)
        self._select_btn.setEnabled(True)
        self._worker = None
    
    def _open_result_file(self):
        if hasattr(self, '_result_path') and os.path.exists(self._result_path):
            os.startfile(self._result_path)
    
    def _open_result_folder(self):
        if hasattr(self, '_result_path'):
            folder = os.path.dirname(self._result_path)
            if os.path.exists(folder):
                os.startfile(folder)
    
    def update_language(self, lang: str):
        """تحديث اللغة."""
        # يتم تحديث النصوص عند إعادة بناء الواجهة
        pass

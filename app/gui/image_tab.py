"""
Image Tab - تبويب تحويل الصور إلى Word
========================================
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFileDialog, QFrame, QMessageBox
)
from PySide6.QtCore import Qt
import os

from app.gui.styles import COLORS
from app.gui.widgets import DragDropArea, ProgressCard, FileListWidget
from app.gui.workers import ImageConversionWorker
from app.utils.arabic_utils import tr
from app.utils.file_handler import (
    get_supported_image_filters, get_word_save_filter, ensure_docx_extension
)
from app.utils.security import validate_file_integrity, ALLOWED_IMAGE_EXTENSIONS


class ImageTab(QWidget):
    """تبويب تحويل الصور إلى Word."""
    
    def __init__(self, ocr_engine, image_processor, settings, parent=None):
        super().__init__(parent)
        self.ocr_engine = ocr_engine
        self.image_processor = image_processor
        self.settings = settings
        self._worker = None
        
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lang = self.settings.get('language', 'ar')
        
        # ===== العنوان =====
        self._title_label = QLabel(tr('tab_images', lang))
        self._title_label.setObjectName("title")
        layout.addWidget(self._title_label)
        
        # ===== منطقة السحب والإفلات =====
        self._drag_area = DragDropArea(
            text=tr('drag_drop', lang),
            accepted_extensions=ALLOWED_IMAGE_EXTENSIONS
        )
        self._drag_area.files_dropped.connect(self._on_files_dropped)
        self._drag_area.clicked.connect(self._select_images)
        layout.addWidget(self._drag_area)
        
        # ===== أزرار الاختيار =====
        btn_row = QHBoxLayout()
        
        self._select_images_btn = QPushButton("🖼️  " + tr('select_images', lang))
        self._select_images_btn.setObjectName("btn_secondary")
        self._select_images_btn.setMinimumHeight(40)
        self._select_images_btn.clicked.connect(self._select_images)
        btn_row.addWidget(self._select_images_btn)
        
        self._select_folder_btn = QPushButton("📁  " + tr('select_folder', lang))
        self._select_folder_btn.setObjectName("btn_secondary")
        self._select_folder_btn.setMinimumHeight(40)
        self._select_folder_btn.clicked.connect(self._select_folder)
        btn_row.addWidget(self._select_folder_btn)
        
        btn_row.addStretch()
        layout.addLayout(btn_row)
        
        # ===== قائمة الملفات =====
        self._file_list = FileListWidget()
        self._file_list.files_changed.connect(self._on_files_changed)
        layout.addWidget(self._file_list)
        
        # ===== شريط التقدم =====
        self._progress_card = ProgressCard()
        self._progress_card.cancel_clicked.connect(self._cancel_conversion)
        layout.addWidget(self._progress_card)
        
        # ===== زر التحويل =====
        btn_row2 = QHBoxLayout()
        btn_row2.addStretch()
        
        self._convert_btn = QPushButton("🚀  " + tr('start_conversion', lang))
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
        
        self._open_file_btn = QPushButton("📂  " + tr('open_file', lang))
        self._open_file_btn.setObjectName("btn_success")
        self._open_file_btn.clicked.connect(self._open_result_file)
        result_layout.addWidget(self._open_file_btn)
        
        self._open_folder_btn = QPushButton("📁  " + tr('open_folder', lang))
        self._open_folder_btn.setObjectName("btn_secondary")
        self._open_folder_btn.clicked.connect(self._open_result_folder)
        result_layout.addWidget(self._open_folder_btn)
        
        result_layout.addStretch()
        layout.addWidget(self._result_frame)
        
        layout.addStretch()
    
    def _select_images(self):
        lang = self.settings.get('language', 'ar')
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            tr('select_images', lang),
            self.settings.get('last_open_path', ''),
            get_supported_image_filters(lang)
        )
        
        if paths:
            self.settings['last_open_path'] = os.path.dirname(paths[0])
            valid_paths = []
            for p in paths:
                valid, msg = validate_file_integrity(p, 'image')
                if valid:
                    valid_paths.append(p)
            
            if valid_paths:
                self._file_list.add_files(valid_paths)
    
    def _select_folder(self):
        lang = self.settings.get('language', 'ar')
        folder = QFileDialog.getExistingDirectory(
            self,
            tr('select_folder', lang),
            self.settings.get('last_open_path', '')
        )
        
        if folder:
            self.settings['last_open_path'] = folder
            files = []
            for f in os.listdir(folder):
                _, ext = os.path.splitext(f)
                if ext.lower() in ALLOWED_IMAGE_EXTENSIONS:
                    full_path = os.path.join(folder, f)
                    valid, _ = validate_file_integrity(full_path, 'image')
                    if valid:
                        files.append(full_path)
            
            if files:
                files.sort()
                self._file_list.add_files(files)
    
    def _on_files_dropped(self, files):
        valid_files = []
        for f in files:
            valid, _ = validate_file_integrity(f, 'image')
            if valid:
                valid_files.append(f)
        
        if valid_files:
            self._file_list.add_files(valid_files)
    
    def _on_files_changed(self, files):
        self._convert_btn.setEnabled(len(files) > 0)
    
    def _start_conversion(self):
        files = self._file_list.get_files()
        if not files:
            return
        
        lang = self.settings.get('language', 'ar')
        
        # اختيار مكان الحفظ
        default_name = "images_converted.docx"
        save_dir = self.settings.get('default_save_path', os.path.expanduser('~\\Documents'))
        
        path, _ = QFileDialog.getSaveFileName(
            self,
            tr('save_as', lang),
            os.path.join(save_dir, default_name),
            get_word_save_filter(lang)
        )
        
        if not path:
            return
        
        path = ensure_docx_extension(path)
        
        # تحديد الوضع
        if not self.settings.get('preprocessing', True):
            mode = 'graphic'
        else:
            mode = 'handwritten' if self.settings.get('handwriting_mode', False) else 'photo'
        
        # إعداد الواجهة
        self._convert_btn.setEnabled(False)
        self._progress_card.start(tr('converting', lang))
        self._result_frame.hide()
        
        # بدء التحويل
        self._worker = ImageConversionWorker(
            image_paths=files,
            output_path=path,
            ocr_engine=self.ocr_engine,
            image_processor=self.image_processor,
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
        """تحديث نصوص الواجهة عند تغيير اللغة."""
        self._title_label.setText(tr('tab_images', lang))
        if hasattr(self._drag_area, 'update_language'):
            self._drag_area.update_language(lang)
        self._select_images_btn.setText("🖼️  " + tr('select_images', lang))
        self._select_folder_btn.setText("📁  " + tr('select_folder', lang))
        self._convert_btn.setText("🚀  " + tr('start_conversion', lang))
        self._open_file_btn.setText("📂  " + tr('open_file', lang))
        self._open_folder_btn.setText("📁  " + tr('open_folder', lang))
        if hasattr(self._file_list, 'update_language'):
            self._file_list.update_language(lang)
        if hasattr(self._progress_card, 'update_language'):
            self._progress_card.update_language(lang)

"""
Settings Tab - تبويب الإعدادات
================================
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QFormLayout, QFileDialog, QFrame,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal
import os
import json

from app.gui.styles import COLORS
from app.utils.arabic_utils import tr


# مسار ملف الإعدادات في APPDATA لضمان صلاحيات الكتابة دائماً
appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
settings_dir = os.path.join(appdata, 'SmartDocumentConverter')
os.makedirs(settings_dir, exist_ok=True)
SETTINGS_FILE = os.path.join(settings_dir, 'settings.json')

# الإعدادات الافتراضية
DEFAULT_SETTINGS = {
    'language': 'ar',
    'ocr_languages': ['ar', 'en'],
    'ocr_quality': 'balanced',
    'default_save_path': os.path.expanduser('~\\Documents'),
    'font_name': 'Simplified Arabic',
    'font_size': 14,
    'handwriting_mode': False,
    'preprocessing': True,
    'last_open_path': '',
}


def load_settings() -> dict:
    """تحميل الإعدادات من الملف."""
    settings = DEFAULT_SETTINGS.copy()
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                settings.update(saved)
    except Exception:
        pass
    return settings


def save_settings(settings: dict):
    """حفظ الإعدادات في الملف."""
    try:
        # حفظ فقط الإعدادات المختلفة عن الافتراضية
        to_save = {}
        for key, value in settings.items():
            to_save[key] = value
        
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(to_save, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class SettingsTab(QWidget):
    """تبويب الإعدادات."""
    
    language_changed = Signal(str)
    settings_changed = Signal(dict)
    
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.settings = settings
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(24, 24, 24, 24)
        
        lang = self.settings.get('language', 'ar')
        
        # ===== العنوان =====
        self._title_label = QLabel(tr('tab_settings', lang))
        self._title_label.setObjectName("title")
        layout.addWidget(self._title_label)
        
        # ===== إعدادات الواجهة =====
        self._ui_group = QGroupBox(tr('interface_language', lang))
        ui_form = QFormLayout(self._ui_group)
        ui_form.setSpacing(12)
        
        self._lang_combo = QComboBox()
        self._lang_combo.addItem("العربية", "ar")
        self._lang_combo.addItem("English", "en")
        self._lang_combo.setCurrentIndex(0 if lang == 'ar' else 1)
        self._lang_combo.currentIndexChanged.connect(self._on_language_changed)
        self._lang_label = QLabel(tr('language', lang) + ":")
        ui_form.addRow(self._lang_label, self._lang_combo)
        
        layout.addWidget(self._ui_group)
        
        # ===== إعدادات OCR =====
        self._ocr_group = QGroupBox(tr('ocr_language', lang))
        ocr_form = QFormLayout(self._ocr_group)
        ocr_form.setSpacing(12)
        
        self._ocr_lang_combo = QComboBox()
        self._ocr_lang_combo.addItem(tr('both_languages', lang), "both")
        self._ocr_lang_combo.addItem(tr('arabic_only', lang), "ar")
        self._ocr_lang_combo.addItem(tr('english_only', lang), "en")
        
        current_ocr = self.settings.get('ocr_languages', ['ar', 'en'])
        if current_ocr == ['ar']:
            self._ocr_lang_combo.setCurrentIndex(1)
        elif current_ocr == ['en']:
            self._ocr_lang_combo.setCurrentIndex(2)
        else:
            self._ocr_lang_combo.setCurrentIndex(0)
        
        self._ocr_lang_combo.currentIndexChanged.connect(self._on_settings_changed)
        self._ocr_lang_label = QLabel(tr('ocr_language', lang) + ":")
        ocr_form.addRow(self._ocr_lang_label, self._ocr_lang_combo)
        
        # جودة OCR
        self._quality_combo = QComboBox()
        self._quality_combo.addItem(tr('quality_fast', lang), "fast")
        self._quality_combo.addItem(tr('quality_balanced', lang), "balanced")
        self._quality_combo.addItem(tr('quality_high', lang), "high")
        
        quality = self.settings.get('ocr_quality', 'balanced')
        quality_idx = {'fast': 0, 'balanced': 1, 'high': 2}.get(quality, 1)
        self._quality_combo.setCurrentIndex(quality_idx)
        self._quality_combo.currentIndexChanged.connect(self._on_settings_changed)
        self._quality_label = QLabel(tr('ocr_quality', lang) + ":")
        ocr_form.addRow(self._quality_label, self._quality_combo)
        
        # وضع الخط اليدوي
        self._handwriting_check = QCheckBox(tr('handwriting_mode', lang))
        self._handwriting_check.setChecked(self.settings.get('handwriting_mode', False))
        self._handwriting_check.toggled.connect(self._on_settings_changed)
        ocr_form.addRow("", self._handwriting_check)
        
        # معالجة الصور المسبقة
        self._preprocess_check = QCheckBox(tr('preprocessing', lang))
        self._preprocess_check.setChecked(self.settings.get('preprocessing', True))
        self._preprocess_check.toggled.connect(self._on_settings_changed)
        ocr_form.addRow("", self._preprocess_check)
        
        layout.addWidget(self._ocr_group)
        
        # ===== إعدادات الخط =====
        self._font_group = QGroupBox(tr('font_name', lang))
        font_form = QFormLayout(self._font_group)
        font_form.setSpacing(12)
        
        self._font_combo = QComboBox()
        fonts = ['Simplified Arabic', 'Traditional Arabic', 'Arial', 
                 'Tahoma', 'Times New Roman', 'Sakkal Majalla']
        self._font_combo.addItems(fonts)
        current_font = self.settings.get('font_name', 'Simplified Arabic')
        if current_font in fonts:
            self._font_combo.setCurrentText(current_font)
        self._font_combo.currentIndexChanged.connect(self._on_settings_changed)
        self._font_name_label = QLabel(tr('font_name', lang) + ":")
        font_form.addRow(self._font_name_label, self._font_combo)
        
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(8, 36)
        self._font_size_spin.setValue(self.settings.get('font_size', 14))
        self._font_size_spin.valueChanged.connect(self._on_settings_changed)
        self._font_size_label = QLabel(tr('font_size', lang) + ":")
        font_form.addRow(self._font_size_label, self._font_size_spin)
        
        layout.addWidget(self._font_group)
        
        # ===== مسار الحفظ الافتراضي =====
        self._save_group = QGroupBox(tr('default_save_path', lang))
        save_layout_inner = QHBoxLayout(self._save_group)
        
        self._save_path_label = QLabel(
            self.settings.get('default_save_path', os.path.expanduser('~\\Documents'))
        )
        self._save_path_label.setStyleSheet(f"color: {COLORS['text_primary']};")
        self._save_path_label.setWordWrap(True)
        save_layout_inner.addWidget(self._save_path_label, 1)
        
        self._browse_btn = QPushButton(tr('browse', lang))
        self._browse_btn.setObjectName("btn_secondary")
        self._browse_btn.clicked.connect(self._browse_default_path)
        save_layout_inner.addWidget(self._browse_btn)
        
        layout.addWidget(self._save_group)
        
        # ===== أزرار =====
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        self._save_msg = QLabel("")
        self._save_msg.setStyleSheet(f"color: {COLORS['success']}; font-weight: bold;")
        self._save_msg.hide()
        btn_row.addWidget(self._save_msg)
        
        self._save_btn = QPushButton("💾  " + (tr('save_settings', lang) if hasattr(self, 'tr') else "حفظ الإعدادات"))
        self._save_btn.setObjectName("btn_success")
        self._save_btn.clicked.connect(self._manual_save)
        btn_row.addWidget(self._save_btn)
        
        self._reset_btn = QPushButton("🔄  " + tr('reset_settings', lang))
        self._reset_btn.setObjectName("btn_danger")
        self._reset_btn.clicked.connect(self._reset_settings)
        btn_row.addWidget(self._reset_btn)
        
        layout.addLayout(btn_row)
        
        layout.addStretch()
    
    def _on_language_changed(self):
        lang = self._lang_combo.currentData()
        self.settings['language'] = lang
        save_settings(self.settings)
        self.language_changed.emit(lang)
    
    def _on_settings_changed(self):
        # تحديث إعدادات OCR
        ocr_val = self._ocr_lang_combo.currentData()
        if ocr_val == 'ar':
            self.settings['ocr_languages'] = ['ar']
        elif ocr_val == 'en':
            self.settings['ocr_languages'] = ['en']
        else:
            self.settings['ocr_languages'] = ['ar', 'en']
        
        self.settings['ocr_quality'] = self._quality_combo.currentData()
        self.settings['handwriting_mode'] = self._handwriting_check.isChecked()
        self.settings['preprocessing'] = self._preprocess_check.isChecked()
        self.settings['font_name'] = self._font_combo.currentText()
        self.settings['font_size'] = self._font_size_spin.value()
        
        save_settings(self.settings)
        self.settings_changed.emit(self.settings)
    
    def _browse_default_path(self):
        lang = self.settings.get('language', 'ar')
        folder = QFileDialog.getExistingDirectory(
            self,
            tr('default_save_path', lang),
            self.settings.get('default_save_path', '')
        )
        if folder:
            self.settings['default_save_path'] = folder
            self._save_path_label.setText(folder)
            save_settings(self.settings)
    
    def _reset_settings(self):
        self.settings.update(DEFAULT_SETTINGS.copy())
        save_settings(self.settings)
        
        # إعادة تعيين الواجهة
        self._lang_combo.setCurrentIndex(0)
        self._ocr_lang_combo.setCurrentIndex(0)
        self._quality_combo.setCurrentIndex(1)
        self._handwriting_check.setChecked(False)
        self._preprocess_check.setChecked(True)
        self._font_combo.setCurrentText('Simplified Arabic')
        self._font_size_spin.setValue(14)
        self._save_path_label.setText(DEFAULT_SETTINGS['default_save_path'])
        
        self.settings_changed.emit(self.settings)

    def _manual_save(self):
        """حفظ يدوي للإعدادات وإظهار رسالة تأكيد."""
        save_settings(self.settings)
        lang = self.settings.get('language', 'ar')
        from PySide6.QtCore import QTimer
        
        # محاولة جلب الترجمة أو استخدام نص ثابت
        try:
            msg = tr('settings_saved', lang)
        except:
            msg = "تم حفظ الإعدادات بنجاح!" if lang == 'ar' else "Settings saved successfully!"
            
        self._save_msg.setText(f"✅ {msg}")
        self._save_msg.show()
        
        # إخفاء الرسالة بعد 3 ثوانٍ
        QTimer.singleShot(3000, self._save_msg.hide)
        
    def update_language(self, lang: str):
        """تحديث نصوص الواجهة عند تغيير اللغة."""
        self._title_label.setText(tr('tab_settings', lang))
        
        self._ui_group.setTitle(tr('interface_language', lang))
        self._lang_label.setText(tr('language', lang) + ":")
        
        self._ocr_group.setTitle(tr('ocr_language', lang))
        self._ocr_lang_label.setText(tr('ocr_language', lang) + ":")
        self._ocr_lang_combo.setItemText(0, tr('both_languages', lang))
        self._ocr_lang_combo.setItemText(1, tr('arabic_only', lang))
        self._ocr_lang_combo.setItemText(2, tr('english_only', lang))
        
        self._quality_label.setText(tr('ocr_quality', lang) + ":")
        self._quality_combo.setItemText(0, tr('quality_fast', lang))
        self._quality_combo.setItemText(1, tr('quality_balanced', lang))
        self._quality_combo.setItemText(2, tr('quality_high', lang))
        
        self._handwriting_check.setText(tr('handwriting_mode', lang))
        self._preprocess_check.setText(tr('preprocessing', lang))
        
        self._font_group.setTitle(tr('font_name', lang))
        self._font_name_label.setText(tr('font_name', lang) + ":")
        self._font_size_label.setText(tr('font_size', lang) + ":")
        
        self._save_group.setTitle(tr('default_save_path', lang))
        self._browse_btn.setText(tr('browse', lang))
        
        self._save_btn.setText("💾  " + tr('save_settings', lang))
        self._reset_btn.setText("🔄  " + tr('reset_settings', lang))


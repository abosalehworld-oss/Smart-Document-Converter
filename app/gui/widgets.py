"""
Widgets - مكونات واجهة مشتركة
================================
مكونات UI قابلة لإعادة الاستخدام.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QFrame, QPushButton, QProgressBar, QListWidget,
    QListWidgetItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QMimeData
from PySide6.QtGui import QDragEnterEvent, QDropEvent, QFont
import os

from app.gui.styles import COLORS


class DragDropArea(QFrame):
    """منطقة سحب وإفلات الملفات."""
    
    files_dropped = Signal(list)  # قائمة مسارات الملفات
    clicked = Signal()
    
    def __init__(self, text: str = "اسحب وأفلت الملفات هنا", 
                 accepted_extensions: set = None, parent=None):
        super().__init__(parent)
        self.accepted_extensions = accepted_extensions or {
            '.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp', '.pdf'
        }
        
        self.setAcceptDrops(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(180)
        
        # التصميم
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_input']};
                border: 2px dashed {COLORS['border']};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary']};
                background-color: {COLORS['bg_card']};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # أيقونة
        icon_label = QLabel("📁")
        icon_label.setStyleSheet("font-size: 48px; border: none;")
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)
        
        # نص
        self._text_label = QLabel(text)
        self._text_label.setStyleSheet(f"""
            color: {COLORS['text_secondary']};
            font-size: 14px;
            border: none;
        """)
        self._text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._text_label.setWordWrap(True)
        layout.addWidget(self._text_label)
    
    def set_text(self, text: str):
        self._text_label.setText(text)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {COLORS['bg_card']};
                    border: 2px dashed {COLORS['primary']};
                    border-radius: 16px;
                }}
            """)
    
    def dragLeaveEvent(self, event):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_input']};
                border: 2px dashed {COLORS['border']};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary']};
                background-color: {COLORS['bg_card']};
            }}
        """)
    
    def dropEvent(self, event: QDropEvent):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['bg_input']};
                border: 2px dashed {COLORS['border']};
                border-radius: 16px;
            }}
            QFrame:hover {{
                border-color: {COLORS['primary']};
                background-color: {COLORS['bg_card']};
            }}
        """)
        
        files = []
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if os.path.isfile(path):
                _, ext = os.path.splitext(path)
                if ext.lower() in self.accepted_extensions:
                    files.append(path)
            elif os.path.isdir(path):
                for f in os.listdir(path):
                    _, ext = os.path.splitext(f)
                    if ext.lower() in self.accepted_extensions:
                        files.append(os.path.join(path, f))
        
        if files:
            self.files_dropped.emit(files)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


class ProgressCard(QFrame):
    """بطاقة شريط التقدم مع تفاصيل."""
    
    cancel_clicked = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet(f"""
            QFrame#card {{
                background-color: {COLORS['bg_card']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        
        # عنوان العملية
        self._title = QLabel("جاري التحويل...")
        self._title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['text_primary']};")
        layout.addWidget(self._title)
        
        # تفاصيل
        self._detail = QLabel("")
        self._detail.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(self._detail)
        
        # شريط التقدم
        self._progress = QProgressBar()
        self._progress.setMinimum(0)
        self._progress.setMaximum(100)
        self._progress.setValue(0)
        self._progress.setMinimumHeight(24)
        layout.addWidget(self._progress)
        
        # صف الأزرار
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self._cancel_btn = QPushButton("إلغاء")
        self._cancel_btn.setObjectName("btn_danger")
        self._cancel_btn.setFixedWidth(100)
        self._cancel_btn.clicked.connect(self.cancel_clicked.emit)
        btn_layout.addWidget(self._cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.hide()
    
    def start(self, title: str = "جاري التحويل..."):
        self._title.setText(title)
        self._detail.setText("")
        self._progress.setValue(0)
        self._cancel_btn.setEnabled(True)
        self.show()
    
    def update_progress(self, current: int, total: int, message: str = ""):
        if total > 0:
            percent = int((current / total) * 100)
            self._progress.setValue(percent)
            self._progress.setFormat(f"{percent}%")
        self._detail.setText(message)
    
    def finish_success(self, message: str = "تم بنجاح!"):
        self._progress.setValue(100)
        self._title.setText("✅ " + message)
        self._title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['success']};")
        self._cancel_btn.hide()
    
    def finish_error(self, message: str = "فشل"):
        self._title.setText("❌ " + message)
        self._title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['danger']};")
        self._cancel_btn.hide()
    
    def reset(self):
        self._title.setStyleSheet(f"font-size: 15px; font-weight: bold; color: {COLORS['text_primary']};")
        self._cancel_btn.show()
        self._progress.setValue(0)
        self.hide()


class FileListWidget(QFrame):
    """قائمة الملفات المختارة مع إمكانية الحذف."""
    
    files_changed = Signal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._files = []
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # عنوان + عداد
        header = QHBoxLayout()
        self._count_label = QLabel("0 ملفات")
        self._count_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        header.addWidget(self._count_label)
        
        header.addStretch()
        
        clear_btn = QPushButton("مسح الكل")
        clear_btn.setObjectName("btn_secondary")
        clear_btn.setFixedHeight(30)
        clear_btn.clicked.connect(self.clear_files)
        header.addWidget(clear_btn)
        
        layout.addLayout(header)
        
        # قائمة الملفات
        self._list = QListWidget()
        self._list.setMinimumHeight(100)
        layout.addWidget(self._list)
    
    def add_files(self, paths: list):
        for path in paths:
            if path not in self._files:
                self._files.append(path)
                filename = os.path.basename(path)
                item = QListWidgetItem(f"📄 {filename}")
                item.setData(Qt.ItemDataRole.UserRole, path)
                self._list.addItem(item)
        
        self._update_count()
        self.files_changed.emit(self._files)
    
    def clear_files(self):
        self._files.clear()
        self._list.clear()
        self._update_count()
        self.files_changed.emit(self._files)
    
    def get_files(self) -> list:
        return list(self._files)
    
    def _update_count(self):
        count = len(self._files)
        self._count_label.setText(f"{count} ملفات" if count != 1 else "1 ملف")
    
    @property
    def file_count(self) -> int:
        return len(self._files)

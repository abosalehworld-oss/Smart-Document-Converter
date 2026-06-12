; ============================================
; PyInstaller Spec File
; محوّل المستندات الذكي - Smart Document Converter
; ============================================

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),
    ],
    hiddenimports=[
        # EasyOCR
        'easyocr',
        'easyocr.easyocr',
        'easyocr.detection',
        'easyocr.recognition',
        'easyocr.utils',
        'easyocr.config',
        # PyTorch
        'torch',
        'torch.nn',
        'torch.nn.functional',
        'torchvision',
        'torchvision.transforms',
        'torchvision.models',
        # OpenCV
        'cv2',
        # PyMuPDF
        'fitz',
        # python-docx
        'docx',
        'docx.shared',
        'docx.enum',
        'docx.enum.text',
        'docx.oxml',
        'docx.oxml.ns',
        # PySide6
        'PySide6',
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        # Arabic
        'arabic_reshaper',
        'bidi',
        'bidi.algorithm',
        # Pillow
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        # Other
        'numpy',
        'scipy',
        'skimage',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # استبعاد حاجات مش محتاجينها عشان نقلل الحجم
        'matplotlib',
        'notebook',
        'ipython',
        'jupyter',
        'tkinter',
        'unittest',
        'email',
        'html',
        'http',
        'urllib',
        'xmlrpc',
        'ftplib',
        'smtplib',
        'imaplib',
        'poplib',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='SmartDocConverter',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # بدون نافذة كونسول
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='SmartDocConverter',
)

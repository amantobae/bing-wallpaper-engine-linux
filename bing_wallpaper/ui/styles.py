"""Modern Fluent/KDE Breeze inspired stylesheet for Bing Wallpaper Manager."""

MODERN_STYLE = """
/* Base Window & Global Fonts */
QMainWindow, QDialog {
    background-color: #1c1d21;
    color: #f0f0f5;
    font-family: 'Segoe UI', 'Noto Sans', sans-serif;
    font-size: 13px;
}

QWidget {
    color: #e4e4e7;
    outline: none;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #18191c;
    width: 8px;
    border-radius: 4px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #3f3f46;
    min-height: 25px;
    border-radius: 4px;
}
QScrollBar::handle:vertical:hover {
    background: #52525b;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}

/* Category Navigation Bar / Segmented Tabs */
#NavBar {
    background-color: #24252a;
    border-bottom: 1px solid #2f3036;
    padding: 6px 16px;
}

QPushButton.nav-btn {
    background-color: transparent;
    color: #a1a1aa;
    font-size: 14px;
    font-weight: 600;
    padding: 8px 18px;
    border-radius: 8px;
    border: none;
    text-align: center;
}
QPushButton.nav-btn:hover {
    background-color: #2e3037;
    color: #ffffff;
}
QPushButton.nav-btn:checked {
    background-color: #0078d4;
    color: #ffffff;
}

/* Hero Section (Monitor & Current Info) */
#HeroFrame {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #25262c, stop:1 #1e1f24);
    border: 1px solid #32343c;
    border-radius: 14px;
    padding: 16px;
    margin: 8px 16px;
}

QLabel#HeroTitle {
    font-size: 17px;
    font-weight: bold;
    color: #ffffff;
}

QLabel#HeroSubtitle {
    font-size: 12px;
    color: #94a3b8;
}

/* Primary Action Buttons */
QPushButton.primary-btn {
    background-color: #0078d4;
    color: #ffffff;
    font-size: 13px;
    font-weight: 600;
    padding: 8px 18px;
    border-radius: 8px;
    border: none;
}
QPushButton.primary-btn:hover {
    background-color: #1084d9;
}
QPushButton.primary-btn:pressed {
    background-color: #006cbe;
}
QPushButton.primary-btn:disabled {
    background-color: #333d47;
    color: #71717a;
}

/* Secondary Action Buttons */
QPushButton.secondary-btn {
    background-color: #2a2c33;
    color: #e2e8f0;
    font-size: 13px;
    font-weight: 500;
    padding: 8px 16px;
    border-radius: 8px;
    border: 1px solid #3b3e47;
}
QPushButton.secondary-btn:hover {
    background-color: #353842;
    border-color: #4b4f5a;
}
QPushButton.secondary-btn:pressed {
    background-color: #24262c;
}

/* Wallpaper Cards */
#CardFrame {
    background-color: #24252a;
    border: 1px solid #2f3138;
    border-radius: 12px;
}
#CardFrame:hover {
    border: 1px solid #0078d4;
    background-color: #272830;
}

#CardFrame QPushButton.secondary-btn {
    padding: 6px 8px;
    font-size: 12px;
}

#CardFrame QPushButton.primary-btn {
    padding: 6px 12px;
    font-size: 12px;
}

QLabel#CardTitle {
    font-size: 13px;
    font-weight: 600;
    color: #f4f4f5;
}

QLabel#CardDate {
    font-size: 11px;
    color: #71717a;
}

/* ComboBox & Inputs */
QComboBox {
    background-color: #24252a;
    border: 1px solid #3b3e47;
    border-radius: 6px;
    padding: 5px 12px;
    color: #f4f4f5;
}
QComboBox:hover {
    border-color: #0078d4;
}
QComboBox QAbstractItemView {
    background-color: #24252a;
    border: 1px solid #3b3e47;
    selection-background-color: #0078d4;
    color: #f4f4f5;
}

/* Status Bar */
QStatusBar {
    background-color: #18191c;
    border-top: 1px solid #28292e;
    color: #a1a1aa;
    font-size: 12px;
}
"""

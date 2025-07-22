import sys, pathlib
from PyQt6.QtWidgets import QApplication, QSpinBox

app = QApplication(sys.argv)

spin = QSpinBox()
spin.setRange(0, 99)
spin.setFixedWidth(120)          # wider box so big arrows fit
spin.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)  # default

# ── QSS stylesheet: replace arrow glyphs with SVG / PNG icons and enlarge ──
spin.setStyleSheet("""
/* === up button === */
QSpinBox::up-button {
    subcontrol-origin: border;
    subcontrol-position: right top;
    width: 40px;                 /* ← make it big */
    height: 40px;
    border: none;
    image: url(../images/arrow_up.png);   /*  ✅ your own asset */
}

/* hover / pressed (optional) */
QSpinBox::up-button:hover   { background: rgba(255,255,255,0.10); }
QSpinBox::up-button:pressed { background: rgba(255,255,255,0.20); }

/* === down button === */
QSpinBox::down-button {
    subcontrol-origin: border;
    subcontrol-position: right bottom;
    width: 40px;
    height: 40px;
    border: none;
    image: url(../images/arrow_down.png);
}

QSpinBox::down-button:hover   { background: rgba(255,255,255,0.10); }
QSpinBox::down-button:pressed { background: rgba(255,255,255,0.20); }
""")

spin.show()
sys.exit(app.exec())

# menu_page.py  (new file, or inline class)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore    import Qt
from PyQt6.QtGui     import QPixmap

class MenuPage(QWidget):
    def __init__(self, ser, parent=None):
        super().__init__(parent)
        
        self.ser = ser 

        self.setObjectName("CentralArea")                      
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        with open("Styles/styleMainPage.qss", "r") as f:
                    self.setStyleSheet(f.read())

        lay = QVBoxLayout(self)
        lay.setSpacing(16)

        # logo
        logo_lbl = QLabel()
        logo_lbl.setPixmap(
            QPixmap("images/logo.png")
            .scaledToWidth(150, Qt.TransformationMode.SmoothTransformation)
        )
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo_lbl, alignment=Qt.AlignmentFlag.AlignHCenter)

        # headline banner
        headline = QLabel("Welcome to the Interactive Demo Kit!")
        headline.setObjectName("IntroLabel")
        headline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(headline, alignment=Qt.AlignmentFlag.AlignHCenter)

        lay.addSpacing(18) 

        # primary button → AFM page
        self.afm_btn = QPushButton("Atomic Force Microscope")
        self.afm_btn.setObjectName("AfmBtn")
        lay.addWidget(self.afm_btn, alignment=Qt.AlignmentFlag.AlignHCenter)
        self.afm_btn.clicked.connect(self.on_afm_btn_clicked)

        lay.addSpacing(12) 

        # secondary → AFM page
        self.pwrpng_btn = QPushButton("Power Pong!")
        self.pwrpng_btn.setObjectName("PwrPngBtn")
        lay.addWidget(self.pwrpng_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        lay.addSpacing(12) 

        # tertiary -> Motor Fun page
        self.mtrfun_btn = QPushButton("Control and Feedback Tuning")
        self.mtrfun_btn.setObjectName("MtrFunBtn")
        lay.addWidget(self.mtrfun_btn, alignment=Qt.AlignmentFlag.AlignHCenter)

        lay.addSpacing(12) 

        lay.addStretch()    
    
    def on_afm_btn_clicked(self):
        """
        Send a single raw byte 0x01 (decimal 1 = AFM).
        """
        if self.ser.is_open:
            self.ser.write(b"\x01")      # GOOD: raw byte, not an int
            self.ser.flush()
        


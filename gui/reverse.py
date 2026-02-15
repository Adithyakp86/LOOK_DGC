from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QLabel, QVBoxLayout, QRadioButton, QHBoxLayout

from tools import ToolWidget


class ReverseWidget(ToolWidget):
    def __init__(self, parent=None):
        super(ReverseWidget, self).__init__(parent)

        self.google_radio = QRadioButton(self.tr("Google Images"))
        self.google_radio.setIcon(QIcon("icons/google.svg"))
        self.yandex_radio = QRadioButton(self.tr("Yandex"))
        self.bing_radio = QRadioButton(self.tr("Bing"))
        self.bing_radio.setIcon(QIcon("icons/bing.svg"))
        self.tineye_radio = QRadioButton(self.tr("TinEye"))
        self.tineye_radio.setIcon(QIcon("icons/tineye.png"))
        self.google_radio.setChecked(True)
        self.last_radio = self.google_radio
        self.web_view = QWebEngineView()
        self.web_view.setZoomFactor(1.1)
        self.choose()

        self.google_radio.clicked.connect(self.choose)
        self.yandex_radio.clicked.connect(self.choose)
        self.bing_radio.clicked.connect(self.choose)
        self.tineye_radio.clicked.connect(self.choose)

        top_layout = QHBoxLayout()
        top_layout.addWidget(QLabel(self.tr("Search engine:")))
        top_layout.addWidget(self.google_radio)
        top_layout.addWidget(self.yandex_radio)
        top_layout.addWidget(self.bing_radio)
        top_layout.addWidget(self.tineye_radio)
        top_layout.addStretch()
        main_layout = QVBoxLayout()
        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.web_view)
        self.setLayout(main_layout)

    def choose(self):
        if self.google_radio.isChecked():
            self.web_view.load(QUrl("https://images.google.com/"))
            self.last_radio = self.google_radio
        elif self.yandex_radio.isChecked():
            self.web_view.load(QUrl("https://yandex.com/images/"))
            self.last_radio = self.yandex_radio
        elif self.bing_radio.isChecked():
            self.web_view.load(QUrl("https://www.bing.com/images"))
            self.last_radio = self.bing_radio
        elif self.tineye_radio.isChecked():
            self.web_view.load(QUrl("https://tineye.com/"))
            self.last_radio = self.tineye_radio
        else:
            self.last_radio.setChecked(True)

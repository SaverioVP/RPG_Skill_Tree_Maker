from PyQt5.QtWidgets import QGraphicsTextItem, QGraphicsRectItem
from PyQt5.QtGui import QFont, QColor, QBrush, QPen
from PyQt5.QtCore import Qt, QRectF


class Tooltip(QGraphicsTextItem):
    # A floating tooltip for showing upgrade details when hovering over a node.
    def __init__(self, scene):
        super().__init__("")
        self.scene = scene
        self.setDefaultTextColor(Qt.white)
        self.setFont(QFont("Arial", 10, QFont.Bold))

        self.bg_rect = QGraphicsRectItem()
        self.bg_rect.setBrush(QBrush(QColor(0, 0, 0, 200)))  # Semi-transparent black
        self.bg_rect.setPen(QPen(Qt.white))  # Border
        self.scene.addItem(self.bg_rect)  # Add background first

        self.scene.addItem(self)  # Add text AFTER background
        self.setZValue(10)  # Ensure tooltip text appears above everything
        self.bg_rect.setZValue(9)  # Background is just below text
        self.setVisible(False)
        self.bg_rect.setVisible(False)

    def update_tooltip(self, text, position):
        self.setPlainText(text)
        self.setVisible(True)
        self.bg_rect.setVisible(True)

        # Adjust background size dynamically
        text_rect = self.boundingRect()
        padding = 10  # Space around text
        self.bg_rect.setRect(QRectF(0, 0, text_rect.width() + padding * 2, text_rect.height() + padding * 2))

        # Make Background stays behind text
        self.bg_rect.setPos(position.x() + 10, position.y() + 10)
        self.setPos(position.x() + 15, position.y() + 15)  # Slight offset

    def hide_tooltip(self):
        self.setVisible(False)
        self.bg_rect.setVisible(False)

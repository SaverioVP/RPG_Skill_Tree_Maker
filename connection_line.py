from PyQt5.QtWidgets import QGraphicsLineItem, QGraphicsPolygonItem
from PyQt5.QtGui import QPen, QPolygonF
from PyQt5.QtCore import Qt, QLineF, QPointF
import math

class ConnectionLine(QGraphicsLineItem):
    def __init__(self, start_node, end_node=None):
        super().__init__()
        self.start_node = start_node
        self.end_node = end_node  # This is None while following mouse

        self.setPen(QPen(Qt.black, 2))
        self.arrow_head = QGraphicsPolygonItem(self)
        self.arrow_head.setPen(QPen(Qt.black))
        self.arrow_head.setBrush(Qt.black)

        self.update_position()

    def update_position(self, mouse_pos=None):
        # Call while moving mouse or on dest. node
        start_center = self.start_node.sceneBoundingRect().center()

        if self.end_node:
            end_center = self.end_node.sceneBoundingRect().center()
        elif mouse_pos:
            end_center = mouse_pos
        else:
            return

        self.setLine(QLineF(start_center, end_center))
        self.update_arrowhead(start_center, end_center)

    def update_arrowhead(self, start, end):
        # Positions and rotates the arrowhead at the end of the line
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())

        # ✅ Define the arrowhead triangle
        arrow_size = 10
        p1 = end - QPointF(math.cos(angle - math.pi / 6) * arrow_size,
                           math.sin(angle - math.pi / 6) * arrow_size)
        p2 = end - QPointF(math.cos(angle + math.pi / 6) * arrow_size,
                           math.sin(angle + math.pi / 6) * arrow_size)

        self.arrow_head.setPolygon(QPolygonF([end, p1, p2]))
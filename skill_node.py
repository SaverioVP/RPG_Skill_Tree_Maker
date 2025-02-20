from PyQt5.QtWidgets import QGraphicsEllipseItem, QGraphicsTextItem
from PyQt5.QtGui import QBrush, QPen, QColor
from PyQt5.QtCore import Qt, QPointF
from .upgrade import Upgrade

class SkillNode(QGraphicsEllipseItem):
    def __init__(self, main_window, x, y, upgrade=None):
        super().__init__(-20, -20, 40, 40)  # Bounding box of ellipse is 40,40 and center is at 0,0 (-20, -20 top left)
        self.main_window = main_window  # ✅ Store reference to MainWindow
        self.setPos(x, y)  # ✅ Set initial position using x, y

        self.setBrush(QBrush(QColor(100, 100, 255)))

        self.default_pen = QPen(Qt.black, 2)  # ✅ Default black outline
        self.hover_pen = QPen(QColor(255, 215, 0), 3)  # ✅ Gold outline when hovered
        self.setPen(self.default_pen)

        self.setAcceptHoverEvents(True)  # ✅ Enable hover detection

        self.setFlags(
            QGraphicsEllipseItem.ItemIsMovable |
            QGraphicsEllipseItem.ItemIsSelectable)

        # ✅ Each node starts with an empty upgrade
        self.upgrade = Upgrade()

        # ✅ Initialize relationships
        self.prerequisites = []  # List of prerequisite nodes
        self.postrequisites = []  # List of postrequisite nodes


    def on_left_click_pressed(self):
        """Handles left-click on skill node."""
        print(f"Clicked on {self.skill_type} skill node!")

    def on_right_click_pressed(self):
        """Handles right-click on skill node."""
        print(f"Right-clicked on {self.skill_type} skill node!")

    def on_left_click_released(self):
        print("release left click over skill node")

    def on_right_click_released(self):
        print("release right click over skill node")

    def hoverEnterEvent(self, event):
        self.setPen(self.hover_pen)  # Highlight node
        self.main_window.update_hover_label("Node")

        prereq_text = ", ".join(self.get_prerequisite_names()) or "None"
        postreq_text = ", ".join(self.get_postrequisite_names()) or "None"

        description = f"Upgrade: {self.upgrade.name}\n{self.upgrade.description}\n"
        description += f"Prerequisites: {prereq_text}\nPostrequisites: {postreq_text}"

        self.main_window.tooltip.update_tooltip(description, event.scenePos())
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(self.default_pen)  # Reset to default outline
        self.main_window.update_hover_label(None)  # Reset hover label
        self.main_window.tooltip.hide_tooltip()  # ✅ Hide tooltip
        super().hoverLeaveEvent(event)

    def snap_to_grid(self):
        snapped_x = round(self.pos().x() / self.main_window.GRID_SIZE) * self.main_window.GRID_SIZE
        snapped_y = round(self.pos().y() / self.main_window.GRID_SIZE) * self.main_window.GRID_SIZE
        self.setPos(QPointF(snapped_x, snapped_y))


    def add_prerequisite(self, node):
        """Adds a prerequisite node and ensures it's linked properly."""
        if node not in self.prerequisites:
            self.prerequisites.append(node)
            node.postrequisites.append(self)  # ✅ Automatically add this node as a postrequisite

    def add_postrequisite(self, node):
        """Adds a postrequisite node and ensures it's linked properly."""
        if node not in self.postrequisites:
            self.postrequisites.append(node)
            node.prerequisites.append(self)  # ✅ Automatically add this node as a prerequisite

    def get_prerequisite_names(self):
        return [n.upgrade.name for n in self.prerequisites]

    def get_postrequisite_names(self):
        return [n.upgrade.name for n in self.postrequisites]
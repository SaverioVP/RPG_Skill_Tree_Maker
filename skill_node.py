from PyQt5.QtWidgets import QGraphicsEllipseItem
from PyQt5.QtGui import QBrush, QPen, QColor
from PyQt5.QtCore import Qt, QPointF
from upgrade import Upgrade
from connection_line import ConnectionLine


class SkillNode(QGraphicsEllipseItem):
    def __init__(self, main_window, x, y, upgrade=None, node_id=None):
        super().__init__(-20, -20, 40, 40)  # Bounding box of ellipse is 40,40 and center is at 0,0 (-20, -20 top left)
        self.main_window = main_window


        self.setBrush(QBrush(QColor(100, 100, 255)))

        self.default_pen = QPen(Qt.black, 2)  # Default black outline
        self.hover_pen = QPen(QColor(255, 215, 0), 3)  # Gold outline when hovered
        self.setPen(self.default_pen)

        self.setAcceptHoverEvents(True)

        self.setFlags(
            QGraphicsEllipseItem.ItemIsMovable |
            QGraphicsEllipseItem.ItemIsSelectable)



        # Initialize relationships
        self.prerequisites = []  # List of prerequisite nodes
        self.postrequisites = []  # List of postrequisite nodes

        # Track lines going into and out of node
        self.outgoing_lines = []
        self.incoming_lines = []

        self.setPos(x, y)  # Move after initializing the lines arrays

        # internal stuff
        if node_id is not None:
            self.node_id = node_id
        else:
            self.node_id = self.main_window.current_node_id
            self.main_window.current_node_id += 1

        # Each node starts with an empty upgrade
        self.upgrade = Upgrade(node_id=self.node_id)


    def on_left_click_pressed(self):
        print(f"Clicked on {self.skill_type} skill node!")

    def on_right_click_pressed(self):
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
        self.setPen(self.default_pen)
        self.main_window.update_hover_label(None)
        self.main_window.tooltip.hide_tooltip()
        super().hoverLeaveEvent(event)

    def snap_to_grid(self):
        snapped_x = round(self.pos().x() / self.main_window.GRID_SIZE) * self.main_window.GRID_SIZE
        snapped_y = round(self.pos().y() / self.main_window.GRID_SIZE) * self.main_window.GRID_SIZE
        self.setPos(snapped_x, snapped_y)

    def add_prerequisite(self, node):
        if node not in self.prerequisites:
            self.prerequisites.append(node)
            node.postrequisites.append(self)  # Add this node as a postrequisite

            line = ConnectionLine(node, self)  # direction always node (prereq) → self (postreq)
            self.main_window.scene.addItem(line)
            self.incoming_lines.append(line)
            node.outgoing_lines.append(line)

    def add_postrequisite(self, node):
        #if node not in self.postrequisites:
        #    self.postrequisites.append(node)
        #    node.prerequisites.append(self)  # Add this node as a prerequisite
        node.add_prerequisite(self)

    def get_prerequisite_names(self):
        return [n.upgrade.name for n in self.prerequisites]

    def get_postrequisite_names(self):
        return [n.upgrade.name for n in self.postrequisites]

    def move_lines(self):
        # Call this when moving nodes tou update their position
        for line in self.outgoing_lines:
            line.update_position()
        for line in self.incoming_lines:
            line.update_position()

    def setPos(self, x, y):
        # Overrides setPos to also move attached lines
        super().setPos(x, y)
        self.move_lines()

    def prep_for_deletion(self):
        # Called by main window when this is to be deleted.
        # Will resolve right before being deleted
        for prereq in self.prerequisites:
            if self in prereq.postrequisites:
                prereq.postrequisites.remove(self)
        for postreq in self.postrequisites:
            if self in postreq.prerequisites:
                postreq.prerequisites.remove(self)

        for line in self.incoming_lines:
            self.main_window.delete_connecting_line(line)

        for line in self.outgoing_lines:
            self.main_window.delete_connecting_line(line)

        self.incoming_lines.clear()
        self.outgoing_lines.clear()
        self.prerequisites.clear()
        self.postrequisites.clear()

        self.main_window.current_node_id -= 1

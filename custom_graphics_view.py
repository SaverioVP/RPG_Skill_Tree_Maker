from PyQt5.QtWidgets import QGraphicsView, QRubberBand
from PyQt5.QtCore import Qt, QRect, QPoint, QSize
from mouse_state import MouseState


class CustomGraphicsView(QGraphicsView):
    # This is basically the viewport. So stuff involving panning, selections, mouse inputs usually goes here.
    def __init__(self, scene, parent=None):
        super().__init__(scene, parent)
        self.main_window = parent  # Keep reference to MainWindow
        self.setDragMode(QGraphicsView.NoDrag)  # Disables Qt’s built-in item dragging (because we will handle dragging manually).
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)  # Keeps transformations (zooming, panning) centered around the cursor.

        # Init the rubber band selection box
        # self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        # self.rubber_band_origin = QPoint()

        # Variables for panning
        self.last_mouse_pos = QPoint(0, 0)

    def mousePressEvent(self, event):
        # Handles all mouse presses
        view_pos = event.pos()  # Coordinates relative to the QGraphicsView which is the viewport. Panning doesn't change these

        if event.button() == Qt.MiddleButton:
            # Panning
            self.main_window.mouse_state = MouseState.PANNING
            self.main_window.update_mouse_state_label()
            self.last_mouse_pos = view_pos
            self.setCursor(Qt.ClosedHandCursor)
            return

        elif event.button() == Qt.LeftButton:
            # Begin rubber band selection as long as not in the middle of dragging
            # self.rubber_band_origin = view_pos
            # self.rubber_band.setGeometry(QRect(self.rubber_band_origin, QSize(0,0)))
            # self.rubber_band.show()
            # Tell main window there was a left click press
            self.main_window.on_left_click_press(view_pos)
            return
        elif event.button() == Qt.RightButton:
            # Tell main window there was a right click press
            self.main_window.on_right_click_press(view_pos)
            return

    def mouseMoveEvent(self, event):
        view_pos = event.pos()
        if self.main_window.mouse_state == MouseState.PANNING:
            delta = view_pos - self.last_mouse_pos
            self.last_mouse_pos = view_pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
        # elif self.rubber_band.isVisible():
        #    # If doing a rubber band select, update the size of the rectangle
        #    self.rubber_band.setGeometry(QRect(self.rubber_band_origin, view_pos).normalized())
        elif self.main_window.dragging_nodes:
            self.main_window.on_left_click_drag(event)

        elif (self.main_window.mouse_state == MouseState.SELECTING_PREREQ or
              self.main_window.mouse_state == MouseState.SELECTING_POSTREQ) and self.main_window.temp_line:
            scene_pos = self.mapToScene(view_pos)
            self.main_window.temp_line.update_position(mouse_pos=scene_pos)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        view_pos = event.pos()
        if event.button() == Qt.MiddleButton:
            # Stop panning if release middle mouse
            self.main_window.mouse_state = MouseState.IDLE

            self.main_window.update_mouse_state_label()
            self.setCursor(Qt.ArrowCursor)

        elif event.button() == Qt.LeftButton:
            # Stop rubber band if release left click
            self.main_window.on_left_click_release(view_pos)
            # self.rubber_band.hide()

        elif event.button() == Qt.RightButton:
            self.main_window.on_right_click_release(view_pos)

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Delete:
            if self.main_window:
                self.main_window.delete_selected_nodes()
        super().keyPressEvent(event)

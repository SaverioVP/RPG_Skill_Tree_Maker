from PyQt5.QtWidgets import (
    QMainWindow, QGraphicsScene, QVBoxLayout, QMenu,
    QAction, QInputDialog, QLabel, QPushButton, QWidget
)
from PyQt5.QtGui import QPen, QFont, QBrush, QColor
from PyQt5.QtCore import Qt

from .skill_node import SkillNode
from .custom_graphics_view import CustomGraphicsView
from .tooltip import Tooltip
from .skill_panel import SkillPanel
from .mouse_state import MouseState
import json
import os  # To check if the save file exists




class MainWindow(QMainWindow):
    #  MainWindow is the entire application, which includes:
    #  - The QGraphicsScene
    #  - The QGraphicsView
    #  - The UI (labels, menus, etc.)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RPG Skill Tree Designer")
        self.setGeometry(100, 100, 800, 600)

        # Setup the Scene.  self.scene = A canvas that holds all skill nodes.
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 2000, 2000)  # Size of the Scene (need to scroll to get to extents)

        # Griddu
        self.GRID_SIZE = 60
        # Set up the custom graphics view to handle mouse interactions
        # self.view = A viewport (QGraphicsView) that displays scene.
        self.view = CustomGraphicsView(self.scene, self)
        self.view.centerOn(0, 0)  # Center view in top left corner
        self.setCentralWidget(self.view)
        self.dragging_nodes = None  # define the nodes being dragged by mouse cursor

        # Tootip
        # ✅ Create Tooltip (Hidden by Default)
        self.tooltip = Tooltip(self.scene)
        # rest
        self.init_ui()
        # Now laod the skill tree
        self.load_skill_tree()

        # Mouse state tracking
        self.mouse_state = MouseState.IDLE  # ✅ Start in IDLE mode
        self.selected_node = None  # ✅ Track the node being linked
        self.update_mouse_state_label()  # ✅ Update label

    def init_ui(self):
        ## Set up the scene with initial UI widgets and menus
        """Set up UI elements dynamically using a layout to prevent overlap."""
        self.ui_container = QWidget(self)  # ✅ Container for all UI elements
        self.ui_container.setGeometry(10, 10, 220, 250)  # Adjust width & height as needed

        layout = QVBoxLayout(self.ui_container)  # ✅ Vertical layout to stack elements
        # ✅ Labels
        self.debug_label = QLabel("Selected: None", self.ui_container)
        self.hover_label = QLabel("Hovering: None", self.ui_container)
        self.drag_label = QLabel("Dragging: None", self.ui_container)
        self.mouse_state_label = QLabel("Mouse State: IDLE", self.ui_container)
        # ✅ Buttons
        self.grid_button = QPushButton("Toggle Grid", self.ui_container)
        self.grid_button.clicked.connect(self.toggle_grid)
        self.save_button = QPushButton("Save Skill Tree", self.ui_container)
        self.save_button.clicked.connect(self.save_skill_tree)
        # ✅ Apply styles
        for label in [self.debug_label, self.hover_label, self.drag_label, self.mouse_state_label]:
            label.setStyleSheet("background-color: white; padding: 5px; border: 1px solid black;")
            layout.addWidget(label)  # ✅ Add labels to layout

        for button in [self.grid_button, self.save_button]:
            layout.addWidget(button)  # ✅ Add buttons to layout

        self.ui_container.setLayout(layout)  # ✅ Set layout to container

        # Grid init
        self.grid_visible = True  # Track grid state
        self.grid_lines = []  # Store grid lines
        self.draw_grid()

        # Font
        self.default_font = QFont("Arial", 10, QFont.Bold)  # ✅ Set default font for skill labels
        # Skill Panel
        self.skill_panel = SkillPanel(self)  # Make it a child of MainWindow
        self.skill_panel.move(10, 400)  # Position it on the left side
        self.skill_panel.hide()  # Hide it initially



    def on_left_click_press(self, view_pos):
        ##Handles left-click press to start dragging if clicking on selected nodes
        scene_pos = self.view.mapToScene(view_pos)
        clicked_items = self.scene.items(scene_pos)

        # If left click press on node, select it and prepare to drag
        if self.mouse_state == MouseState.IDLE:
            for item in clicked_items:
                if isinstance(item, SkillNode):
                    self.scene.clearSelection()
                    item.setSelected(True)
                    self.dragging_nodes = [node for node in self.scene.selectedItems()]  # Add all nodes clicked as selected (only 1 for now)
                    self.mouse_state = MouseState.DRAGGING
                    self.update_mouse_state_label()
                    self.view.last_mouse_pos = view_pos  # Store the start position of drag
                    self.update_drag_label()
                    self.debug_update_selection_label()
                    self.open_skill_panel(item)  # Opens the panel to show selected node's information
                    break

    def on_right_click_press(self, view_pos):
        ## Process right click from graphics view
        pass

    def on_left_click_release(self, view_pos):
        scene_pos = self.view.mapToScene(view_pos)
        # If was dragging a node, keep it selected
        # Check if over a node. If so, select it. If not, clear selection
        clicked_items = self.scene.items(scene_pos)
        if len(clicked_items) > 0:
            for item in clicked_items:
                if isinstance(item, SkillNode):
                    if self.mouse_state == MouseState.SELECTING_PREREQ:
                        ## set node as the prereq of selected node
                        self.selected_node.add_prerequisite(item)
                    elif self.mouse_state == MouseState.SELECTING_POSTREQ:
                        self.selected_node.add_postrequisite(item)
                    else:
                        self.scene.clearSelection()
                        item.setSelected(True)
                        item.snap_to_grid()
                    break  # Stop after selecting the first node
        else:
            self.scene.clearSelection()
            self.skill_panel.hide_panel()

        # Stop dragging
        self.dragging_nodes = None
        self.mouse_state = MouseState.IDLE
        self.update_mouse_state_label()
        self.update_drag_label()  # ✅ Reset drag label

        self.debug_update_selection_label()  # Ensure label updates when clicking empty space

    def on_left_click_drag(self, event):
        ## Handles dragging of multiple selected nodes.
        ## Called by mouse move event when beginning a drag action
        if not self.dragging_nodes:
            return
        if not self.view.last_mouse_pos:
            return
        scene_pos = self.view.mapToScene(event.pos())
        last_scene_pos = self.view.mapToScene(self.view.last_mouse_pos)
        delta = scene_pos - last_scene_pos  # Compute movement delta

        for node in self.dragging_nodes:
            node.setPos(node.pos() + delta)  # Move all selected nodes together
        self.view.last_mouse_pos = event.pos()  # Update drag position

    def on_right_click_release(self, view_pos):
        scene_pos = self.view.mapToScene(view_pos)
        # If release right click on a skill node, ignore it
        clicked_items = self.scene.items(scene_pos)
        if clicked_items:
            #Right-clicking a skill node opens the upgrade menu.
            scene_pos = self.view.mapToScene(view_pos)
            clicked_items = self.scene.items(scene_pos)

            for item in clicked_items:
                if isinstance(item, SkillNode):
                    self.show_rclick_menu_node(view_pos, item)
                    return
        else:
            self.show_rclick_menu_blank(view_pos)  # show right click menu on release if right click on blank canvas

    def show_rclick_menu_blank(self, view_pos):
        ## Context menu for right-clicking on the blank canvas.
        scene_pos = self.view.mapToScene(view_pos)
        screen_pos = self.view.mapToGlobal(view_pos)
        menu = QMenu(self)

        # Add new skill option
        add_skill_action = QAction("Add New Skill", self)
        menu.addAction(add_skill_action)

        action = menu.exec_(screen_pos)  # create the menu using screen position

        if action == add_skill_action:
            self.add_skill(scene_pos)

    def show_rclick_menu_node(self, view_pos, node):
        ## Context menu for right-clicking on a node
        scene_pos = self.view.mapToScene(view_pos)
        screen_pos = self.view.mapToGlobal(view_pos)
        menu = QMenu(self)

        delete_node_action = QAction("Delete node", self)
        set_prereq_action = QAction("Set node as prerequisite", self)
        set_postreq_action = QAction("Set node as postrequisite", self)

        menu.addAction(delete_node_action)
        menu.addAction(set_prereq_action)
        menu.addAction(set_postreq_action)

        action = menu.exec_(screen_pos)  # create the menu using screen position

        if action == delete_node_action:
            self.delete_node(node)
        elif action == set_prereq_action:
            self.begin_set_prereq(node)
        elif action == set_postreq_action:
            self.begin_set_postreq(node)

    def add_skill(self, scene_pos):
        """Adds a blank skill node to the canvas using scene coordinates."""
        skill = SkillNode(self, scene_pos.x(), scene_pos.y())  # ✅ No type or name
        self.scene.addItem(skill)
        self.scene.update()  # ✅ Force a UI refresh to avoid rendering issues

    def delete_node(self, node):
        if node in self.scene.items():
            self.scene.removeItem(node)  # ✅ Remove node from the scene
            del node  # ✅ Delete from memory (optional)
            print("Node deleted!")
        else:
            print("Node not found in scene!")

    def debug_update_selection_label(self):
        """Updates the debug label to show the current selection."""
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, SkillNode)]

        if len(selected_nodes) >= 1:
            self.debug_label.setText(f"Selected {len(selected_nodes)} nodes")
        else:
            self.debug_label.setText("Selected: None")

    def update_hover_label(self, textu):
        """Updates the hover label to show the currently hovered node."""
        if textu:
            self.hover_label.setText(f"Hovering: {textu}")
        else:
            self.hover_label.setText("Hovering: None")

    def update_drag_label(self):
        """Updates the label to show the currently dragged node(s)."""
        if self.dragging_nodes:
            self.drag_label.setText(f"Dragging: {len(self.dragging_nodes)} nodes")
        else:
            self.drag_label.setText("Dragging: None")

    def delete_selected_nodes(self):
        #Deletes all selected skill nodes.
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, SkillNode)]
        if selected_nodes:
            for node in selected_nodes:
                self.scene.removeItem(node)
            self.debug_update_selection_label()
            self.update_drag_label()

    def draw_grid(self):
        """Draws a background grid in the scene."""
        if not self.grid_visible:
            return  # Don't draw if grid is disabled

        scene_width = 2000
        scene_height = 2000

        self.grid_lines = []  # Store grid lines so we can remove them later

        # Vertical lines
        for x in range(0, scene_width, self.GRID_SIZE):
            line = self.scene.addLine(x, 0, x, scene_height, pen=QPen(Qt.lightGray))
            self.grid_lines.append(line)

        # Horizontal lines
        for y in range(0, scene_height, self.GRID_SIZE):
            line = self.scene.addLine(0, y, scene_width, y, pen=QPen(Qt.lightGray))
            self.grid_lines.append(line)

    def toggle_grid(self):
        """Toggles visibility of the grid."""
        self.grid_visible = not self.grid_visible

        # Remove existing grid lines
        for line in self.grid_lines:
            self.scene.removeItem(line)

        # Redraw if enabled
        if self.grid_visible:
            self.draw_grid()

    def get_skill_name_input(self, current_name):
        """Opens an input dialog to rename a skill node."""
        new_name, ok = QInputDialog.getText(self, "Rename Skill", "Enter new skill name:", text=current_name)
        return new_name, ok

    def open_skill_panel(self, node):
        # Open a panel on the left side of the screen which shows the currently selected node and the name/description of its Upgrade
        self.skill_panel.load_node(node)

    def save_skill_tree(self):
        """Saves all skill nodes and their upgrade info to a JSON file."""
        data = []

        for item in self.scene.items():
            if isinstance(item, SkillNode):
                node_data = {
                    "x": item.pos().x(),
                    "y": item.pos().y(),
                    "upgrade": {
                        "name": item.upgrade.name,
                        "description": item.upgrade.description
                    }
                }
                data.append(node_data)

        # Save to JSON file
        with open("skill_tree/skill_tree.json", "w") as file:
            json.dump(data, file, indent=4)

        print("Skill tree saved!")

    def load_skill_tree(self):
        """Loads skill nodes from a JSON file (if it exists) and adds them to the scene."""
        if not os.path.exists("skill_tree/skill_tree.json"):
            return  # No save file, do nothing

        with open("skill_tree/skill_tree.json", "r") as file:
            data = json.load(file)

        for node_data in data:
            x, y = node_data["x"], node_data["y"]
            upgrade_name = node_data["upgrade"]["name"]
            upgrade_desc = node_data["upgrade"]["description"]

            # Create new skill node and restore upgrade
            node = SkillNode(self, x, y)
            node.upgrade.name = upgrade_name
            node.upgrade.description = upgrade_desc
            self.scene.addItem(node)

        print("Skill tree loaded!")


    def begin_set_prereq(self, node):
        """Starts the process of setting a prerequisite."""
        self.mouse_state = MouseState.SELECTING_PREREQ
        self.update_mouse_state_label()  # ✅ Update label
        self.selected_node = node  # this is the node that will receive the prereq on click

    def begin_set_postreq(self, node):
        """Starts the process of setting a postrequisite."""
        self.mouse_state = MouseState.SELECTING_POSTREQ
        self.update_mouse_state_label()  # ✅ Update label
        self.selected_node = node

    def update_mouse_state_label(self):
        """Updates the mouse state label."""
        state_text = {
            MouseState.IDLE: "IDLE",
            MouseState.DRAGGING: "DRAGGING",
            MouseState.PANNING: "PANNING",
            MouseState.SELECTING_PREREQ: f"SELECTING PREREQ: {self.selected_node.upgrade.name if self.selected_node else None}",
            MouseState.SELECTING_POSTREQ: "SELECTING POSTREQ"
        }.get(self.mouse_state, "UNKNOWN")

        self.mouse_state_label.setText(f"Mouse State: {state_text}")
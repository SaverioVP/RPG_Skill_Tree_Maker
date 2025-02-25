from PyQt5.QtWidgets import (
    QMainWindow, QGraphicsScene, QVBoxLayout, QMenu,
    QAction, QInputDialog, QLabel, QPushButton, QWidget,
    QMessageBox
)
from PyQt5.QtGui import QPen, QFont, QBrush, QColor
from PyQt5.QtCore import Qt
from datetime import datetime
from skill_node import SkillNode
from custom_graphics_view import CustomGraphicsView
from tooltip import Tooltip
from skill_panel import SkillPanel
from mouse_state import MouseState
from connection_line import ConnectionLine
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

        # Set up the Scene.  self.scene = A canvas that holds all skill nodes.
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, 20000, 20000)  # Size of the Scene (need to scroll to get to extents)

        # Griddu
        self.GRID_SIZE = 60
        # Set up the custom graphics view to handle mouse interactions
        self.view = CustomGraphicsView(self.scene, self)
        self.view.centerOn(0, 0)  # Center view in top left corner
        self.setCentralWidget(self.view)
        self.dragging_nodes = None  # define the nodes being dragged by mouse cursor

        # rest oif the shit
        self.tooltip = Tooltip(self.scene)
        self.init_ui()
        self.temp_line = None  # ConnectingLine class


        # Mouse state tracking using state machine
        self.mouse_state = MouseState.IDLE
        self.selected_node = None
        self.update_mouse_state_label()

        # Node stuff
        self.current_node_id = 0  # id of the highest node. will be updated on loading skill ttree
        self.load_skill_tree()

    def init_ui(self):
        # Set up the scene with initial UI widgets and menus
        self.ui_container = QWidget(self)
        self.ui_container.setGeometry(10, 10, 220, 250)
        layout = QVBoxLayout(self.ui_container)  # This stacks labels automatically
        # Labels
        self.debug_label = QLabel("Selected: None", self.ui_container)
        self.hover_label = QLabel("Hovering: None", self.ui_container)
        self.drag_label = QLabel("Dragging: None", self.ui_container)
        self.mouse_state_label = QLabel("Mouse State: IDLE", self.ui_container)
        # Buttons
        self.grid_button = QPushButton("Toggle Grid", self.ui_container)
        self.grid_button.clicked.connect(self.toggle_grid)
        self.save_button = QPushButton("Save Skill Tree", self.ui_container)
        self.save_button.clicked.connect(self.on_save_button_clicked)
        # harry Styles
        for label in [self.debug_label, self.hover_label, self.drag_label, self.mouse_state_label]:
            label.setStyleSheet("background-color: white; padding: 5px; border: 1px solid black;")
            layout.addWidget(label)
        for button in [self.grid_button, self.save_button]:
            layout.addWidget(button)
        self.ui_container.setLayout(layout)

        # Grid init
        self.grid_visible = True  # Track grid state
        self.grid_lines = []
        self.draw_grid()

        # Font
        self.default_font = QFont("Arial", 10, QFont.Bold)  # default font for skill labels
        # Skill Panel
        self.skill_panel = SkillPanel(self)  # Make it a child of MainWindow
        self.skill_panel.move(10, 400)  # Position it on the left side
        self.skill_panel.hide()

    def on_left_click_press(self, view_pos):
        # Handles left-click press to start dragging if clicking on selected nodes
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
        # Process right click from graphics view
        pass

    def on_left_click_release(self, view_pos):
        scene_pos = self.view.mapToScene(view_pos)
        # If was dragging a node, keep it selected
        # Check if over a node. If so, select it. If not, clear selection
        clicked_items = self.scene.items(scene_pos)
        if len(clicked_items) > 0:
            for item in clicked_items:
                if isinstance(item, SkillNode):
                    # Check for selecting a prereq
                    if self.mouse_state == MouseState.SELECTING_PREREQ or self.mouse_state == MouseState.SELECTING_POSTREQ or self.mouse_state == MouseState.DELETING_CONNECTIONS:
                        if item == self.selected_node:
                            return
                        self.complete_node_selection(item)
                    else:  # just clicking on a node
                        self.scene.clearSelection()
                        item.setSelected(True)
                        item.snap_to_grid()
                    break  # Stop after selecting the first node
        else:
            self.scene.clearSelection()
            self.skill_panel.hide_panel()

        self.dragging_nodes = None  # this stops the dragging flag
        self.mouse_state = MouseState.IDLE
        self.delete_temp_line()  # in case was looking for a prereq / postreq
        self.update_mouse_state_label()
        self.update_drag_label()
        self.debug_update_selection_label()  # Ensure label updates when clicking empty space

    def on_left_click_drag(self, event):
        # Handles dragging of multiple selected nodes.
        # Called by mouse move event when beginning a drag action
        if not self.dragging_nodes:
            return
        if not self.view.last_mouse_pos:
            return
        scene_pos = self.view.mapToScene(event.pos())
        last_scene_pos = self.view.mapToScene(self.view.last_mouse_pos)
        delta = scene_pos - last_scene_pos  # Compute movement delta

        for node in self.dragging_nodes:
            new_pos = node.pos() + delta
            node.setPos(new_pos.x(), new_pos.y())
        self.view.last_mouse_pos = event.pos()  # Update drag position

    def on_right_click_release(self, view_pos):
        if self.mouse_state != MouseState.IDLE:
            return
        scene_pos = self.view.mapToScene(view_pos)
        clicked_items = self.scene.items(scene_pos)
        if clicked_items:
            # Right-clicking a skill node opens the upgrade menu.
            scene_pos = self.view.mapToScene(view_pos)
            clicked_items = self.scene.items(scene_pos)

            for item in clicked_items:
                if isinstance(item, SkillNode):
                    self.show_rclick_menu_node(view_pos, item)
                    return
        else:
            self.show_rclick_menu_blank(view_pos)  # show right click menu for blank canvas

    def show_rclick_menu_blank(self, view_pos):
        # Context menu for right-clicking on the blank canvas.
        scene_pos = self.view.mapToScene(view_pos)
        screen_pos = self.view.mapToGlobal(view_pos)
        menu = QMenu(self)

        add_skill_action = QAction("Add New Skill", self)
        menu.addAction(add_skill_action)

        action = menu.exec_(screen_pos)  # creates the menu using screen position

        if action == add_skill_action:
            self.add_skill(scene_pos)

    def show_rclick_menu_node(self, view_pos, node):
        # Context menu for right-clicking on a node
        scene_pos = self.view.mapToScene(view_pos)
        screen_pos = self.view.mapToGlobal(view_pos)
        menu = QMenu(self)

        delete_node_action = QAction("Delete node", self)
        set_prereq_action = QAction("Set node as prerequisite", self)
        set_postreq_action = QAction("Set node as postrequisite", self)
        delete_connections_action = QAction("Delete node as pre- or postrequisite", self)
        menu.addAction(delete_node_action)
        menu.addAction(set_prereq_action)
        menu.addAction(set_postreq_action)
        menu.addAction(delete_connections_action)

        action = menu.exec_(screen_pos)  # create the menu using screen position

        if action == delete_node_action:
            self.delete_node(node)
        elif action == set_prereq_action:
            self.begin_set_prereq(node)
        elif action == set_postreq_action:
            self.begin_set_postreq(node)
        elif action == delete_connections_action:
            self.begin_delete_connections(node)

    def add_skill(self, scene_pos):
        # Adds a blank skill node to the canvas using scene coordinates.

        skill = SkillNode(self, scene_pos.x(), scene_pos.y())
        self.scene.addItem(skill)
        self.scene.update()  # Force a UI refresh to avoid rendering issues
        self.auto_save_skill_tree()  # Save when adding a skill

    def delete_node(self, node):
        if node in self.scene.items():
            node.prep_for_deletion()
            self.scene.removeItem(node)
            del node  # delete from memory. Is this even needed?
            self.auto_save_skill_tree()
            print("Node deleted!")
        else:
            print("Node not found in scene!")

    def debug_update_selection_label(self):
        # Updates the debug label to show the current selectied nodes
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, SkillNode)]
        if len(selected_nodes) >= 1:
            self.debug_label.setText(f"Selected {len(selected_nodes)} nodes")
        else:
            self.debug_label.setText("Selected: None")

    def update_hover_label(self, textu):
        # Updates the hover label to show the currently hovered node
        if textu:
            self.hover_label.setText(f"Hovering: {textu}")
        else:
            self.hover_label.setText("Hovering: None")

    def update_drag_label(self):
        # Updates the label to show the currently dragged node(s).
        if self.dragging_nodes:
            self.drag_label.setText(f"Dragging: {len(self.dragging_nodes)} nodes")
        else:
            self.drag_label.setText("Dragging: None")

    def delete_selected_nodes(self):
        # Deletes all selected skill nodes. Called by delete key
        selected_nodes = [item for item in self.scene.selectedItems() if isinstance(item, SkillNode)]
        if selected_nodes:
            for node in selected_nodes:
                self.delete_node(node)
            self.debug_update_selection_label()
            self.update_drag_label()

    def draw_grid(self):
        if not self.grid_visible:
            return
        scene_width = 2000  # TODO: define constants at top of file
        scene_height = 2000
        self.grid_lines = []  # Store grid lines so can remove them later
        # Vertical lines
        for x in range(0, scene_width, self.GRID_SIZE):
            line = self.scene.addLine(x, 0, x, scene_height, pen=QPen(Qt.lightGray))
            self.grid_lines.append(line)
        # Horizontal lines
        for y in range(0, scene_height, self.GRID_SIZE):
            line = self.scene.addLine(0, y, scene_width, y, pen=QPen(Qt.lightGray))
            self.grid_lines.append(line)

    def toggle_grid(self):
        self.grid_visible = not self.grid_visible
        # Remove existing grid lines
        for line in self.grid_lines:
            self.scene.removeItem(line)
        # Redraw if enabled
        if self.grid_visible:
            self.draw_grid()

    def open_skill_panel(self, node):
        # Open a panel on the left side of the screen which shows the currently selected node and the name/description of its Upgrade
        self.skill_panel.load_node(node)

    def save_skill_tree(self, filepath):
        # Saves all skill nodes and their upgrade info to a JSON file.
        self.update_node_ids()
        skill_nodes = [item for item in self.scene.items() if isinstance(item, SkillNode)]
        save_data = {"nodes": []}
        for node in skill_nodes:
            node_data = {
                "node_id": node.node_id,
                "x": node.pos().x(),
                "y": node.pos().y(),
                "upgrade": {
                    "name": node.upgrade.name,
                    "description": node.upgrade.description
                },
                "prerequisites": [prereq.node_id for prereq in node.prerequisites],
                "postrequisites": [postreq.node_id for postreq in node.postrequisites]
            }
            save_data["nodes"].append(node_data)
        with open(filepath, "w") as file:
            json.dump(save_data, file, indent=4)

        print(f"Skill tree saved to {filepath}!")

    def update_node_ids(self):
        # update the id of all nodes based on their x,y coordinates
        skill_nodes = sorted(
            [item for item in self.scene.items() if isinstance(item, SkillNode)],
            key=lambda node: (node.pos().y(), node.pos().x())  # Sort by Y first, then X
        )
        # Assign new sequential IDs
        for new_id, node in enumerate(skill_nodes):
            node.change_id(new_id)
        # Update the current_node_id to reflect the highest ID + 1
        self.current_node_id = len(skill_nodes)
        print("Node IDs updated")

    def auto_save_skill_tree(self):
        temp_file = "skill_tree/_temp_skill_tree.json"
        self.save_skill_tree(temp_file)  # Pass temp file path

    def on_save_button_clicked(self):
        save_file = "skill_tree/skill_tree.json"
        temp_file = "skill_tree/_temp_skill_tree.json"
        self.save_skill_tree(save_file)  # Save to permanent file

        if os.path.exists(temp_file):
            os.remove(temp_file)  # get rid of temp file


    def load_skill_tree(self):
        # Loads skill nodes from a JSON file (if it exists) and adds them to the scene.
        # Called on startup
        save_file = "skill_tree/skill_tree.json"
        if not os.path.exists(save_file):
            return  # No save file, do nothing

        # Generate a backup file with timestamp
        #timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        backup_file = f"skill_tree/skill_tree_BACKUP.json"
        try:
            with open(save_file, "r") as original, open(backup_file, "w") as backup:
                data = original.read()
                backup.write(data)
            print(f"Backup created: {backup_file}")
        except Exception as e:
            print(f"Error creating backup: {e}")

        # Proceed with normal saving
        with open("skill_tree/skill_tree.json", "r") as file:
            save_data = json.load(file)
        # Restore the last highest node_id to prevent ID duplication
        self.current_node_id = max((node["node_id"] for node in save_data["nodes"]), default=-1) + 1
        node_list = {}  # Map node_id to node objects
        # Load Nodes
        for node_data in save_data["nodes"]:
            node_id = node_data["node_id"]
            x, y = node_data["x"], node_data["y"]
            upgrade_name = node_data["upgrade"]["name"]
            upgrade_desc = node_data["upgrade"]["description"]

            # Create new skill node with its saved ID
            node = SkillNode(self, x, y, node_id=node_id)
            node.upgrade.name = upgrade_name
            node.upgrade.description = upgrade_desc
            self.scene.addItem(node)
            node_list[node_id] = node  # Store for linking later

        # Reconnect Relationships
        for node_data in save_data["nodes"]:
            node = node_list[node_data["node_id"]]
            for prereq_id in node_data["prerequisites"]:
                if prereq_id in node_list:
                    node.add_prerequisite(node_list[prereq_id])
            for postreq_id in node_data["postrequisites"]:
                if postreq_id in node_list:
                    node.add_postrequisite(node_list[postreq_id])
        print("Skill tree loaded!")

    def closeEvent(self, event):
        # Checks if there are unsaved changes before exiting.
        temp_file = "skill_tree/_temp_skill_tree.json"
        save_file = "skill_tree/skill_tree.json"

        if os.path.exists(temp_file):  # ✅ Check if temp save exists
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "There are unsaved changes. Do you want to save before exiting?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                self.save_skill_tree(save_file)  # ✅ Save the temp file permanently
                os.remove(temp_file)  # ✅ Clean up temp file
                print("Changes saved before exit.")
                event.accept()  # ✅ Allow exit

            elif reply == QMessageBox.Discard:
                os.remove(temp_file)  # ❌ Delete temp file (Exit without saving)
                print("Exiting without saving changes.")
                event.accept()  # ✅ Allow exit

            else:
                print("Exit canceled.")
                event.ignore()  # 🔄 Cancel exit
        else:
            event.accept()  # ✅ Normal exit if no temp file exists

    def begin_set_prereq(self, node):
        # Starts the process of setting a prerequisite to a node. Called by right click menu
        self.mouse_state = MouseState.SELECTING_PREREQ
        self.update_mouse_state_label()
        self.selected_node = node  # this is the node that will receive the prereq on click
        # Create temp line to follow mouse
        self.temp_line = ConnectionLine(node)
        self.scene.addItem(self.temp_line)

    def begin_set_postreq(self, node):
        self.mouse_state = MouseState.SELECTING_POSTREQ
        self.update_mouse_state_label()
        self.selected_node = node
        # Line
        self.temp_line = ConnectionLine(node)
        self.scene.addItem(self.temp_line)


    def begin_delete_connections(self, node):
        # Begins process of deleting connections of selected node to another
        self.mouse_state = MouseState.DELETING_CONNECTIONS
        self.update_mouse_state_label()
        self.selected_node = node

    def complete_node_selection(self, node):
        # Complete setting pre/postreq and finalized the connection line
        if node == self.selected_node:
            return
        if self.mouse_state == MouseState.SELECTING_PREREQ:
            self.selected_node.add_prerequisite(node)
        elif self.mouse_state == MouseState.SELECTING_POSTREQ:
            self.selected_node.add_postrequisite(node)
        elif self.mouse_state == MouseState.DELETING_CONNECTIONS:
            self.selected_node.delete_connections(node)

        if self.temp_line:
            self.delete_temp_line()

    def update_mouse_state_label(self):
        state_text = {
            MouseState.IDLE: "IDLE",
            MouseState.DRAGGING: "DRAGGING",
            MouseState.PANNING: "PANNING",
            MouseState.SELECTING_PREREQ: f"SELECTING PREREQ: {self.selected_node.upgrade.name if self.selected_node else None}",
            MouseState.SELECTING_POSTREQ: "SELECTING POSTREQ",
            MouseState.DELETING_CONNECTIONS: "DELETING CONNECTIONS"
        }.get(self.mouse_state, "UNKNOWN")

        self.mouse_state_label.setText(f"Mouse State: {state_text}")

    def delete_temp_line(self):
        if self.temp_line:
            self.scene.removeItem(self.temp_line)
            del self.temp_line
            self.temp_line = None

    def delete_connecting_line(self, line):
        if line:
            self.scene.removeItem(line)
            del line

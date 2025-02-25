from enum import Enum


class MouseState(Enum):
    IDLE = 0
    DRAGGING = 1
    PANNING = 2
    SELECTING_PREREQ = 3
    SELECTING_POSTREQ = 4
    DELETING_CONNECTIONS = 5

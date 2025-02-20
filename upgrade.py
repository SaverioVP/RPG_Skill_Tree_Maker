class Upgrade:
    # Base upgrade that can contain various upgrade types

    def __init__(self, node_id=None):
        self.name = f"Node {node_id}" if node_id is not None else "Unnamed Node"
        self.description = "im a description!"

    def set_description(self, new_description):
        self.description = new_description

    def get_description(self):
        return self.description

class Upgrade:
    ##Base upgrade that can contain various upgrade types."""

    def __init__(self):
        self.name = "Hello"
        self.description = "im a description!"

    def set_description(self, new_description):
        """Sets a new description for the upgrade."""
        self.description = new_description

    def get_description(self):
        """Returns the upgrade description."""
        return self.description
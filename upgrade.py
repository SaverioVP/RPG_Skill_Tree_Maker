class Upgrade:
    # Base upgrade that can contain various upgrade types
    class Upgrade_Type:
        WEAPON_UNLOCK = "Weapon Unlock"
        CLASS_UNLOCK = "Class Unlock"
        ACTIVE_ABILITY = "Active Ability"
        PASSIVE_ABILITY = "Passive Ability"
    def __init__(self, name, description, upgrade_type):
        self.name = name
        self.description = description
        self.upgrade_type = upgrade_type

    def set_description(self, new_description):
        self.description = new_description

    def get_description(self):
        return self.description

import json
import os

class PreferenceManager:
    def __init__(self, parent, filename="config.json"):
        self.parent = parent
        self.filename = filename
        self.default_preferences = {
            "format_capture": False,
            "post_traitement": False,
            "format_export_text": [False, False, True]
        }
        self.load_preferences()

    def load_preferences(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    preferences = json.load(f)
            except (json.JSONDecodeError, IOError):
                print("erreur lecture val par défault")
                preferences = self.default_preferences
        else:
            print("pas de fichier création")
            preferences = self.default_preferences
            self.save_preferences()

        for key, value in preferences.items():
            setattr(self.parent, key, value)

    def save_preferences(self):
        preferences = {
            "format_capture": getattr(self.parent, "format_capture", False),
            "post_traitement": getattr(self.parent, "post_traitement", False),
            "format_export_text": getattr(self.parent, "format_export_text", [False, False, True])
        }

        try:
            with open(self.filename, "w") as f:
                json.dump(preferences, f, indent=4)
            print(f"pref save dans {self.filename}")
        except IOError as e:
            print(f"erreur save: {e}")

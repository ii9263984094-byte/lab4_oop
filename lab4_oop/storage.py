import json
import os


class SettingsStorage:
    """Управляет загрузкой и сохранением темы и избранных книг в JSON."""

    def __init__(self, filepath="settings.json"):
        self.filepath = filepath

    def load(self):
        default = {"theme": "light", "favorites": []}
        if not os.path.exists(self.filepath):
            return default
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            return {
                "theme": data.get("theme", "light"),
                "favorites": data.get("favorites", []),
            }
        except (json.JSONDecodeError, OSError):
            return default

    def save(self, data):
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
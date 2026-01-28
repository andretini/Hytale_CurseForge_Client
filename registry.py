import json
import os

REGISTRY_FILE = "installed_mods.json"


class ModRegistry:
    def __init__(self, game_path):
        self.game_path = game_path
        self._data = {}
        self.load()

    @property
    def path(self):
        return os.path.join(self.game_path, REGISTRY_FILE)

    def load(self):
        if not self.game_path:
            self._data = {}
            return
        try:
            with open(self.path, "r") as f:
                self._data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._data = {}

    def save(self):
        if not self.game_path:
            return
        os.makedirs(self.game_path, exist_ok=True)
        with open(self.path, "w") as f:
            json.dump(self._data, f, indent=2)

    def add(self, mod_id, mod_name, file_name, file_id, file_date, class_id):
        self._data[str(mod_id)] = {
            "mod_name": mod_name,
            "file_name": file_name,
            "file_id": file_id,
            "file_date": file_date,
            "class_id": class_id,
        }
        self.save()

    def remove(self, mod_id):
        self._data.pop(str(mod_id), None)
        self.save()

    def get(self, mod_id):
        return self._data.get(str(mod_id))

    def get_all(self):
        return dict(self._data)

    def find_by_filename(self, file_name):
        for mid, entry in self._data.items():
            if entry.get("file_name") == file_name:
                return mid, entry
        return None, None

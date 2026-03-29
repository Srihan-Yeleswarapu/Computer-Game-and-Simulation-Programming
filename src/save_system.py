import hashlib
import hmac
import json
import os
from typing import Any

SECRET_KEY = os.getenv("GAME_SECRET_KEY", "fallback_secure_key_2025").encode()

_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
SAVE_FILE = os.path.join(_project_root, "save_data.json")
LEGACY_FRAGMENT_FILES = {
    "completed_worlds": "completed_worlds.json",
    "world_grades": "world_grades.json",
    "settings": "game_settings.json",
}


class SaveSystem:
    def __init__(self) -> None:
        self.data: dict[str, Any] = self._default_data()
        self.integrity_error = False
        print(f"[SaveSystem] Save file location: {SAVE_FILE}")
        self.load()

    def _default_data(self) -> dict[str, Any]:
        return {
            "version": 2,
            "progress": {
                "completed_worlds": [],
                "world_grades": {},
            },
            "settings": {
                "high_contrast": False,
                "music_on": True,
            },
        }

    def _legacy_search_dirs(self) -> list[str]:
        return [
            _project_root,
            _current_dir,
            os.path.join(_project_root, "__pycache__"),
            os.path.join(_current_dir, "__pycache__"),
        ]

    def _normalize_data(self, loaded: Any) -> dict[str, Any]:
        normalized = self._default_data()

        if not isinstance(loaded, dict):
            return normalized

        if "progress" in loaded or "settings" in loaded:
            progress = loaded.get("progress", {})
            settings = loaded.get("settings", {})
        else:
            progress = loaded
            settings = loaded.get("settings", {})

        if isinstance(progress, dict):
            completed_worlds = progress.get("completed_worlds", [])
            world_grades = progress.get("world_grades", {})
            if isinstance(completed_worlds, list):
                normalized["progress"]["completed_worlds"] = completed_worlds
            if isinstance(world_grades, dict):
                normalized["progress"]["world_grades"] = world_grades

        if isinstance(settings, dict):
            for key, default in normalized["settings"].items():
                value = settings.get(key, default)
                if isinstance(value, bool):
                    normalized["settings"][key] = value

        return normalized

    def _load_legacy_fragments(self) -> dict[str, Any]:
        merged = self._default_data()

        for folder in self._legacy_search_dirs():
            if not os.path.isdir(folder):
                continue
            for section, filename in LEGACY_FRAGMENT_FILES.items():
                path = os.path.join(folder, filename)
                if not os.path.exists(path):
                    continue
                try:
                    with open(path, "r", encoding="utf-8") as file:
                        loaded = json.load(file)
                except Exception as error:
                    print(f"[SaveSystem] Failed to read legacy save fragment '{path}': {error}")
                    continue

                if section == "completed_worlds" and isinstance(loaded, list):
                    merged["progress"]["completed_worlds"] = loaded
                elif section == "world_grades" and isinstance(loaded, dict):
                    merged["progress"]["world_grades"] = loaded
                elif section == "settings" and isinstance(loaded, dict):
                    for key, default in merged["settings"].items():
                        value = loaded.get(key, default)
                        if isinstance(value, bool):
                            merged["settings"][key] = value

        return merged

    def get_signature(self, data_str: str) -> str:
        return hmac.new(SECRET_KEY, data_str.encode(), hashlib.sha256).hexdigest()

    def save(self) -> None:
        try:
            json_str = json.dumps(self.data, sort_keys=True)
            signature = self.get_signature(json_str)
            with open(SAVE_FILE, "w", encoding="utf-8") as file:
                json.dump({"payload": json_str, "signature": signature}, file)
            print(
                "[SaveSystem] Saved! Completed:"
                f" {self.data['progress']['completed_worlds']}"
            )
        except Exception as error:
            print(f"[SaveSystem] Failed to save: {error}")

    def load(self) -> None:
        if os.path.exists(SAVE_FILE):
            try:
                with open(SAVE_FILE, "r", encoding="utf-8") as file:
                    wrapper = json.load(file)

                payload = wrapper["payload"]
                signature = wrapper["signature"]

                if self.get_signature(payload) != signature:
                    print("Save file signature mismatch. Resetting data.")
                    self.integrity_error = True
                    self.data = self._default_data()
                    return

                loaded = json.loads(payload)
                self.data = self._normalize_data(loaded)
                return
            except Exception as error:
                print(f"[SaveSystem] Failed to load canonical save file: {error}")

        migrated = self._load_legacy_fragments()
        if migrated != self._default_data():
            self.data = migrated
            self.save()

    def mark_world_complete(self, world_id: str, grade: str = "-", display_name: str | None = None) -> None:
        display_name = display_name or world_id
        print(f"[SaveSystem] Marking world '{display_name}' ({world_id}) as complete with rank {grade}...")

        ranks = {"S": 5, "A": 4, "B": 3, "C": 2, "-": 1}
        current_grade = self.data["progress"]["world_grades"].get(world_id, "-")

        if ranks.get(grade, 0) > ranks.get(current_grade, 0):
            self.data["progress"]["world_grades"][world_id] = grade

        if display_name not in self.data["progress"]["completed_worlds"]:
            self.data["progress"]["completed_worlds"].append(display_name)
            print(
                f"[SaveSystem] World '{display_name}' added! "
                f"Total: {len(self.data['progress']['completed_worlds'])}"
            )

        self.save()

    def get_grade(self, world_id: str, default: str | None = None) -> str | None:
        return self.data["progress"]["world_grades"].get(world_id, default)

    def get_completed_worlds(self) -> list[str]:
        return list(self.data["progress"]["completed_worlds"])

    def get_completed_world_count(self) -> int:
        return len(self.data["progress"]["completed_worlds"])

    def get_setting(self, key: str, default: Any = None) -> Any:
        return self.data["settings"].get(key, default)

    def set_setting(self, key: str, value: Any, *, save_immediately: bool = True) -> None:
        self.data["settings"][key] = value
        if save_immediately:
            self.save()



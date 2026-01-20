import json
import os
import hmac
import hashlib

SECRET_KEY = b"secure_career_game_key_2025"

# Get the directory where this file is located, then go up one level to project root
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)
SAVE_FILE = os.path.join(_project_root, "save_data.json")

class SaveSystem:
    def __init__(self):
        self.data = {
            "completed_worlds": []
        }
        print(f"[SaveSystem] Save file location: {SAVE_FILE}")
        self.load()

    def get_signature(self, data_str: str) -> str:
        return hmac.new(SECRET_KEY, data_str.encode(), hashlib.sha256).hexdigest()

    def save(self):
        try:
            json_str = json.dumps(self.data, sort_keys=True)
            signature = self.get_signature(json_str)
            with open(SAVE_FILE, "w") as f:
                f.write(json.dumps({"payload": json_str, "signature": signature}))
            print(f"[SaveSystem] Saved! Completed: {self.data['completed_worlds']}, Military: {self.data['military_unlocked']}")
        except Exception as e:
            print(f"[SaveSystem] Failed to save: {e}")

    def load(self):
        if not os.path.exists(SAVE_FILE):
            return
        
        try:
            with open(SAVE_FILE, "r") as f:
                wrapper = json.loads(f.read())
            
            payload = wrapper["payload"]
            signature = wrapper["signature"]
            
            # Verify HMAC
            if self.get_signature(payload) != signature:
                print("Save file signature mismatch. Resetting data.")
                self.data = {"completed_worlds": []}
                return
            
            loaded = json.loads(payload)
            self.data = loaded
                
        except Exception as e:
            print(f"Failed to load save: {e}")

    def mark_world_complete(self, world_id: str):
        print(f"[SaveSystem] Marking world '{world_id}' as complete...")
        if world_id not in self.data["completed_worlds"]:
            self.data["completed_worlds"].append(world_id)
            print(f"[SaveSystem] World '{world_id}' added! Total: {len(self.data['completed_worlds'])}/6")
            self.save()
        else:
            print(f"[SaveSystem] World '{world_id}' already completed (no duplicate credit)")

def clamp(value, low, high):
    return max(low, min(high, value))

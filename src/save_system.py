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
            "completed_worlds": [],
            "world_grades": {} 
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
            print(f"[SaveSystem] Saved! Completed: {self.data['completed_worlds']}")
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
                self.data = {"completed_worlds": [], "world_grades": {}}
                return
            
            loaded = json.loads(payload)
            self.data = loaded
            
            # Migration for old saves
            if "world_grades" not in self.data:
                self.data["world_grades"] = {}
                
        except Exception as e:
            print(f"Failed to load save: {e}")

    def mark_world_complete(self, world_id: str, grade: str = "-"):
        print(f"[SaveSystem] Marking world '{world_id}' as complete with rank {grade}...")
        
        # Always update grade if better (S > A > B > C > -)
        ranks = {"S": 5, "A": 4, "B": 3, "C": 2, "-": 1}
        current_grade = self.data["world_grades"].get(world_id, "-")
        
        if ranks.get(grade, 0) > ranks.get(current_grade, 0):
             self.data["world_grades"][world_id] = grade
             
        if world_id not in self.data["completed_worlds"]:
            self.data["completed_worlds"].append(world_id)
            print(f"[SaveSystem] World '{world_id}' added! Total: {len(self.data['completed_worlds'])}/6")
            
        self.save()

def clamp(value, low, high):
    return max(low, min(high, value))

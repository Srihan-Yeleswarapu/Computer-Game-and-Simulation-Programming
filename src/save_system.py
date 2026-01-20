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
            "military_unlocked": False,
            "rank_index": 0,  # 0 to 11 (PVT to SMA)
            "military_history": []
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
                content = json.load(f)
            
            payload = content["payload"]
            signature = content["signature"]
            
            # Verify signature
            expected_sig = self.get_signature(payload)
            if hmac.compare_digest(signature, expected_sig):
                self.data = json.loads(payload)
            else:
                print("Save file tampering detected! Resetting progress.")
                # We do not load corrupted data, effectively resetting
            
            # Self-healing: Unlock military if requirements met
            if len(self.data["completed_worlds"]) >= 6 and not self.data.get("military_unlocked"):
                 self.data["military_unlocked"] = True
                 self.save()
        except Exception as e:
            print(f"Failed to load save: {e}")

    def mark_world_complete(self, world_id: str):
        print(f"[SaveSystem] Marking world '{world_id}' as complete...")
        if world_id not in self.data["completed_worlds"]:
            self.data["completed_worlds"].append(world_id)
            print(f"[SaveSystem] World '{world_id}' added! Total: {len(self.data['completed_worlds'])}/6")
            # Check for military unlock - require 6 worlds now (1-6)
            # For now, let's keep it simple: if we have 6 unique completed, unlock
            if len(self.data["completed_worlds"]) >= 6:
                 self.data["military_unlocked"] = True
                 print(f"[SaveSystem] MILITARY UNLOCKED!")
            self.save()
        else:
            print(f"[SaveSystem] World '{world_id}' already completed (no duplicate credit)")

    def get_rank(self) -> str:
        ranks = [
            "Noob", "Novice", "Rookie", "Advanced Beginner", 
            "Intermediate", "Competent", "Proficient", "Seasoned", 
            "Advanced", "Senior", "Expert", "Master"
        ]
        idx = clamp(self.data["rank_index"], 0, len(ranks) - 1)
        return ranks[idx]

    def promote(self):
        if self.data["rank_index"] < 11:
            self.data["rank_index"] += 1
            self.save()
            return True
        return False

    def log_mission(self, world_name: str, time_taken: float, successful: bool):
        entry = {
            "rank": self.get_rank(),
            "world": world_name,
            "time": round(time_taken, 2),
            "outcome": "Success" if successful else "Fail"
        }
        if "military_history" not in self.data:
            self.data["military_history"] = []
        self.data["military_history"].append(entry)
        self.save()

    def demote_reset(self):
        self.data["rank_index"] = 0
        self.save()

def clamp(value, low, high):
    return max(low, min(high, value))

"""
Analytics module for TITAN.
Handles asynchronous, non-blocking file I/O for decision logging and match recording.
"""
import os
import json
import time
import threading
from queue import Queue, Empty
from datetime import datetime
from configs.settings import ENABLE_ANALYTICS, ANALYTICS_DIR, REPLAYS_DIR


class AnalyticsEngine:
    """
    Singleton-style background engine that processes logs asynchronously.
    """
    def __init__(self):
        self.enabled = ENABLE_ANALYTICS
        if not self.enabled:
            return

        self.log_queue = Queue()
        self.running = True
        
        # Ensure directories exist
        os.makedirs(ANALYTICS_DIR, exist_ok=True)
        os.makedirs(REPLAYS_DIR, exist_ok=True)
        
        self.worker = threading.Thread(target=self._process_queue, daemon=True)
        self.worker.start()

    def _process_queue(self):
        while self.running:
            try:
                # Wait up to 1 second for a task
                task = self.log_queue.get(timeout=1.0)
                try:
                    task_type, data = task
                    if task_type == "decision":
                        self._write_decision_log(data)
                    elif task_type == "match":
                        self._write_match_log(data)
                except Exception as e:
                    print(f"[Analytics] Error processing log: {e}")
                finally:
                    self.log_queue.task_done()
            except Empty:
                continue

    def _write_decision_log(self, data):
        filepath = data["filepath"]
        log_entry = data["entry"]
        # Write JSONL
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")

    def _write_match_log(self, data):
        filepath = data["filepath"]
        log_entry = data["entry"]
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(log_entry, f, indent=4)

    def log_decision(self, filepath, entry):
        if self.enabled:
            self.log_queue.put(("decision", {"filepath": filepath, "entry": entry}))

    def log_match(self, filepath, entry):
        if self.enabled:
            self.log_queue.put(("match", {"filepath": filepath, "entry": entry}))

    def stop(self):
        self.running = False
        if self.enabled:
            self.worker.join(timeout=2.0)


class DecisionLogger:
    def __init__(self, engine, session_id):
        self.engine = engine
        self.session_id = session_id
        self.filepath = os.path.join(ANALYTICS_DIR, f"decisions_{self.session_id}.jsonl")
        
        # State tracking to avoid spamming the log
        self.last_action_str = None
        self.last_reason = None
        self.last_log_time = 0

    def log(self, game_time, my_elixir, enemy_elixir, best_action, best_reason, all_scores, predicted_deck):
        if not self.engine.enabled:
            return

        action_str = best_action.action.name
        if action_str == "PLAY_CARD":
            action_str = f"PLAY_{best_action.card_to_play}_({best_action.target_x},{best_action.target_y})"

        current_time = time.time()
        
        # Meaningful change logic:
        # Log if the action changes, OR if the reason changes, OR if it's been 2 seconds since the last log
        is_meaningful = (
            action_str != self.last_action_str or
            best_reason != self.last_reason or
            (current_time - self.last_log_time > 2.0)
        )

        if not is_meaningful:
            return

        self.last_action_str = action_str
        self.last_reason = best_reason
        self.last_log_time = current_time

        # Format rejected actions
        rejected = []
        for score, action_cmd, reason in all_scores:
            cmd_str = action_cmd.action.name
            if cmd_str == "PLAY_CARD":
                cmd_str = f"PLAY_{action_cmd.card_to_play}"
            if cmd_str != action_str:
                rejected.append({"action": cmd_str, "score": float(score), "reason": reason})

        entry = {
            "timestamp": datetime.now().isoformat(),
            "game_time": float(game_time),
            "my_elixir": float(my_elixir),
            "estimated_enemy_elixir": float(enemy_elixir),
            "chosen_action": action_str,
            "action_score": float(all_scores[0][0]) if all_scores else 0.0,
            "reason": best_reason,
            "rejected_actions": rejected,
            "predicted_deck": list(predicted_deck)
        }
        
        self.engine.log_decision(self.filepath, entry)


class MatchLogger:
    def __init__(self, engine, session_id):
        self.engine = engine
        self.session_id = session_id
        self.filepath = os.path.join(ANALYTICS_DIR, f"match_{self.session_id}.json")
        
        self.start_time = None
        self.actions_played = 0

    def start_match(self):
        self.start_time = time.time()
        self.actions_played = 0

    def record_action(self):
        self.actions_played += 1

    def end_match(self, won):
        if not self.engine.enabled or not self.start_time:
            return

        duration = time.time() - self.start_time
        
        entry = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": round(duration, 1),
            "won": won,
            "total_cards_played": self.actions_played
        }
        
        self.engine.log_match(self.filepath, entry)
        self.start_time = None


import cv2

class ReplayLogger:
    """
    Records video asynchronously to prevent blocking the main pipeline.
    """
    def __init__(self, session_id, width=720, height=1280, fps=15.0):
        self.session_id = session_id
        self.filepath = os.path.join(REPLAYS_DIR, f"replay_{self.session_id}.mp4")
        self.frame_queue = Queue()
        self.running = True
        self.width = width
        self.height = height
        self.fps = fps
        
        self.writer = None
        
        if ENABLE_ANALYTICS:
            self.worker = threading.Thread(target=self._write_frames, daemon=True)
            self.worker.start()

    def _write_frames(self):
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.writer = cv2.VideoWriter(self.filepath, fourcc, self.fps, (self.width, self.height))
        
        while self.running or not self.frame_queue.empty():
            try:
                frame = self.frame_queue.get(timeout=0.5)
                if frame is not None:
                    # Resize if necessary to match initialization
                    if frame.shape[:2] != (self.height, self.width):
                        frame = cv2.resize(frame, (self.width, self.height))
                    self.writer.write(frame)
                self.frame_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"[ReplayLogger] Error writing frame: {e}")
                
        if self.writer:
            self.writer.release()

    def log_frame(self, frame):
        if not ENABLE_ANALYTICS:
            return
        
        # Drop frame if queue is too large to prevent memory leak
        if self.frame_queue.qsize() < 100:
            self.frame_queue.put(frame)

    def stop(self):
        if ENABLE_ANALYTICS:
            self.running = False
            self.worker.join(timeout=2.0)

# Global Instance
_analytics_engine = AnalyticsEngine()

def get_engine():
    return _analytics_engine

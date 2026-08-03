"""
Asynchronous Real-Time Engine for TITAN.
Decouples screen capture from AI inference so the game feed
never stutters. Runs YOLO detection on a background thread
and only processes every Nth frame for maximum speed.
"""

import threading
import time
import logging
import queue

from engine.pipeline import Pipeline
from vision.screen_classifier import ScreenState

logger = logging.getLogger("TITAN.AsyncEngine")


class AsyncEngine:
    """
    Wraps the synchronous Pipeline in an async architecture.

    - The main thread captures frames at full speed.
    - A background worker thread runs the AI pipeline on every Nth frame.
    - Results are stored and can be read by the main thread at any time
      without waiting for inference to complete.
    """

    def __init__(self, model_path, process_every_n=4):
        """
        Args:
            model_path: Path to the YOLO model (.pt or .onnx)
            process_every_n: Only run AI on every Nth frame (default=4).
                             At 30fps video, this means ~7.5 inferences/sec.
        """
        if process_every_n < 1:
            raise ValueError("process_every_n must be >= 1")
            
        self.pipeline = Pipeline(model_path)
        self.process_every_n = process_every_n

        # Latest results (thread-safe via lock)
        self._lock = threading.Lock()
        self._latest_game_state = None
        self._latest_action = None
        self._latest_screen_state = ScreenState.UNKNOWN
        self._latest_suggestion = None
        self._latest_result_id = 0
        self._latest_telemetry = None
        self._inference_counter = 0

        # Frame counter
        self._frame_count = 0

        # Background thread control
        self._worker_thread = None
        self._frame_queue = queue.Queue(maxsize=1)
        self._running = False
        self._stop_event = threading.Event()

    def start(self):
        """Start the background processing thread."""
        if self._worker_thread is not None:
            raise RuntimeError("Thread already running")
        self._running = True
        self._worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._worker_thread.start()

    def stop(self):
        """Stop the background processing thread."""
        self._running = False
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
            self._worker_thread = None

    def submit_frame(self, frame):
        """
        Submit a new frame for processing.
        Only every Nth frame is actually sent to the AI.
        Returns the latest cached results immediately.

        Args:
            frame: BGR image (numpy array)

        Returns:
            tuple: (game_state, action, screen_state, suggestion, result_id, telemetry)
        """
        self._frame_count += 1

        # Always capture the latest frame if it's the Nth
        if self._frame_count % self.process_every_n == 0:
            try:
                self._frame_queue.put_nowait(frame.copy())
            except queue.Full:
                pass

        # Always return the latest cached results (zero latency)
        with self._lock:
            return (
                self._latest_game_state,
                self._latest_action,
                self._latest_screen_state,
                self._latest_suggestion,
                self._latest_result_id,
                self._latest_telemetry
            )

    def _worker_loop(self):
        """Background thread that processes queued frames."""
        while self._running:
            try:
                frame = self._frame_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            try:
                with self._lock:
                    game_state, action, screen_state, suggestion = self.pipeline.process_frame(
                        frame
                    )

                    self._inference_counter += 1
                    self._latest_game_state = game_state
                    self._latest_action = action
                    self._latest_screen_state = screen_state
                    self._latest_suggestion = suggestion
                    self._latest_result_id = self._inference_counter
                    
                    # Snapshot telemetry data safely inside the lock
                    telemetry = {
                        "enemy_elixir": 0.0,
                        "elixir_advantage": 0.0,
                        "predicted_deck": [],
                        "hot_lane": "balanced",
                        "pressure": False
                    }
                    
                    if hasattr(self.pipeline, 'strategy'):
                        strat = self.pipeline.strategy
                        if hasattr(strat, 'memory'):
                            telemetry["predicted_deck"] = list(strat.memory.deck)
                        if hasattr(strat, 'elixir'):
                            telemetry["elixir_advantage"] = strat.elixir.get_elixir_advantage()
                            telemetry["enemy_elixir"] = strat.elixir.opponent_elixir
                        if game_state:
                            if hasattr(self.pipeline, 'last_threat_report'):
                                report = self.pipeline.last_threat_report
                                telemetry["hot_lane"] = report.hot_lane
                                telemetry["pressure"] = report.pressure
                                
                    self._latest_telemetry = telemetry

            except Exception as e:
                logger.error(f"Error in async worker: {e}", exc_info=True)

    def reset_pipeline(self):
        """Thread-safe reset for the pipeline state (called when match ends)."""
        with self._lock:
            self.pipeline.reset()
            self._latest_game_state = None
            self._latest_action = None
            self._latest_suggestion = None

    def notify_card_played(self, card_name):
        """Thread-safe deduction of elixir for manual/bot plays."""
        with self._lock:
            if hasattr(self.pipeline, 'strategy') and hasattr(self.pipeline.strategy, 'elixir'):
                self.pipeline.strategy.elixir.deduct_card_play(card_name)

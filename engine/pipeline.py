from vision.detector import Detector
from vision.screen_classifier import ScreenClassifier, ScreenState
from vision.region_filter import RegionFilter
from tracker.tracker import Tracker
from ui_reader.reader import UIReader
from state_builder.state_builder import StateBuilder
from strategy.strategy import Strategy
from actions.action_detector import ActionDetector
from strategy.threat_assessment import ThreatReport
import time


class Pipeline:

    def __init__(self, model_path):

        self.screen_classifier = ScreenClassifier()

        self.detector = Detector(model_path)

        self.region_filter = RegionFilter()

        self.tracker = Tracker()

        self.ui_reader = UIReader()

        self.state_builder = StateBuilder()

        self.strategy = Strategy()

        self.action_detector = ActionDetector()

        self.frame_count = 0
        self.match_start_time = None

        # Latest filtered detections, exposed for telemetry/visualization
        self.last_detections = []
        
        self._last_game_state = None
        self._last_rl_action = "WAIT"
        self.last_threat_report = None

    def reset(self):
        """Reset internal state for a new match."""
        self.tracker = Tracker()
        self.action_detector = ActionDetector()
        self.screen_classifier.reset()
        self.ui_reader.reset()
        self.frame_count = 0
        self.match_start_time = None
        self.last_detections = []
        self.strategy.reset_match()
        
        self._last_game_state = None
        self._last_rl_action = "WAIT"
        self.last_threat_report = None
        
        if self.strategy.is_rl_mode and hasattr(self.strategy, 'trainer') and self.strategy.trainer:
            self.strategy.trainer.last_state_key = None
            self.strategy.trainer.last_action = None
            self.strategy.trainer.episode_done = False

    def _extract_rl_action(self, action, suggestion):
        if not suggestion:
            return "WAIT"
        
        macros = [
            "ATTACK_LEFT", "ATTACK_RIGHT", 
            "DEFEND_LEFT", "DEFEND_RIGHT", 
            "PUNISH_LEFT", "PUNISH_RIGHT", 
            "SUPPORT_LEFT", "SUPPORT_RIGHT", 
            "CYCLE", "WAIT"
        ]
        for macro in macros:
            if macro in suggestion:
                return macro
                
        return "WAIT"

    def process_frame(self, frame):

        # Step 1: Check if this is a gameplay frame
        screen_state = self.screen_classifier.classify(frame)

        if screen_state != ScreenState.GAMEPLAY:
            # Any confirmed non-gameplay screen ends the current match context.
            # Clearing the clock here also protects against abandoned matches:
            # without this, game_time would leak into the next battle and
            # trigger double-elixir logic immediately.
            self.match_start_time = None
            self.last_detections = []

            # Send terminal states to the RL Trainer for Win/Loss rewards
            if screen_state in (ScreenState.VICTORY, ScreenState.DEFEAT):
                if self.strategy.is_rl_mode:
                    self.strategy.trainer.step(
                        state=self._last_game_state,
                        threat_report=ThreatReport(),
                        elixir_tracker=self.strategy.elixir,
                        action=self._last_rl_action,
                        screen_state=screen_state
                    )
                
            return None, None, screen_state, None
            
        # If we are in GAMEPLAY but haven't started the timer, start it now
        if self.match_start_time is None:
            self.match_start_time = time.time()

        # Step 2: Detect objects
        detections = self.detector.detect(frame)

        # Step 3: Filter by screen region
        detections = self.region_filter.filter(detections)
        self.last_detections = detections

        # Step 4: Track (with frame number)
        self.tracker.update(detections, self.frame_count)

        # Step 5: Get confirmed tracks only
        confirmed = self.tracker.get_confirmed_tracks()

        # Step 5.5: Detect actions for confirmed tracks
        for track in confirmed:
            self.action_detector.detect(track)

        # Step 6: Read UI
        ui_state = self.ui_reader.read(frame)

        # Step 7: Build GameState from confirmed tracks
        game_state = self.state_builder.build(confirmed, ui_state)

        # Step 8: Decide next action
        game_time = time.time() - self.match_start_time
        action, suggestion = self.strategy.decide(game_state, ui_state, game_time)

        # Step 9: Train RL Agent (ONLY in RL mode)
        if self.strategy.is_rl_mode:
            rl_action = self._extract_rl_action(action, suggestion)
            self._last_rl_action = rl_action
            self._last_game_state = game_state
            
            report = self.strategy.get_threat_report(game_state)
            self.last_threat_report = report
            
            self.strategy.trainer.step(
                state=game_state,
                threat_report=report,
                elixir_tracker=self.strategy.elixir,
                action=rl_action,
                screen_state=screen_state
            )

        self.frame_count += 1

        return game_state, action, screen_state, suggestion

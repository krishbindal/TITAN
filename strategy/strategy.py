"""
TITAN Strategy Engine — The Brain.
Routes decisions to game-mode-specific strategy modules.
"""

import inspect
import random
import time

from strategy.actions import Action, ActionCommand
from strategy.threat_assessment import ThreatAssessment
from strategy.elixir_tracker import ElixirTracker
from memory.enemy_tracker import EnemyTracker
from actions.placement import PlacementEngine
from configs.game_config import GAME_MODE
from experiments.rl.learning.trainer import Trainer

from strategy.modes import standard, sudden_death, rl
from strategy.modes import grandmaster
from core.analytics import get_engine, DecisionLogger

# Mode registry — maps config strings to mode modules
MODE_REGISTRY = {
    "standard": standard,
    "sudden_death": sudden_death,
    "rl": rl,
    "grandmaster": grandmaster,
}


def _cache_mode_sig(mode):
    """Cache the mode's decide() signature, or None if missing."""
    if hasattr(mode, 'decide'):
        return inspect.signature(mode.decide)
    return None


class Strategy:

    def __init__(self):
        self.threat = ThreatAssessment()
        self.elixir = ElixirTracker()
        self.memory = EnemyTracker()
        self.placement = PlacementEngine()
        
        # Initialize RL Trainer
        self.trainer = Trainer(actions=["WAIT", "DEFEND_LEFT", "DEFEND_RIGHT", "ATTACK_LEFT", "ATTACK_RIGHT"])

        # Load the active mode
        self._mode = MODE_REGISTRY.get(GAME_MODE, standard)
        self._mode_sig = _cache_mode_sig(self._mode)
        
        # Human-like delay queue state
        self._queued_action = None
        self._queued_time = 0
        
        # Initialize Analytics Logger
        self.session_id = int(time.time())
        self.logger = DecisionLogger(get_engine(), self.session_id)

    @property
    def is_rl_mode(self):
        return self._mode.__name__.endswith("rl")

    def reset_match(self):
        """Reset all stateful subsystems for a new match."""
        self.elixir = ElixirTracker()
        self.memory.clear()
        self._queued_action = None
        self._queued_time = 0
        if hasattr(self._mode, 'reset'):
            self._mode.reset()

    def decide(self, game_state, ui_state=None, game_time=0.0):
        """
        Analyze the battlefield and delegate to the active mode.
        """
        # Update subsystems
        # Activate double elixir at 2 minutes into the match
        if game_time >= 120.0 and not self.elixir._double_elixir:
            self.elixir.set_double_elixir(True)
            print("[Strategy] Double Elixir activated!")

        self.elixir.update(game_state, ui_state, game_time)
        self.memory.update(game_state, game_time)

        # Delegate to active mode
        if self._mode_sig is not None:
            if 'game_time' in self._mode_sig.parameters:
                result = self._mode.decide(
                    game_state, self.threat, self.elixir, self.memory, self.placement, game_time=game_time, ui_state=ui_state
                )
            else:
                result = self._mode.decide(
                    game_state, self.threat, self.elixir, self.memory, self.placement
                )
        else:
            # Mode has no decide() — default to WAIT
            return ActionCommand(Action.WAIT), "Mode has no decide()"
        
        # Handle different return signatures (Standard mode vs others)
        if len(result) == 3:
            action_cmd, suggestion, all_scores = result
        else:
            action_cmd, suggestion = result
            all_scores = []

        # Intercept action for human-like delay (Anti-Bot)
        current_time = time.time()
        
        # Check if we have a queued action
        is_queued = self._queued_action is not None
        
        # If strategy wants to WAIT, cancel any non-emergency queued action
        if action_cmd.action == Action.WAIT:
            if is_queued and "EMERGENCY" not in suggestion:
                self._queued_action = None
            
            # If we are STILL queued (emergency), check if it's time
            if self._queued_action is not None:
                if current_time >= self._queued_time:
                    action_cmd = self._queued_action
                    self._queued_action = None
                    suggestion = f"✅ Executing queued emergency"
                else:
                    suggestion = f"🤔 Hovering... ({self._queued_action.card_to_play})"
                    
        else: # Strategy wants to do something
            # If no queue, or the strategy changed its mind to a NEW action
            if not is_queued or self._queued_action.card_to_play != action_cmd.card_to_play:
                if "EMERGENCY" in suggestion:
                    delay = random.uniform(0.3, 0.5)
                elif "PUSH" in suggestion or "COMBO" in suggestion:
                    delay = random.uniform(0.8, 1.2)
                else:
                    delay = random.uniform(0.5, 0.8)
                    
                self._queued_action = action_cmd
                self._queued_time = current_time + delay
                
                action_cmd = ActionCommand(Action.WAIT)
                suggestion = f"🤔 Thinking... (Will play {self._queued_action.card_to_play} in {delay:.1f}s)"
            else:
                # We are queued and strategy still wants to do the same thing
                if current_time < self._queued_time:
                    action_cmd = ActionCommand(Action.WAIT)
                    suggestion = f"🤔 Hovering... ({self._queued_action.card_to_play})"
                else:
                    action_cmd = self._queued_action
                    self._queued_action = None
                    suggestion = f"✅ Executing: {suggestion}"
                    
        # Decision Logging
        if hasattr(self, 'logger') and self.logger:
            self.logger.log(
                game_time=game_time,
                my_elixir=self.elixir.player_elixir,
                enemy_elixir=self.elixir.opponent_elixir,
                best_action=action_cmd,
                best_reason=suggestion,
                all_scores=all_scores,
                predicted_deck=self.memory.deck
            )

        return action_cmd, suggestion

    def set_mode(self, mode_name):
        """Switch strategy mode at runtime."""
        if mode_name in MODE_REGISTRY:
            self._mode = MODE_REGISTRY[mode_name]
            self._mode_sig = _cache_mode_sig(self._mode)
            print(f"[Strategy] Switched to {mode_name} mode")
        else:
            print(f"[Strategy] Unknown mode: {mode_name}")

    def get_threat_report(self, game_state):
        """Get a detailed threat report for debugging/display."""
        return self.threat.assess(game_state)

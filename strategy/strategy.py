"""
TITAN Strategy Engine — The Brain.
Routes decisions to game-mode-specific strategy modules.
"""

from strategy.actions import Action, ActionCommand
from strategy.threat_assessment import ThreatAssessment
from strategy.elixir_tracker import ElixirTracker
from memory.enemy_tracker import EnemyTracker
from actions.placement import PlacementEngine
from configs.game_config import GAME_MODE
from learning.trainer import Trainer

from strategy.modes import standard, sudden_death, rl

# Mode registry — maps config strings to mode modules
MODE_REGISTRY = {
    "standard": standard,
    "sudden_death": sudden_death,
    "rl": rl,
}


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

    def decide(self, game_state, ui_state=None, game_time=0.0):
        """
        Analyze the battlefield and delegate to the active mode.
        """
        # Update subsystems
        self.elixir.update(game_state, ui_state, game_time)
        self.memory.update(game_state, game_time)

        # Delegate to active mode (returns ActionCommand, Suggestion_String)
        action_cmd, suggestion = self._mode.decide(
            game_state, self.threat, self.elixir, self.memory, self.placement
        )
        
        return action_cmd, suggestion

    def set_mode(self, mode_name):
        """Switch strategy mode at runtime."""
        if mode_name in MODE_REGISTRY:
            self._mode = MODE_REGISTRY[mode_name]
            print(f"[Strategy] Switched to {mode_name} mode")
        else:
            print(f"[Strategy] Unknown mode: {mode_name}")

    def get_threat_report(self, game_state):
        """Get a detailed threat report for debugging/display."""
        return self.threat.assess(game_state)

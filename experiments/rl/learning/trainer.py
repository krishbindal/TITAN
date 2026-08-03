import threading

from experiments.rl.learning.reinforcement import QLearningAgent
from experiments.rl.learning.replay_buffer import ReplayBuffer
from vision.screen_classifier import ScreenState


class Trainer:
    def __init__(self, actions):
        self.agent = QLearningAgent(actions=actions)
        self.buffer = ReplayBuffer()
        
        self.last_state_key = None
        self.last_action = None
        self.episode_done = False
        self._save_lock = threading.Lock()

    def reset(self):
        """Reset trainer state for a new match."""
        self.last_state_key = None
        self.last_action = None
        self.episode_done = False

    def step(self, state, threat_report, elixir_tracker, action, screen_state):
        """
        Takes a step in the environment, calculates reward, and updates the agent.
        """
        current_state_key = self.agent._get_state_key(state, threat_report, elixir_tracker)
        # Terminal state handling
        done = screen_state in [ScreenState.VICTORY, ScreenState.DEFEAT]
        
        if self.episode_done and done:
            return # Already processed terminal state for this episode

        if screen_state == ScreenState.GAMEPLAY:
            self.episode_done = False

        # Calculate Reward
        reward = self._calculate_reward(elixir_tracker, screen_state)

        # Save to buffer and update Q-table if we have a previous state
        if self.last_state_key is not None and self.last_action is not None:
            self.buffer.push(self.last_state_key, self.last_action, reward, current_state_key, done)
            self.agent.update(self.last_state_key, self.last_action, reward, current_state_key, done=done)

        self.last_state_key = current_state_key
        self.last_action = action
        
        # Save model on episode end
        if done:
            self.episode_done = True
            self.agent.decay_epsilon()
            with self._save_lock:
                self.agent.save()
            # Reset state tracking for next game
            self.last_state_key = None
            self.last_action = None

    def _calculate_reward(self, elixir_tracker, screen_state):
        reward = 0.0
        
        # Intermediate reward: Elixir advantage
        # elixir_adv = elixir_tracker.get_elixir_advantage()
        # reward += elixir_adv * 0.1  # (Removed to prevent continuous reward hacking)
        
        # Terminal rewards
        if screen_state == ScreenState.VICTORY:
            reward += 10.0
            print("[Trainer] Episode Finished: VICTORY! (+10 Reward)")
        elif screen_state == ScreenState.DEFEAT:
            reward -= 10.0
            print("[Trainer] Episode Finished: DEFEAT! (-10 Reward)")
            
        return reward

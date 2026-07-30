import random
import json
import os
import ast
from learning.vector_state import StateVectorizer

class QLearningAgent:
    def __init__(self, actions, alpha=0.1, gamma=0.9, epsilon=0.1, model_path="models/q_table.json"):
        self.q_table = {}
        self.actions = actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.model_path = model_path
        
        # Phase 7: Deep Learning Vectorizer (Future-proofing)
        self.vectorizer = StateVectorizer()
        
        self.load()

    def get_vectorized_state(self, game_state, ui_state, threat_report, elixir_tracker, memory, game_time):
        """
        Returns a dense numpy tensor suitable for DQN/PPO.
        This bridges the gap between the CV pipeline and Deep RL.
        """
        return self.vectorizer.vectorize(game_state, ui_state, threat_report, elixir_tracker, memory, game_time)

    def _get_state_key(self, state, threat_report, elixir_tracker, memory=None):
        """
        Legacy: Simplify the vast state space into a discrete tuple for the Q-Table.
        """
        # Discretize Player Elixir
        elixir = elixir_tracker.player_elixir
        if elixir < 4:
            e_state = "LOW"
        elif elixir < 8:
            e_state = "MED"
        else:
            e_state = "HIGH"
            
        # Discretize Pressure
        if threat_report.pressure == False:
            p_state = "SAFE"
        else:
            p_state = "DANGER"
            
        # Add Lane Control
        l_state = threat_report.hot_lane
        
        # Enemy Win Condition Tracker
        w_state = "WIN_CON_READY" if (memory and memory.has_win_condition_in_cycle()) else "NO_WIN_CON"
        
        # Elixir Advantage
        adv_state = "NEUTRAL"
        if memory:
            adv = elixir_tracker.get_elixir_advantage()
            if adv > 2.0:
                adv_state = "ADVANTAGE"
            elif adv < -2.0:
                adv_state = "DISADVANTAGE"
            
        return (e_state, p_state, l_state, w_state, adv_state)

    def get_q_value(self, state_key, action):
        return self.q_table.get((state_key, action), 0.0)

    def get_action(self, state, threat_report, elixir_tracker, valid_actions, memory=None):
        state_key = self._get_state_key(state, threat_report, elixir_tracker, memory)
        
        # Exploration
        if random.random() < self.epsilon:
            action = random.choice(valid_actions)
            return action, "Exploring new strategies..."
            
        # Exploitation
        q_values = [self.get_q_value(state_key, a) for a in valid_actions]
        max_q = max(q_values)
        
        # In case of tie, pick randomly among the best
        best_actions = [a for a, q in zip(valid_actions, q_values) if q == max_q]
        action = random.choice(best_actions)
        
        return action, f"Exploiting known strategy (Q: {max_q:.2f})"

    def update(self, state_key, action, reward, next_state_key):
        old_q = self.get_q_value(state_key, action)
        
        # Max Q for next state
        next_max = max([self.get_q_value(next_state_key, a) for a in self.actions])
        
        # Q-learning formula
        new_q = (1 - self.alpha) * old_q + self.alpha * (reward + self.gamma * next_max)
        self.q_table[(state_key, action)] = new_q

    def save(self):
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        # Convert tuple keys to strings for JSON serialization
        serializable_table = {str(k): v for k, v in self.q_table.items()}
        with open(self.model_path, 'w') as f:
            json.dump(serializable_table, f)

    def load(self):
        if os.path.exists(self.model_path):
            with open(self.model_path, 'r') as f:
                serializable_table = json.load(f)
                # Reconstruct tuple keys from string (e.g. "(('MED', 'SAFE', ...), 'WAIT')")
                self.q_table = {}
                for k_str, v in serializable_table.items():
                    try:
                        # Safely parse the string back into a tuple
                        k_tuple = ast.literal_eval(k_str)
                        self.q_table[k_tuple] = v
                    except Exception:
                        print(f"Warning: could not parse q-table key {k_str}")

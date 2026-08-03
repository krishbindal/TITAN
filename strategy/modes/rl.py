import time
import random
from strategy.actions import Action, ActionCommand
from experiments.rl.learning.reinforcement import QLearningAgent

# Global state for RL
_actions = ["WAIT", "DEFEND_LEFT", "DEFEND_RIGHT", "ATTACK_LEFT", "ATTACK_RIGHT"]
_agent = QLearningAgent(actions=_actions, epsilon=0.2)
_last_state_key = None
_last_action = None
_last_pressure = 0
_last_action_time = 0

def pick_best_counter(hand, top_threat_name):
    """Select the best card from hand to counter the incoming threat."""
    if not top_threat_name:
        return random.choice(hand)
        
    from knowledge.card_database import CardDatabase
    threat_lower = CardDatabase.normalize(top_threat_name)
    
    # Define hard counters using canonical names
    synergy_matrix = {
        # Swarms
        "skeleton_army": ["log", "arrows", "valkyrie", "baby_dragon", "wizard", "zap"],
        "goblin_barrel": ["log", "arrows", "valkyrie", "zap"],
        "minions": ["arrows", "wizard", "baby_dragon", "fireball"],
        # Tanks
        "giant": ["skeleton_army", "mini_pekka", "goblin_cage", "inferno_dragon", "tesla", "pekka"],
        "golem": ["skeleton_army", "mini_pekka", "goblin_cage", "inferno_dragon", "tesla", "pekka"],
        "hog_rider": ["skeleton_army", "goblin_cage", "tesla", "mini_pekka", "cannon"],
        # Air
        "balloon": ["musketeer", "wizard", "tesla", "inferno_dragon", "archers"],
        "baby_dragon": ["musketeer", "wizard", "tesla"],
        # Glass cannons
        "musketeer": ["valkyrie", "mini_pekka", "fireball", "knight"],
        "wizard": ["valkyrie", "mini_pekka", "fireball", "knight"],
        "witch": ["valkyrie", "baby_dragon", "log", "fireball", "knight"]
    }
    
    # If we have a specific counter strategy for this threat
    if threat_lower in synergy_matrix:
        preferred_counters = synergy_matrix[threat_lower]
        for counter in preferred_counters:
            if counter in hand:
                return counter
                
    # Fallback: if we didn't find a hard counter, return a random card
    return random.choice(hand)

def decide(game_state, threat_report, elixir_tracker, memory, placement):
    """
    Called every loop. Decides whether to WAIT or PLAY.
    """
    global _last_state_key, _last_action, _last_pressure, _last_action_time
    
    current_time = time.time()
    
    # We only make decisions every 2.0 seconds to allow animations to play
    if current_time - _last_action_time < 2.0:
        return ActionCommand(Action.WAIT), "RL cooldown"
        
    report = threat_report.assess(game_state)
    
    current_state_key = _agent._get_state_key(game_state, report, elixir_tracker, memory)

    
    if _last_state_key is not None and _last_action is not None:
        reward = 0
        # If pressure dropped, GOOD (+5)
        if report.pressure < _last_pressure:
            reward += 5
        # If pressure increased, BAD (-5)
        elif report.pressure > _last_pressure:
            reward -= 5
            
        # If we were at HIGH elixir and chose WAIT, BAD (-1 elixir leak)
        if _last_state_key[0] == "HIGH" and _last_action == "WAIT":
            reward -= 1
            
        _agent.update(_last_state_key, _last_action, reward, current_state_key)

    # 2. Get action from Q-Table
    action, reason = _agent.get_action(game_state, report, elixir_tracker, _actions, memory)
    
    # Save state for the next update step
    _last_state_key = current_state_key
    _last_action = action
    _last_pressure = report.pressure
    _last_action_time = current_time

    # 3. Translate Macro Action to ActionCommand
    if action == "WAIT" or not game_state.hand:
        return ActionCommand(Action.WAIT), f"RL chose WAIT ({reason})"
        
    # Translate macro action into card choice and placement
    target_x, target_y = 360, 900
    card_name = game_state.hand[0] # Fallback
    
    # We need to pick a card based on the intent (Attack vs Defense)
    # This is a heuristic translation layer from RL -> Micro
    # In the future, we could have the RL choose BOTH macro and micro.
    
    if action == "DEFEND_LEFT":
        target_x, target_y = 180, 850
        top_threat = report.top_threat.name if report.top_threat else None
        card_name = pick_best_counter(game_state.hand, top_threat)
    elif action == "DEFEND_RIGHT":
        target_x, target_y = 540, 850
        top_threat = report.top_threat.name if report.top_threat else None
        card_name = pick_best_counter(game_state.hand, top_threat)
    elif action == "ATTACK_LEFT":
        target_x, target_y = 180, 650
        # Try to find a tank or win condition
        card_name = game_state.hand[-1] # Simple heuristic
    elif action == "ATTACK_RIGHT":
        target_x, target_y = 540, 650
        card_name = game_state.hand[-1]

    return ActionCommand(
        Action.PLAY_CARD, 
        card_to_play=card_name, 
        target_x=target_x, 
        target_y=target_y
    ), f"RL chose {action} ({reason})"

def apply_match_result(won):
    """Called at the end of a match to apply massive rewards"""
    global _last_state_key, _last_action
    
    reward = 100 if won else -100
    if _last_state_key is not None and _last_action is not None:
        old_q = _agent.get_q_value(_last_state_key, _last_action)
        new_q = (1 - _agent.alpha) * old_q + _agent.alpha * reward
        _agent.q_table[(_last_state_key, _last_action)] = new_q
        
    _agent.save()

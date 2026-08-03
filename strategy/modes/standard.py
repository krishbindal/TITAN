"""
Standard Mode Strategy — PREDICTIVE.
Transforms TITAN into an intelligent bot by scoring actions using Memory,
Elixir tracking, and Counter matrices to preempt and outsmart the opponent.
"""

import json
import os
import random
from typing import Dict, List
from strategy.actions import Action, ActionCommand
from knowledge.counter_matrix import get_counters
from configs.settings import DECK_CONFIG_PATH

# Load deck config once at module level
_deck_config: Dict[str, List[str]] = {"win_conditions": [], "tanks": [], "spells": []}
if os.path.exists(DECK_CONFIG_PATH):
    with open(DECK_CONFIG_PATH, "r") as f:
        _deck_config = json.load(f)

# Hardcoded enemy win conditions for general evaluation
ENEMY_WIN_CONDITIONS = {
    "hog_rider", "giant", "golem", "balloon", "miner", 
    "goblin_barrel", "royal_giant", "wall_breakers", "battle_ram",
    "ram_rider", "goblin_drill", "skeleton_barrel", "graveyard",
    "lava_hound", "xbow", "mortar"
}


def can_afford(card_name, current_elixir, card_db):
    """Checks if we have enough elixir to play the card."""
    cost = 3.0  # Fallback cost for unknowns
    if not card_name.startswith("unknown_"):
        card_data = card_db.get(card_name)
        if card_data and card_data.cost:
            cost = card_data.cost
    return current_elixir >= cost, cost


def calculate_action_scores(game_state, threat, elixir, memory, placement):
    """
    Evaluates and scores all possible actions based on current game state and memory.
    Returns a list of tuples: (score, ActionCommand, reason)
    """
    scores = []
    hand = game_state.hand
    
    if not hand:
        return [(0.0, ActionCommand(Action.WAIT), "No cards detected in hand.")]

    current_elixir = elixir.player_elixir
    report = threat.assess(game_state)
    
    # Extract Memory Analytics
    elixir_adv = elixir.get_elixir_advantage()
    enemy_win_con_ready = memory.has_win_condition_in_cycle()
    
    win_cons = set(_deck_config.get("win_conditions", []))
    tanks = set(_deck_config.get("tanks", []))

    # =========================================================
    # 1. SCORE 'WAIT' ACTION
    # =========================================================
    wait_score = 10.0  # Base wait score
    
    # Predictive Defense: Enemy has high elixir and a win-con ready
    if enemy_win_con_ready and elixir.opponent_elixir >= 6.0:
        wait_score += 50.0  
        
    # Prevent leaking elixir
    if current_elixir >= 9.5:
        wait_score -= 200.0 
    # Force wait if broke
    elif current_elixir < 3.0:
        wait_score += 40.0
        
    scores.append((wait_score, ActionCommand(Action.WAIT), f"Waiting (Adv: {elixir_adv:.1f})"))

    # =========================================================
    # 2. SCORE CARD ACTIONS
    # =========================================================
    for card in hand:
        if card.startswith("unknown_"):
            continue
            
        afford, cost = can_afford(card, current_elixir, elixir.card_db)
        if not afford:
            continue

        tx, ty = placement.calculate_drop(card, report, game_state)
        
        card_score = 0.0
        reason = ""
        saved_for_defense = False

        # --- A) Counter Preservation Logic ---
        # Don't waste a critical counter if the enemy is holding their win condition
        for e_card in memory.deck:
            if e_card in ENEMY_WIN_CONDITIONS and memory.is_in_cycle(e_card):
                if card in get_counters(e_card):
                    # This card is a primary counter to a ready enemy win condition!
                    card_score -= 100.0
                    saved_for_defense = True
                    reason = f"Saving {card} for {e_card}"
                    break

        # --- B) Defense Score ---
        if report.pressure and report.top_threat:
            enemy_key = report.top_threat.name.replace("enemy_", "")
            valid_counters = get_counters(enemy_key)
            
            if card in valid_counters:
                # Better counters (lower index) get higher scores
                rank = valid_counters.index(card)
                card_score += 100.0 + (10 - rank)
                reason = f"Defending {enemy_key} with {card}"
                saved_for_defense = False  # Override preservation if we MUST defend now
            else:
                card_score += 20.0  # Desperate defense
                if not reason:
                    reason = f"Desperate defend with {card}"
                    
        # --- C) Offense / Push Score ---
        elif not saved_for_defense:
            if card in win_cons:
                # Smart Win Condition Usage: Check if direct counter is available
                countered = False
                for e_counter in get_counters(card):
                    if e_counter in memory.deck and memory.is_in_cycle(e_counter):
                        card_score -= 80.0
                        reason = f"{card} countered by {e_counter}"
                        countered = True
                        break
                
                if not countered:
                    # Elixir Advantage scaling
                    card_score += 60.0 + (elixir_adv * 15.0)
                    reason = f"Pushing with {card} (Adv: {elixir_adv:.1f})"
                    
            elif card in tanks:
                card_score += 40.0 + (elixir_adv * 10.0)
                reason = f"Building push with {card} (Adv: {elixir_adv:.1f})"
                
            else:
                # Cycling / Support cards
                if current_elixir >= 7.0:
                    card_score += 20.0 + (elixir_adv * 5.0)
                    reason = f"Cycling {card}"

        # --- D) Overflow Fallback ---
        # If we are leaking elixir and this is our best valid card, force it
        if current_elixir >= 9.5 and card_score <= wait_score:
            card_score = wait_score + 10.0 + random.random()
            reason = f"Elixir Overflow: Dumping {card}"

        scores.append((
            card_score, 
            ActionCommand(Action.PLAY_CARD, card_to_play=card, target_x=tx, target_y=ty), 
            f"{reason} [Score: {card_score:.1f}]"
        ))

    return scores


def decide(game_state, threat, elixir, memory, placement):
    """
    Main entry point for strategy evaluation.
    Delegates to the scoring system and picks the highest scoring action.
    Returns: best_action, best_reason, all_scores
    """
    scores = calculate_action_scores(game_state, threat, elixir, memory, placement)
    
    # Sort actions by score descending
    scores.sort(key=lambda x: x[0], reverse=True)
    
    # Pick the highest scoring action
    best_score, best_action, best_reason = scores[0]
    
    return best_action, best_reason, scores

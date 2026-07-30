"""
Standard Mode Strategy — AGGRESSIVE.
Key Rule: NEVER sit at high elixir. Always play a card if elixir >= 8.
Defend immediately, counter-push with any advantage, push at 7+.
"""

import json
import os
import random
from strategy.actions import Action, ActionCommand
from knowledge.counter_matrix import best_counter
from configs.settings import DECK_CONFIG_PATH

# Load deck config once at module level
_deck_config = {"win_conditions": [], "tanks": []}
if os.path.exists(DECK_CONFIG_PATH):
    with open(DECK_CONFIG_PATH, "r") as f:
        _deck_config = json.load(f)


def can_afford(card_name, current_elixir, card_db):
    """Checks if we have enough elixir to play the card."""
    cost = 3.0  # Fallback cost for unknowns
    if not card_name.startswith("unknown_"):
        card_data = card_db.get(card_name)
        if card_data and card_data.cost:
            cost = card_data.cost
    return current_elixir >= cost, cost


def pick_best_card(hand, report, mode, card_db):
    """
    Pick the best card for the situation.
    mode: 'defend', 'push', 'overflow'
    """
    win_cons = set(_deck_config.get("win_conditions", []))
    tanks = set(_deck_config.get("tanks", []))

    if mode == "defend" and report.top_threat:
        enemy_key = report.top_threat.name.replace("enemy_", "")
        counter = best_counter(enemy_key, hand)
        if counter:
            return counter

    if mode == "push":
        # Prefer win conditions first, then tanks
        for c in hand:
            if c in win_cons and not c.startswith("unknown_"):
                return c
        for c in hand:
            if c in tanks and not c.startswith("unknown_"):
                return c

    if mode == "overflow":
        # At max elixir, prefer tanks (build push from back) then anything
        for c in hand:
            if c in tanks and not c.startswith("unknown_"):
                return c
        for c in hand:
            if c in win_cons and not c.startswith("unknown_"):
                return c

    # Fallback: pick a known card, or random unknown
    known = [c for c in hand if not c.startswith("unknown_")]
    if known:
        return random.choice(known)

    unknowns = [c for c in hand if c.startswith("unknown_")]
    if unknowns:
        return random.choice(unknowns)

    return hand[0] if hand else None


def decide(game_state, threat, elixir, memory, placement):
    """
    Aggressive standard mode decision logic.
    NEVER leaks elixir. Always plays a card at 8+.
    """
    hand = game_state.hand
    if not hand:
        return ActionCommand(Action.WAIT), "No cards detected in hand."

    current_elixir = elixir.player_elixir
    report = threat.assess(game_state)

    # =========================================================
    # RULE 1: NEVER LEAK ELIXIR — At 8+, play SOMETHING now.
    # Sitting at 10 elixir = wasting 1 elixir every 2.8 seconds.
    # =========================================================
    if current_elixir >= 8.0:
        # If there are enemies, try to counter. Otherwise push.
        if report.enemy_count > 0 and report.top_threat:
            card = pick_best_card(hand, report, "defend", elixir.card_db)
        else:
            card = pick_best_card(hand, report, "overflow", elixir.card_db)

        if card:
            afford, cost = can_afford(card, current_elixir, elixir.card_db)
            if afford:
                tx, ty = placement.calculate_drop(card, report, game_state)
                return ActionCommand(
                    Action.PLAY_CARD, card_to_play=card, target_x=tx, target_y=ty
                ), f"Elixir overflow ({current_elixir:.0f}/10)! Playing {card.replace('_', ' ').title()}"

    # =========================================================
    # RULE 2: DEFEND — Enemy in danger zone, counter immediately.
    # =========================================================
    if report.pressure and report.top_threat:
        enemy_key = report.top_threat.name.replace("enemy_", "")
        counter = best_counter(enemy_key, hand)

        if not counter:
            counter = pick_best_card(hand, report, "defend", elixir.card_db)

        if counter:
            afford, cost = can_afford(counter, current_elixir, elixir.card_db)
            if afford:
                tx, ty = placement.calculate_drop(counter, report, game_state)
                return ActionCommand(
                    Action.PLAY_CARD, card_to_play=counter, target_x=tx, target_y=ty
                ), f"DEFENDING! {counter.replace('_', ' ').title()} vs {enemy_key.replace('_', ' ').title()}"
            else:
                return ActionCommand(Action.WAIT), f"Under attack! Need {cost:.0f} elixir, have {current_elixir:.0f}"

    # =========================================================
    # RULE 3: PRE-DEFEND — Enemies exist but not yet in danger zone.
    # If we have 5+ elixir, play a counter preemptively.
    # =========================================================
    if report.enemy_count > 0 and current_elixir >= 5:
        card = pick_best_card(hand, report, "defend", elixir.card_db)
        if card:
            afford, cost = can_afford(card, current_elixir, elixir.card_db)
            if afford:
                tx, ty = placement.calculate_drop(card, report, game_state)
                return ActionCommand(
                    Action.PLAY_CARD, card_to_play=card, target_x=tx, target_y=ty
                ), f"Pre-defending with {card.replace('_', ' ').title()} ({current_elixir:.0f} elixir)"

    # =========================================================
    # RULE 4: PUSH — No enemies, 7+ elixir, start a push.
    # =========================================================
    if report.enemy_count == 0 and current_elixir >= 7:
        card = pick_best_card(hand, report, "push", elixir.card_db)
        if card:
            afford, cost = can_afford(card, current_elixir, elixir.card_db)
            if afford:
                tx, ty = placement.calculate_drop(card, report, game_state)
                return ActionCommand(
                    Action.PLAY_CARD, card_to_play=card, target_x=tx, target_y=ty
                ), f"Pushing with {card.replace('_', ' ').title()} ({current_elixir:.0f} elixir)"

    # =========================================================
    # DEFAULT: Save elixir, build up for a play.
    # =========================================================
    return ActionCommand(Action.WAIT), f"Building elixir ({current_elixir:.1f}/10)"

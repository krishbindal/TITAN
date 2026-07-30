"""
Sudden Death Mode Strategy.
Extremely aggressive: push the weakest enemy tower with everything.
No elixir conservation — go all-in to score a crown.
"""

from strategy.actions import Action, ActionCommand
from knowledge.counter_matrix import best_counter


def decide(game_state, threat, elixir, memory, placement):
    """
    Sudden Death mode — always push aggressively.
    """
    report = threat.assess(game_state)

    # If under heavy pressure, still defend
    if report.pressure and report.top_threat:
        enemy_key = report.top_threat.name.replace("enemy_", "")
        counter_card = best_counter(enemy_key, game_state.hand)

        if counter_card:
            tx, ty = placement.calculate_drop(counter_card, report, game_state)
            return ActionCommand(
                Action.PLAY_CARD, card_to_play=counter_card, target_x=tx, target_y=ty
            ), "Defending top threat"

    # Aggressive: play cards as soon as we have enough elixir
    if elixir.player_elixir >= 4 and len(game_state.hand) > 0:
        # Priority: win conditions first
        win_cons = {
            "hog_rider",
            "ram_rider",
            "balloon",
            "goblin_barrel",
            "miner",
            "wall_breakers",
            "battle_ram",
            "royal_giant",
        }

        card_to_play = None
        for c in game_state.hand:
            if c in win_cons:
                card_to_play = c
                break

        # Fallback: play any available card
        if not card_to_play:
            card_to_play = game_state.hand[0]

        # Target the hot lane (where enemy is weakest)
        if report.hot_lane == "left":
            target_x = 540  # Push right (enemy's weakest)
        else:
            target_x = 180  # Push left

        target_y = 400  # Deep in enemy territory

        return ActionCommand(
            Action.PLAY_CARD,
            card_to_play=card_to_play,
            target_x=target_x,
            target_y=target_y,
        ), f"Sudden death push: {card_to_play}"

    return ActionCommand(Action.WAIT), "Waiting for elixir"

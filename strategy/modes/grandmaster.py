"""
Grandmaster Strategy Mode — TITAN's Expert System.

Decision Priority (evaluated top to bottom, first match wins):
  1. EMERGENCY DEFEND — Enemy in danger zone, must counter NOW
  2. SPELL FINISH — Enemy tower < spell damage, cycle to spell and fire
  3. PUNISH — Enemy just played expensive card, rush opposite lane
  4. COMBO PUSH — We have a tank + support combo in hand, build a push
  5. PRE-DEFEND — Enemies approaching, place counter early for value
  6. ELIXIR OVERFLOW — At 9+ elixir, play something to avoid leak
  7. CYCLE — Play cheapest card to rotate toward win condition
  8. WAIT — Save elixir, opponent has nothing threatening

Key Principles:
  - NEVER play into the enemy's spell (don't stack squishies)
  - ALWAYS evaluate elixir trades (don't spend 7 to counter 3)
  - PHASE AWARENESS: passive in single elixir, aggressive in double
  - HOLD spells for maximum value (don't Fireball 1 unit)
"""

import time
import random
from strategy.actions import Action, ActionCommand
from knowledge.counter_matrix import best_counter
from knowledge.card_database import CardDatabase

_card_db = CardDatabase()
_last_action_time = 0
_MIN_ACTION_DELAY = 1.5  # seconds between plays

def reset():
    """Reset the grandmaster state for a new match."""
    global _last_action_time
    _last_action_time = 0

# ─── Card Role Classification ───
SPELLS = {"log", "zap", "fireball", "arrows", "poison", "rocket", 
          "lightning", "snowball", "tornado", "earthquake"}
TANKS = {"giant", "golem", "pekka", "mega_knight", "lava_hound", 
         "royal_giant", "goblin_giant", "skeleton_giant"}
WIN_CONDITIONS = {"hog_rider", "ram_rider", "balloon", "goblin_barrel", 
                  "miner", "wall_breakers", "battle_ram", "royal_giant",
                  "graveyard", "xbow", "mortar"}
SUPPORT = {"musketeer", "wizard", "witch", "electro_wizard", "ice_wizard",
           "baby_dragon", "executioner", "magic_archer", "hunter",
           "fire_cracker", "archers", "flying_machine"}
SWARMS = {"skeleton_army", "minion_horde", "goblin_gang", "bats",
          "skeletons", "minions", "guards"}
MINI_TANKS = {"knight", "valkyrie", "mini_pekka", "dark_prince", 
              "prince", "bandit", "lumberjack", "ice_golem"}
CHEAP_CYCLE = {"skeletons", "ice_spirit", "fire_spirit", "electro_spirit",
               "ice_golem", "bats", "log", "zap"}

# ─── Combo/Synergy Definitions ───
# Tank + Support combos that should be played together
COMBOS = [
    ({"giant", "golem", "goblin_giant"}, {"musketeer", "wizard", "witch", 
     "baby_dragon", "electro_wizard"}),
    ({"hog_rider"}, {"ice_golem", "ice_spirit", "skeletons", "earthquake"}),
    ({"lava_hound"}, {"balloon", "minions", "baby_dragon"}),
    ({"pekka"}, {"electro_wizard", "baby_dragon", "magic_archer", "battle_ram"}),
]


def get_card_cost(card_name):
    """Get elixir cost of a card."""
    if card_name.startswith("unknown_"):
        return 4.0  # Conservative estimate
    card = _card_db.get(card_name)
    return card.cost if card and card.cost else 4.0


def can_afford(card_name, current_elixir):
    """Check if we can afford a card."""
    cost = get_card_cost(card_name)
    return current_elixir >= cost, cost


def find_cheapest(hand):
    """Find the cheapest card in hand."""
    best = None
    best_cost = 99
    for c in hand:
        cost = get_card_cost(c)
        if cost < best_cost:
            best_cost = cost
            best = c
    return best, best_cost


def evaluate_spell_value(spell_name, troops_in_range):
    """
    Calculate the value of casting a spell.
    Returns (total_elixir_value_killed, number_of_targets).
    Only cast if value >= spell cost.
    """
    spell_card = _card_db.get(spell_name)
    if not spell_card:
        return 0, 0

    spell_damage = spell_card.combat.damage
    total_value = 0
    targets = 0

    for troop in troops_in_range:
        troop_key = troop.name.replace("enemy_", "")
        troop_card = _card_db.get(troop_key)
        if troop_card and troop_card.combat.hp <= spell_damage * 1.1:
            # This spell would kill this troop
            total_value += troop_card.cost
            targets += 1

    return total_value, targets


def find_combo_in_hand(hand):
    """Check if we have a tank+support combo ready."""
    for tank_set, support_set in COMBOS:
        tank = None
        support = None
        for c in hand:
            if c in tank_set:
                tank = c
            if c in support_set:
                support = c
        if tank and support:
            return tank, support
    return None, None


def evaluate_trade(our_card, enemy_card):
    """
    Returns the elixir trade value.
    Positive = good trade for us.
    Example: We play Skeleton Army (3) to kill PEKKA (7) = +4 trade.
    """
    our_cost = get_card_cost(our_card)
    enemy_cost = get_card_cost(enemy_card)
    return enemy_cost - our_cost


def detect_punish_window(memory, elixir_tracker):
    """
    Check if the enemy just spent a lot of elixir (heavy card)
    and we have an elixir advantage >= 4 for a punish play.
    """
    if not memory.play_history:
        return False
    
    last_played = memory.play_history[-1]
    last_cost = get_card_cost(last_played)
    advantage = elixir_tracker.get_elixir_advantage()
    
    # If they just dropped an expensive card and we have elixir advantage
    return last_cost >= 5 and advantage >= 3


def get_game_phase(game_time):
    """
    Determine the game phase for strategy adjustment.
    CR match: 3 minutes = 180 seconds.
    - Single elixir:  0:00 - 2:00 (first 120s)  → CONSERVATIVE
    - Double elixir:  2:00 - 3:00 (120-180s)     → AGGRESSIVE
    - Overtime:       3:00+                        → ALL-IN
    """
    if game_time < 120:
        return "single_elixir"
    elif game_time < 180:
        return "double_elixir"
    else:
        return "overtime"


def get_opposite_lane(hot_lane):
    """Return the opposite lane."""
    if hot_lane == "left":
        return "right"
    elif hot_lane == "right":
        return "left"
    return random.choice(["left", "right"])


def decide(game_state, threat, elixir, memory, placement, game_time=0.0, ui_state=None):
    """
    Grandmaster-level decision engine.
    Evaluates every situation and picks the optimal play.
    """
    global _last_action_time
    
    current_time = time.time()
    hand = game_state.hand
    
    if not hand:
        return ActionCommand(Action.WAIT), "No cards in hand"
    
    phase = get_game_phase(game_time)
    
    # Phase adjustments
    if phase == "double_elixir":
        min_action_delay = 1.0  # Faster plays in double elixir
    elif phase == "overtime":
        min_action_delay = 0.5  # All-in mode
    else:
        min_action_delay = 1.5

    # Throttle actions — don't spam faster than the game can handle
    if current_time - _last_action_time < min_action_delay:
        return ActionCommand(Action.WAIT), "Action cooldown"
    
    current_elixir = elixir.player_elixir
    report = threat.assess(game_state)
    
    elixir_advantage = elixir.get_elixir_advantage()
    
    # ═══════════════════════════════════════════════════════
    # PHASE 5: ENEMY CYCLE PREDICTION (PREDICTIVE DEFENSE)
    # Check if the enemy has a win condition ready in their hand.
    # If so, reserve our best counter so we don't waste it on lesser threats.
    # ═══════════════════════════════════════════════════════
    reserved_card = None
    if memory.has_win_condition_in_cycle():
        enemy_win_con = next((c for c in memory.deck if c in WIN_CONDITIONS and memory.is_in_cycle(c)), None)
        if enemy_win_con:
            reserved_card = best_counter(enemy_win_con, hand)
            
    # ═══════════════════════════════════════════════════════
    # PRIORITY 1: EMERGENCY DEFENSE
    # Enemy troops in danger zone — MUST counter immediately
    # ═══════════════════════════════════════════════════════
    if report.pressure and report.top_threat:
        enemy_key = report.top_threat.name.replace("enemy_", "")
        
        # Find the best affordable counter
        counter = best_counter(enemy_key, hand)
        
        if counter:
            # Evaluate the trade — don't use PEKKA (7) to kill Skeletons (1)
            trade_value = evaluate_trade(counter, enemy_key)
            
            # Accept even slightly negative trades when under pressure
            if trade_value >= -2:
                afford, cost = can_afford(counter, current_elixir)
                if afford:
                    tx, ty = placement.calculate_drop(counter, report, game_state)
                    _last_action_time = current_time
                    return ActionCommand(
                        Action.PLAY_CARD, card_to_play=counter,
                        target_x=tx, target_y=ty
                    ), f"🛡️ EMERGENCY: {counter} vs {enemy_key} (trade: {trade_value:+.0f})"
        
        # Fallback: if no good counter, use cheapest card to distract
        cheapest, cheap_cost = find_cheapest(hand)
        if cheapest and current_elixir >= cheap_cost:
            tx, ty = placement.calculate_drop(cheapest, report, game_state)
            _last_action_time = current_time
            return ActionCommand(
                Action.PLAY_CARD, card_to_play=cheapest,
                target_x=tx, target_y=ty
            ), f"🛡️ PANIC: Distract with {cheapest}"
    
    # ═══════════════════════════════════════════════════════
    # PRIORITY 2: SPELL FINISH
    # If enemy tower is low enough to spell, just fire it
    # ═══════════════════════════════════════════════════════
    if ui_state and (ui_state.enemy_left_tower_hp or ui_state.enemy_right_tower_hp):
        for c in hand:
            if c in SPELLS and c != "tornado":
                spell_card = _card_db.get(c)
                # Ensure the spell has damage and we can afford it
                if spell_card and hasattr(spell_card.combat, 'damage') and spell_card.combat.damage:
                    afford, cost = can_afford(c, current_elixir)
                    if afford:
                        # Crown tower damage is usually ~30% of troop damage, but we use what we have in DB
                        # For now, let's assume the DB has crown_tower_damage or we calculate it (30%)
                        ct_damage = getattr(spell_card.combat, 'crown_tower_damage', spell_card.combat.damage * 0.3)
                        
                        # Check left tower
                        if ui_state.enemy_left_tower_hp and ui_state.enemy_left_tower_hp <= ct_damage:
                            _last_action_time = current_time
                            return ActionCommand(
                                Action.PLAY_CARD, card_to_play=c,
                                target_x=180, target_y=250
                            ), f"💥 SPELL FINISH: {c} on Left Tower (HP: {ui_state.enemy_left_tower_hp} <= {ct_damage:.0f})"
                            
                        # Check right tower
                        if ui_state.enemy_right_tower_hp and ui_state.enemy_right_tower_hp <= ct_damage:
                            _last_action_time = current_time
                            return ActionCommand(
                                Action.PLAY_CARD, card_to_play=c,
                                target_x=540, target_y=250
                            ), f"💥 SPELL FINISH: {c} on Right Tower (HP: {ui_state.enemy_right_tower_hp} <= {ct_damage:.0f})"
    
    # ═══════════════════════════════════════════════════════
    # PRIORITY 3: PUNISH PLAY
    # Enemy just dropped an expensive card — rush opposite lane!
    # ═══════════════════════════════════════════════════════
    # ═══════════════════════════════════════════════════════
    if detect_punish_window(memory, elixir):
        # Find a fast win condition or bridge spam card (but don't use our reserved counter)
        punish_card = None
        for c in hand:
            if c in WIN_CONDITIONS and c not in SPELLS and c != reserved_card:
                punish_card = c
                break
        if not punish_card:
            for c in hand:
                if c in MINI_TANKS and c != reserved_card:
                    punish_card = c
                    break
        
        if punish_card:
            afford, cost = can_afford(punish_card, current_elixir)
            if afford:
                # Rush OPPOSITE lane from where enemy committed
                opposite = get_opposite_lane(report.hot_lane)
                push_x = 180 if opposite == "left" else 540
                bridge_y = 550
                
                _last_action_time = current_time
                return ActionCommand(
                    Action.PLAY_CARD, card_to_play=punish_card,
                    target_x=push_x, target_y=bridge_y
                ), f"⚡ PUNISH! {punish_card} opposite lane (enemy just spent heavy)"
    
    # ═══════════════════════════════════════════════════════
    # PRIORITY 4: SPELL VALUE
    # If we have a spell and there's a big cluster of enemies,
    # check if the trade is positive before casting
    # ═══════════════════════════════════════════════════════
    for card in hand:
        if card in SPELLS and card not in {"log", "zap"}:  # Save small spells for swarms
            spell_cost = get_card_cost(card)
            afford, _ = can_afford(card, current_elixir)
            if not afford:
                continue
            
            # Find enemy troops in a cluster (within spell radius)
            enemy_troops = [t for t in game_state.troops if t.team == "enemy"]
            if len(enemy_troops) >= 2:
                value, targets = evaluate_spell_value(card, enemy_troops)
                if value >= spell_cost:
                    # Positive trade — fire the spell at the cluster centroid
                    cx = sum(t.x for t in enemy_troops) / len(enemy_troops)
                    cy = sum(t.y for t in enemy_troops) / len(enemy_troops)
                    _last_action_time = current_time
                    return ActionCommand(
                        Action.PLAY_CARD, card_to_play=card,
                        target_x=int(cx), target_y=int(cy)
                    ), f"🎯 SPELL VALUE: {card} on {targets} troops ({value:.0f} elixir value)"
                    
    # ═══════════════════════════════════════════════════════
    # PRIORITY 4.5: CYCLE-AWARE AGGRESSION
    # If enemy just played their best counter to our swarm/win condition,
    # punish them with the card they can no longer counter.
    # ═══════════════════════════════════════════════════════
    if memory.play_history and report.enemy_count == 0:
        last_played = memory.play_history[-1]
        # Example: if they just played Valkyrie, they are vulnerable to swarms
        if last_played in {"valkyrie", "wizard", "executioner", "bomb_tower"}:
            for c in hand:
                if c in SWARMS and c != reserved_card:
                    afford, _ = can_afford(c, current_elixir)
                    if afford:
                        _last_action_time = current_time
                        tx, ty = placement.calculate_drop(c, report, game_state)
                        return ActionCommand(
                            Action.PLAY_CARD, card_to_play=c,
                            target_x=tx, target_y=ty
                        ), f"⚡ CYCLE AGGRESSION: {c} at bridge (enemy just played {last_played})"
    
    # ═══════════════════════════════════════════════════════
    # PRIORITY 5: COMBO PUSH
    # If we have a tank + support in hand AND enough elixir
    # AND no immediate threats, start building a push
    # ═══════════════════════════════════════════════════════
    if report.enemy_count == 0 or not report.pressure:
        tank, support = find_combo_in_hand(hand)
        if tank and support and tank != reserved_card and support != reserved_card:
            tank_cost = get_card_cost(tank)
            support_cost = get_card_cost(support)
            total_cost = tank_cost + support_cost
            
            # Only combo if we can afford the tank AND have enough left for defense
            if current_elixir >= tank_cost + 3:  # +3 buffer for emergency defense
                # Play tank in the back to start a push
                push_x = 180 if report.hot_lane != "right" else 540
                back_y = 1100  # Behind king tower
                
                _last_action_time = current_time
                return ActionCommand(
                    Action.PLAY_CARD, card_to_play=tank,
                    target_x=push_x, target_y=back_y
                ), f"🏗️ COMBO: Starting push with {tank} (support: {support} ready)"
    
    # ═══════════════════════════════════════════════════════
    # PRIORITY 6: PRE-DEFEND
    # Enemies exist but not yet in danger zone.
    # Place counter early for maximum value.
    # ═══════════════════════════════════════════════════════
    if report.enemy_count > 0 and report.top_threat and current_elixir >= 5:
        enemy_key = report.top_threat.name.replace("enemy_", "")
        counter = best_counter(enemy_key, hand)
        
        if counter:
            trade_value = evaluate_trade(counter, enemy_key)
            # Only pre-defend if trade is positive or neutral
            if trade_value >= 0:
                afford, cost = can_afford(counter, current_elixir)
                if afford:
                    tx, ty = placement.calculate_drop(counter, report, game_state)
                    _last_action_time = current_time
                    return ActionCommand(
                        Action.PLAY_CARD, card_to_play=counter,
                        target_x=tx, target_y=ty
                    ), f"🔰 Pre-defend: {counter} vs {enemy_key} (trade: {trade_value:+.0f})"
    
    # ═══════════════════════════════════════════════════════
    # PRIORITY 7: ELIXIR OVERFLOW PREVENTION
    # At 9+ elixir, play SOMETHING to avoid leaking
    # ═══════════════════════════════════════════════════════
    if current_elixir >= 9.0:
        # Prefer tanks in the back (start a push)
        for c in hand:
            if c in TANKS and c != reserved_card:
                afford, _ = can_afford(c, current_elixir)
                if afford:
                    push_x = random.choice([180, 540])
                    _last_action_time = current_time
                    return ActionCommand(
                        Action.PLAY_CARD, card_to_play=c,
                        target_x=push_x, target_y=1100
                    ), f"💧 Overflow: {c} in the back (avoiding leak)"
        
        # No tank? Play cheapest card
        cheapest_available = None
        cheap_cost = 99
        for c in hand:
            if c != reserved_card:
                cost = get_card_cost(c)
                if cost < cheap_cost:
                    cheap_cost = cost
                    cheapest_available = c
                    
        if cheapest_available and current_elixir >= cheap_cost:
            tx, ty = placement.calculate_drop(cheapest_available, report, game_state)
            _last_action_time = current_time
            return ActionCommand(
                Action.PLAY_CARD, card_to_play=cheapest_available,
                target_x=tx, target_y=ty
            ), f"💧 Overflow: {cheapest_available} to avoid leak"
    
    # ═══════════════════════════════════════════════════════
    # PRIORITY 8: PUSH (when safe)
    # No enemies, 7+ elixir, push with a win condition
    # ═══════════════════════════════════════════════════════
    if report.enemy_count == 0 and current_elixir >= 7:
        for c in hand:
            if c in WIN_CONDITIONS and c not in SPELLS and c != reserved_card:
                afford, cost = can_afford(c, current_elixir)
                if afford:
                    tx, ty = placement.calculate_drop(c, report, game_state)
                    _last_action_time = current_time
                    return ActionCommand(
                        Action.PLAY_CARD, card_to_play=c,
                        target_x=tx, target_y=ty
                    ), f"⚔️ PUSH: {c} at bridge"
    
    # ═══════════════════════════════════════════════════════
    # DEFAULT: WAIT
    # Build elixir, wait for the right moment
    # ═══════════════════════════════════════════════════════
    return ActionCommand(Action.WAIT), f"⏳ Building elixir ({current_elixir:.1f}/10)"

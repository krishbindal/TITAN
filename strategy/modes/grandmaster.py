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
            unit_value = troop_card.cost
            if hasattr(troop_card, 'count') and troop_card.count > 1:
                unit_value = troop_card.cost / troop_card.count
            total_value += unit_value
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
    if len(memory.play_history) < 2:
        return False
    
    # Check the last 3 cards played for an expensive one
    recent = memory.play_history[-3:]
    for card in recent:
        cost = get_card_cost(card)
        if cost >= 5:
            advantage = elixir_tracker.get_elixir_advantage()
            return advantage >= 3
    return False


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
    doomed_lane = None
    if ui_state and hasattr(ui_state, 'our_left_tower_hp') and hasattr(ui_state, 'our_right_tower_hp'):
        if ui_state.our_left_tower_hp is not None and ui_state.our_left_tower_hp < 400:
            doomed_lane = "left"
        elif ui_state.our_right_tower_hp is not None and ui_state.our_right_tower_hp < 400:
            doomed_lane = "right"
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
        # SACRIFICE PROTOCOL: If tower is doomed, ignore and save elixir for opposite lane push
        if ui_state and hasattr(ui_state, 'our_left_tower_hp') and hasattr(ui_state, 'our_right_tower_hp'):
            left_doomed = report.hot_lane == "left" and ui_state.our_left_tower_hp is not None and ui_state.our_left_tower_hp < 400
            right_doomed = report.hot_lane == "right" and ui_state.our_right_tower_hp is not None and ui_state.our_right_tower_hp < 400
            
            # If doomed and heavy push (> 8 elixir push), sacrifice it
            if (left_doomed or right_doomed) and report.enemy_count >= 3:
                report.pressure = False
                
        if report.pressure: # Only defend if not sacrificed
            enemy_key = report.top_threat.name.replace("enemy_", "")
        
            # Try ALL counters in order, not just the best one
            from knowledge.counter_matrix import get_counters
            for counter in get_counters(enemy_key):
                if counter not in hand:
                    continue
                
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
                bridge_y = 700
                
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
                # Find the tightest cluster of enemies within spell radius (~200px)
                SPELL_RADIUS = 200
                best_cluster = []
                best_cx, best_cy = 0, 0
                for anchor in enemy_troops:
                    cluster = [t for t in enemy_troops 
                              if abs(t.x - anchor.x) < SPELL_RADIUS 
                              and abs(t.y - anchor.y) < SPELL_RADIUS]
                    if len(cluster) > len(best_cluster):
                        best_cluster = cluster
                        best_cx = sum(t.x for t in cluster) / len(cluster)
                        best_cy = sum(t.y for t in cluster) / len(cluster)
                
                if len(best_cluster) >= 2:
                    value, targets = evaluate_spell_value(card, best_cluster)
                    if value >= spell_cost:
                        cx, cy = int(best_cx), int(best_cy)
                        _last_action_time = current_time
                        return ActionCommand(
                            Action.PLAY_CARD, card_to_play=card,
                            target_x=cx, target_y=cy
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
                # Push OPPOSITE lane from where enemy is strongest
                opposite = get_opposite_lane(report.hot_lane)
                push_x = 180 if opposite == "left" else 540
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
        if report.hot_lane != doomed_lane:
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
    # PRIORITY 6.2: PREDICTIVE SPELL
    # If we have a win condition attacking and enemy has swarms in cycle
    # ═══════════════════════════════════════════════════════
    allied_win_con = None
    for troop in game_state.troops:
        if troop.team == "ally":
            key = troop.name.replace("ally_", "")
            if key in WIN_CONDITIONS and troop.y < 700:
                allied_win_con = troop
                break
                
    if allied_win_con and current_elixir >= 2:
        swarm_in_cycle = any(c in SWARMS and memory.is_in_cycle(c) for c in memory.deck)
        if swarm_in_cycle:
            for c in hand:
                if c in {"log", "zap", "snowball", "arrows"} and c != reserved_card:
                    afford, _ = can_afford(c, current_elixir)
                    if afford:
                        _last_action_time = current_time
                        tx = int(allied_win_con.x)
                        ty = max(250, int(allied_win_con.y - 150))
                        return ActionCommand(
                            Action.PLAY_CARD, card_to_play=c,
                            target_x=tx, target_y=ty
                        ), f"🔮 PREDICTION: {c} supporting {allied_win_con.name.replace('ally_', '')}"

    # ═══════════════════════════════════════════════════════
    # PRIORITY 6.5: SUPPORT EXISTING PUSH
    # If we have allied troops crossing the bridge, stack support behind them
    # ═══════════════════════════════════════════════════════
    allied_tank = placement._find_allied_tank(game_state)
    if allied_tank and allied_tank.y < 700 and current_elixir >= 4:  # Tank is past bridge
        for c in hand:
            if c in SUPPORT and c != reserved_card:
                afford, _ = can_afford(c, current_elixir)
                if afford:
                    tx = int(allied_tank.x)
                    ty = int(allied_tank.y + 120)
                    _last_action_time = current_time
                    return ActionCommand(
                        Action.PLAY_CARD, card_to_play=c,
                        target_x=tx, target_y=ty
                    ), f"🏗️ SUPPORT: {c} behind {allied_tank.name.replace('ally_', '')}"
    
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
        
        # No tank? Play cheapest card (ignore reservation at 10 elixir to prevent leak)
        cheapest_available = None
        cheap_cost = 99
        for c in hand:
            if c != reserved_card or current_elixir >= 10.0:
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

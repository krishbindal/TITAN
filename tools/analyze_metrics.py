"""
Offline Analysis Tool for TITAN Match Data.
Parses logs from logs/analytics/ and computes aggregate metrics.
"""

import os
import json
import glob
from collections import defaultdict
from configs.settings import ANALYTICS_DIR


def analyze_matches():
    match_files = glob.glob(os.path.join(ANALYTICS_DIR, "match_*.json"))
    
    if not match_files:
        print("No match logs found.")
        return

    total_matches = len(match_files)
    wins = 0
    total_duration = 0
    total_cards_played = 0

    for fpath in match_files:
        with open(fpath, "r") as f:
            data = json.load(f)
            if data.get("won"):
                wins += 1
            total_duration += data.get("duration_seconds", 0)
            total_cards_played += data.get("total_cards_played", 0)

    win_rate = (wins / total_matches) * 100
    avg_duration = total_duration / total_matches
    avg_cards = total_cards_played / total_matches

    print("="*40)
    print("        TITAN MATCH METRICS")
    print("="*40)
    print(f"Total Matches Played: {total_matches}")
    print(f"Win Rate:             {win_rate:.1f}% ({wins} wins)")
    print(f"Average Duration:     {avg_duration:.1f} seconds")
    print(f"Average Cards Played: {avg_cards:.1f} per match")
    print("="*40)


def analyze_decisions():
    decision_files = glob.glob(os.path.join(ANALYTICS_DIR, "decisions_*.jsonl"))
    
    if not decision_files:
        return

    total_decisions = 0
    wait_actions = 0
    play_actions = 0
    elixir_leaks = 0

    for fpath in decision_files:
        with open(fpath, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                data = json.loads(line)
                total_decisions += 1
                
                action = data.get("chosen_action", "")
                if action == "WAIT":
                    wait_actions += 1
                elif action.startswith("PLAY"):
                    play_actions += 1
                    
                if data.get("my_elixir", 0) >= 9.9 and action == "WAIT":
                    elixir_leaks += 1

    print("\n" + "="*40)
    print("      TITAN DECISION METRICS")
    print("="*40)
    print(f"Meaningful Decisions Logged: {total_decisions}")
    print(f"Total Play Actions:          {play_actions}")
    print(f"Frames Leaking Elixir:       {elixir_leaks}")
    print("="*40)


if __name__ == "__main__":
    analyze_matches()
    analyze_decisions()

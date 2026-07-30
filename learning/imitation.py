import os
import json
import glob

def process_session_logs(log_dir="data/gameplay_logs"):
    """
    Parses all session_*.jsonl files and infers (State, Action) pairs.
    """
    dataset = []
    
    if not os.path.exists(log_dir):
        print(f"Directory {log_dir} does not exist.")
        return dataset
        
    log_files = glob.glob(os.path.join(log_dir, "session_*.jsonl"))
    print(f"Found {len(log_files)} session logs.")
    
    for log_file in log_files:
        print(f"Processing {log_file}...")
        
        # Load all frames
        frames = []
        with open(log_file, "r") as f:
            for line in f:
                if line.strip():
                    frames.append(json.loads(line))
                    
        # Infer actions
        for i in range(len(frames) - 1):
            curr_frame = frames[i]
            next_frame = frames[i+1]
            
            curr_elixir = curr_frame.get("elixir", 0.0)
            next_elixir = next_frame.get("elixir", 0.0)
            
            # If elixir drops by more than 1.0, user played a card!
            if next_elixir < curr_elixir - 1.0:
                curr_hand = curr_frame.get("hand", [])
                next_hand = next_frame.get("hand", [])
                
                # Find the card that disappeared
                played_card = None
                for c in curr_hand:
                    if c not in next_hand:
                        played_card = c
                        break
                        
                # If YOLO detection jittered, just pick the first card in hand as a fallback
                if not played_card and curr_hand:
                    played_card = curr_hand[0]
                    
                # Look ahead to find where the card was placed (X, Y)
                # We check the next 5 frames for a new ally troop
                target_x, target_y = 360, 800 # Default to middle of our side
                found_target = False
                
                curr_ally_troops = [t for t in curr_frame.get("troops", []) if t.get("is_ally")]
                curr_ally_count = len(curr_ally_troops)
                
                for lookahead in range(1, 6):
                    if i + lookahead < len(frames):
                        future_frame = frames[i + lookahead]
                        future_ally_troops = [t for t in future_frame.get("troops", []) if t.get("is_ally")]
                        
                        # If a new ally troop appeared!
                        if len(future_ally_troops) > curr_ally_count:
                            # Heuristic: The newly deployed troop is likely the one closest to our side
                            # or just pick the first one not in the previous list.
                            for ft in future_ally_troops:
                                # Simple check: is this troop at roughly the same position as an old one?
                                is_new = True
                                for ct in curr_ally_troops:
                                    if abs(ft["x"] - ct["x"]) < 50 and abs(ft["y"] - ct["y"]) < 50:
                                        is_new = False
                                        break
                                if is_new:
                                    target_x = ft["x"]
                                    target_y = ft["y"]
                                    found_target = True
                                    break
                            
                            if found_target:
                                break
                                
                action = {
                    "played_card": played_card,
                    "target_x": target_x,
                    "target_y": target_y,
                    "cost": curr_elixir - next_elixir
                }
                
                experience = {
                    "state": curr_frame,
                    "action": action
                }
                
                dataset.append(experience)
                print(f"  -> Inferred Action: Played {played_card} at ({target_x}, {target_y}) for {action['cost']:.1f} Elixir")
                
    # Save dataset
    dataset_file = os.path.join("data", "imitation_dataset.json")
    with open(dataset_file, "w") as f:
        json.dump(dataset, f, indent=2)
        
    print(f"Extraction complete! Generated {len(dataset)} training samples.")
    print(f"Saved dataset to {dataset_file}")
    
    return dataset

if __name__ == "__main__":
    process_session_logs()

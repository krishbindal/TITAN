import json
import yaml
import os
import sys
import hashlib

# Add project root to path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from knowledge.card import CardModel

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "knowledge")
OLD_CARDS_FILE = os.path.join(KNOWLEDGE_DIR, "cards.json")
AI_TAGS_FILE = os.path.join(KNOWLEDGE_DIR, "ai_tags.yaml")
OUTPUT_FILE = os.path.join(KNOWLEDGE_DIR, "titan_cards.json")


def load_raw_data():
    """
    In a real production environment, this would fetch from a community RoyaleAPI dump:
    response = requests.get("https://raw.githubusercontent.com/royaleapi/cr-api-data/master/cards.json")
    return response.json()
    
    For migration, we use the local cards.json.
    """
    with open(OLD_CARDS_FILE, "r") as f:
        return json.load(f)


def load_ai_tags():
    with open(AI_TAGS_FILE, "r") as f:
        return yaml.safe_load(f) or {}


def build_database():
    raw_cards = load_raw_data()
    ai_tags = load_ai_tags()
    
    titan_cards = {}
    
    for card_key, data in raw_cards.items():
        # Fallback tags if missing
        tags = ai_tags.get(card_key, {
            "roles": [],
            "strengths": [],
            "weaknesses": [],
            "kiting_priority": 0
        })
        
        # Calculate derived stats
        damage = data.get("damage", 0)
        hit_speed = data.get("hit_speed", 1.0)
        dps = round(damage / hit_speed) if hit_speed > 0 else 0
        
        # Map target
        raw_target = data.get("target", "ground")
        target_type = "any" if raw_target == "any" else ("air_ground" if raw_target == "air_ground" else raw_target)
        targets_air = raw_target in ["air_ground", "air", "any"]
        targets_ground = raw_target in ["ground", "air_ground", "building", "any"]
        
        speed_numeric = data.get("speed", 60)
        if speed_numeric >= 120:
            speed_class = "very_fast"
        elif speed_numeric >= 90:
            speed_class = "fast"
        elif speed_numeric >= 60:
            speed_class = "medium"
        else:
            speed_class = "slow"
            
        # Build Pydantic model dictionary
        card_dict = {
            "metadata": {
                "id": int(hashlib.md5(card_key.encode('utf-8')).hexdigest()[:8], 16),  # Deterministic ID
                "name": data.get("name", card_key),
                "rarity": "common",  # Placeholder
                "cost": data.get("cost", 0),
                "type": data.get("type", "troop"),
                "arena": 1,
                "is_evolution": False,
                "is_champion": False
            },
            "combat": {
                "hp": data.get("hp", 0),
                "damage": damage,
                "dps": dps,
                "hit_speed": hit_speed,
                "range": data.get("range", 1.0) or 1.0,
                "speed_numeric": speed_numeric,
                "speed_class": speed_class,
                "target_type": target_type,
                "targets_air": targets_air,
                "targets_ground": targets_ground,
                "splash_radius": data.get("radius", 0.0) or 0.0,
                "projectile_speed": None,
                "deploy_time": data.get("deploy_time", 1.0),
                "count": data.get("count", 1)
            },
            "mechanics": {
                "shield_hp": 0,
                "death_damage": 0,
                "charge_damage": 0,
                "stun_duration": 0.0,
                "knockback": False,
                "jumps_river": False
            },
            "ai_tags": tags
        }
        
        # Validate via Pydantic
        model = CardModel(**card_dict)
        titan_cards[card_key] = model.model_dump()
        print(f"Validated: {card_key}")

    # Write output
    with open(OUTPUT_FILE, "w") as f:
        json.dump(titan_cards, f, indent=4)
        
    print(f"Successfully generated {OUTPUT_FILE} with {len(titan_cards)} cards.")

if __name__ == "__main__":
    build_database()

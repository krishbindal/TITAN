from state_builder.game_state import GameState
from state_builder.troop import Troop


class StateBuilder:

    def build(self, tracks, ui_state=None):

        state = GameState()

        # Initialize a 4-slot hand with generic names
        hand_slots = ["unknown_0", "unknown_1", "unknown_2", "unknown_3"]

        for track in tracks:
            # Phase 4: Track objects no longer have a .detection attribute.
            # They store their own state (name, position, confidence).
            x, y = track.latest_position()

            # If it's a card in our hand at the bottom of the screen
            if track.name.startswith("card_"):
                # Clean up name using CardDatabase normalization
                from knowledge.card_database import CardDatabase
                clean_name = CardDatabase.normalize(track.name)

                # Determine slot index (0 to 3) based on X coordinate (assuming screen width 720)
                if x < 290:
                    idx = 0
                elif x < 430:
                    idx = 1
                elif x < 570:
                    idx = 2
                else:
                    idx = 3
                
                hand_slots[idx] = clean_name
                continue

            # Otherwise, it's a troop on the battlefield
            team = "ally" if track.name.startswith("ally_") else "enemy"

            troop = Troop(
                track_id=track.id,
                name=track.name,
                x=x,
                y=y,
                team=team,
                confidence=track.confidence,
            )

            state.add_troop(troop)

        # Add the 4 slots to the game state hand
        for card in hand_slots:
            state.add_card_to_hand(card)

        return state

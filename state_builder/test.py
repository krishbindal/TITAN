from state_builder.game_state import GameState
from state_builder.troop import Troop

game = GameState()

# Use the correct attribute names
game.hand = ["hog_rider", "fireball", "knight", "log"]

# Use Troop objects instead of raw strings
game.troops.append(Troop("enemy_wizard", 300, 500, "enemy"))
game.troops.append(Troop("enemy_mini_pekka", 400, 600, "enemy"))

print(game)

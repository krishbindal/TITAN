class UIState:

    def __init__(self):

        self.time = 180

        self.player_elixir = None

        self.enemy_elixir = None

        self.player_hand = []

        self.selected_card = None

        self.enemy_left_tower_hp = None

        self.enemy_right_tower_hp = None

    def __str__(self):

        return f"""
Time : {self.time}

Player Elixir : {self.player_elixir}

Selected Card : {self.selected_card}
"""

"""Классы игроков"""

from itertools import cycle
from random import shuffle
from classes import Game


class Player:
    def __init__(self, name, game):
        self.name = name
        self.score = max(5 * round(game.size ** 2, -1), 100)
        self.penalty = 11

    def make_step(self, game, sides):
        pass

    def take_penalty(self, penalty=11):
        self.score = max(0, self.score - penalty)


class Human(Player):
    def __init__(self, name: str, game: Game):
        super().__init__(name, game)
        self.step = None
        self.penalty = 10

    def make_step(self, game, sides):
        if self.step is not None and game[self.step].player is None:
            result = game.make_step(*self.step, side=sides[self.name])
            self.step = None
            self.take_penalty(self.penalty)
            return result

    def set_step(self, step):
        self.step = step


class AI(Player):
    def __init__(self, name: str, game: Game):
        super().__init__(name, game)
        free_cells = [*game.cells.keys()]
        shuffle(free_cells)
        self.cycle = cycle(free_cells)

    def make_step(self, game, sides):
        for coords in self.cycle:
            if game[coords].player is None:
                self.take_penalty()
                return game.make_step(*coords, side=sides[self.name])


def create_player(name, spinbox_value, game):
    if spinbox_value == 'AI':
        return AI(name, game)
    else:
        return Human(name, game)

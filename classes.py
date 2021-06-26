"""Основные классы"""

from math import ceil, floor
from itertools import product
from copy import deepcopy


class Cell:
    def __init__(self):
        self.player = None
        self._connected = set()
        self._neighbours = set()

    def update_side(self, side):
        if side in self._connected:
            return
        self._connected.add(side)
        for neib in self._neighbours:
            neib.update_side(side)

    def sides_connected(self):
        return '0' in self._connected and '=' in self._connected

    def add_link(self, neighbour):
        if len(self._neighbours) > 5:
            raise Exception("Too much neighbours")
        self._neighbours.add(neighbour)
        for side in self._connected:
            neighbour.update_side(side)

    def __str__(self):
        return str(self._connected) + str(self._neighbours)


class Game:
    def __init__(self, size, player1='Player1', player2='Player2'):
        self.size = size
        self.cells = {}

        self.player1 = player1
        self.player2 = player2

        self.winner = None
        self.dx_dy = [(-1, -1), (-1, 0), (0, -1), (0, 1), (1, 0), (1, 1)]

        for i in range(self.size * 2):
            if i < self.size:
                for j in range(i + 1):
                    self[i, j] = Cell()
            else:
                for j in range(2 * self.size - i - 1):
                    self[i, j] = Cell()

    def __getitem__(self, item):
        return self.cells[item]

    def __setitem__(self, key, value):
        self.cells[key] = value

    def make_step(self, x, y, side):
        if self[x, y].player:
            return self

        player = self.player1
        new_game = deepcopy(self)
        new_game.player1, new_game.player2 = self.player2, self.player1

        cell = new_game[x, y]
        cell.player = player
        if side == '\\':
            if x < self.size and x == y:
                cell.update_side('=')
            if x >= self.size - 1 and y == 0:
                cell.update_side('0')
        if side == '/':
            if x < self.size and y == 0:
                cell.update_side('0')
            if x >= self.size - 1 and y == 2 * self.size - 2 - x:
                cell.update_side('=')
        for neighbour in new_game.get_neighbours(x, y):
            if neighbour.player == player:
                cell.add_link(neighbour)
                neighbour.add_link(cell)
        if cell.sides_connected() and not new_game.winner:
            new_game.winner = player

        return new_game

    def get_neighbours(self, x, y):
        for dx, dy in self.dx_dy:
            if (0 <= x + dx < 2 * self.size and
                    ((0 <= y + dy <= x + dx < self.size) or
                     (0 <= y + dy < (2 * self.size - x - dx - 1) and dx + x >=
                      self.size))):
                yield self[(x + dx, y + dy)]


def get_valid_rounded_coordinates(x, y, game):
    for i, j in product({floor(x), ceil(x)}, {floor(y), ceil(y)}):
        if (0 <= i < 2 * game.size and
                ((0 <= j <= i < game.size) or
                 (0 <= j < (2 * game.size - i - 1) and i >= game.size))):
            yield i, j

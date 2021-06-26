from itertools import zip_longest
from unittest import TestCase
from classes import Game, Cell, get_valid_rounded_coordinates


def parse_game_field(field: str):
    lines = field.split('\n')
    game = Game(len(lines) - 1, '1', '2')
    first, second = enumerate_players_steps(field)
    for step1, step2 in zip_longest(first, second):
        game = game.make_step(*step1)
        if step2:
            game = game.make_step(*step2)
    return game


def enumerate_players_steps(field: str):
    first = []
    second = []
    for i, line in enumerate(field.split('\n')):
        for j, player in enumerate(line.split()):
            if player == '1':
                first.append((i, j))
            elif player == '2':
                second.append((i, j))
    return first, second


class CellTest(TestCase):
    def test_single_cel_work_with_sides(self):
        cell = Cell()
        self.assertFalse(cell.sides_connected())
        cell.update_side('0')
        self.assertFalse(cell.sides_connected())
        cell.update_side('=')
        cell.update_side('0')
        self.assertTrue(cell.sides_connected())
        cell.update_side('=')
        self.assertTrue(cell.sides_connected())


class GameTests(TestCase):
    def test_init(self):
        field = Game(5)
        self.assertTrue(field.size, 5)
        self.assertTrue(field.winner is None)

    def test_get_neighbours_1(self):
        game = Game(1)
        self.assertSetEqual(set(game.get_neighbours(0, 0)), set())

    def test_get_neighbours_2(self):
        game = Game(2)
        neighbours = set(game.get_neighbours(0, 0))
        self.assertEqual(len(neighbours), 2)

    def test_get_neighbours_3(self):
        game = Game(4)
        neighbours = set(game.get_neighbours(0, 0))
        self.assertEqual(len(neighbours), 2)
        neighbours = set(game.get_neighbours(2, 1))
        self.assertEqual(len(neighbours), 6)

    def test_make_step(self):
        game = Game(3)
        game = game.make_step(0, 0, '/')
        self.assertFalse(game[0, 0].sides_connected())
        game = game.make_step(2, 0, '\\')
        self.assertFalse(game[0, 0].sides_connected())
        self.assertFalse(game[2, 0].sides_connected())
        game = game.make_step(2, 2, '/')
        self.assertFalse(game[0, 0].sides_connected())
        self.assertFalse(game[2, 0].sides_connected())
        self.assertFalse(game[2, 2].sides_connected())
        self.assertFalse(game[1, 0].sides_connected())
        game = game.make_step(2, 2, '\\')
        game = game.make_step(1, 1, '\\')
        self.assertFalse(game[1, 1].sides_connected())
        game = game.make_step(1, 0, '/')
        self.assertFalse(game[0, 0].sides_connected())
        self.assertFalse(game[2, 2].sides_connected())
        self.assertFalse(game[1, 0].sides_connected())
        game = game.make_step(2, 1, '\\')
        self.assertTrue(game[2, 0].sides_connected())
        self.assertTrue(game[1, 1].sides_connected())
        self.assertTrue(game[2, 1].sides_connected())

    def test_coordinate_validation_1(self, ):
        game = Game(1)
        coords = [*get_valid_rounded_coordinates(0.5, 0, game)]
        self.assertSequenceEqual(coords, [(0, 0)])
        coords = [*get_valid_rounded_coordinates(-5, -1, game)]
        self.assertSequenceEqual(coords, [])

    def test_coordinate_validation_2(self):
        g = Game(5)
        coords = [*get_valid_rounded_coordinates(2.5, 1.1, g)]
        self.assertSequenceEqual(coords, [(2, 1), (2, 2), (3, 1), (3, 2)])
        coords = [*get_valid_rounded_coordinates(-5, -5, g)]
        self.assertSequenceEqual(coords, [])
        coords = set(get_valid_rounded_coordinates(-0.5, 0.1, g))
        self.assertSetEqual(coords, {(0, 0)})

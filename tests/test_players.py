from unittest import TestCase
from classes import Game
from players import Player, Human, AI, create_player


class PlayersTest(TestCase):
    def setUp(self) -> None:
        self.name1 = 'Biba'
        self.name2 = 'Boba'
        self.game = Game(10, self.name1, self.name2)

    def test_base_player(self):
        player = Player(self.name1, self.game)
        self.assertFalse(player.make_step(self.game, {self.name1: '/'}))
        count = 0
        for cell in self.game.cells.values():
            if cell.player is not None:
                count += 1

        self.assertEqual(count, 0)

    def test_Human(self):
        human = Human(self.name1, self.game)
        self.assertFalse(human.make_step(self.game, {self.name1: '/'}))
        human.step = (0, 0)
        self.game = human.make_step(self.game, {self.name1: '/'})
        self.assertTrue(self.game)
        self.assertFalse(human.make_step(self.game, {self.name1: '/'}))

        self.assertEqual(self.game[0, 0].player, self.name1)

        human.step = (0, 0)
        self.assertFalse(human.make_step(self.game, {self.name1: '/'}))

        self.game = self.game.make_step(1, 1, '/')

        self.assertFalse(human.make_step(self.game, {self.name1: '/'}))
        human.step = (1, 1)
        self.assertFalse(human.make_step(self.game, {self.name1: '/'}))

        human.step = (2, 2)

        self.game = human.make_step(self.game, {self.name1: '/'})
        self.assertTrue(self.game)
        self.assertFalse(human.make_step(self.game, {self.name1: '/'}))

    def test_AI(self):
        ai = AI(self.name1, self.game)
        self.game = ai.make_step(self.game, {self.name1: '/'})
        self.assertTrue(self.game)

        count = 0
        for cell in self.game.cells.values():
            if cell.player is self.name1:
                count += 1

        self.assertEqual(count, 1)

    def test_create_player(self):
        player = create_player('Vupsen', 'Human', self.game)
        self.assertTrue(isinstance(player, Human))
        player = create_player('Pupsen', AI.__name__, self.game)
        self.assertTrue(isinstance(player, AI))

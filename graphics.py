"""Классы для рисования"""

import argparse
from classes import Game, get_valid_rounded_coordinates
from players import Human, AI, create_player
from utilites import *
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import (QFrame, QAction, QMessageBox, QDialog,
                             QDialogButtonBox, QLabel, QVBoxLayout,
                             QHBoxLayout, QLineEdit, QSpinBox, QComboBox)
from PyQt5.QtCore import Qt, QPoint, QTimerEvent
from PyQt5.QtGui import QPen, QBrush


def point_to_qt_point(point):
    return QPoint(int(point[0]), int(point[1]))


def get_hex_points(center, radius):
    for x, y in [(0, 1), (sin60, 1 / 2), (sin60, -1 / 2),
                 (0, -1), (-sin60, -1 / 2), (-sin60, 1 / 2)]:
        yield QPoint(int(center[0] + x * radius), int(center[1] + y * radius))


class Gui(QFrame):
    """Игровое поле"""

    def __init__(self, game: Game, players,
                 cell_size: int, parent):
        super().__init__(parent)
        self.game = game
        self.radius = cell_size
        self.distance = self.radius * sin60
        self.shoulder = self.game.size * self.radius * 2 * sin60
        self.center = (self.radius * (sin60 * self.game.size + 1),
                       self.radius / sin60 +
                       self.shoulder * sin60)
        self.setGeometry(0, 0, 2 * int(self.center[0]),
                         2 * int(self.center[1]))
        self.player_to_brush = {
            None: QBrush(),
            players[0].name: QBrush(Qt.blue),
            players[1].name: QBrush(Qt.red)}
        self.players_to_side = {
            players[0].name: '/',
            players[1].name: '\\'
        }
        self.side_to_pen = [QPen(color, 3, Qt.SolidLine) for color in
                            [Qt.blue, Qt.red, Qt.blue, Qt.red]]
        self.blackPen = QPen(Qt.black, 1, Qt.SolidLine)
        self.players = players
        self.index = 0
        self.interval = 50
        self.period = 2000
        self.timer_id = self.startTimer(self.interval)
        self.wait_ticks = 0

    def update_geometry(self, radius):
        self.radius = radius
        self.distance = self.radius * sin60
        self.shoulder = self.game.size * self.radius * 2 * sin60
        self.center = (self.radius * (sin60 * self.game.size + 1),
                       self.radius / sin60 +
                       self.shoulder * sin60)
        self.setGeometry(0, 0, 2 * int(self.center[0]),
                         2 * int(self.center[1]))

    def _draw_cell(self, i, j, painter):
        painter.setPen(self.blackPen)
        painter.setBrush(self.player_to_brush[self.game[i, j].player])
        gui_point = self.get_gui_from_math(i, j)
        painter.drawPolygon(*get_hex_points(gui_point, self.radius))

    def _draw_rhombus(self, painter):
        inner, outer = get_rhombuses(self.center, self.shoulder, self.radius)
        inner = [*map(point_to_qt_point, inner)]
        outer = [*map(point_to_qt_point, outer)]
        for i in range(4):
            painter.setPen(self.blackPen)
            painter.drawLine(outer[i], inner[i])
            painter.setPen(self.side_to_pen[i])
            painter.drawLine(outer[i], outer[(i + 1) % 4])

    def draw_score(self, painter: QtGui.QPainter):
        painter.setFont(QtGui.QFont("Arial", int(self.distance / 2), False))
        painter.setPen(self.blackPen)
        for i in range(2):
            player = self.players[i]
            painter.setBrush(self.player_to_brush[player.name])
            center = (int(self.distance / 2) + 2, self.radius * (0.5 + i))
            painter.drawPolygon(*get_hex_points(center, self.radius / 2))
            x = int(4 + self.distance)
            y = int(self.radius * (i + 0.75))
            message = f'{player.name}: {player.score}'
            painter.drawText(x, y, message)

    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        self._draw_rhombus(painter)
        for i, j in self.game.cells.keys():
            self._draw_cell(i, j, painter)
        self.draw_score(painter)

    def mousePressEvent(self, event: QtGui.QMouseEvent):
        if self.game.winner:
            return
        cell, length = self.get_closest_cell((event.x(), event.y()))
        if length > self.radius:
            return
        current_player = self.players[self.index]
        if not isinstance(current_player, Human):
            return
        self.wait_ticks = 0
        current_player.set_step(cell)
        self.timer_method()

    def get_closest_cell(self, point):
        x, y = self.get_math_from_gui(point[0], point[1])
        result = (-1, -1)
        min_length = 2 * self.radius
        for i, j in get_valid_rounded_coordinates(x, y, self.game):
            center = self.get_gui_from_math(i, j)
            length = distance(point, center)
            if length < min_length:
                min_length = length
                result = i, j
        return result, min_length

    def get_gui_from_math(self, i, j):
        if i < self.game.size:
            x = self.center[0] + (2 * j - i) * self.distance
        else:
            x = self.center[0] + (2 * j - 2 * self.game.size + i + 2) * \
                self.distance
        y = (3 * i + (1 + 1 / sin60) * 2) * self.radius / 2
        return x, y

    def get_math_from_gui(self, x, y):
        i = 2 * (y - (1 + 1 / sin60) * self.radius) / (3 * self.radius)
        if i < self.game.size:
            j = ((x - self.center[0]) / self.distance + i) / 2
        else:
            j = ((x - self.center[0]) / self.distance + (2 * self.game.size - i
                                                         - 1)) / 2
        return i, j

    def timerEvent(self, event: QTimerEvent):
        self.timer_method()

    def timer_method(self):
        self.wait_ticks += 1
        current = self.players[self.index]
        if (isinstance(current, Human) and
                self.wait_ticks * self.interval >= self.period):
            current.take_penalty(self.wait_ticks * self.interval //
                                 self.period)
            self.wait_ticks = (self.wait_ticks * self.interval %
                               self.period)
        modified = current.make_step(self.game, self.players_to_side)
        if modified:
            self.game = modified
            self.index = 1 - self.index
            self.wait_ticks = 0
        if self.game.winner:
            self.killTimer(self.timer_id)
            self.show_game_won_message(current.name, current.score)

        self.repaint()

    def show_game_won_message(self, name, score):
        message = QMessageBox(self)
        message.setWindowTitle('Game won!')
        message.setIcon(QMessageBox.Information)
        message.setText(f"Player {name} won with score {score}")
        message.exec_()


class GameDialog(QDialog):
    def __init__(self, current_size, players, parent=None):
        super().__init__(parent)
        self.setWindowTitle('New Game')
        self.player_data = {}

        self._init_ui(current_size, players)

    def _init_ui(self, size, players):
        self.setFixedSize(370, 200)

        self.layout = QVBoxLayout()

        self.field_size_layout = QHBoxLayout()

        self.label = QLabel('Choose game side size')
        self.spinBox = QSpinBox()
        self.spinBox.setMinimum(1)
        self.spinBox.setMaximum(150)
        self.spinBox.setValue(size)

        self.field_size_layout.addWidget(self.label)
        self.field_size_layout.addWidget(self.spinBox)

        self.layout.addLayout(self.field_size_layout)

        for i in range(2):
            self.layout.addLayout(self.make_player_layout(players[i], i))

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def make_player_layout(self, player, key):
        layout = QHBoxLayout()
        label = QLabel(f'Player{key + 1}')
        text = QLineEdit(player.name, self)
        combo_box = QComboBox()

        combo_box.addItems(['AI', 'Human'])
        index = combo_box.findText(player.__class__.__name__)
        if index >= 0:
            combo_box.setCurrentIndex(index)

        layout.addWidget(label)
        layout.addWidget(text)
        layout.addWidget(combo_box)

        self.player_data[key] = (text, combo_box)

        return layout

    def get_field_size(self):
        return self.spinBox.value()

    def get_player_data(self, key):
        name, ai = self.player_data[key]
        return name.text(), ai.currentText()


class ChangeCellSizeDialog(QDialog):
    def __init__(self, current_cell_size, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Time to choose')
        self.setFixedSize(270, 100)

        self._init_ui(current_cell_size)

    def _init_ui(self, cell_size):
        self.layout = QVBoxLayout()

        self.h_layout = QHBoxLayout()
        self.label = QLabel('Choose cell size')
        self.spinBox = QSpinBox()
        self.spinBox.setMinimum(5)
        self.spinBox.setMaximum(70)
        self.spinBox.setValue(cell_size)

        self.h_layout.addWidget(self.label)
        self.h_layout.addWidget(self.spinBox)

        self.layout.addLayout(self.h_layout)

        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Ok |
                                          QDialogButtonBox.Cancel)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.buttonBox)
        self.setLayout(self.layout)

    def get_cell_size(self):
        return self.spinBox.value()


class Window(QtWidgets.QMainWindow):
    def __init__(self, game, players, cell_size, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nex")
        self.cell_size = cell_size

        self._init_menu()
        self._init_ui(game, players)

        self.was_maximized = self.isMaximized()
        self.showFullScreen()

    def _init_menu(self):
        menu = self.menuBar()

        game = menu.addMenu('&Game')
        new_game_action = QAction('&New Game', self)
        new_game_action.setShortcut('Ctrl+N')
        new_game_action.triggered.connect(self.update_field)
        game.addAction(new_game_action)

        close = QAction('&Close', self)
        close.setShortcut('Esc')
        close.triggered.connect(self.close_method)
        game.addAction(close)

        parameters = menu.addMenu('&Parameters')
        change_cell_size = QAction('&Cell size', self)
        change_cell_size.triggered.connect(self.update_field_geometry)
        parameters.addAction(change_cell_size)

    def close_method(self):
        exit_confirm = QMessageBox(self)
        exit_confirm.setWindowTitle('Exit')
        exit_confirm.setIcon(QMessageBox.Question)
        exit_confirm.setText('Are you sure you want to exit?')
        exit_confirm.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        exit_confirm.setDefaultButton(QMessageBox.Cancel)
        exit_confirm.setEscapeButton(QMessageBox.Cancel)
        exit_confirm.exec_()
        if exit_confirm.result() == QMessageBox.Ok:
            self.close()

    def _init_ui(self, game, players):
        self.scroller = QtWidgets.QScrollArea(self)
        self.scroller.setFrameStyle(QFrame.NoFrame)
        self.gui_game = Gui(game, players, self.cell_size, self.scroller)
        self.gui_game.setFrameStyle(QFrame.Box)

        self.scroller.setWidget(self.gui_game)

        self.setCentralWidget(self.scroller)

    def update_field(self):
        dialog = GameDialog(self.gui_game.game.size,
                            self.gui_game.players, self)
        dialog.exec_()

        result = dialog.result()

        if result:
            size = dialog.get_field_size()
            name1, type1 = dialog.get_player_data(0)
            name2, type2 = dialog.get_player_data(1)

            game = Game(size, name1, name2)
            player1 = create_player(name1, type1, game)
            player2 = create_player(name2, type2, game)
            self._init_ui(game, (player1, player2))

    def update_field_geometry(self):
        dialog = ChangeCellSizeDialog(self.cell_size, self)
        dialog.exec_()
        result = dialog.result()

        if result:
            self.cell_size = dialog.get_cell_size()
            self.gui_game.update_geometry(self.cell_size)


def run(game, players, cell_size):
    app = QtWidgets.QApplication([])
    wnd = Window(game, players, cell_size)
    wnd.show()
    return app.exec_()


def main():
    parser = argparse.ArgumentParser(
        usage='%(prog)s [OPTIONS]',
        description='Nex Game')
    parser.add_argument('--field-size', '-n', type=int, default=11,
                        help='Field size')
    parser.add_argument(f'--first', '-f', type=str, help='name', default="One")
    parser.add_argument(f'--second', '-s', type=str, help='name',
                        default="Two")
    parser.add_argument(f'--first-role', type=str, help='role mode',
                        default=Human,
                        choices=['Human', 'AI'])
    parser.add_argument(f'--second-role', type=str, help='role mode',
                        default=AI,
                        choices=['Human', 'AI'])
    parser.add_argument('--cell-size', '-r', type=int, default=25,
                        help='Cell side size (from 5 to 50)')
    args = parser.parse_args()
    game = Game(args.field_size, args.first, args.second)

    player1 = create_player(args.first, args.first_role, game)
    player2 = create_player(args.second, args.second_role, game)

    run(game, (player1, player2), args.cell_size)


if __name__ == '__main__':
    main()

import argparse
import os
import sys
import math
from Game import Game


ERROR_QT_VERSION = 5

MESSAGE_FORMAT = 'Player {} won!\nAnd their score is {}'

try:
    from PyQt5 import QtGui, QtWidgets
    from PyQt5.QtWidgets import (QFrame, QDialog, QVBoxLayout, QHBoxLayout,
                                 QDialogButtonBox, QAction, QLabel, QLineEdit,
                                 QSpinBox, QMessageBox)
    from PyQt5.QtCore import Qt, QPoint, QTimerEvent
    from PyQt5.QtGui import QPen, QBrush, QColor, QIcon
except Exception as e:
    print(f'PyQt5 not found: "{e}".', file=sys.stderr)
    sys.exit(ERROR_QT_VERSION)


def point_to_qt(point):
    return QPoint(int(point[0]), int(point[1]))


sin60 = math.sin(math.radians(60))
HEX_POINTS = [(0, 1), (sin60, 1 / 2),
              (sin60, -1 / 2),
              (0, -1), (-sin60, -1 / 2),
              (-sin60, 1 / 2)]
COLORS = [QColor(118, 60, 40), QColor(216, 199, 25), QColor(132, 148, 206)]


def get_hex_points(center, radius):
    for x, y in HEX_POINTS:
        yield QPoint(int(center[0] + x * radius), int(center[1] + y * radius))


class GuiGame(QFrame):
    """Компонент «игровое поле»"""
    def __init__(self, game: Game, players,
                 cell_size: int, parent):
        super().__init__(parent)
        self.game = game
        self._init_geometry(cell_size)
        self.player_to_brush = {
            None: QBrush(),
            players[0].name: QBrush(Qt.cyan),
            players[1].name: QBrush(QColor(255, 182, 193))}
        self.side_to_pen = [QPen(color, 3, Qt.SolidLine) for color in COLORS]
        self.blackPen2Solid = QPen(Qt.black, 1, Qt.SolidLine)

        self.players = players
        self.index = 0

        self._init_timer()
        self.wait_ticks = 0

        self.undo_stack = []
        self.redo_stack = []

    def _init_geometry(self, radius):
        self.radius = radius
        self.distance = self.radius * sin60
        self.shoulder = self.game.size * self.radius
        self.center = (self.radius * (sin60 * self.game.size + 1),
                       self.radius / sin60 + self.shoulder)
        self.setGeometry(0, 0, 2 * int(self.center[0]),
                         int(self.radius * (2 + 1.5 * self.game.size)))

    def _init_timer(self):
        self.interval = 50
        self.penalty_period = 2000
        self.timer_id = self.startTimer(self.interval)

    def update_geometry(self, radius):
        self._init_geometry(radius)

    def _draw_cell(self, i, j, painter):
        painter.setPen(self.blackPen2Solid)
        painter.setBrush(self.player_to_brush[self.game[i, j].player])
        gui_point = self.get_gui_from_math(i, j)
        painter.drawPolygon(*get_hex_points(gui_point, self.radius))

    def _draw_triangle(self, painter):
        inner, outer = get_triangles(self.center, self.shoulder, self.radius)
        inner = [*map(point_to_qt, inner)]
        outer = [*map(point_to_qt, outer)]
        for i in range(3):
            painter.setPen(self.blackPen2Solid)
            painter.drawLine(outer[i], inner[i])
            painter.setPen(self.side_to_pen[i])
            painter.drawLine(outer[i], outer[(i + 1) % 3])

    def draw_score(self, painter: QtGui.QPainter):
        painter.setFont(QtGui.QFont("Times New Roman", int(self.distance / 2),
                                    False))
        painter.setPen(self.blackPen2Solid)
        for i in range(2):
            player = self.players[i]
            painter.setBrush(self.player_to_brush[player.name])
            center = (self.distance // 2 + 2, self.radius * (1/2 + i))
            painter.drawPolygon(*get_hex_points(center, self.radius / 2))
            x = int(4 + self.distance)
            y = int(self.radius * (i + 0.75))
            message = f'{player.name}: {player.score}'
            painter.drawText(x, y, message)

    def paintEvent(self, event: QtGui.QPaintEvent):
        painter = QtGui.QPainter(self)
        self._draw_triangle(painter)
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
        x = self.center[0] + (2 * j - i) * self.distance
        y = (3 * i + (1 + 1 / sin60) * 2) * self.radius / 2
        return x, y

    def get_math_from_gui(self, x, y):
        i = 2 * (y - (1 + 1 / sin60) * self.radius) / (3 * self.radius)
        j = ((x - self.center[0]) / self.distance + i) / 2
        return i, j

    def timerEvent(self, event: QTimerEvent) -> None:
        self.timer_method()

    def timer_method(self):
        self.wait_ticks += 1
        current = self.players[self.index]
        if (isinstance(current, Human) and
                self.wait_ticks * self.interval >= self.penalty_period):
            current.take_penalty(self.wait_ticks * self.interval //
                                 self.penalty_period)
            self.wait_ticks = (self.wait_ticks * self.interval %
                               self.penalty_period)
        modified = current.make_step(self.game)
        if modified:
            self.undo_stack.append(self.game)
            self.game = modified
            self.redo_stack = []
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
        message.setText(MESSAGE_FORMAT.format(name, score))
        message.exec_()

    def undo(self):
        restart_timer = self.game.winner is not None
        self.shift_stacks(self.undo_stack, self.redo_stack, -1)
        if restart_timer:
            self._init_timer()

    def redo(self):
        self.shift_stacks(self.redo_stack, self.undo_stack, 1)
        if self.game.winner:
            self.killTimer(self.timer_id)

    def shift_stacks(self, from_stack: list, to_stack: list, coefficient: int):
        if len(from_stack) in [0, 1]:
            return

        to_stack.append(self.game)
        to_stack.append(from_stack.pop())
        self.game = from_stack.pop()

        undone_player: Player = self.players[1 - self.index]
        undone_player.take_penalty(coefficient * undone_player.penalty)


class YWindow(QtWidgets.QMainWindow):
    """Главное окно приложения"""
    def __init__(self, game, players, cell_size, parent=None):
        super().__init__(parent)
        self.setWindowIcon(QIcon(os.path.join('Source', 'wind_icon.png')))
        self.setWindowTitle("Y")
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

        undo = QAction('&Undo', self)
        undo.setShortcut('Ctrl+Z')
        undo.triggered.connect(self.undo)
        game.addAction(undo)

        redo = QAction('&Redo', self)
        redo.setShortcut('Ctrl+Y')
        redo.triggered.connect(self.redo)
        game.addAction(redo)

        close = QAction('&Close', self)
        close.setShortcut('Esc')
        close.triggered.connect(self.close_method)
        game.addAction(close)

        parameters = menu.addMenu('&Parameters')
        change_cell_size = QAction('&Cell size', self)
        change_cell_size.triggered.connect(self.update_field_geometry)
        parameters.addAction(change_cell_size)

        full_screen = QAction('&Full screen', self)
        full_screen.setShortcut('F')
        full_screen.triggered.connect(self.full_screen_method)
        parameters.addAction(full_screen)

    def close_method(self):
        exit_confirm = QMessageBox(self)
        exit_confirm.setWindowTitle('Exit confirm')
        exit_confirm.setIcon(QMessageBox.Question)
        exit_confirm.setText('Are you sure you want to exit Y?')
        exit_confirm.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        exit_confirm.setDefaultButton(QMessageBox.Cancel)
        exit_confirm.setEscapeButton(QMessageBox.Cancel)
        exit_confirm.exec_()
        if exit_confirm.result() == QMessageBox.Ok:
            self.close()

    def full_screen_method(self):
        if self.isFullScreen():
            if self.was_maximized:
                self.showMaximized()
            else:
                self.showNormal()
        else:
            self.was_maximized = self.isMaximized()
            self.showFullScreen()

    def undo(self):
        self.gui_game.undo()

    def redo(self):
        self.gui_game.redo()

    def _init_ui(self, game, players):
        # Main widget init

        self.scroller = QtWidgets.QScrollArea(self)
        self.scroller.setFrameStyle(QFrame.NoFrame)
        self.gui_game = GuiGame(game, players, self.cell_size, self.scroller)
        self.gui_game.setFrameStyle(QFrame.Box)

        self.scroller.setWidget(self.gui_game)

        self.setCentralWidget(self.scroller)

    def update_field(self):
        dialog = NewGameDialog(self.gui_game.game.size,
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
    """Запуск логики «Y»"""
    app = QtWidgets.QApplication([])

    wnd = YWindow(game, players, cell_size)

    wnd.show()

    return app.exec_()


def main():
    parser = argparse.ArgumentParser(usage='%(prog)s [OPTIONS]')
    parser.add_argument('--field-size', type=ranged_size(1, 150), default=14,
                        help='Field side size')
    order = ['first', 'second']
    names = ['One-One', 'Two']
    types = [Human, DumbAI]
    for i in range(2):
        parser.add_argument(f'--{order[i]}', type=str, help='name',
                            default=names[i])
        parser.add_argument(f'--{order[i]}-role', type=str, help='role mode',
                            default=types[i].__name__,
                            choices=[*map(name_of, inheritors(Player))])
    parser.add_argument('--cell-size', type=ranged_size(5, 70), default=35,
                        help='Cell side size (from 5 to 70)')
    args = parser.parse_args()

    game = Game(args.field_size, args.first, args.second)

    player1 = create_player(args.first, args.first_role, game)
    player2 = create_player(args.second, args.second_role, game)

    run(game, (player1, player2), args.cell_size)


if __name__ == '__main__':
    main()

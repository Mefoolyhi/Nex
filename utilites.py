"""Вспомогательные методы"""
sin60 = 3 ** 0.5 / 2


def distance(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return (dx * dx + dy * dy) ** 0.5


def get_rhombus(center, shoulder, radius):
    up = (center[0], center[1] - shoulder * sin60)
    left = (center[0] - shoulder / 2, center[1] - radius / 2)
    right = (center[0] + shoulder / 2, center[1] - radius / 2)
    down = (center[0], center[1] + shoulder * sin60 - radius)
    return up, left, down, right


def get_rhombuses(center, shoulder, radius):
    inner = get_rhombus(center, shoulder, radius)
    outer = get_rhombus(center, shoulder + radius, radius)
    return inner, outer

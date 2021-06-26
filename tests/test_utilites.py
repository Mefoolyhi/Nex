from unittest import TestCase
from utilites import distance, get_rhombus, get_rhombuses


class UtilitesTest(TestCase):
    def test_distance(self):
        p1 = (0, 0)
        p2 = (3, 4)
        p3 = (4, 3)
        self.assertAlmostEqual(5, distance(p1, p2), delta=1e-5)
        self.assertAlmostEqual(5, distance(p1, p3), delta=1e-5)

    def test_get_rhombus(self):
        center = (0, 0)
        shoulder = 5
        radius = 1
        rhombus = get_rhombus(center, shoulder, radius)
        self.assertEqual(len(rhombus), 4)
        up, left, down, right = rhombus
        self.assertAlmostEqual(distance(up, left), distance(right, up),
                               delta=1e-4)
        self.assertAlmostEqual(distance(down, left), distance(right, down),
                               delta=1e-4)
        center_x = (up[0] + left[0] + right[0] + down[0]) / 4
        center_y = (up[1] + left[1] + right[1] + down[1]) / 4 + radius / 2
        self.assertAlmostEqual(center[0], center_x, delta=1e-4)
        self.assertAlmostEqual(center[1], center_y, delta=1e-4)

    def test_get_rhombuses(self):
        center = (0, 0)
        shoulder = 5
        diff = 12
        inner, outer = get_rhombuses(center, shoulder, diff)
        self.assertSequenceEqual(inner, get_rhombus(center, shoulder, diff))
        self.assertSequenceEqual(outer, get_rhombus(center, shoulder + diff,
                                                    diff))

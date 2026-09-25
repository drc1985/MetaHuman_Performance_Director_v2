"""Regression checks for preserving animation outside a breathing revision window."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('take_generator_under_test', Path(__file__).parents[1] / 'generate_acting_take.py')
generator = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {'unreal': types.ModuleType('unreal')}):
    spec.loader.exec_module(generator)


class BreathingWindowTests(unittest.TestCase):
    def test_later_slice_preserves_both_sides_and_boundary_values(self):
        result = dict(generator._merge_breathing_window(
            [0, 4, 6, 8, 12], [0, 4, 6, 8, 12],
            [(5, 2), (6, 2), (7, 2)], 5, 7))
        self.assertEqual({t: result[t] for t in [0, 4, 8, 12]}, {0: 0, 4: 4, 8: 8, 12: 12})
        self.assertEqual(result[5], 5)
        self.assertEqual(result[7], 7)
        self.assertEqual(result[6], 8)

    def test_first_slice_preserves_tail_and_releases_at_end(self):
        result = dict(generator._merge_breathing_window(
            [0, 7, 10], [0.3, 0.8, 0.4], [(0, 2), (3, 2), (7, 2)], 0, 7))
        self.assertEqual(result[0], 0.3)
        self.assertEqual(result[7], 0.8)
        self.assertEqual(result[10], 0.4)
        self.assertGreater(result[3], 2)

    def test_new_curve_has_zero_boundary_values(self):
        self.assertEqual(generator._merge_breathing_window(
            [], [], [(5, 1), (6, 1), (7, 1)], 5, 7), [(5, 0), (6, 1), (7, 0)])

    def test_zero_duration_is_safe_and_deduplicates_boundary(self):
        self.assertEqual(generator._merge_breathing_window(
            [0, 5, 10], [1, 2, 3], [(5, 10)], 5, 5), [(0, 1), (5, 2), (10, 3)])

    def test_bulk_writer_rejects_mismatched_buffers(self):
        with self.assertRaises(ValueError):
            generator._set_float_curve_keys(None, 'test', [0, 1], [1])


if __name__ == '__main__':
    unittest.main()

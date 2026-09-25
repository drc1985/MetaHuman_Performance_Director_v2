"""Head directives must not introduce a second pose owner in the facial curves."""
import unittest
from unittest.mock import patch
from test_revision_window import generator

class HeadRoutingTests(unittest.TestCase):
    def ops(self, instructions):
        with patch.object(generator.unreal, 'log', lambda *_: None, create=True):
            return generator._curve_ops_from_plan({'instructions': instructions},
                ['HeadYaw', 'HeadPitch', 'HeadRoll', 'HeadControlSwitch', 'FACIAL_C_NeckYaw'])

    def test_all_head_behaviors_preserve_face_head_curves(self):
        for behavior in generator.HEAD_MOVEMENT_BEHAVIORS:
            with self.subTest(behavior=behavior):
                self.assertEqual(self.ops([{'behavior_id': behavior, 'weight': 1.0,
                    'channel': 'head_movement'}]), {})

    def test_locked_and_zero_weight_head_behaviors_preserve_curves(self):
        for extra in [{'weight': 0.0}, {'weight': 1.0, 'preserve_original': True}]:
            self.assertEqual(self.ops([{'behavior_id': 'head_turn_right',
                'channel': 'head_movement', **extra}]), {})

    def test_sigh_generated_torso_instruction_cannot_fuzzy_map_into_face(self):
        # Exact unwanted instruction from newtest7, plus an unknown body
        # behavior whose description would otherwise fuzzy-match jaw tension.
        for instruction in [
            {'channel': 'body_posture', 'behavior_id': 'thoracic_sorrow_deflation',
             'description': 'Clavicle depression and thoracic deflation on breath release.', 'weight': 0.69936},
            {'channel': 'body_posture', 'behavior_id': 'new_body_behavior',
             'description': 'Clench jaw tightly', 'weight': 1.0},
            {'channel': 'gesture', 'behavior_id': 'new_gesture',
             'description': 'Clench jaw tightly', 'weight': 1.0},
        ]:
            with self.subTest(instruction=instruction):
                self.assertEqual(self.ops([instruction]), {})

    def test_excluding_body_does_not_discard_facial_jaw_instruction(self):
        jaw = {'channel': 'facial_expression', 'behavior_id': 'clench_jaw', 'weight': 1.0}
        body = {'channel': 'body_posture', 'behavior_id': 'thoracic_sorrow_deflation', 'weight': 0.69936}
        with patch.object(generator.unreal, 'log', lambda *_: None, create=True), patch.object(generator.unreal, 'log_warning', lambda *_: None, create=True):
            curves = ['CTRL_expressions_jawClenchL', 'CTRL_expressions_jawClenchR']
            expected = generator._curve_ops_from_plan({'instructions': [jaw]}, curves)
            actual = generator._curve_ops_from_plan({'instructions': [jaw, body]}, curves)
            self.assertTrue(expected)
            self.assertEqual(actual, expected)

if __name__ == '__main__':
    unittest.main()

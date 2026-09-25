"""Ocular stability and eyelid dynamics tests."""
import unittest
from test_revision_window import generator

class OcularStabilityTests(unittest.TestCase):
    def test_exhaustion_does_not_clamp_eyeblinks(self):
        """Exhaustion must use soft inner squint / mouth frown rather than full eyeBlink holds."""
        ops = generator._curve_ops_from_plan({
            'instructions': [{'behavior_id': 'express_exhaustion', 'weight': 1.0, 'channel': 'facial_expression'}]
        }, ['CTRL_expressions_eyeBlinkL', 'CTRL_expressions_eyeBlinkR', 'CTRL_expressions_eyeSquintInnerL', 'CTRL_expressions_eyeSquintInnerR'])
        
        self.assertNotIn('CTRL_expressions_eyeBlinkL', ops)
        self.assertNotIn('CTRL_expressions_eyeBlinkR', ops)
        self.assertIn('CTRL_expressions_eyeSquintInnerL', ops)
        self.assertIn('CTRL_expressions_eyeSquintInnerR', ops)

    def test_relief_does_not_clamp_eyeblinks(self):
        """Relief must use soft eyes / smile rather than gluing eyelids shut."""
        ops = generator._curve_ops_from_plan({
            'instructions': [{'behavior_id': 'express_relief', 'weight': 1.0, 'channel': 'facial_expression'}]
        }, ['CTRL_expressions_eyeBlinkL', 'CTRL_expressions_eyeBlinkR', 'CTRL_expressions_eyeSquintInnerL', 'CTRL_expressions_mouthSmileL'])
        
        self.assertNotIn('CTRL_expressions_eyeBlinkL', ops)
        self.assertNotIn('CTRL_expressions_eyeBlinkR', ops)
        self.assertIn('CTRL_expressions_eyeSquintInnerL', ops)

    def test_ocular_curves_exempt_from_wander(self):
        """Peri-orbital, eyelid, gaze, and squint curves must have 0.0 wander to prevent twitching."""
        for curve in ['eyeBlinkL', 'eyeSquintInnerR', 'eyeLookDownL', 'eyeCheekRaiseL', 'pupilDilationL']:
            with self.subTest(curve=curve):
                self.assertEqual(generator._get_decorrelated_wander(1.5, curve, 0.8), 0.0)

    def test_gaze_hold_is_stable_without_2hz_jitter(self):
        """Standard gaze shifts should hold steady between onset and recovery without intermediate jitter keys."""
        keys = generator._ramp_keys(0.0, 5.0, 0.85, is_high_status=False)
        # Verify onset key and hold end key are both 0.85
        hold_keys = [v for t, v in keys if 0.69 <= t <= 2.01]
        self.assertEqual(hold_keys, [0.85, 0.85])
        # Verify no oscillating keys exist inside the hold window
        interior_keys = [v for t, v in keys if 0.71 < t < 1.99]
        self.assertEqual(interior_keys, [])

if __name__ == '__main__':
    unittest.main()

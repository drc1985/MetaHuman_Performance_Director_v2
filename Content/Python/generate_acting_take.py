# Copyright (c) 2026 David Cobbins / Frontier Mindworks. All Rights Reserved.
# MetaHuman Performance Director (MHPD) — Architected & Developed by David Cobbins.

import unreal
import os
import re
import math
import json
import hashlib
import time

# ==============================================================================
# MetaHuman Performance Director - Acting Take Generator
# ==============================================================================
# Executes the C++ subsystem's performance plan (passed as a JSON file) against
# the duplicated baseline AnimSequence. The plan is the SINGLE interpreter of
# the director's note — this script only maps behavior_ids onto the 4 Universal
# Animation Curve Patterns and bakes keys:
#
#   1. PULSE       - Short periodic pulses (blinks)
#   2. HOLD        - Sustained curve state (eyes closed, held tension)
#   3. RAMP        - Shift out + sustain + ease back (gaze breaks / gaze shifts)
#   4. OSCILLATION - Micro-jitter / trembling (brow/eyelid tremor)
#
# Instruction weight (already intensity-scaled and zeroed by channel locks in
# C++) becomes the curve target value, so the Intensity slider and "Preserve
# channels" checkboxes directly shape the baked animation.
# ==============================================================================

# behavior_id -> (pattern, curve group). Behaviors on body/timing channels have
# no facial curves and are skipped with a log line.
# ------------------------------------------------------------------------------
# Canonical 111 Directorial Behavior ID Taxonomy & Channel Sets
# ------------------------------------------------------------------------------

HEAD_MOVEMENT_BEHAVIORS = {
    "head_pitch_down", "head_pitch_up", "head_tilt", "head_warmth_tilt",
    "head_turn_left", "head_turn_right", "head_nod", "head_shake",
    "small_recoil_then_reset", "sudden_startle_pitch_up", "slow_contemptuous_head_turn",
    "dismissive_head_toss", "inquisitive_cocked_head", "weary_head_hang", "level_chin_steady_lock"
}

BODY_POSTURE_BEHAVIORS = {
    "forward_assertive_posture", "closed_guarded_posture", "stiff_protective_posture",
    "slight_forward_recoil", "collapsed_heavy_posture", "slumped_exhausted_posture",
    "upright_regal_posture", "clavicle_defensive_elevation", "thoracic_sorrow_deflation",
    "asymmetric_weight_shift", "leaning_back_detachment", "held_stillness",
    "tentative_lean_in", "braced_chest_dominance", "social_baseline_posture"
}

GESTURE_BEHAVIORS = {
    "sharp_forward_emphasis", "small_defensive_hand_raise", "slow_deliberate_gesture",
    "dismissive_wave_wrist_flick", "fidgeting_hand_clasp", "clenched_fist_tension",
    "asymmetric_shoulder_shrug", "bilateral_shoulder_shrug", "self_comforting_arm_touch",
    "open_palms_plea", "finger_to_lip_contemplation", "restrained_hands_locked"
}

TIMING_AND_PAUSE_BEHAVIORS = {
    "delayed_response_beat", "anticipatory_breath_lead", "anticipatory_masseter_set",
    "anticipatory_gaze_lead", "abrupt_cutting_interruption", "truth_decision_pause",
    "short_pre_response_pause", "stifled_breath_catch", "sigh_exhale_release",
    "double_take_timing", "micro_swallow_beat", "cadence_deceleration",
    "rapid_staccato_burst", "post_line_lingering_hold", "intentional_pre_answer_hold"
}

BEHAVIOR_TO_PATTERN = {
    # 1. Facial Expression - Brows & Forehead
    "brow_lower_lip_press":            ("HOLD",        "brow"),
    "micro_brow_knot":                 ("HOLD",        "sadness"),
    "wide_eyes_brow_raise":            ("HOLD",        "surprise"),
    "soft_defensive_brow":             ("HOLD",        "brow"),
    "eyebrow_flash_micro_squint":      ("PULSE",       "brow"),
    "unilateral_brow_cock":            ("HOLD",        "brow_cock"),
    "glabella_micro_tension":          ("OSCILLATION", "tremor"),

    # 2. Facial Expression - Eyes & Eyelids
    "subtle_squint_scrutiny":          ("HOLD",        "squint"),
    "predatory_eye_narrow":            ("HOLD",        "squint"),
    "heavy_eyelids_jaw_slack":         ("HOLD",        "exhaustion"),
    "eyelid_ptosis_droop":             ("HOLD",        "exhaustion"),
    "quick_blink_lip_part":            ("PULSE",       "blink"),
    "directed_blink_pulse":            ("PULSE",       "blink"),
    "close_eyes_before_answer":        ("PULSE",       "blink"),   # legacy alias
    "cognitive_eye_flutter":           ("FLUTTER",     "blink"),
    "sustained_eye_closure":           ("HOLD",        "blink"),
    "micro_tremor":                    ("OSCILLATION", "tremor"),

    # 3. Facial Expression - Mouth, Lips & Zygomaticus (Lower Face Permeable)
    "open_smile_cheek_raise":          ("HOLD",        "happy"),
    "lip_corner_pull_bilateral":       ("HOLD",        "smile"),
    "asymmetric_smug_lip_corner":      ("HOLD",        "smugness"),
    "suppressed_tell_micro_smirk":     ("HOLD",        "smugness"),
    "lip_corner_depressor_unilateral": ("HOLD",        "contempt"),
    "somber_brow_slight_mouth_drop":   ("HOLD",        "sadness"),
    "subtle_snarl_asymmetric_brow":    ("HOLD",        "contempt"),
    "unilateral_canine_sneer":         ("HOLD",        "contempt"),
    "lip_bite_suppression":            ("HOLD",        "lip_bite"),
    "mouth_pucker_deliberation":       ("HOLD",        "deliberation"),
    "subtle_eye_tension_masked_smile": ("HOLD",        "squint"),
    "masked_expression_leak":          ("HOLD",        "squint"),
    "subtle_expression_shift":         ("HOLD",        "squint"),

    # 4. Facial Expression - Jaw, Masseter & Somatic Tension
    "tight_jaw_micro_tension":         ("HOLD",        "jaw_tension"),
    "clench_jaw":                      ("HOLD",        "jaw_tension"),
    "jaw_clench":                      ("HOLD",        "jaw_tension"),
    "masseter_lock_nostril_flare":     ("HOLD",        "jaw_tension"),
    "micro_grimace_wince":             ("HOLD",        "pain"),
    "slack_jaw_wonder":                ("HOLD",        "wonder"),
    "nervous_anticipation":            ("FLUTTER",     "blink"),
    "sadness_quiver":                  ("OSCILLATION", "tremor"),
    "defiance":                        ("HOLD",        "contempt"),
    "smug_head_tilt":                  ("HOLD",        "smugness"),
    # --------------------------------------------------------------------------
    # 5. Head Movement & Cervical Column Kinematics (C1-C7)
    # --------------------------------------------------------------------------
    "head_pitch_down":                 ("HEAD_PITCH_DOWN", "head_pitch"),
    "head_pitch_up":                   ("HEAD_PITCH_UP",   "head_pitch"),
    "head_tilt":                       ("HEAD_TILT",       "head_roll"),
    "head_warmth_tilt":                ("HEAD_WARMTH",     "head_roll"),
    "head_turn_left":                  ("HEAD_LEFT",       "head_yaw"),
    "head_turn_right":                 ("HEAD_RIGHT",      "head_yaw"),
    "head_nod":                        ("NOD",             "head_pitch"),
    "head_shake":                      ("HEAD_SHAKE",      "head_yaw"),
    "small_recoil_then_reset":         ("HEAD_RECOIL",     "head_pitch"),
    "sudden_startle_pitch_up":         ("HEAD_STARTLE",    "head_pitch"),
    "slow_contemptuous_head_turn":     ("HEAD_CONTEMPT",   "head_yaw"),
    "dismissive_head_toss":            ("HEAD_TOSS",       "head_yaw"),
    "inquisitive_cocked_head":         ("HEAD_COCKED",     "head_roll"),
    "weary_head_hang":                 ("HEAD_HANG",       "head_pitch"),
    "level_chin_steady_lock":          ("HEAD_LOCK",       "head_pitch"),
    "drop_head":                       ("HEAD_HANG",       "head_pitch"),

    # --------------------------------------------------------------------------
    # 6. Clavicular Kinematics, Shoulder Dynamics & Posture
    # --------------------------------------------------------------------------
    "clavicle_defensive_elevation":    ("HOLD",            "clavicle_both"),
    "bilateral_shoulder_shrug":        ("RAMP",            "clavicle_both"),
    "asymmetric_shoulder_shrug":       ("RAMP",            "clavicle_asym"),
    "thoracic_sorrow_deflation":       ("HOLD",            "clavicle_down"),
    "collapsed_heavy_posture":         ("HOLD",            "clavicle_down"),
    "forward_assertive_posture":       ("HOLD",            "clavicle_retract"),
    "braced_chest_dominance":          ("HOLD",            "clavicle_retract"),

    # Backward-Compatible Emotional States
    "express_surprise":                ("HOLD",        "surprise"),
    "express_disgust":                 ("HOLD",        "disgust"),
    "express_sadness":                 ("HOLD",        "sadness"),
    "express_frown":                   ("HOLD",        "frown"),
    "express_upset":                   ("HOLD",        "upset"),
    "express_smile":                   ("HOLD",        "smile"),
    "express_happy":                   ("HOLD",        "happy"),
    "express_annoyance":               ("HOLD",        "annoyance"),
    "express_pain":                    ("HOLD",        "pain"),
    "express_frustration":             ("HOLD",        "frustration"),
    "express_suspicion":               ("HOLD",        "suspicion"),
    "express_guilt":                   ("HOLD",        "guilt"),
    "express_attraction":              ("HOLD",        "attraction"),
    "express_smugness":                ("HOLD",        "smugness"),
    "express_fear":                    ("HOLD",        "fear"),
    "express_exhaustion":              ("HOLD",        "exhaustion"),
    "express_contempt":                ("HOLD",        "contempt"),
    "express_incredulity":             ("HOLD",        "incredulity"),
    "express_anticipation":            ("HOLD",        "anticipation"),
    "express_warmth":                  ("HOLD",        "warmth"),
    "express_relief":                  ("HOLD",        "relief"),
    "express_pride":                   ("HOLD",        "pride"),
    "express_playful":                 ("HOLD",        "playful"),
    "express_wonder":                  ("HOLD",        "wonder"),
    "express_serenity":                ("HOLD",        "serenity"),
    "express_gratitude":               ("HOLD",        "gratitude"),
    "express_listening":               ("HOLD",        "listening"),
    "express_deliberation":            ("HOLD",        "deliberation"),
    "express_stoic":                   ("HOLD",        "stoic"),
    "express_casual":                  ("HOLD",        "casual"),
    "express_daydreaming":             ("HOLD",        "daydreaming"),
}

# Curve group -> list of ((introspection substrings), canonical fallback)
CURVE_GROUPS = {
    "blink": [
        (("eyeblinkl", "eyeblink_l"), "CTRL_expressions_eyeBlinkL"),
        (("eyeblinkr", "eyeblink_r"), "CTRL_expressions_eyeBlinkR"),
    ],
    "gaze_left": [
        (("eyelookleftl", "eyelookleft_l"), "CTRL_expressions_eyeLookLeftL"),
        (("eyelookleftr", "eyelookleft_r"), "CTRL_expressions_eyeLookLeftR"),
    ],
    "gaze_right": [
        (("eyelookrightl", "eyelookright_l"), "CTRL_expressions_eyeLookRightL"),
        (("eyelookrightr", "eyelookright_r"), "CTRL_expressions_eyeLookRightR"),
    ],
    "gaze_up": [
        (("eyelookupl", "eyelookup_l"), "CTRL_expressions_eyeLookUpL"),
        (("eyelookupr", "eyelookup_r"), "CTRL_expressions_eyeLookUpR"),
    ],
    "gaze_down": [
        (("eyelookdownl", "eyelookdown_l"), "CTRL_expressions_eyeLookDownL"),
        (("eyelookdownr", "eyelookdown_r"), "CTRL_expressions_eyeLookDownR"),
    ],
    "pupil_dilate": [
        (("pupildilatel", "pupildilationl", "eyepupildilatel"), "CTRL_expressions_pupilDilationL"),
        (("pupildilater", "pupildilationr", "eyepupildilater"), "CTRL_expressions_pupilDilationR"),
    ],
    "pupil_constrict": [
        (("pupilconstrictl", "pupilconstrictionl", "eyepupilconstrictl"), "CTRL_expressions_pupilConstrictL"),
        (("pupilconstrictr", "pupilconstrictionr", "eyepupilconstrictr"), "CTRL_expressions_pupilConstrictR"),
    ],
    "squint": [
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "brow": [
        (("browdownl", "browlowerl", "browlower_l"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr", "browlower_r"), "CTRL_expressions_browDownR"),
    ],
    "brow_cock": [
        (("browraiseouterr", "browraiseouter_r"), "CTRL_expressions_browRaiseOuterR"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("browdownl", "browlowerl"), "CTRL_expressions_browDownL"),
    ],
    "lip_bite": [
        (("mouthlowerlipdepressl", "mouthlowerlipdepress_l"), "CTRL_expressions_mouthLowerLipDepressL"),
        (("mouthlowerlipdepressr", "mouthlowerlipdepress_r"), "CTRL_expressions_mouthLowerLipDepressR"),
        (("mouthlipspressl", "mouthpressl"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr"), "CTRL_expressions_mouthLipsPressR"),
    ],
    "tremor": [
        (("browdownl", "browlowerl", "browlower_l"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr", "browlower_r"), "CTRL_expressions_browDownR"),
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "surprise": [
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("browraiseouterl", "browraiseouter_l"), "CTRL_expressions_browRaiseOuterL"),
        (("browraiseouterr", "browraiseouter_r"), "CTRL_expressions_browRaiseOuterR"),
        (("eyewidenl", "eyewiden_l"), "CTRL_expressions_eyeWidenL"),
        (("eyewidenr", "eyewiden_r"), "CTRL_expressions_eyeWidenR"),
        (("jawopen", "jaw_open"), "CTRL_expressions_jawOpen"),
    ],
    "disgust": [
        (("nosewrinklel", "nosewrinkle_l"), "CTRL_expressions_noseWrinkleL"),
        (("nosewrinkler", "nosewrinkle_r"), "CTRL_expressions_noseWrinkleR"),
        (("nosenasolabialdeepenl", "nasolabialdeepenl"), "CTRL_expressions_noseNasolabialDeepenL"),
        (("nosenasolabialdeepenr", "nasolabialdeepenr"), "CTRL_expressions_noseNasolabialDeepenR"),
        (("cheeksquintl", "cheeksquint_l"), "CTRL_expressions_cheekSquintL"),
        (("cheeksquintr", "cheeksquint_r"), "CTRL_expressions_cheekSquintR"),
        (("mouthupperupl", "mouthupperup_l"), "CTRL_expressions_mouthUpperUpL"),
        (("mouthupperupr", "mouthupperup_r"), "CTRL_expressions_mouthUpperUpR"),
        (("mouthcornerdepressl", "mouthfrownl", "mouthfrown_l"), "CTRL_expressions_mouthCornerDepressL"),
        (("mouthcornerdepressr", "mouthfrownr", "mouthfrown_r"), "CTRL_expressions_mouthCornerDepressR"),
        (("browdownl", "browlowerl", "browlower_l"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr", "browlower_r"), "CTRL_expressions_browDownR"),
    ],
    "jaw_tension": [
        (("jawclenchl", "jawclench"), "CTRL_expressions_jawClenchL"),
        (("jawclenchr", "jawclench"), "CTRL_expressions_jawClenchR"),
        (("mouthlipspressl", "mouthpressl", "mouthpress_l"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr", "mouthpress_r"), "CTRL_expressions_mouthLipsPressR"),
        (("browdownl", "browlowerl", "browlower_l"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr", "browlower_r"), "CTRL_expressions_browDownR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
        (("cheeksquintl", "cheeksquint_l"), "CTRL_expressions_cheekSquintL"),
        (("cheeksquintr", "cheeksquint_r"), "CTRL_expressions_cheekSquintR"),
        (("nosewrinklel", "nosewrinkle_l"), "CTRL_expressions_noseWrinkleL"),
        (("nosewrinkler", "nosewrinkle_r"), "CTRL_expressions_noseWrinkleR"),
    ],
    "sadness": [
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("eyelookdownl", "eyelookdown_l"), "CTRL_expressions_eyeLookDownL"),
        (("eyelookdownr", "eyelookdown_r"), "CTRL_expressions_eyeLookDownR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
        (("mouthcornerdepressl", "mouthfrownl", "mouthfrown_l"), "CTRL_expressions_mouthCornerDepressL"),
        (("mouthcornerdepressr", "mouthfrownr", "mouthfrown_r"), "CTRL_expressions_mouthCornerDepressR"),
    ],
    "frown": [
        (("browdownl", "browlowerl", "browlower_l"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr", "browlower_r"), "CTRL_expressions_browDownR"),
        (("mouthcornerdepressl", "mouthfrownl", "mouthfrown_l"), "CTRL_expressions_mouthCornerDepressL"),
        (("mouthcornerdepressr", "mouthfrownr", "mouthfrown_r"), "CTRL_expressions_mouthCornerDepressR"),
    ],
    "upset": [
        (("browdownl", "browlowerl", "browlower_l"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr", "browlower_r"), "CTRL_expressions_browDownR"),
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("jawclenchl", "jawclench"), "CTRL_expressions_jawClenchL"),
        (("jawclenchr", "jawclench"), "CTRL_expressions_jawClenchR"),
        (("mouthlipspressl", "mouthpressl", "mouthpress_l"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr", "mouthpress_r"), "CTRL_expressions_mouthLipsPressR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "happy": [
        (("cheekraisel", "eyecheekraisel"), "CTRL_expressions_eyeCheekRaiseL"),
        (("cheekraiser", "eyecheekraiser"), "CTRL_expressions_eyeCheekRaiseR"),
        (("cheeksquintl", "cheeksquint_l"), "CTRL_expressions_cheekSquintL"),
        (("cheeksquintr", "cheeksquint_r"), "CTRL_expressions_cheekSquintR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthsmiler", "mouthsmile_r"), "CTRL_expressions_mouthSmileR"),
        (("mouthcornerpulll", "mouthcornerpull_l"), "CTRL_expressions_mouthCornerPullL"),
        (("mouthcornerpullr", "mouthcornerpull_r"), "CTRL_expressions_mouthCornerPullR"),
    ],
    "smile": [
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthsmiler", "mouthsmile_r"), "CTRL_expressions_mouthSmileR"),
        (("mouthcornerpulll", "mouthcornerpull_l"), "CTRL_expressions_mouthCornerPullL"),
        (("mouthcornerpullr", "mouthcornerpull_r"), "CTRL_expressions_mouthCornerPullR"),
        (("mouthsharpcornerpulll", "mouthsharpcornerpull_l"), "CTRL_expressions_mouthSharpCornerPullL"),
        (("mouthsharpcornerpullr", "mouthsharpcornerpull_r"), "CTRL_expressions_mouthSharpCornerPullR"),
        (("cheekraisel", "eyecheekraisel"), "CTRL_expressions_eyeCheekRaiseL"),
        (("cheekraiser", "eyecheekraiser"), "CTRL_expressions_eyeCheekRaiseR"),
        (("cheeksquintl", "cheeksquint_l"), "CTRL_expressions_cheekSquintL"),
        (("cheeksquintr", "cheeksquint_r"), "CTRL_expressions_cheekSquintR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "annoyance": [
        (("mouthlipspressl", "mouthpressl"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr"), "CTRL_expressions_mouthLipsPressR"),
        (("mouthupperupl",), "CTRL_expressions_mouthUpperUpL"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "pain": [
        (("browdownl", "browlowerl"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr"), "CTRL_expressions_browDownR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
        (("mouthlipspressl", "mouthpressl"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr"), "CTRL_expressions_mouthLipsPressR"),
        (("mouthupperupl",), "CTRL_expressions_mouthUpperUpL"),
        (("mouthupperupr",), "CTRL_expressions_mouthUpperUpR"),
        (("jawchinraisedl", "chinraisedl"), "CTRL_expressions_jawChinRaiseDL"),
        (("jawchinraisedr", "chinraisedr"), "CTRL_expressions_jawChinRaiseDR"),
    ],
    "frustration": [
        (("mouthlipspressl", "mouthpressl"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr"), "CTRL_expressions_mouthLipsPressR"),
        (("jawclenchl", "jawclench"), "CTRL_expressions_jawClenchL"),
        (("jawclenchr", "jawclench"), "CTRL_expressions_jawClenchR"),
        (("browdownl", "browlowerl"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr"), "CTRL_expressions_browDownR"),
        (("eyelookupl", "eyelookup_l"), "CTRL_expressions_eyeLookUpL"),
        (("eyelookupr", "eyelookupr_r"), "CTRL_expressions_eyeLookUpR"),
    ],
    "suspicion": [
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
        (("browdownl", "browlowerl"), "CTRL_expressions_browDownL"),
        (("browraiseouterr", "browraiseouter_r"), "CTRL_expressions_browRaiseOuterR"),
        (("mouthlipspressl", "mouthpressl"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr"), "CTRL_expressions_mouthLipsPressR"),
        (("pupilconstrictl", "pupilconstrictionl", "eyepupilconstrictl"), "CTRL_expressions_pupilConstrictL"),
        (("pupilconstrictr", "pupilconstrictionr", "eyepupilconstrictr"), "CTRL_expressions_pupilConstrictR"),
    ],
    "guilt": [
        (("eyelookdownl", "eyelookdown_l"), "CTRL_expressions_eyeLookDownL"),
        (("eyelookdownr", "eyelookdown_r"), "CTRL_expressions_eyeLookDownR"),
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("mouthcornerdepressl", "mouthfrownl"), "CTRL_expressions_mouthCornerDepressL"),
        (("mouthcornerdepressr", "mouthfrownr"), "CTRL_expressions_mouthCornerDepressR"),
    ],
    "attraction": [
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthsmiler", "mouthsmile_r"), "CTRL_expressions_mouthSmileR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
        (("cheekraisel", "eyecheekraisel"), "CTRL_expressions_eyeCheekRaiseL"),
        (("cheekraiser", "eyecheekraiser"), "CTRL_expressions_eyeCheekRaiseR"),
        (("pupildilatel", "pupildilationl", "eyepupildilatel"), "CTRL_expressions_pupilDilationL"),
        (("pupildilater", "pupildilationr", "eyepupildilater"), "CTRL_expressions_pupilDilationR"),
    ],
    "smugness": [
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthupperupl",), "CTRL_expressions_mouthUpperUpL"),
        (("mouthcornerpulll",), "CTRL_expressions_mouthCornerPullL"),
        (("browraiseouterl",), "CTRL_expressions_browRaiseOuterL"),
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browdownr", "browlower_r"), "CTRL_expressions_browDownR"),
        (("jawchinraisedl",), "CTRL_expressions_jawChinRaiseDL"),
    ],
    "fear": [
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("browraiseouterl", "browraiseouter_l"), "CTRL_expressions_browRaiseOuterL"),
        (("browraiseouterr", "browraiseouter_r"), "CTRL_expressions_browRaiseOuterR"),
        (("eyewidenl", "eyewiden_l"), "CTRL_expressions_eyeWidenL"),
        (("eyewidenr", "eyewiden_r"), "CTRL_expressions_eyeWidenR"),
        (("jawopen", "jaw_open"), "CTRL_expressions_jawOpen"),
        (("pupildilatel", "pupildilationl", "eyepupildilatel"), "CTRL_expressions_pupilDilationL"),
        (("pupildilater", "pupildilationr", "eyepupildilater"), "CTRL_expressions_pupilDilationR"),
    ],
    "exhaustion": [
        (("eyeblinkl", "eyeblink_l"), "CTRL_expressions_eyeBlinkL"),
        (("eyeblinkr", "eyeblink_r"), "CTRL_expressions_eyeBlinkR"),
        (("mouthcornerdepressl", "mouthfrownl"), "CTRL_expressions_mouthCornerDepressL"),
        (("mouthcornerdepressr", "mouthfrownr"), "CTRL_expressions_mouthCornerDepressR"),
        (("jawopen", "jaw_open"), "CTRL_expressions_jawOpen"),
    ],
    "contempt": [
        (("mouthupperupl",), "CTRL_expressions_mouthUpperUpL"),
        (("nosewrinklel",), "CTRL_expressions_noseWrinkleL"),
        (("jawclenchl", "jawclench"), "CTRL_expressions_jawClenchL"),
        (("mouthcornerdepressr",), "CTRL_expressions_mouthCornerDepressR"),
    ],
    "incredulity": [
        (("browdownl", "browlowerl"), "CTRL_expressions_browDownL"),
        (("browraiseouterr",), "CTRL_expressions_browRaiseOuterR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
        (("jawopen", "jaw_open"), "CTRL_expressions_jawOpen"),
    ],
    "anticipation": [
        (("eyewidenl", "eyewiden_l"), "CTRL_expressions_eyeWidenL"),
        (("eyewidenr", "eyewiden_r"), "CTRL_expressions_eyeWidenR"),
        (("mouthlipspressl", "mouthpressl"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr"), "CTRL_expressions_mouthLipsPressR"),
    ],
    "warmth": [
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthsmiler", "mouthsmile_r"), "CTRL_expressions_mouthSmileR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
        (("cheekraisel", "eyecheekraisel"), "CTRL_expressions_eyeCheekRaiseL"),
        (("cheekraiser", "eyecheekraiser"), "CTRL_expressions_eyeCheekRaiseR"),
    ],
    "relief": [
        (("eyeblinkl", "eyeblink_l"), "CTRL_expressions_eyeBlinkL"),
        (("eyeblinkr", "eyeblink_r"), "CTRL_expressions_eyeBlinkR"),
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthsmiler", "mouthsmile_r"), "CTRL_expressions_mouthSmileR"),
    ],
    "pride": [
        (("mouthcornerpulll", "mouthcornerpull_l"), "CTRL_expressions_mouthCornerPullL"),
        (("mouthcornerpullr", "mouthcornerpull_r"), "CTRL_expressions_mouthCornerPullR"),
        (("jawchinraisedl", "chinraisedl"), "CTRL_expressions_jawChinRaiseDL"),
        (("jawchinraisedr", "chinraisedr"), "CTRL_expressions_jawChinRaiseDR"),
    ],
    "playful": [
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthcornerpulll", "mouthcornerpull_l"), "CTRL_expressions_mouthCornerPullL"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
    ],
    "wonder": [
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("browraiseouterl", "browraiseouter_l"), "CTRL_expressions_browRaiseOuterL"),
        (("browraiseouterr", "browraiseouter_r"), "CTRL_expressions_browRaiseOuterR"),
        (("eyewidenl", "eyewiden_l"), "CTRL_expressions_eyeWidenL"),
        (("eyewidenr", "eyewiden_r"), "CTRL_expressions_eyeWidenR"),
        (("jawopen", "jaw_open"), "CTRL_expressions_jawOpen"),
        (("pupildilatel", "pupildilationl", "eyepupildilatel"), "CTRL_expressions_pupilDilationL"),
        (("pupildilater", "pupildilationr", "eyepupildilater"), "CTRL_expressions_pupilDilationR"),
    ],
    "serenity": [
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthsmiler", "mouthsmile_r"), "CTRL_expressions_mouthSmileR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "gratitude": [
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthsmiler", "mouthsmile_r"), "CTRL_expressions_mouthSmileR"),
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "listening": [
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "deliberation": [
        (("browdownl", "browlowerl"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr"), "CTRL_expressions_browDownR"),
        (("mouthlipspressl", "mouthpressl"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr"), "CTRL_expressions_mouthLipsPressR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
        (("pupilconstrictl", "pupilconstrictionl", "eyepupilconstrictl"), "CTRL_expressions_pupilConstrictL"),
        (("pupilconstrictr", "pupilconstrictionr", "eyepupilconstrictr"), "CTRL_expressions_pupilConstrictR"),
    ],
    "stoic": [
        (("mouthlipspressl", "mouthpressl"), "CTRL_expressions_mouthLipsPressL"),
        (("mouthlipspressr", "mouthpressr"), "CTRL_expressions_mouthLipsPressR"),
    ],
    "casual": [
        (("mouthsmilel", "mouthsmile_l"), "CTRL_expressions_mouthSmileL"),
        (("mouthsmiler", "mouthsmile_r"), "CTRL_expressions_mouthSmileR"),
    ],
    "daydreaming": [
        (("jawopen", "jaw_open"), "CTRL_expressions_jawOpen"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "head_yaw": [
        (("facial_c_headyaw", "facial_c_head_yaw", "c_headyaw", "headyaw", "head_yaw"), "FACIAL_C_HeadYaw"),
        (("ctrl_expressions_headyaw", "ctrl_head_yaw"), "CTRL_expressions_headYaw"),
    ],
    "head_pitch": [
        (("facial_c_headpitch", "facial_c_head_pitch", "c_headpitch", "headpitch", "head_pitch"), "FACIAL_C_HeadPitch"),
        (("ctrl_expressions_headpitch", "ctrl_head_pitch"), "CTRL_expressions_headPitch"),
    ],
    "head_roll": [
        (("facial_c_headroll", "facial_c_head_roll", "c_headroll", "headroll", "head_roll"), "FACIAL_C_HeadRoll"),
        (("ctrl_expressions_headroll", "ctrl_head_roll"), "CTRL_expressions_headRoll"),
    ],
    "neck_yaw": [
        (("facial_c_neckyaw", "facial_c_neck_yaw", "c_neckyaw", "neckyaw", "neck_yaw"), "FACIAL_C_NeckYaw"),
        (("ctrl_expressions_neckyaw", "ctrl_neck_yaw"), "CTRL_expressions_neckYaw"),
    ],
    "neck_pitch": [
        (("facial_c_neckpitch", "facial_c_neck_pitch", "c_neckpitch", "neckpitch", "neck_pitch"), "FACIAL_C_NeckPitch"),
        (("ctrl_expressions_neckpitch", "ctrl_neck_pitch"), "CTRL_expressions_neckPitch"),
    ],
    "neck_roll": [
        (("facial_c_neckroll", "facial_c_neck_roll", "c_neckroll", "neckroll", "neck_roll"), "FACIAL_C_NeckRoll"),
        (("ctrl_expressions_neckroll", "ctrl_neck_roll"), "CTRL_expressions_neckRoll"),
    ],
    "head_switch": [
        (("headcontrolswitch", "head_control_switch", "headcontrol"), "HeadControlSwitch"),
    ],
    "clavicle_both": [
        (("clavicle_l_up", "clavicleraisel", "clavicle_raise_l"), "Clavicle_L_Up"),
        (("clavicle_r_up", "clavicleraiser", "clavicle_raise_r"), "Clavicle_R_Up"),
    ],
    "clavicle_asym": [
        (("clavicle_l_up", "clavicleraisel", "clavicle_raise_l"), "Clavicle_L_Up"),
    ],
    "clavicle_down": [
        (("clavicle_l_down", "clavicledepressl", "clavicle_depress_l"), "Clavicle_L_Down"),
        (("clavicle_r_down", "clavicledepressr", "clavicle_depress_r"), "Clavicle_R_Down"),
    ],
    "clavicle_retract": [
        (("clavicle_l_fwd", "clavicleretractl"), "Clavicle_L_Fwd"),
        (("clavicle_r_fwd", "clavicleretractr"), "Clavicle_R_Fwd"),
    ],
    "chest_breathing": [
        (("chest_breathing", "breathing", "diaphragm", "chest_expand"), "Chest_Breathing"),
    ],
}

_WORD_NUMBERS = {
    "once": 1, "twice": 2, "thrice": 3,
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
}


def _parse_blink_count(text, default=4):
    """Extracts a blink count near the word 'blink' ('blinks 4 times', 'blink twice')."""
    t = (text or "").lower()
    m = (re.search(r"\bblink\w*\b[^.]*?\b(\d{1,2})\b", t)
         or re.search(r"\b(\d{1,2})\b[^.]*?\bblink\w*\b", t))
    if m:
        return max(1, min(12, int(m.group(1))))
    for word, num in _WORD_NUMBERS.items():
        if (re.search(rf"\bblink\w*\b[^.]*?\b{word}\b", t)
                or re.search(rf"\b{word}\b[^.]*?\bblink\w*\b", t)):
            return max(1, min(12, num))
    return default


def _resolve_group(group, existing_curve_names):
    """Finds real curve names on the asset for each semantic item in the group, or falls back to DNA names."""
    items = CURVE_GROUPS.get(group, [])
    resolved = []
    for substrings, fallback in items:
        hit = None
        for n in existing_curve_names:
            nl = n.lower()
            if any(s in nl for s in substrings):
                hit = n
                break
        resolved.append(hit if hit else fallback)
    return list(dict.fromkeys(resolved))  # unique, preserving order


def _soft_knee_saturate(val, max_limit=1.0, knee=0.70):
    """
    Biological non-linear soft-knee saturation curve for RigLogic curves.
    Prevents linear overshoot past anatomical limits (preserving mesh volume & soft skinning).
    f(x) = x if x <= knee else knee + (max_limit - knee) * tanh((x - knee) / (max_limit - knee))
    """
    if val <= knee:
        return max(0.0, float(val))
    span = max_limit - knee
    if span <= 0.0:
        return knee
    normalized = (val - knee) / span
    saturated = knee + span * math.tanh(normalized)
    return min(max_limit, float(saturated))


# ------------------------------------------------------------------------------
# Pattern key generators. All patterns start AND end at 0 inside the range so
# they never snap against preserved solver keys at the range boundaries.
# ------------------------------------------------------------------------------

def _pulse_keys(r_start, r_end, val, count):
    """
    Periodic blinks with biologically authentic asymmetric kinematics:
    Rapid ballistic downstroke (~50ms) driven by orbicularis oculi contraction,
    followed by viscoelastic reopening (~140ms) driven by levator palpebrae superioris.
    """
    r_dur = r_end - r_start
    count = max(1, min(count, max(1, int(r_dur / 0.35))))
    step = r_dur / (count + 1)
    keys = []
    for i in range(count):
        t_close = r_start + (i + 1) * step
        t_peak = min(r_end, t_close + 0.05)
        t_ease = min(r_end, t_close + 0.12)
        t_open = min(r_end, t_close + 0.19)
        keys += [
            (t_close, 0.0),
            (t_peak, val),
            (t_ease, val * 0.35),
            (t_open, 0.0)
        ]
    return sorted(list(dict.fromkeys(keys)), key=lambda kv: kv[0])


def _get_fatigue_params(curve_name):
    """
    Returns fatigue decay amplitude (d) and time constant (tau) in seconds per muscle group (§6.4).
    T(t) = T * (1 - d * (1 - e^(-t/tau)))
    """
    c = (curve_name or "").lower()
    if "jaw" in c or "masseter" in c:
        return 0.20, 7.0
    elif "mouth" in c or "lip" in c:
        return 0.13, 10.0
    elif "squint" in c or "blink" in c:
        return 0.12, 6.0
    elif "brow" in c:
        return 0.07, 20.0
    elif "cheek" in c:
        return 0.15, 6.0
    elif "nose" in c:
        return 0.35, 3.0
    return 0.10, 8.0


def _get_decorrelated_wander(t_rel, curve_name, base_val):
    """
    Band-limited multi-frequency decorrelated micro-wander (0.17 Hz, 0.31 Hz, 0.53 Hz) (§6.7).
    Eliminates uniform sinusoidal breathing artifacts ('metronome face') with deterministic phase hashing.
    Strictly exempts eyelids/blinks so eyelids remain rock-steady without unnatural micro-twitching.
    """
    c = (curve_name or "").lower()
    if any(k in c for k in ("blink", "eyeblink", "eyelid")):
        return 0.0

    h = int(hashlib.md5((curve_name or "wander").encode('utf-8')).hexdigest()[:6], 16)
    phi1 = ((h % 100) / 100.0) * 2.0 * math.pi
    phi2 = (((h >> 8) % 100) / 100.0) * 2.0 * math.pi
    phi3 = (((h >> 16) % 100) / 100.0) * 2.0 * math.pi

    w1 = 0.015 * math.sin(2.0 * math.pi * 0.17 * t_rel + phi1)
    w2 = 0.010 * math.sin(2.0 * math.pi * 0.31 * t_rel + phi2)
    w3 = 0.007 * math.sin(2.0 * math.pi * 0.53 * t_rel + phi3)
    return (w1 + w2 + w3) * min(1.0, float(base_val))


def _hold_keys(r_start, r_end, val, is_masseter_tension=False, is_high_status=False, curve_name="", direction_text=""):
    """
    Sustained affective state with biological asymmetric onset (ballistic overshoot and viscoelastic clamp),
    fatigue decay, re-articulation dips/re-grips (>2s), decorrelated multi-frequency micro-wander,
    and staggered typed release (§6).
    """
    r_dur = r_end - r_start
    if r_dur < 0.4:
        return [(r_start, 0.0), (r_start + r_dur * 0.35, val), (r_end, 0.0)]

    # 1. Ballistic rapid entry with overshoot and viscoelastic clamp (§6.7)
    # Reach ~1.18x at 120ms, settle back to target over 350ms
    t_overshoot = min(r_end, r_start + 0.12)
    v_overshoot = _soft_knee_saturate(val * 1.18)
    t_settle = min(r_end, r_start + 0.35)
    v_settle = val

    # 2. Staggered per-control release offset (40-120ms desynchronization)
    h_curve = int(hashlib.md5((curve_name or "curve").encode('utf-8')).hexdigest()[:4], 16) if curve_name else 0
    stagger_offset = ((h_curve % 11) - 5) * 0.012  # -0.06s to +0.06s

    # Viscoelastic release or status lingering hold
    release_lead = 0.08 if is_high_status else 0.28
    t_out = max(t_settle, r_end - release_lead + stagger_offset)

    keys = [
        (r_start, 0.0),
        (t_overshoot, v_overshoot),
        (t_settle, v_settle)
    ]

    sustain_dur = t_out - t_settle
    if sustain_dur > 0.4:
        d_fatigue, tau = _get_fatigue_params(curve_name)

        if is_masseter_tension:
            # 4-6 Hz masseter tremor under cold fury / isometric clench (amplitude ~0.03)
            # plus transient +12% clamping pulses on hard plosive beats
            freq = 5.0
            n_steps = max(4, int(sustain_dur * 20))
            dt = sustain_dur / (n_steps + 1)
            for i in range(1, n_steps + 1):
                tk = t_settle + i * dt
                t_rel = tk - t_settle
                tremor = 0.03 * math.sin(2.0 * math.pi * freq * t_rel)
                plosive = 0.12 * val * (max(0.0, math.sin(2.0 * math.pi * 1.5 * t_rel)) ** 4)
                keys.append((round(tk, 3), round(max(0.0, min(1.0, val + tremor + plosive)), 3)))
        else:
            # Deterministic re-articulation schedule (§6.3) for sustained holds >= 2.0s
            # Human performers re-grip voluntary holds every ~2.6 - 3.6s
            rearticulation_points = []
            if sustain_dur >= 2.0:
                base_interval = 3.0
                n_grips = int(sustain_dur / base_interval)
                for g in range(1, n_grips + 1):
                    jitter = (((h_curve + g * 37) % 21) - 10) * 0.04  # -0.4s to +0.4s
                    t_grip = t_settle + g * base_interval + jitter
                    if t_settle + 0.6 < t_grip < t_out - 0.6:
                        rearticulation_points.append(t_grip)

            # Sample keys across sustain duration with fatigue decay + decorrelated wander
            n_steps = max(3, int(sustain_dur / 0.40))
            step_dt = sustain_dur / (n_steps + 1)

            last_reartic_time = t_settle

            for i in range(1, n_steps + 1):
                tk = t_settle + i * step_dt
                t_rel = tk - t_settle

                # Fatigue decay: T(t) = T * (1 - d * (1 - exp(-t_fatigue / tau)))
                t_fatigue = max(0.0, tk - last_reartic_time)
                fatigue_factor = 1.0 - d_fatigue * (1.0 - math.exp(-t_fatigue / tau))

                # Decorrelated multi-frequency micro-wander (not a uniform sine wave)
                wander = _get_decorrelated_wander(t_rel, curve_name, val)

                target_v = val * fatigue_factor + wander
                keys.append((round(tk, 3), round(max(0.0, min(1.0, target_v)), 3)))

            # Inject explicit physiological re-articulation dip and re-grip keys (§6.3)
            for rg_t in rearticulation_points:
                t_dip = min(t_out - 0.20, rg_t + 0.14)
                w_dip = _get_decorrelated_wander(t_dip - t_settle, curve_name, val)
                v_dip = max(0.0, val * 0.74 + w_dip)
                keys.append((round(t_dip, 3), round(v_dip, 3)))

                t_regrip = min(t_out - 0.05, rg_t + 0.32)
                w_regrip = _get_decorrelated_wander(t_regrip - t_settle, curve_name, val)
                v_regrip = _soft_knee_saturate(val * 1.04 + w_regrip)
                keys.append((round(t_regrip, 3), round(v_regrip, 3)))

    keys.append((round(t_out, 3), val))

    if is_high_status:
        # Status lingering: sustains defiant/smug posture into the cut
        keys.append((round(r_end, 3), round(val * 0.65, 3)))
    else:
        # Viscoelastic release settling
        t_settle_rel = t_out + (r_end - t_out) * 0.45
        keys.append((round(t_settle_rel, 3), round(val * 0.25, 3)))
        keys.append((round(r_end, 3), 0.0))

    # Deduplicate and sort
    seen = set()
    clean_keys = []
    for t, v in sorted(keys, key=lambda kv: kv[0]):
        rt = round(t, 4)
        if rt not in seen and t <= r_end:
            seen.add(rt)
            clean_keys.append((t, v))
    return clean_keys


def _head_switch_keys(r_start, r_end):
    """Activates procedural HeadControlSwitch: 40ms ramp to 1.0, hold, 40ms ramp down."""
    t_in = min(r_end, r_start + 0.04)
    t_out = max(t_in, r_end - 0.04)
    return [(r_start, 0.0), (t_in, 1.0), (t_out, 1.0), (r_end, 0.0)]


def _cervical_distributed_keys(r_start, r_end, angle_deg, is_neck=False, offset=0.0, onset_dur=0.35, is_toss=False):
    """
    Biomechanical Multi-Segment Cervical Spine Kinematics (C1-C7):
    Distributes total head/neck rotational attitude across the cervical vertebral column:
    - Head (Atlanto-Occipital C1-C2): 40% of pitch/yaw/roll with rapid initial lead.
    - Neck (C3-C7 column): 60% of pitch/yaw/roll with organic 40ms viscoelastic phase lag.
    """
    r_dur = r_end - r_start
    if r_dur < 0.4:
        factor = 0.60 if is_neck else 0.40
        return [(r_start, 0.0), (r_start + r_dur * 0.5, angle_deg * factor), (r_end, 0.0)]

    factor = 0.60 if is_neck else 0.40
    target_val = angle_deg * factor

    phase_lag = 0.04 if is_neck else 0.0
    t0 = r_start + max(0.0, offset) + phase_lag
    t_in = min(r_end - 0.20, t0 + (0.18 if is_toss else onset_dur))
    t_out = max(t_in + 0.10, r_end - (0.12 if is_toss else 0.35))

    keys = [
        (r_start, 0.0),
        (t0, 0.0),
        (t_in, target_val),
    ]

    # Subtle organic fixational micro-sway during sustained head attitude
    hold_span = t_out - t_in
    if hold_span > 0.4:
        n_steps = max(1, int(hold_span / 0.30))
        step_dt = hold_span / (n_steps + 1)
        for i in range(1, n_steps + 1):
            tk = t_in + i * step_dt
            sway = (0.04 * target_val) * math.sin(2.0 * math.pi * 1.2 * (tk - t_in))
            keys.append((round(tk, 3), round(target_val + sway, 3)))

    keys.append((round(t_out, 3), target_val))
    keys.append((round(r_end, 3), 0.0))

    seen = set()
    clean = []
    for t, v in sorted(keys, key=lambda kv: kv[0]):
        rt = round(t, 4)
        if rt not in seen and t <= r_end:
            seen.add(rt)
            clean.append((t, v))
    return clean


def _head_toss_keys(r_start, r_end, angle_deg, is_neck=False):
    """Dismissive / incredulous head toss: sharp 180ms ease-in, 0.5s linger, smooth settle."""
    return _cervical_distributed_keys(r_start, r_end, angle_deg, is_neck=is_neck, onset_dur=0.18, is_toss=True)


def _head_shake_keys(r_start, r_end, angle_deg, is_neck=False, freq=2.2):
    """Subtle rotational head shake (incredulity / skepticism / disagreement)."""
    factor = 0.55 if is_neck else 0.45
    val = angle_deg * factor
    r_dur = r_end - r_start
    n = max(6, int(r_dur * freq * 4.0))
    keys = [(r_start, 0.0)]
    for i in range(1, n):
        t_rel = (i / n) * r_dur
        v = val * math.sin(2.0 * math.pi * freq * t_rel)
        keys.append((round(r_start + t_rel, 3), round(v, 3)))
    keys.append((r_end, 0.0))
    return sorted(list(dict.fromkeys(keys)), key=lambda kv: kv[0])


def _clavicle_keys(r_start, r_end, angle_deg, offset=0.0):
    """Clavicular elevation / retraction / shrug with organic rise and viscoelastic settle."""
    r_dur = r_end - r_start
    t0 = r_start + max(0.0, offset)
    t_in = min(r_end - 0.15, t0 + min(0.35, r_dur * 0.25))
    t_out = max(t_in + 0.10, r_end - min(0.30, r_dur * 0.20))
    return [
        (r_start, 0.0),
        (t0, 0.0),
        (t_in, angle_deg),
        (t_out, angle_deg),
        (r_end, 0.0)
    ]


def _head_ramp_keys(r_start, r_end, val, offset=0.0):
    """Head rotation in degrees: smooth ease-in, hold, smooth ease-out back to 0."""
    return _cervical_distributed_keys(r_start, r_end, val, is_neck=False, offset=offset)


def _nod_keys(r_start, r_end, val, count=3):
    """Nodding in pitch degrees across head and cervical chain."""
    r_dur = r_end - r_start
    step = r_dur / max(1, count)
    keys = [(r_start, 0.0)]
    for i in range(count):
        t0 = r_start + i * step
        keys.append((round(t0 + step * 0.35, 3), round(val * 0.45, 3)))
        keys.append((round(t0 + step * 0.70, 3), round(val * -0.10, 3)))
        keys.append((round(t0 + step, 3), 0.0))
    return keys


def _flutter_keys(r_start, r_end, val=0.85):
    """
    Cognitive double micro-blink (eyelid flutter):
    Two rapid blinks (~50ms down, ~60ms up, 40ms separation, 60ms down, 90ms up)
    placed near the lead-in of the revision range. Total duration ~300ms.
    """
    r_dur = r_end - r_start
    t_base = r_start + min(0.12, r_dur * 0.1)
    k1_start = t_base
    k1_peak  = min(r_end, t_base + 0.05)
    k1_end   = min(r_end, t_base + 0.11)

    k2_start = min(r_end, k1_end + 0.04)
    k2_peak  = min(r_end, k2_start + 0.06)
    k2_end   = min(r_end, k2_start + 0.15)

    keys = [
        (r_start, 0.0),
        (k1_start, 0.0),
        (k1_peak, val * 0.90),
        (k1_end, 0.0),
        (k2_start, 0.0),
        (k2_peak, val),
        (k2_end, 0.0),
        (r_end, 0.0)
    ]
    unique_keys = []
    seen = set()
    for t, v in sorted(keys, key=lambda x: x[0]):
        rt = round(t, 4)
        if rt not in seen and t <= r_end:
            seen.add(rt)
            unique_keys.append((t, v))
    return unique_keys


def _ramp_keys(r_start, r_end, val, offset=0.0, is_eye_roll=False, is_quick_glance=False, is_slow_glance=False, is_compound_saccade=False, is_high_status=False):
    """
    Biological gaze shift: fast saccadic burst (80-100ms), discrete dramatic fixation hold,
    and smooth recovery back to neutral conversational target.
    Eliminates the 'sticky gaze' bug where eyes remain frozen in the socket corner for seconds.
    Glance and roll durations dynamically adjust to directorial intent and emotional subtext:
    - Compound cognitive saccade: 3-stage dynamic curve (burst -> search hold -> sharp snapback)
    - Triangular eye-scanning: subtle horizontal shifts (+-0.035) during high-status lingering holds
    - Quick glance / dart / return: 0.35s - 0.65s hold, fast 160ms return
    - Standard look-away / collection of thought: 0.7s - 1.3s hold, smooth 220ms return
    - Slow / lingering / deliberate glance: 1.4s - 2.2s hold, measured 350ms return
    - Eye roll: rapid 650-850ms arc (or ~1.1s if slow/dramatic), returning cleanly to center.
    """
    r_dur = r_end - r_start
    if r_dur < 0.6:
        return [(r_start, 0.0), (r_start + r_dur * 0.4, val), (r_start + r_dur * 0.8, 0.0), (r_end, 0.0)]

    if is_compound_saccade:
        # 3-Stage Dynamic Cognitive Saccade:
        # Stage 1: Fast initial off-axis saccadic break (80-100ms)
        # Stage 2: Downcast / cognitive search fixation with organic micro-drift
        # Stage 3: Sharp saccadic snapback (100-140ms) locking back onto target
        t0 = r_start + (offset if offset > 0 else 0.05)
        t_peak = t0 + 0.09
        hold_dur = min(0.80, max(0.40, r_dur * 0.35))
        t_hold_end = t_peak + hold_dur
        t_snap = min(r_end, t_hold_end + 0.12)

        keys = [(r_start, 0.0), (t0, 0.0), (t_peak, val)]
        drift_span = t_hold_end - t_peak
        if drift_span > 0.25:
            n_steps = max(1, int(drift_span / 0.20))
            dt = drift_span / (n_steps + 1)
            for i in range(1, n_steps + 1):
                tk = t_peak + i * dt
                drift = 0.02 * math.sin(2.0 * math.pi * 2.5 * (tk - t_peak))
                keys.append((tk, max(0.0, min(1.0, val + drift))))
        keys.append((t_hold_end, val))
        keys.append((t_snap, 0.0))
        if t_snap < r_end:
            keys.append((r_end, 0.0))
        seen = set()
        clean = []
        for t, v in sorted(keys, key=lambda kv: kv[0]):
            rt = round(t, 4)
            if rt not in seen and t <= r_end:
                seen.add(rt)
                clean.append((t, v))
        return clean

    if is_eye_roll:
        # Rapid ocular arc: 300ms to peak, 150ms crest, 300ms drop back to neutral
        roll_dur = min(1.10 if is_slow_glance else 0.80, r_dur * 0.45)
        t_lead = min(0.25, max(0.0, offset) if offset > 0 else 0.12 * r_dur)
        t0 = r_start + t_lead
        t_peak = t0 + roll_dur * 0.45
        t_end = min(r_end, t0 + roll_dur)
        return [(r_start, 0.0), (t0, 0.0), (t_peak, val), (t_end, 0.0), (r_end, 0.0)]

    # Saccade onset
    if offset < 0.0:
        t0 = r_start
    else:
        lead = min(max(0.0, 0.12 * r_dur + offset), r_dur * 0.35)
        t0 = r_start + lead
    t1 = min(t0 + 0.10, r_end - 0.35)

    # Discrete dramatic hold duration based on emotional intent
    if is_quick_glance:
        hold_dur = min(0.65, max(0.35, (r_end - t1) * 0.25))
        recovery_dur = 0.16
    elif is_slow_glance:
        hold_dur = min(2.20, max(1.20, (r_end - t1) * 0.50))
        recovery_dur = 0.35
    else:
        hold_dur = min(1.30, max(0.50, (r_end - t1) * 0.35))
        recovery_dur = 0.22

    t2 = t1 + hold_dur
    t3 = min(r_end - 0.05, t2 + recovery_dur)  # Smooth recovery to center

    keys = [(r_start, 0.0), (t0, 0.0), (t1, val)]

    # Organic fixational micro-drift or lingering saccadic eye-scanning
    drift_span = t2 - t1
    if drift_span > 0.30:
        if is_high_status:
            # Triangular dominance scanning between interlocutor's eyes (+-0.035 every ~0.30s)
            scan_step = 0.30
            n_scans = max(2, int(drift_span / scan_step))
            for i in range(1, n_scans + 1):
                tk = t1 + i * scan_step
                scan_dir = 0.035 if (i % 2 == 1) else -0.035
                keys.append((round(tk, 3), round(max(0.0, min(1.0, val + scan_dir)), 3)))
        else:
            step_dur = 0.24
            n_steps = max(1, int(drift_span / step_dur))
            actual_step = drift_span / (n_steps + 1)
            for i in range(1, n_steps + 1):
                tk = t1 + i * actual_step
                t_rel = tk - t1
                drift = 0.02 * math.sin(2.0 * math.pi * 2.0 * t_rel)
                keys.append((tk, max(0.0, min(1.0, val + drift))))

    keys.append((t2, val))
    keys.append((t3, 0.0))
    if t3 < r_end:
        keys.append((r_end, 0.0))

    # Remove duplicates and sort
    seen = set()
    unique = []
    for k in sorted(keys, key=lambda kv: kv[0]):
        rk = round(k[0], 4)
        if rk not in seen:
            seen.add(rk)
            unique.append((k[0], k[1]))
    return unique


def _oscillation_keys(r_start, r_end, val, freq=8.0):
    """Micro-tremor: 8 Hz, 8x oversampled, phase-locked to range start, faded ends."""
    r_dur = r_end - r_start
    n = max(8, int(r_dur * freq * 8.0))
    fade = min(0.15, r_dur * 0.25)
    keys = []
    for i in range(n):
        t_rel = (i / (n - 1)) * r_dur
        env = 1.0 if fade <= 0 else min(1.0, t_rel / fade, (r_dur - t_rel) / fade)
        v = val * 0.5 * (1.0 - math.cos(2.0 * math.pi * freq * t_rel)) * env
        keys.append((r_start + t_rel, v))
    return keys


def _generate_keys(pattern, r_start, r_end, val, blink_count, offset, direction_text="", curve_name=""):
    d_lower = (direction_text or "").lower()
    c_lower = (curve_name or "").lower()
    is_eye_roll = "roll" in d_lower and "eye" in d_lower
    is_quick_glance = any(w in d_lower for w in ("quick", "brief", "dart", "glance", "starting position", "return", "scrubbed", "flick"))
    is_slow_glance = any(w in d_lower for w in ("slow", "linger", "deliberat", "ponder", "measure"))
    is_compound_saccade = any(w in d_lower for w in ("hesitat", "search", "calculat", "before answer", "look away", "turns away", "aversion"))
    is_masseter_tension = any(w in d_lower for w in ("clench", "fury", "anger", "suppress", "tight", "jaw")) and any(k in c_lower for k in ("jawclench", "mouthlipspress", "mouthpress"))
    is_high_status = any(w in d_lower for w in ("defian", "smug", "insolent", "arrogant", "proud", "deadpan"))

    if pattern == "PULSE":
        return _pulse_keys(r_start, r_end, val, blink_count)
    if pattern == "FLUTTER":
        return _flutter_keys(r_start, r_end, val)
    if pattern == "HOLD":
        if "clavicle" in c_lower:
            return _clavicle_keys(r_start, r_end, val * 3.5, offset=offset)
        return _hold_keys(r_start, r_end, val, is_masseter_tension=is_masseter_tension, is_high_status=is_high_status, curve_name=curve_name, direction_text=direction_text)
    if pattern == "HEAD_SWITCH":
        return _head_switch_keys(r_start, r_end)
    if pattern == "HEAD_RAMP":
        return _head_ramp_keys(r_start, r_end, val, offset)
    if pattern == "HEAD_PITCH_DOWN":
        return _cervical_distributed_keys(r_start, r_end, val * 14.0, is_neck=("neck" in c_lower), offset=offset)
    if pattern == "HEAD_PITCH_UP":
        return _cervical_distributed_keys(r_start, r_end, -val * 12.0, is_neck=("neck" in c_lower), offset=offset)
    if pattern == "HEAD_TILT":
        return _cervical_distributed_keys(r_start, r_end, val * 8.0, is_neck=("neck" in c_lower), offset=offset)
    if pattern == "HEAD_WARMTH":
        return _cervical_distributed_keys(r_start, r_end, val * 6.0, is_neck=("neck" in c_lower), offset=offset)
    if pattern == "HEAD_LEFT":
        return _cervical_distributed_keys(r_start, r_end, -val * 16.0, is_neck=("neck" in c_lower), offset=offset)
    if pattern == "HEAD_RIGHT":
        return _cervical_distributed_keys(r_start, r_end, val * 16.0, is_neck=("neck" in c_lower), offset=offset)
    if pattern == "HEAD_CONTEMPT":
        return _cervical_distributed_keys(r_start, r_end, val * 14.0, is_neck=("neck" in c_lower), offset=offset, onset_dur=0.55)
    if pattern == "HEAD_TOSS":
        return _head_toss_keys(r_start, r_end, val * 15.0, is_neck=("neck" in c_lower))
    if pattern == "HEAD_COCKED":
        return _cervical_distributed_keys(r_start, r_end, val * 9.0, is_neck=("neck" in c_lower), offset=offset)
    if pattern == "HEAD_HANG":
        return _cervical_distributed_keys(r_start, r_end, val * 16.0, is_neck=("neck" in c_lower), offset=offset, onset_dur=0.60)
    if pattern == "HEAD_SHAKE":
        return _head_shake_keys(r_start, r_end, val * 8.0, is_neck=("neck" in c_lower))
    if pattern == "HEAD_RECOIL":
        return _cervical_distributed_keys(r_start, r_end, -val * 6.0, is_neck=("neck" in c_lower), onset_dur=0.15)
    if pattern == "HEAD_STARTLE":
        return _cervical_distributed_keys(r_start, r_end, -val * 12.0, is_neck=("neck" in c_lower), onset_dur=0.12)
    if pattern == "HEAD_LOCK":
        return [(r_start, 0.0), (r_end, 0.0)]
    if pattern == "NOD":
        return _nod_keys(r_start, r_end, val * 6.0, blink_count if blink_count > 0 else 3)
    if pattern == "RAMP":
        if "clavicle" in c_lower:
            return _clavicle_keys(r_start, r_end, val * 4.0, offset=offset)
        return _ramp_keys(r_start, r_end, val, offset, is_eye_roll=is_eye_roll,
                          is_quick_glance=is_quick_glance, is_slow_glance=is_slow_glance,
                          is_compound_saccade=is_compound_saccade, is_high_status=is_high_status)
    if pattern == "OSCILLATION":
        return _oscillation_keys(r_start, r_end, val)
    return []


# ------------------------------------------------------------------------------
# Plan execution
# ------------------------------------------------------------------------------

# Lower-face articulators that fight against speech visemes / jaw movement during dialogue
LOWER_FACE_SPEECH_ARTICULATORS = (
    "mouthcornerdepress", "mouthfrown", "mouthsmile", "mouthcornerpull",
    "mouthsharpcornerpull", "mouthlipspress", "mouthpress", "jawchinraise",
    "chinraised", "mouthupperup", "mouthlowerlipdepress"
)
SPEECH_HEADROOM_CEILING = 0.35

# In affective sorrow/melancholy/guilt, downward ocular rotation must remain subtle (0.28)
# so the eyeballs do not roll into the floor and drag the upper eyelids into complete closure.
AFFECTIVE_GAZE_DOWN_CEILING = 0.28
AFFECTIVE_SQUINT_CEILING = 0.30


def _apply_hemifacial_asymmetry(ops, seed_key="take", direction_text=""):
    """
    Applies calibrated ±5-10% hemifacial micro-asymmetry across bilateral left/right paired RigLogic curves.
    Real somatic grief, suppressed rage, and smiles exhibit subtle left-right asymmetry.
    Eliminates synthetic digital symmetry while strictly preserving intentional unilateral cues
    (smirks, sneers, unilateral brow cocks).
    """
    import hashlib
    curve_names = list(ops.keys())
    paired = []
    seen = set()

    for c in curve_names:
        if c in seen:
            continue
        cl = c.lower()
        partner = None
        if c.endswith("L"):
            candidate = c[:-1] + "R"
            if candidate in ops:
                partner = candidate
        elif c.endswith("R"):
            candidate = c[:-1] + "L"
            if candidate in ops:
                partner = candidate
        elif cl.endswith("_l"):
            candidate = c[:-2] + "_r"
            if candidate in ops:
                partner = candidate
        elif cl.endswith("_r"):
            candidate = c[:-2] + "_l"
            if candidate in ops:
                partner = candidate

        if partner and partner not in seen:
            c_l = c if (c.endswith("L") or cl.endswith("_l")) else partner
            c_r = partner if c_l == c else c
            paired.append((c_l, c_r))
            seen.add(c_l)
            seen.add(c_r)

    h_val = int(hashlib.md5(f"{seed_key}_{direction_text}".encode("utf-8")).hexdigest(), 16)

    for c_l, c_r in paired:
        # Ocular gaze rotation (look left/right/up/down) is bi-directionally locked by conjugate oculomotor innervation (Hering's Law).
        # Only facial muscular blendshapes (brows, cheeks, mouth, jaw) exhibit hemifacial asymmetry.
        if any(g in c_l.lower() for g in ("lookleft", "lookright", "lookup", "lookdown", "eyelook", "pupil")):
            continue

        pattern_l, val_l, offset_l, count_l = ops[c_l]
        pattern_r, val_r, offset_r, count_r = ops[c_r]

        # Only apply asymmetry if both curves are actively engaged (non-zero)
        # and roughly equal in weight (i.e. bilateral expression, not intentional unilateral suppression)
        if val_l > 0.05 and val_r > 0.05 and abs(val_l - val_r) <= 0.12:
            # Calibrated delta: 4.5% up on one side, 4.5% down on the other (net ~9% asymmetry delta)
            side = 1 if ((h_val % 2) == 0) else -1
            delta = 0.045
            new_val_l = _soft_knee_saturate(val_l * (1.0 + side * delta))
            new_val_r = _soft_knee_saturate(val_r * (1.0 - side * delta))

            # Enforce headroom ceiling for lower face speech articulators
            if any(art in c_l.lower() for art in LOWER_FACE_SPEECH_ARTICULATORS):
                new_val_l = min(new_val_l, SPEECH_HEADROOM_CEILING)
            if any(art in c_r.lower() for art in LOWER_FACE_SPEECH_ARTICULATORS):
                new_val_r = min(new_val_r, SPEECH_HEADROOM_CEILING)

            ops[c_l] = (pattern_l, round(new_val_l, 4), offset_l, count_l)
            ops[c_r] = (pattern_r, round(new_val_r, 4), offset_r, count_r)
            h_val //= 2


def _fuzzy_resolve_behavior(behavior, description="", direction_text=""):
    """
    Fuzzy semantic behavior resolver. Maps non-canonical or composite SLM behavior IDs
    and free-text descriptions onto (pattern, curve_group).
    """
    text = f"{behavior} {description} {direction_text}".lower().replace("_", " ")

    # 1. Gaze directions
    if any(k in text for k in ("look left", "glance left", "gaze left", "turn left")):
        return ("RAMP", "gaze_left")
    if any(k in text for k in ("look right", "glance right", "gaze right", "turn right")):
        return ("RAMP", "gaze_right")
    if any(k in text for k in ("look down", "glance down", "gaze down", "downcast", "drop gaze", "look downward")):
        return ("RAMP", "gaze_down")
    if any(k in text for k in ("look up", "glance up", "gaze up", "upward gaze")):
        return ("RAMP", "gaze_up")

    # 2. Blinks & Gaze
    if any(k in text for k in ("blink", "flutter", "eyelid flutter", "winks")):
        return ("PULSE", "blink")
    if any(k in text for k in ("close eyes", "sustained eye closure", "shut eyes")):
        return ("HOLD", "blink")

    # 3. Anger, Fury, Clench, Tension
    if any(k in text for k in ("clench", "masseter", "jaw tight", "teeth grind", "bite jaw", "jaw lock")):
        return ("HOLD", "jaw_tension")
    if any(k in text for k in ("fury", "rage", "fuming", "hostil", "glare", "wrath", "seeth", "livid", "anger", "angry")):
        return ("HOLD", "jaw_tension")

    # 4. Brow dynamics
    if any(k in text for k in ("brow cock", "arch brow", "eyebrow raise outer", "one brow")):
        return ("HOLD", "brow_cock")
    if any(k in text for k in ("brow knot", "furrow", "knit brow", "brow lower", "brow down", "corrugator")):
        return ("HOLD", "brow")
    if any(k in text for k in ("brow raise", "wide eyes", "startle", "surprise", "shock", "wonder")):
        return ("HOLD", "surprise")

    # 5. Eye narrowing / Squint
    if any(k in text for k in ("squint", "narrow eye", "scrutiny", "peer", "predatory", "suspicio")):
        return ("HOLD", "squint")

    # 6. Smirk / Smug / Contempt / Disgust
    if any(k in text for k in ("smirk", "smug", "sneer", "contempt", "mock", "deris")):
        return ("HOLD", "smugness")
    if any(k in text for k in ("disgust", "revolt", "nausea", "gross")):
        return ("HOLD", "disgust")

    # 7. Smiles / Joy / Warmth
    if any(k in text for k in ("smile", "grin", "happy", "beam", "warmth", "cheer", "glad")):
        return ("HOLD", "smile")

    # 8. Sadness / Pain / Upset
    if any(k in text for k in ("sad", "sorrow", "grief", "melancholy", "tears", "mourn", "heartbreak")):
        return ("HOLD", "sadness")
    if any(k in text for k in ("frown", "pout", "displeasure")):
        return ("HOLD", "frown")
    if any(k in text for k in ("pain", "wince", "grimace", "hurt", "agony")):
        return ("HOLD", "pain")
    if any(k in text for k in ("upset", "distress", "anguish")):
        return ("HOLD", "upset")

    # 9. Tremor / Oscillation
    if any(k in text for k in ("tremor", "tremble", "quiver", "shiver", "jitter", "twitch", "spasm")):
        return ("OSCILLATION", "tremor")

    # 10. Exhaustion / Droop
    if any(k in text for k in ("exhaust", "weary", "fatigue", "droop", "sleepy", "drowsy")):
        return ("HOLD", "exhaustion")

    return None


def _curve_ops_from_plan(plan, existing_curve_names):
    """
    Maps plan instructions to per-curve operations {curve_name: (pattern, val, offset)}.
    First instruction wins on curve conflicts (plan lists primary intent first).
    Enforces the Speech Headroom Ceiling on lower-face curves during dialogue.
    """
    ops = {}
    direction_text = plan.get("direction_text", "")
    blink_count = _parse_blink_count(direction_text)

    for inst in plan.get("instructions", []):
        behavior = inst.get("behavior_id", "")
        weight = float(inst.get("weight", 0.0))
        offset = float(inst.get("timing_offset_seconds", 0.0))
        desc = inst.get("description", "")

        if inst.get("preserve_original", False) or weight <= 0.0:
            unreal.log(f"MHPD: '{behavior}' locked/zero-weight - preserved original")
            continue

        # A sigh/emotion may expand into parser-generated torso instructions.
        # Those must not enter this face/head/neck workflow, including via fuzzy
        # fallback mapping based on the shared direction text.
        if (inst.get("channel") in {"body_posture", "gesture"}
                or behavior in BODY_POSTURE_BEHAVIORS or behavior in GESTURE_BEHAVIORS):
            unreal.log(f"MHPD: '{behavior}' omitted from face/head/neck take")
            continue

        # ------------------------------------------------------------------
        # Channel Routing: Head, Cervical Spine, Clavicles, Body Posture
        # ------------------------------------------------------------------
        mapping = BEHAVIOR_TO_PATTERN.get(behavior)
        if not mapping:
            mapping = _fuzzy_resolve_behavior(behavior, desc, direction_text)
            if mapping:
                unreal.log(f"MHPD: Fuzzy resolved '{behavior}' -> pattern '{mapping[0]}', group '{mapping[1]}'")
            else:
                if behavior in GESTURE_BEHAVIORS:
                    unreal.log(f"MHPD: '{behavior}' is a limb gesture behavior - handled by Kimodo body motion engine")
                elif behavior in TIMING_AND_PAUSE_BEHAVIORS:
                    unreal.log(f"MHPD: '{behavior}' is a timing/pause behavior - handled by pre-speech lead/Sequencer")
                else:
                    unreal.log(f"MHPD: '{behavior}' has no curve mapping - skipped")
                continue

        safe_weight = _soft_knee_saturate(weight)
        pattern, group = mapping

        # Directed head/neck motion is authored once on the cervical skeletal
        # track by C++. Preserve captured face curves instead of adding a second
        # procedural head solver input that can disagree with the shared pose.
        if behavior in HEAD_MOVEMENT_BEHAVIORS:
            unreal.log(f"MHPD: '{behavior}' routed to synchronized cervical animation")
            continue

        for curve_name in _resolve_group(group, existing_curve_names):
            if curve_name in ops:
                unreal.log_warning(f"MHPD: '{behavior}' also targets '{curve_name}' - keeping earlier instruction")
                continue

            target_weight = safe_weight
            cl = curve_name.lower()
            if any(art in cl for art in LOWER_FACE_SPEECH_ARTICULATORS):
                # Clamp to speech headroom ceiling to give the speech viseme solver
                # 0.65 headroom to articulate syllables without open-mouthed grimaces
                target_weight = min(target_weight, SPEECH_HEADROOM_CEILING)

            if "lookdown" in cl and behavior in ("express_sadness", "express_guilt", "express_shame", "express_exhaustion"):
                target_weight = min(target_weight, AFFECTIVE_GAZE_DOWN_CEILING)

            if "squint" in cl:
                target_weight = min(target_weight, AFFECTIVE_SQUINT_CEILING)

            ops[curve_name] = (pattern, target_weight, offset, blink_count)

        positive_states = ("express_smile", "express_happy", "express_warmth", "express_serenity", "express_relief", "express_gratitude", "express_pride")
        negative_states = ("express_sadness", "express_frown", "express_upset", "express_pain", "express_fear", "express_frustration", "express_contempt")
        anger_states = (
            "tight_jaw_micro_tension", "brow_lower_lip_press", "clench_jaw", "jaw_clench",
            "masseter_lock_nostril_flare", "express_anger", "express_rage", "express_frustration",
            "express_annoyance"
        )
        is_anger_directive = (behavior in anger_states) or any(w in direction_text.lower() for w in (
            "anger", "angry", "fury", "clench", "rage", "hostil", "fuming", "wrath", "livid", "seeth"
        )) or any(w in desc.lower() for w in ("anger", "fury", "clench", "rage", "hostil", "glare"))

        if is_anger_directive:
            # Active suppression of opposing upper-face & positive expression curves:
            # Inhibits Frontalis (brow raise / horizontal forehead lines), wide eyes (AU 5), and smile curves
            # so the Corrugator / Glabella furrow (AU 4/9) and predatory eye narrowing (AU 6/7) dominate cleanly.
            for suppress_token in ("browraisein", "browraiseouter", "browraise", "eyewiden", "mouthsmile", "mouthcornerpull", "mouthsharpcornerpull"):
                for curve_name in existing_curve_names:
                    if suppress_token in curve_name.lower():
                        ops[curve_name] = ("HOLD", 0.0, offset, blink_count)

            # Active Biomechanical Co-Activation for Anger / Suppressed Hostility:
            # Engage Corrugator (AU4 brow down), Orbicularis Oculi (AU7 inner squint), Procerus (AU9 nose wrinkle),
            # and Masseter (AU24/26 jaw clench) so the upper face and jaw are visibly tensioned, not frozen.
            anger_coactivation = [
                ("brow", "HOLD", max(0.45, safe_weight * 0.75)),
                ("squint", "HOLD", max(0.35, safe_weight * 0.55)),
                ("jaw_tension", "HOLD", max(0.40, safe_weight * 0.80)),
            ]
            for co_group, co_pattern, co_weight in anger_coactivation:
                for c_name in _resolve_group(co_group, existing_curve_names):
                    if c_name not in ops:
                        c_cl = c_name.lower()
                        c_wt = co_weight
                        if any(art in c_cl for art in LOWER_FACE_SPEECH_ARTICULATORS):
                            c_wt = min(c_wt, SPEECH_HEADROOM_CEILING)
                        ops[c_name] = (co_pattern, round(c_wt, 4), offset, blink_count)

        if behavior in positive_states:
            # Suppress conflicting brow furrow, mouth frown, and pain markers
            for suppress_group in ("brow", "sadness", "frown", "pain", "upset"):
                for curve_name in _resolve_group(suppress_group, existing_curve_names):
                    cl = curve_name.lower()
                    if any(token in cl for token in ("frown", "depress", "browlower", "browdown", "upperup")):
                        ops[curve_name] = ("HOLD", 0.0, offset, blink_count)

        elif behavior in negative_states:
            # Suppress conflicting smile, cheek raise, and mouth corner pull curves
            for suppress_group in ("smile", "happy", "warmth", "serenity"):
                for curve_name in _resolve_group(suppress_group, existing_curve_names):
                    cl = curve_name.lower()
                    if any(token in cl for token in ("smile", "cornerpull", "cheekraise")):
                        ops[curve_name] = ("HOLD", 0.0, offset, blink_count)

        asymmetric_smug = ("express_smugness", "asymmetric_smug_lip_corner", "suppressed_tell_micro_smirk")
        if behavior in asymmetric_smug:
            # Actively suppress contralateral (right-side) smile & corner pull
            # to prevent pre-existing baseline smile keys from turning a smirk into a bilateral grin
            for suppress_token in ("mouthsmiler", "mouthsmile_r", "mouthcornerpullr", "mouthsharpcornerpullr", "browraiseouterr", "browraiseinr"):
                for curve_name in existing_curve_names:
                    if suppress_token in curve_name.lower():
                        ops[curve_name] = ("HOLD", 0.0, offset, blink_count)

        elif behavior == "unilateral_brow_cock":
            # Suppress left brow raising so only the right brow arches prominently
            for suppress_token in ("browraiseouterl", "browraiseinl"):
                for curve_name in existing_curve_names:
                    if suppress_token in curve_name.lower():
                        ops[curve_name] = ("HOLD", 0.0, offset, blink_count)

        elif behavior in ("unilateral_canine_sneer", "subtle_snarl_asymmetric_brow"):
            # Suppress contralateral upper lip lift
            for suppress_token in ("mouthupperupr", "nosewrinkler"):
                for curve_name in existing_curve_names:
                    if suppress_token in curve_name.lower():
                        ops[curve_name] = ("HOLD", 0.0, offset, blink_count)

    _apply_hemifacial_asymmetry(ops, seed_key=plan.get("plan_id", "take"), direction_text=direction_text)
    return ops


def parse_pattern_and_targets(direction_text, existing_curve_names):
    """
    LEGACY fallback when no plan file is provided (e.g. direct console use).
    Word-boundary matching so 'holds his gaze' / 'looks closely' can't
    false-trigger eye closure.
    """
    d = (direction_text or "").lower().strip()

    def has(p):
        return re.search(p, d) is not None

    if has(r"\b(eyes?|eyelids?)\b") and has(r"\b(close[sd]?|closing|shut(s|ting)?)\b"):
        return "HOLD", _resolve_group("blink", existing_curve_names), 1.0

    if has(r"\b(look(s|ing|ed)?|gaz(e|es|ing)|glanc(e|es|ed|ing))\b"):
        for word, group in (("left", "gaze_left"), ("right", "gaze_right"),
                            ("up", "gaze_up"), ("down", "gaze_down"), ("away", "gaze_left")):
            if has(rf"\b{word}\b"):
                return "RAMP", _resolve_group(group, existing_curve_names), 0.85

    if has(r"\b(surpris|shock|startl)\w*"):
        return "HOLD", _resolve_group("surprise", existing_curve_names), 0.85

    if has(r"\b(disgust|revolt|gross)\w*"):
        return "HOLD", _resolve_group("disgust", existing_curve_names), 0.85

    if has(r"\b(clench|jaw tension|jaw clench)\b"):
        return "HOLD", _resolve_group("jaw_tension", existing_curve_names), 0.75

    if (has(r"\b(upset|distressed|distress|hurt|holding back tears)\b")):
        return "HOLD", _resolve_group("upset", existing_curve_names), 0.85

    if (has(r"\b(frown|frowns|frowning|knit\w* brows?|furrow\w* brows?)\b")):
        return "HOLD", _resolve_group("frown", existing_curve_names), 0.85

    if has(r"\b(sad|sadness|sorrow|grief|heartbrok|unhappy|downcast|melancholy|mourn)\w*"):
        return "HOLD", _resolve_group("sadness", existing_curve_names), 0.85

    if has(r"\b(happy|joy|joyful|cheerful|elated)\w*"):
        return "HOLD", _resolve_group("happy", existing_curve_names), 0.85

    if has(r"\b(smile|smiling|grin|grinning|beam)\w*"):
        return "HOLD", _resolve_group("smile", existing_curve_names), 0.85

    if has(r"\b(trembl|jitter|quiver|shiver|shak)\w*"):
        return "OSCILLATION", _resolve_group("tremor", existing_curve_names), 0.35

    return "PULSE", _resolve_group("blink", existing_curve_names), 1.0


def _set_float_curve_keys(anim_sequence, curve_name, times, values):
    """Replace a complete float-key buffer with one controller notification."""
    if len(times) != len(values):
        raise ValueError("Curve times and values must have matching lengths")
    curve_id = unreal.AnimationCurveIdentifier()
    curve_id.set_curve_identifier(curve_name, unreal.RawCurveTrackTypes.RCT_FLOAT)
    keys = [unreal.RichCurveKey(time=float(t), value=float(v))
            for t, v in zip(times, values)]
    if not anim_sequence.controller.set_curve_keys(curve_id, keys, False):
        raise RuntimeError(f"Could not replace curve '{curve_name}'")


def _merge_breathing_window(times, values, generated, start, end):
    """Keep outside keys and blend the respiratory overlay to baseline at boundaries."""
    original = sorted(zip(times, values))

    def baseline_at(t):
        if not original:
            return 0.0
        if t <= original[0][0]:
            return float(original[0][1])
        for (a, va), (b, vb) in zip(original, original[1:]):
            if t <= b:
                return float(va + (vb - va) * (t - a) / (b - a)) if b > a else float(vb)
        return float(original[-1][1])

    fade = min(0.25, (end - start) / 2.0)
    merged = [(float(t), float(v)) for t, v in original if t < start or t > end]
    for t, value in generated:
        alpha = min(1.0, max(0.0, (t - start) / fade), max(0.0, (end - t) / fade)) if fade > 0 else 0.0
        alpha = alpha * alpha * (3.0 - 2.0 * alpha)
        merged.append((t, baseline_at(t) + alpha * value))
    merged.extend([(start, baseline_at(start)), (end, baseline_at(end))])
    return sorted(dict(merged).items())


def create_acting_take(baseline_anim_path, take_name, output_dir, blink_count=4,
                       range_start=0.0, range_end=0.0, gaze_shift=False,
                       direction_text="", plan_path=""):
    """
    Duplicates baseline AnimSequence and bakes the performance plan onto its curves.
    """
    take_started = time.perf_counter()
    unreal.log(f"MHPD: Loading baseline AnimSequence: {baseline_anim_path}")
    baseline_anim = unreal.EditorAssetLibrary.load_asset(baseline_anim_path)

    if not baseline_anim:
        unreal.log_error(f"MHPD: Failed to load baseline AnimSequence at: {baseline_anim_path}")
        return None

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    # Destination asset path
    new_anim_path = f"{output_dir}/{take_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(new_anim_path):
        unreal.EditorAssetLibrary.delete_asset(new_anim_path)

    duplicate_started = time.perf_counter()
    duplicated_anim = asset_tools.duplicate_asset(take_name, output_dir, baseline_anim)
    if not duplicated_anim:
        unreal.log_error(f"MHPD: Failed to duplicate baseline anim to {new_anim_path}")
        return None

    unreal.log(f"MHPD TIMING duplicate: {time.perf_counter() - duplicate_started:.3f}s")
    seq_length = unreal.AnimationLibrary.get_sequence_length(duplicated_anim)

    # Respect range_start / range_end if provided
    r_start = range_start if (range_start > 0 and range_start < seq_length) else 0.0
    r_end   = range_end   if (range_end > r_start and range_end <= seq_length) else seq_length

    # Introspect existing curves to find RigLogic curve names
    existing_curve_names = [str(n) for n in unreal.AnimationLibrary.get_animation_curve_names(
        duplicated_anim, unreal.RawCurveTrackTypes.RCT_FLOAT
    )]

    # ------------------------------------------------------------------
    # Build per-curve operations from the plan (single interpreter), or
    # fall back to legacy direction-text parsing without a plan file.
    # ------------------------------------------------------------------
    ops = {}
    plan_loaded = False
    plan_dict = {}
    if plan_path and os.path.exists(plan_path):
        try:
            with open(plan_path, "r", encoding="utf-8") as f:
                plan_dict = json.load(f)
            ops = _curve_ops_from_plan(plan_dict, existing_curve_names)
            plan_loaded = True
            unreal.log(f"MHPD: Executing plan {plan_dict.get('plan_id', '?')} - {len(ops)} curve op(s)")
        except Exception as e:
            unreal.log_warning(f"MHPD: Failed to read plan '{plan_path}': {e} - falling back to direction text")

    if not plan_loaded and not ops and direction_text:
        pattern, targets, val = parse_pattern_and_targets(direction_text, existing_curve_names)
        count = _parse_blink_count(direction_text, blink_count)
        safe_val = _soft_knee_saturate(val)
        for curve in targets:
            c_val = min(safe_val, SPEECH_HEADROOM_CEILING) if any(art in curve.lower() for art in LOWER_FACE_SPEECH_ARTICULATORS) else safe_val
            cl = curve.lower()
            if "lookdown" in cl:
                c_val = min(c_val, AFFECTIVE_GAZE_DOWN_CEILING)
            if "squint" in cl:
                c_val = min(c_val, AFFECTIVE_SQUINT_CEILING)
            ops[curve] = (pattern, c_val, 0.0, count)
        _apply_hemifacial_asymmetry(ops, seed_key="legacy", direction_text=direction_text)
        unreal.log(f"MHPD: Legacy parse -> pattern '{pattern}' on {targets}")

    if not ops:
        unreal.log_warning("MHPD: No curve operations produced - take will be an unmodified duplicate")

    combined_dir_text = direction_text
    if plan_loaded and plan_dict.get("direction_text"):
        combined_dir_text = f"{direction_text} {plan_dict.get('direction_text', '')}".strip()

    # ------------------------------------------------------------------
    # Bake: keep solver keys outside the revision range, director owns inside
    # ------------------------------------------------------------------
    curve_started = time.perf_counter()
    controller = duplicated_anim.controller
    controller.open_bracket("MHPD acting take curve edits", False)
    try:
        for curve_name, (pattern, val, offset, count) in ops.items():
            try:
                curve_exists = curve_name in existing_curve_names

                bake_start = max(0.0, r_start + offset) if offset < 0.0 else r_start

                merged = []
                times, values = [], []
                if curve_exists:
                    times, values = unreal.AnimationLibrary.get_float_keys(duplicated_anim, curve_name)
                    merged = [(float(t), float(v)) for t, v in zip(times, values)
                              if t < bake_start or t > r_end]

                generated = _generate_keys(pattern, bake_start, r_end, val, count, offset, direction_text=combined_dir_text, curve_name=curve_name)
                merged.extend(generated)
                merged.sort(key=lambda kv: kv[0])

                # Rebuild curve
                if curve_exists:
                    unreal.AnimationLibrary.remove_curve(duplicated_anim, curve_name)
                unreal.AnimationLibrary.add_curve(duplicated_anim, curve_name)
                _set_float_curve_keys(
                    duplicated_anim, curve_name,
                    [kv[0] for kv in merged], [kv[1] for kv in merged]
                )
                unreal.log(f"MHPD: Rebuilt '{curve_name}' [{pattern}, val {val:.2f}] ({len(merged)} keys)")
            except Exception as e:
                unreal.log_warning(f"MHPD: Exception keying '{curve_name}': {e}")

        # ------------------------------------------------------------------
        # Autonomic Poisson Blink Engine:
        # Only inject blinks across the active slice or if whole take is directed
        # ------------------------------------------------------------------
        has_explicit_blinks = any("eyeblink" in c.lower() for c in ops.keys())
        if not has_explicit_blinks and (r_end - r_start) > 3.0:
            blink_curves = _resolve_group("blink", existing_curve_names)
            is_high_tension = any(w in combined_dir_text.lower() for w in (
                "anger", "angry", "fury", "clench", "rage", "hostil", "fuming", "wrath", "livid", "seeth", "intense", "focus"
            ))

            min_interval = 5.5 if is_high_tension else 3.2
            max_interval = 7.5 if is_high_tension else 5.2

            seed_val = int(hashlib.md5(take_name.encode("utf-8")).hexdigest()[:8], 16)
            cur_t = r_start + 1.2 + ((seed_val % 100) / 100.0) * 1.5
            blink_times = []
            step_idx = 0
            while cur_t < (r_end - 0.5):
                blink_times.append(cur_t)
                pseudo_rand = ((seed_val * (step_idx + 13) + 71) % 1000) / 1000.0
                cur_t += min_interval + pseudo_rand * (max_interval - min_interval)
                step_idx += 1

            if blink_times:
                autonomic_keys = []
                for bt in blink_times:
                    t_close = bt
                    t_peak = min(r_end, bt + 0.045)
                    t_ease = min(r_end, bt + 0.110)
                    t_open = min(r_end, bt + 0.180)
                    blink_val = 0.90 + (((seed_val + int(bt * 10)) % 15) / 100.0)
                    autonomic_keys += [
                        (t_close, 0.0),
                        (t_peak, blink_val),
                        (t_ease, blink_val * 0.35),
                        (t_open, 0.0)
                    ]

                autonomic_keys.sort(key=lambda kv: kv[0])

                for bc in blink_curves:
                    try:
                        c_exists = bc in existing_curve_names
                        merged_blink = []
                        if c_exists:
                            t_k, v_k = unreal.AnimationLibrary.get_float_keys(duplicated_anim, bc)
                            for tk, vk in zip(t_k, v_k):
                                tk_f = float(tk)
                                if not any(abs(tk_f - bt) < 0.22 for bt in blink_times):
                                    merged_blink.append((tk_f, float(vk)))
                        merged_blink.extend(autonomic_keys)
                        merged_blink.sort(key=lambda kv: kv[0])

                        seen = set()
                        clean_b = []
                        for tk, vk in merged_blink:
                            rtk = round(tk, 4)
                            if rtk not in seen:
                                seen.add(rtk)
                                clean_b.append((tk, vk))

                        if c_exists:
                            unreal.AnimationLibrary.remove_curve(duplicated_anim, bc)
                        unreal.AnimationLibrary.add_curve(duplicated_anim, bc)
                        _set_float_curve_keys(
                            duplicated_anim, bc,
                            [k[0] for k in clean_b], [k[1] for k in clean_b]
                        )
                    except Exception as e:
                        unreal.log_warning(f"MHPD: Exception injecting autonomic blinks on '{bc}': {e}")

        # Only settle phonetic mouth curves if this take covers through the tail end of the sequence
        if r_end >= (seq_length - 0.5):
            settle_mouth_curves(duplicated_anim, exclude_curves=set(ops.keys()))

        # Synthesize physiological pre-speech lead (anticipatory breath & tension)
        prep_offset_ms = float(plan_dict.get("preparation_offset_ms", 250.0)) if plan_loaded else 250.0
        _inject_prespeech_lead(
            duplicated_anim, existing_curve_names, r_start, r_end,
            prep_offset_ms=prep_offset_ms, direction_text=combined_dir_text,
            exclude_curves=set(ops.keys())
        )

        # Face/head/neck takes must not synthesize chest or clavicle motion.
        # Facial sigh and pre-speech mouth/jaw behavior are handled above;
        # existing non-facial curves in the duplicated baseline are preserved.

    finally:
        controller.close_bracket(False)
    unreal.log(f"MHPD TIMING curve edits: {time.perf_counter() - curve_started:.3f}s")

    # Save the modified take AnimSequence once at the very end
    save_started = time.perf_counter()
    unreal.EditorAssetLibrary.save_loaded_asset(duplicated_anim)
    unreal.log(f"MHPD TIMING save: {time.perf_counter() - save_started:.3f}s; total: {time.perf_counter() - take_started:.3f}s")
    unreal.log(f"MHPD SUCCESS: Saved acting take: {new_anim_path}")
    return new_anim_path


def _inject_autonomic_breathing(anim_sequence, existing_curve_names, seq_length,
                                direction_text="", exclude_curves=None, range_start=0.0):
    """
    Autonomic Diaphragmatic & Clavicular Respiration Engine:
    Injects a continuous organic respiratory rhythm (0.20-0.25 Hz ≈ 12-15 breaths/min)
    across chest expansion and bilateral clavicular micro-elevation.
    Eliminates completely rigid upper-torso / shoulder deadness during dialogue holds.
    """
    duration = seq_length - range_start
    if not anim_sequence or duration < 1.0:
        return

    excluded = {c.lower() for c in (exclude_curves or set())}
    d_lower = (direction_text or "").lower()

    # Dynamic respiratory rate & depth based on physiological arousal
    is_agitated = any(w in d_lower for w in ("anger", "angry", "fury", "panic", "fear", "frustrat", "breathless"))
    is_exhausted = any(w in d_lower for w in ("exhaust", "weary", "sigh", "deflate", "sorrow", "grief"))

    resp_freq = 0.32 if is_agitated else (0.18 if is_exhausted else 0.22)
    chest_depth = 0.14 if is_agitated else (0.06 if is_exhausted else 0.09)
    clavicle_depth = 1.60 if is_agitated else (0.60 if is_exhausted else 1.00)

    # Resolve target curves
    chest_curves = _resolve_group("chest_breathing", existing_curve_names)
    clavicle_curves = _resolve_group("clavicle_both", existing_curve_names)

    # Sample keys across duration (10 samples per second)
    n_samples = max(10, int(duration * 10))
    dt = duration / n_samples

    time_samples = [range_start + i * dt for i in range(n_samples + 1)]

    # 1. Chest Expansion
    for cc in chest_curves:
        if cc.lower() in excluded:
            continue
        try:
            keys = []
            for t in time_samples:
                phase = 2.0 * math.pi * resp_freq * t
                # Asymmetric respiratory waveform: faster inhalation (40%), longer passive exhalation (60%)
                v = chest_depth * 0.5 * (1.0 - math.cos(phase))
                keys.append((round(t, 3), round(max(0.0, min(1.0, v)), 4)))

            c_exists = cc in existing_curve_names
            original_times, original_values = unreal.AnimationLibrary.get_float_keys(anim_sequence, cc) if c_exists else ([], [])
            keys = _merge_breathing_window(original_times, original_values, keys, range_start, seq_length)
            if c_exists:
                unreal.AnimationLibrary.remove_curve(anim_sequence, cc)
            unreal.AnimationLibrary.add_curve(anim_sequence, cc)
            _set_float_curve_keys(
                anim_sequence, cc,
                [k[0] for k in keys], [k[1] for k in keys]
            )
            unreal.log(f"MHPD: Injected autonomic diaphragm respiration on '{cc}' ({resp_freq:.2f} Hz)")
        except Exception as e:
            unreal.log_warning(f"MHPD: Exception injecting chest respiration: {e}")

    # 2. Clavicle Micro-Elevation
    for clvc in clavicle_curves:
        if clvc.lower() in excluded:
            continue
        try:
            is_right = clvc.endswith("R") or "clavicle_r" in clvc.lower()
            side_mult = 0.90 if is_right else 1.05  # subtle bilateral micro-asymmetry
            clv_keys = []
            for t in time_samples:
                phase = 2.0 * math.pi * resp_freq * t - 0.15  # 150ms phase lag behind diaphragm
                v = clavicle_depth * side_mult * 0.5 * (1.0 - math.cos(phase))
                clv_keys.append((round(t, 3), round(max(0.0, v), 3)))

            c_exists = clvc in existing_curve_names
            original_times, original_values = unreal.AnimationLibrary.get_float_keys(anim_sequence, clvc) if c_exists else ([], [])
            clv_keys = _merge_breathing_window(original_times, original_values, clv_keys, range_start, seq_length)
            if c_exists:
                unreal.AnimationLibrary.remove_curve(anim_sequence, clvc)
            unreal.AnimationLibrary.add_curve(anim_sequence, clvc)
            _set_float_curve_keys(
                anim_sequence, clvc,
                [k[0] for k in clv_keys], [k[1] for k in clv_keys]
            )
            unreal.log(f"MHPD: Injected autonomic clavicular respiration on '{clvc}'")
        except Exception as e:
            unreal.log_warning(f"MHPD: Exception injecting clavicular respiration: {e}")


def _inject_prespeech_lead(anim_sequence, existing_curve_names, r_start, r_end,
                           prep_offset_ms=250.0, direction_text="", exclude_curves=None):
    """
    Synthesizes physiological pre-speech preparation:
    1. Anticipatory breath inhalation: soft lip-parting (jawOpen ~0.07-0.08) leading into speech phonemes.
    2. Anticipatory masseter tension: subtle jaw clench (jawClenchL/R ~0.40-0.45) holding during the pre-beat
       and releasing right as speech articulates (for anger, threat, interrogation, suppression, tension).
    """
    if not anim_sequence:
        return

    excluded = {c.lower() for c in (exclude_curves or set())}

    lead_sec = max(0.18, min(0.60, float(prep_offset_ms) / 1000.0))
    speech_onset = r_start if r_start > 0.05 else 0.0

    jaw_open_curve = next((c for c in existing_curve_names if "jawopen" in c.lower() or "jaw_open" in c.lower()), None)
    if not jaw_open_curve:
        jaw_open_curve = "CTRL_expressions_jawOpen"

    # If r_start <= 0.05, detect when mouth first begins opening for speech in baseline
    if speech_onset <= 0.05 and jaw_open_curve in existing_curve_names:
        try:
            times, values = unreal.AnimationLibrary.get_float_keys(anim_sequence, jaw_open_curve)
            for t, v in zip(times, values):
                if v >= 0.05 and t <= 2.5:
                    speech_onset = float(t)
                    break
        except Exception:
            pass

    # If dialogue begins immediately (< 0.10s), skip pre-speech breath lead
    # to protect audio-visual phoneme sync and prevent lips locking closed
    if speech_onset < 0.10:
        unreal.log(f"MHPD: Dialogue articulates immediately ({speech_onset:.2f}s); skipping pre-speech breath injection to preserve lip-sync alignment.")
        return

    breath_start = max(0.0, speech_onset - lead_sec)
    breath_peak = breath_start + (speech_onset - breath_start) * 0.60

    # 1. Anticipatory Breath Inhalation on jawOpen
    if jaw_open_curve.lower() not in excluded:
        try:
            curve_exists = jaw_open_curve in existing_curve_names
            raw_keys = []
            if curve_exists:
                t_keys, v_keys = unreal.AnimationLibrary.get_float_keys(anim_sequence, jaw_open_curve)
                raw_keys = [(float(t), float(v)) for t, v in zip(t_keys, v_keys)]

            # Preserve speech phoneme keys at and after speech_onset
            speech_keys = [(t, v) for t, v in raw_keys if t >= speech_onset]
            val_at_onset = speech_keys[0][1] if speech_keys else 0.04

            # Synthetic breath curve: closed lips -> soft parting (0.075) -> blend to speech onset
            breath_keys = [
                (breath_start, 0.0),
                (breath_peak, 0.075),
                (speech_onset, max(0.05, val_at_onset))
            ]
            if breath_start > 0.0:
                breath_keys.insert(0, (0.0, 0.0))

            merged = breath_keys + speech_keys
            seen = set()
            clean_keys = []
            for t, v in sorted(merged, key=lambda kv: kv[0]):
                rt = round(t, 4)
                if rt not in seen:
                    seen.add(rt)
                    clean_keys.append((t, v))

            if curve_exists:
                unreal.AnimationLibrary.remove_curve(anim_sequence, jaw_open_curve)
            unreal.AnimationLibrary.add_curve(anim_sequence, jaw_open_curve)
            _set_float_curve_keys(
                anim_sequence, jaw_open_curve,
                [k[0] for k in clean_keys], [k[1] for k in clean_keys]
            )
            unreal.log(f"MHPD: Synthesized pre-speech breath lead-in on '{jaw_open_curve}' ({breath_start:.2f}s -> {speech_onset:.2f}s)")
        except Exception as e:
            unreal.log_warning(f"MHPD: Exception injecting breath lead-in: {e}")

    # 2. Anticipatory Masseter Tension (jaw clench)
    d_lower = (direction_text or "").lower()
    needs_tension = any(w in d_lower for w in (
        "clench", "anger", "angry", "grit", "rigid", "suppress", "threat", "interrogat",
        "tension", "tight", "fury", "cold", "intimidat", "firm", "lock", "strain"
    ))

    if needs_tension:
        clench_candidates = []
        c_left = next((c for c in existing_curve_names if "jawclenchl" in c.lower() or "jawclench_l" in c.lower()), "CTRL_expressions_jawClenchL")
        c_right = next((c for c in existing_curve_names if "jawclenchr" in c.lower() or "jawclench_r" in c.lower()), "CTRL_expressions_jawClenchR")
        clench_candidates.extend([c_left, c_right])

        for clench_curve in clench_candidates:
            try:
                curve_exists = clench_curve in existing_curve_names
                raw_keys = []
                if curve_exists:
                    t_keys, v_keys = unreal.AnimationLibrary.get_float_keys(anim_sequence, clench_curve)
                    raw_keys = [(float(t), float(v)) for t, v in zip(t_keys, v_keys)]

                post_keys = [(t, v) for t, v in raw_keys if t >= speech_onset]
                onset_val = post_keys[0][1] if post_keys else 0.25

                tension_keys = [
                    (breath_start, 0.0),
                    (breath_start + (speech_onset - breath_start) * 0.40, 0.65),
                    (speech_onset, max(0.20, onset_val))
                ]
                if breath_start > 0.0:
                    tension_keys.insert(0, (0.0, 0.0))

                merged = tension_keys + post_keys
                seen = set()
                clean_keys = []
                for t, v in sorted(merged, key=lambda kv: kv[0]):
                    rt = round(t, 4)
                    if rt not in seen:
                        seen.add(rt)
                        clean_keys.append((t, v))

                if curve_exists:
                    unreal.AnimationLibrary.remove_curve(anim_sequence, clench_curve)
                unreal.AnimationLibrary.add_curve(anim_sequence, clench_curve)
                _set_float_curve_keys(
                    anim_sequence, clench_curve,
                    [k[0] for k in clean_keys], [k[1] for k in clean_keys]
                )
                unreal.log(f"MHPD: Synthesized anticipatory jaw tension on '{clench_curve}' ({breath_start:.2f}s -> {speech_onset:.2f}s)")
            except Exception as e:
                unreal.log_warning(f"MHPD: Exception injecting jaw tension: {e}")


def settle_mouth_curves(anim_sequence, settle_duration=0.40, lead_in_duration=0.20, exclude_curves=None):
    """
    Ensures phonetic speech/mouth-opening RigLogic curves cleanly ease in and
    settle to 0.0 (closed mouth rest pose) at the end of speech, avoiding open-mouth freezes.
    NEVER touches expressive acting curves (smiles, frowning, corner pulls, cheek raises,
    jaw clenching) or any curves explicitly keyed by the performance plan.
    """
    if not anim_sequence:
        return
    seq_length = unreal.AnimationLibrary.get_sequence_length(anim_sequence)
    if seq_length <= (settle_duration + lead_in_duration):
        return

    settle_start = max(0.0, seq_length - settle_duration)
    all_curves = [str(n) for n in unreal.AnimationLibrary.get_animation_curve_names(
        anim_sequence, unreal.RawCurveTrackTypes.RCT_FLOAT
    )]

    excluded_set = {c.lower() for c in (exclude_curves or [])}

    # Only target speech opening and phonetic articulator curves
    phonetic_keywords = (
        "jawopen", "jaw_open", "jawfwd", "jaw_fwd",
        "mouthfunnel", "mouthpucker", "mouthrollupper", "mouthrolllower",
        "mouthshrugupper", "mouthshruglower", "mouthclose",
        "mouthlowerdown"
    )

    # Strictly protect expressive and directorial curves
    protected_keywords = (
        "smile", "cornerpull", "frown", "cheekraise", "squint",
        "brow", "jawclench", "mouthpress", "dimple", "stretch", "pupil"
    )

    for curve_name in all_curves:
        cl = curve_name.lower()
        if cl in excluded_set or any(exc in cl for exc in excluded_set):
            continue
        if any(pk in cl for pk in protected_keywords):
            continue
        if any(k in cl for k in phonetic_keywords):
            times, values = unreal.AnimationLibrary.get_float_keys(anim_sequence, curve_name)
            if not times:
                continue

            raw_keys = [(float(t), float(v)) for t, v in zip(times, values)]
            raw_keys.sort(key=lambda kv: kv[0])

            # Keep keys between lead-in and settle
            middle_keys = [(t, v) for t, v in raw_keys if t >= lead_in_duration and t < settle_start]

            # Build lead-in keys (closed mouth at t=0, easing in)
            lead_in_val = 0.0
            for t, v in raw_keys:
                if t >= lead_in_duration:
                    lead_in_val = v
                    break

            new_keys = [(0.0, 0.0)]
            if abs(lead_in_val) > 0.005:
                new_keys.append((lead_in_duration * 0.5, lead_in_val * 0.35))
            new_keys.extend(middle_keys)

            # Sample value at settle_start
            val_at_settle = 0.0
            for t, v in raw_keys:
                if t <= settle_start:
                    val_at_settle = v

            if abs(val_at_settle) > 0.005:
                mid_time = settle_start + settle_duration * 0.45
                new_keys.append((mid_time, val_at_settle * 0.30))
                pre_end = settle_start + settle_duration * 0.85
                new_keys.append((pre_end, 0.0))

            # Flat zero hold at end of sequence
            new_keys.append((seq_length, 0.0))
            new_keys.sort(key=lambda kv: kv[0])

            unreal.AnimationLibrary.remove_curve(anim_sequence, curve_name)
            unreal.AnimationLibrary.add_curve(anim_sequence, curve_name)
            _set_float_curve_keys(
                anim_sequence,
                curve_name,
                [k[0] for k in new_keys],
                [k[1] for k in new_keys]
            )
    unreal.log(f"MHPD: Successfully settled phonetic mouth curves to closed rest pose on '{anim_sequence.get_name()}'")


def import_motion_asset(file_path: str, destination_path: str = "/Game/MHPD/BodyLibrary", skeleton_path: str = None) -> dict:
    """Import a BVH/FBX animation file into Unreal Engine Content Browser."""
    try:
        import unreal
    except ImportError:
        return {"ok": False, "error": "unreal module not found"}

    file_path = os.path.abspath(file_path)
    if not os.path.exists(file_path):
        return {"ok": False, "error": f"File does not exist: {file_path}"}

    from pathlib import Path
    raw_name = Path(file_path).stem
    asset_name = re.sub(r'[^a-zA-Z0-9_]', '_', raw_name)
    if not asset_name or asset_name[0].isdigit():
        asset_name = f"Motion_{asset_name}"

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

    task = unreal.AssetImportTask()
    task.filename = file_path
    task.destination_path = destination_path
    task.destination_name = asset_name
    task.replace_existing = True
    task.automated = True
    task.save = True

    if skeleton_path:
        skeleton_asset = unreal.EditorAssetLibrary.load_asset(skeleton_path)
        if skeleton_asset:
            factory = unreal.FbxFactory()
            factory.import_ui.skeleton = skeleton_asset
            factory.import_ui.b_import_animations = True
            task.factory = factory

    asset_tools.import_asset_tasks([task])

    expected_asset_path = f"{destination_path}/{asset_name}"
    imported_asset = unreal.EditorAssetLibrary.load_asset(expected_asset_path)
    if imported_asset is None:
        unreal.log_warning(f"MHPD: Automated asset import could not verify asset at {expected_asset_path}")
        return {"ok": False, "error": f"Asset import failed for {file_path}"}

    unreal.log(f"MHPD: Successfully imported animation '{asset_name}' into {destination_path}")
    return {
        "ok": True,
        "asset_path": expected_asset_path,
        "asset_name": asset_name,
        "asset_class": imported_asset.get_class().get_name()
    }


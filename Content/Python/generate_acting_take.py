# Copyright (c) 2026 David Cobbins / Frontier Mindworks. All Rights Reserved.
# MetaHuman Performance Director (MHPD) — Architected & Developed by David Cobbins.

import unreal
import os
import re
import math
import json

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
    "masseter_lock_nostril_flare":     ("HOLD",        "jaw_tension"),
    "micro_grimace_wince":             ("HOLD",        "pain"),
    "slack_jaw_wonder":                ("HOLD",        "wonder"),

    # 5. Facial Expression - Autonomic Pupillometry
    "pupil_dilation":                  ("HOLD",        "pupil_dilate"),
    "pupil_constriction":              ("HOLD",        "pupil_constrict"),

    # 6. Gaze Channel
    "sustained_direct_eye_contact":          ("HOLD",        "blink"),
    "avoidant_gaze_then_recover":            ("RAMP",        "gaze_left"),
    "brief_gaze_break_before_answer":        ("RAMP",        "gaze_left"),
    "downward_glance_then_reluctant_return": ("RAMP",        "gaze_down"),
    "wide_eye_fixed_stare":                  ("HOLD",        "surprise"),
    "gaze_shift_left":                       ("RAMP",        "gaze_left"),
    "gaze_shift_right":                      ("RAMP",        "gaze_right"),
    "gaze_shift_up":                         ("RAMP",        "gaze_up"),
    "gaze_shift_down":                       ("RAMP",        "gaze_down"),
    "controlled_eye_contact_change":         ("RAMP",        "gaze_down"),
    "rapid_eye_roll_rejection":              ("RAMP",        "gaze_up"),
    "slow_dramatic_eye_roll":                ("RAMP",        "gaze_up"),
    "triangular_intimacy_gaze":              ("RAMP",        "gaze_left"),
    "darting_saccadic_scanning":             ("OSCILLATION", "gaze_left"),
    "unfocused_daydream_stare":              ("HOLD",        "daydreaming"),
    "intense_scrutiny_squint_gaze":          ("HOLD",        "squint"),
    "reluctant_upward_confession_gaze":      ("RAMP",        "gaze_up"),
    "averted_downward_submission":           ("RAMP",        "gaze_down"),

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
        (("headyaw", "head_yaw"), "HeadYaw"),
    ],
    "head_pitch": [
        (("headpitch", "head_pitch"), "HeadPitch"),
    ],
    "head_roll": [
        (("headroll", "head_roll"), "HeadRoll"),
    ],
    "head_switch": [
        (("headcontrolswitch", "head_control_switch", "headcontrol"), "HeadControlSwitch"),
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
    """Periodic blinks: 80ms close, 120ms open, count clamped to range."""
    r_dur = r_end - r_start
    count = max(1, min(count, max(1, int(r_dur / 0.35))))
    step = r_dur / (count + 1)
    keys = []
    for i in range(count):
        t_close = r_start + (i + 1) * step
        keys += [(t_close, 0.0),
                 (min(r_end, t_close + 0.08), val),
                 (min(r_end, t_close + 0.20), 0.0)]
    return keys


def _hold_keys(r_start, r_end, val):
    """
    Sustained affective state with biological breathing micro-modulation.
    Prevents rigid static mannequins by adding subtle natural breathing dynamics (~0.4 Hz).
    """
    r_dur = r_end - r_start
    if r_dur < 0.4:
        return [(r_start, 0.0), (r_start + r_dur * 0.5, val), (r_end, 0.0)]

    t_in = min(r_end, r_start + 0.12)
    t_out = max(t_in, r_end - 0.15)

    keys = [(r_start, 0.0), (t_in, val)]
    sustain_dur = t_out - t_in
    if sustain_dur > 1.2:
        n_steps = max(2, int(sustain_dur / 0.80))
        step_dt = sustain_dur / (n_steps + 1)
        for i in range(1, n_steps + 1):
            tk = t_in + i * step_dt
            t_rel = tk - t_in
            mod = 0.03 * math.sin(2.0 * math.pi * 0.4 * t_rel)
            keys.append((round(tk, 3), round(max(0.0, min(1.0, val + mod)), 3)))

    keys.append((round(t_out, 3), val))
    keys.append((round(r_end, 3), 0.0))
    return sorted(keys, key=lambda kv: kv[0])


def _head_switch_keys(r_start, r_end):
    """Activates procedural HeadControlSwitch: 40ms ramp to 1.0, hold, 40ms ramp down."""
    t_in = min(r_end, r_start + 0.04)
    t_out = max(t_in, r_end - 0.04)
    return [(r_start, 0.0), (t_in, 1.0), (t_out, 1.0), (r_end, 0.0)]


def _head_ramp_keys(r_start, r_end, val, offset=0.0):
    """Head rotation in degrees: smooth ease-in, hold, smooth ease-out back to 0."""
    r_dur = r_end - r_start
    if r_dur < 0.6:
        return [(r_start, 0.0), (r_start + r_dur * 0.5, val), (r_end, 0.0)]
    lead = min(0.35, r_dur * 0.2)
    trail = min(0.45, r_dur * 0.25)
    t0 = r_start
    t1 = r_start + lead
    t2 = r_end - trail
    t3 = r_end
    return [(t0, 0.0), (t1, val), (t2, val), (t3, 0.0)]


def _nod_keys(r_start, r_end, val, count=3):
    """Nodding in pitch degrees."""
    r_dur = r_end - r_start
    step = r_dur / max(1, count)
    keys = [(r_start, 0.0)]
    for i in range(count):
        t0 = r_start + i * step
        keys.append((t0 + step * 0.35, val))
        keys.append((t0 + step * 0.70, val * -0.2))
        keys.append((t0 + step, 0.0))
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


def _ramp_keys(r_start, r_end, val, offset=0.0, is_eye_roll=False, is_quick_glance=False, is_slow_glance=False):
    """
    Biological gaze shift: fast saccadic burst (80-100ms), discrete dramatic fixation hold,
    and smooth recovery back to neutral conversational target.
    Eliminates the 'sticky gaze' bug where eyes remain frozen in the socket corner for seconds.
    Glance and roll durations dynamically adjust to directorial intent and emotional subtext:
    - Quick glance / dart / return: 0.35s - 0.65s hold, fast 160ms return
    - Standard look-away / collection of thought: 0.7s - 1.3s hold, smooth 220ms return
    - Slow / lingering / deliberate glance: 1.4s - 2.2s hold, measured 350ms return
    - Eye roll: rapid 650-850ms arc (or ~1.1s if slow/dramatic), returning cleanly to center.
    """
    r_dur = r_end - r_start
    if r_dur < 0.6:
        return [(r_start, 0.0), (r_start + r_dur * 0.4, val), (r_start + r_dur * 0.8, 0.0), (r_end, 0.0)]

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

    # Organic fixational micro-drift during sustained hold
    drift_span = t2 - t1
    if drift_span > 0.30:
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


def _generate_keys(pattern, r_start, r_end, val, blink_count, offset, direction_text=""):
    d_lower = (direction_text or "").lower()
    is_eye_roll = "roll" in d_lower and "eye" in d_lower
    is_quick_glance = any(w in d_lower for w in ("quick", "brief", "dart", "glance", "starting position", "return", "scrubbed", "flick"))
    is_slow_glance = any(w in d_lower for w in ("slow", "linger", "deliberat", "hesitat", "calculat", "ponder", "measure"))
    if pattern == "PULSE":
        return _pulse_keys(r_start, r_end, val, blink_count)
    if pattern == "FLUTTER":
        return _flutter_keys(r_start, r_end, val)
    if pattern == "HOLD":
        return _hold_keys(r_start, r_end, val)
    if pattern == "HEAD_SWITCH":
        return _head_switch_keys(r_start, r_end)
    if pattern == "HEAD_RAMP":
        return _head_ramp_keys(r_start, r_end, val, offset)
    if pattern == "NOD":
        return _nod_keys(r_start, r_end, val, blink_count if blink_count > 0 else 3)
    if pattern == "RAMP":
        return _ramp_keys(r_start, r_end, val, offset, is_eye_roll=is_eye_roll,
                          is_quick_glance=is_quick_glance, is_slow_glance=is_slow_glance)
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

        if inst.get("preserve_original", False) or weight <= 0.0:
            unreal.log(f"MHPD: '{behavior}' locked/zero-weight - preserved original")
            continue

        # ------------------------------------------------------------------
        # Channel Routing: Head, Body Posture, Gesture, Timing
        # ------------------------------------------------------------------
        if behavior in HEAD_MOVEMENT_BEHAVIORS:
            unreal.log(f"MHPD: '{behavior}' is driven by MetaHuman_ControlRig on BodyComponent - facial curves preserved")
            continue

        if behavior in BODY_POSTURE_BEHAVIORS:
            unreal.log(f"MHPD: '{behavior}' is a body posture behavior - handled by Sequencer body track")
            continue

        if behavior in GESTURE_BEHAVIORS:
            unreal.log(f"MHPD: '{behavior}' is a gesture behavior - handled by Sequencer body track")
            continue

        if behavior in TIMING_AND_PAUSE_BEHAVIORS:
            unreal.log(f"MHPD: '{behavior}' is a timing/pause behavior - handled by pre-speech lead/Sequencer")
            continue

        mapping = BEHAVIOR_TO_PATTERN.get(behavior)
        if not mapping:
            unreal.log(f"MHPD: '{behavior}' has no facial/gaze curve mapping - skipped")
            continue

        safe_weight = _soft_knee_saturate(weight)
        pattern, group = mapping
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


def create_acting_take(baseline_anim_path, take_name, output_dir, blink_count=4,
                       range_start=0.0, range_end=0.0, gaze_shift=False,
                       direction_text="", plan_path=""):
    """
    Duplicates baseline AnimSequence and bakes the performance plan onto its curves.
    """
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

    duplicated_anim = asset_tools.duplicate_asset(take_name, output_dir, baseline_anim)
    if not duplicated_anim:
        unreal.log_error(f"MHPD: Failed to duplicate baseline anim to {new_anim_path}")
        return None

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
        unreal.log(f"MHPD: Legacy parse -> pattern '{pattern}' on {targets}")

    if not ops:
        unreal.log_warning("MHPD: No curve operations produced - take will be an unmodified duplicate")

    combined_dir_text = direction_text
    if plan_loaded and plan_dict.get("direction_text"):
        combined_dir_text = f"{direction_text} {plan_dict.get('direction_text', '')}".strip()

    # ------------------------------------------------------------------
    # Bake: keep solver keys outside the revision range, director owns inside
    # ------------------------------------------------------------------
    for curve_name, (pattern, val, offset, count) in ops.items():
        try:
            curve_exists = curve_name in existing_curve_names

            bake_start = max(0.0, r_start + offset) if offset < 0.0 else r_start

            merged = []
            if curve_exists:
                times, values = unreal.AnimationLibrary.get_float_keys(duplicated_anim, curve_name)
                merged = [(float(t), float(v)) for t, v in zip(times, values)
                          if t < bake_start or t > r_end]

            merged.extend(_generate_keys(pattern, bake_start, r_end, val, count, offset, direction_text=combined_dir_text))
            merged.sort(key=lambda kv: kv[0])

            # Rebuild curve
            if curve_exists:
                unreal.AnimationLibrary.remove_curve(duplicated_anim, curve_name)
            unreal.AnimationLibrary.add_curve(duplicated_anim, curve_name)
            unreal.AnimationLibrary.add_float_curve_keys(
                duplicated_anim, curve_name,
                [kv[0] for kv in merged], [kv[1] for kv in merged]
            )
            unreal.log(f"MHPD: Rebuilt '{curve_name}' [{pattern}, val {val:.2f}] ({len(merged)} keys)")
        except Exception as e:
            unreal.log_warning(f"MHPD: Exception keying '{curve_name}': {e}")

    # Ensure mouth/jaw curves cleanly settle to rest pose at the end of the sequence,
    # strictly protecting any curves keyed by the director's performance plan
    settle_mouth_curves(duplicated_anim, exclude_curves=set(ops.keys()))

    # Synthesize physiological pre-speech lead (anticipatory breath & tension)
    prep_offset_ms = float(plan_dict.get("preparation_offset_ms", 250.0)) if plan_loaded else 250.0
    _inject_prespeech_lead(
        duplicated_anim, existing_curve_names, r_start, r_end,
        prep_offset_ms=prep_offset_ms, direction_text=combined_dir_text,
        exclude_curves=set(ops.keys())
    )

    # Save the modified take AnimSequence
    unreal.EditorAssetLibrary.save_loaded_asset(duplicated_anim)
    unreal.log(f"MHPD SUCCESS: Saved acting take: {new_anim_path}")
    return new_anim_path


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
            unreal.AnimationLibrary.add_float_curve_keys(
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
                unreal.AnimationLibrary.add_float_curve_keys(
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
            unreal.AnimationLibrary.add_float_curve_keys(
                anim_sequence,
                curve_name,
                [k[0] for k in new_keys],
                [k[1] for k in new_keys]
            )

    unreal.EditorAssetLibrary.save_loaded_asset(anim_sequence)
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


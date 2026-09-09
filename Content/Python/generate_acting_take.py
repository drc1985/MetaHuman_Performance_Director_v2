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
BEHAVIOR_TO_PATTERN = {
    "directed_blink_pulse":            ("PULSE",       "blink"),
    "close_eyes_before_answer":        ("PULSE",       "blink"),   # legacy plans
    "sustained_eye_closure":           ("HOLD",        "blink"),
    "brief_gaze_break_before_answer":  ("RAMP",        "gaze_left"),
    "avoidant_gaze_then_recover":      ("RAMP",        "gaze_left"),
    "controlled_eye_contact_change":   ("RAMP",        "gaze_down"),
    "gaze_shift_left":                 ("RAMP",        "gaze_left"),
    "gaze_shift_right":                ("RAMP",        "gaze_right"),
    "gaze_shift_up":                   ("RAMP",        "gaze_up"),
    "gaze_shift_down":                 ("RAMP",        "gaze_down"),
    "micro_tremor":                    ("OSCILLATION", "tremor"),
    "subtle_eye_tension_masked_smile": ("HOLD",        "squint"),
    "masked_expression_leak":          ("HOLD",        "squint"),
    "tight_jaw_micro_tension":         ("HOLD",        "jaw_tension"),
    "brow_lower_lip_press":            ("HOLD",        "brow"),
    "subtle_expression_shift":         ("HOLD",        "squint"),
    "express_surprise":                ("HOLD",        "surprise"),
    "express_disgust":                 ("HOLD",        "disgust"),
    "clench_jaw":                      ("HOLD",        "jaw_tension"),
    "express_sadness":                 ("HOLD",        "sadness"),
    "express_frown":                   ("HOLD",        "frown"),
    "express_smile":                   ("HOLD",        "smile"),
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
    "pupil_dilation":                  ("HOLD",        "pupil_dilate"),
    "pupil_constriction":              ("HOLD",        "pupil_constrict"),
    "cognitive_eye_flutter":           ("FLUTTER",     "blink"),
    "glabella_micro_tension":          ("OSCILLATION", "tremor"),
}

# Curve group -> list of ((introspection substrings), canonical fallback)
CURVE_GROUPS = {
    "blink": [
        (("eyeblinkl", "eyeblink_l"), "CTRL_expressions_eyeBlinkL"),
        (("eyeblinkr", "eyeblink_r"), "CTRL_expressions_eyeBlinkR"),
    ],
    "gaze_left": [
        (("eyelookleftl", "eyelookleft_l"), "CTRL_expressions_eyeLookLeftL"),
        (("eyelookleftr", "eyelookleft_r"), "CTRL_expressions_eyeLookRightL"),
    ],
    "gaze_right": [
        (("eyelookrightl", "eyelookright_l"), "CTRL_expressions_eyeLookRightL"),
        (("eyelookrightr", "eyelookright_r"), "CTRL_expressions_eyeLookRightR"),
    ],
    "gaze_up": [
        (("eyelookupl", "eyelookup_l"), "CTRL_expressions_eyeLookUpL"),
        (("eyelookupr", "eyelookupr_r"), "CTRL_expressions_eyeLookUpR"),
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
    ],
    "sadness": [
        (("browraiseinl", "browraisein_l"), "CTRL_expressions_browRaiseInL"),
        (("browraiseinr", "browraisein_r"), "CTRL_expressions_browRaiseInR"),
        (("browdownl", "browlowerl", "browlower_l"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr", "browlower_r"), "CTRL_expressions_browDownR"),
        (("mouthcornerdepressl", "mouthfrownl", "mouthfrown_l"), "CTRL_expressions_mouthCornerDepressL"),
        (("mouthcornerdepressr", "mouthfrownr", "mouthfrown_r"), "CTRL_expressions_mouthCornerDepressR"),
        (("mouthlowerlipdepressl",), "CTRL_expressions_mouthLowerLipDepressL"),
        (("mouthlowerlipdepressr",), "CTRL_expressions_mouthLowerLipDepressR"),
        (("jawchinraisedl", "chinraisedl"), "CTRL_expressions_jawChinRaiseDL"),
        (("jawchinraisedr", "chinraisedr"), "CTRL_expressions_jawChinRaiseDR"),
        (("eyesquintinnerl", "eyesquintinner_l"), "CTRL_expressions_eyeSquintInnerL"),
        (("eyesquintinnerr", "eyesquintinner_r"), "CTRL_expressions_eyeSquintInnerR"),
    ],
    "frown": [
        (("mouthcornerdepressl", "mouthfrownl", "mouthfrown_l"), "CTRL_expressions_mouthCornerDepressL"),
        (("mouthcornerdepressr", "mouthfrownr", "mouthfrown_r"), "CTRL_expressions_mouthCornerDepressR"),
        (("mouthlowerlipdepressl",), "CTRL_expressions_mouthLowerLipDepressL"),
        (("mouthlowerlipdepressr",), "CTRL_expressions_mouthLowerLipDepressR"),
        (("browdownl", "browlowerl", "browlower_l"), "CTRL_expressions_browDownL"),
        (("browdownr", "browlowerr", "browlower_r"), "CTRL_expressions_browDownR"),
        (("jawchinraisedl", "chinraisedl"), "CTRL_expressions_jawChinRaiseDL"),
        (("jawchinraisedr", "chinraisedr"), "CTRL_expressions_jawChinRaiseDR"),
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
    """Sustained state: 80ms ease-in, hold, 80ms ease-out."""
    t_in = min(r_end, r_start + 0.08)
    t_out = max(t_in, r_end - 0.08)
    return [(r_start, 0.0), (t_in, val), (t_out, val), (r_end, 0.0)]


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


def _ramp_keys(r_start, r_end, val, offset=0.0):
    """Gaze shift: hold, fast (saccade-speed) ramp, sustain with fixational micro-drift, ease back to zero."""
    r_dur = r_end - r_start
    if r_dur < 0.6:
        # Degenerate short range: simple out-and-back
        return [(r_start, 0.0), (r_start + r_dur * 0.5, val), (r_end, 0.0)]
    lead = min(max(0.0, 0.15 * r_dur + offset), r_dur * 0.4)
    t0 = r_start + lead                      # gaze still direct until here
    t1 = min(t0 + 0.12, r_end - 0.35)        # ~120ms saccade to target
    t3 = max(t1 + 0.05, r_end - 0.25)        # sustain, then 250ms ease back

    keys = [(r_start, 0.0), (t0, 0.0), (t1, val)]

    # Fixational micro-drift during sustained gaze hold (eliminates glass-eye mannequin stare)
    hold_dur = t3 - t1
    if hold_dur > 0.35:
        step_dur = 0.28
        n_steps = max(1, int(hold_dur / step_dur))
        actual_step = hold_dur / (n_steps + 1)
        for i in range(1, n_steps + 1):
            tk = t1 + i * actual_step
            # Organic multi-frequency micro-saccadic drift (+/- 0.025 amplitude)
            t_rel = tk - t1
            drift = 0.025 * math.sin(2.0 * math.pi * 1.8 * t_rel) * math.cos(2.0 * math.pi * 2.7 * t_rel)
            val_k = max(0.0, min(1.0, val + drift))
            keys.append((tk, val_k))

    keys.append((t3, val))
    keys.append((r_end, 0.0))
    return sorted(keys, key=lambda kv: kv[0])


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


def _generate_keys(pattern, r_start, r_end, val, blink_count, offset):
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
        return _ramp_keys(r_start, r_end, val, offset)
    if pattern == "OSCILLATION":
        return _oscillation_keys(r_start, r_end, val)
    return []


# ------------------------------------------------------------------------------
# Plan execution
# ------------------------------------------------------------------------------

def _curve_ops_from_plan(plan, existing_curve_names):
    """
    Maps plan instructions to per-curve operations {curve_name: (pattern, val, offset)}.
    First instruction wins on curve conflicts (plan lists primary intent first).
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
        # Head Movement Behaviors: Driven by MetaHuman_ControlRig on BodyComponent
        # ------------------------------------------------------------------
        # Head and cervical motion are driven procedurally by MetaHuman_ControlRig
        # on the BodyComponent binding in Sequencer (Solution 3), preserving 100% skin
        # continuity with zero collar tearing. Facial curves focus on expressions/gaze.
        if behavior in ("head_turn_left", "head_turn_right", "head_pitch_up", "head_pitch_down",
                        "head_tilt", "head_nod", "head_shake", "head_warmth_tilt"):
            unreal.log(f"MHPD: '{behavior}' is driven by MetaHuman_ControlRig on BodyComponent - facial curves preserved")
            continue

        mapping = BEHAVIOR_TO_PATTERN.get(behavior)
        if not mapping:
            unreal.log(f"MHPD: '{behavior}' has no facial curve mapping (body/timing channel) - skipped")
            continue

        safe_weight = _soft_knee_saturate(weight)
        pattern, group = mapping
        for curve_name in _resolve_group(group, existing_curve_names):
            if curve_name in ops:
                unreal.log_warning(f"MHPD: '{behavior}' also targets '{curve_name}' - keeping earlier instruction")
                continue
            ops[curve_name] = (pattern, safe_weight, offset, blink_count)

        positive_states = ("express_smile", "express_warmth", "express_serenity", "express_relief", "express_gratitude", "express_pride")
        negative_states = ("express_sadness", "express_frown", "express_pain", "express_fear", "express_frustration", "express_contempt")

        if behavior in positive_states:
            # Suppress conflicting brow furrow, mouth frown, and pain markers
            for suppress_group in ("brow", "sadness", "frown", "pain"):
                for curve_name in _resolve_group(suppress_group, existing_curve_names):
                    cl = curve_name.lower()
                    if any(token in cl for token in ("frown", "depress", "browlower", "browdown", "upperup")):
                        ops[curve_name] = ("HOLD", 0.0, offset, blink_count)

        elif behavior in negative_states:
            # Suppress conflicting smile, cheek raise, and mouth corner pull curves
            for suppress_group in ("smile", "warmth", "serenity"):
                for curve_name in _resolve_group(suppress_group, existing_curve_names):
                    cl = curve_name.lower()
                    if any(token in cl for token in ("smile", "cornerpull", "cheekraise")):
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

    if has(r"\b(frown|frowns|frowning|sad|sorrow|grief|heartbrok|unhappy|pout)\w*"):
        return "HOLD", _resolve_group("sadness", existing_curve_names), 0.85

    if has(r"\b(happy|smile|smiling|joy|pleased|warmth|grin)\w*"):
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
    if plan_path and os.path.exists(plan_path):
        try:
            with open(plan_path, "r", encoding="utf-8") as f:
                plan = json.load(f)
            ops = _curve_ops_from_plan(plan, existing_curve_names)
            plan_loaded = True
            unreal.log(f"MHPD: Executing plan {plan.get('plan_id', '?')} - {len(ops)} curve op(s)")
        except Exception as e:
            unreal.log_warning(f"MHPD: Failed to read plan '{plan_path}': {e} - falling back to direction text")

    if not plan_loaded and not ops and direction_text:
        pattern, targets, val = parse_pattern_and_targets(direction_text, existing_curve_names)
        count = _parse_blink_count(direction_text, blink_count)
        safe_val = _soft_knee_saturate(val)
        ops = {curve: (pattern, safe_val, 0.0, count) for curve in targets}
        unreal.log(f"MHPD: Legacy parse -> pattern '{pattern}' on {targets}")

    if not ops:
        unreal.log_warning("MHPD: No curve operations produced - take will be an unmodified duplicate")

    # ------------------------------------------------------------------
    # Bake: keep solver keys outside the revision range, director owns inside
    # ------------------------------------------------------------------
    for curve_name, (pattern, val, offset, count) in ops.items():
        try:
            curve_exists = curve_name in existing_curve_names

            merged = []
            if curve_exists:
                times, values = unreal.AnimationLibrary.get_float_keys(duplicated_anim, curve_name)
                merged = [(float(t), float(v)) for t, v in zip(times, values)
                          if t < r_start or t > r_end]

            merged.extend(_generate_keys(pattern, r_start, r_end, val, count, offset))
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

    # NOTE: the body-chain bake (head-follows-body) happens in C++ afterwards, in
    # BakeBodyChainIntoFaceAnim. It cannot be done here: writing bone tracks needs
    # the animation data controller, and UAnimSequenceBase::GetController() is not
    # Ensure mouth/jaw curves cleanly settle to rest pose at the end of the sequence,
    # strictly protecting any curves keyed by the director's performance plan
    settle_mouth_curves(duplicated_anim, exclude_curves=set(ops.keys()))

    # Save the modified take AnimSequence
    unreal.EditorAssetLibrary.save_loaded_asset(duplicated_anim)
    unreal.log(f"MHPD SUCCESS: Saved acting take: {new_anim_path}")
    return new_anim_path


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


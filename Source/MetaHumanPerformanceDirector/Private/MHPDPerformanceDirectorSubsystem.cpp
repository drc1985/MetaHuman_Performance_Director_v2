#include "MHPDPerformanceDirectorSubsystem.h"

#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "Internationalization/Regex.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"

namespace
{
// Word-boundary regex matching
bool ContainsPattern(const FString& Text, const TCHAR* Pattern)
{
    const FRegexPattern RegexPattern(Pattern);
    FRegexMatcher Matcher(RegexPattern, Text);
    return Matcher.FindNext();
}

FString ChannelToSchemaString(EMHPDPerformanceChannel Channel)
{
    switch (Channel)
    {
        case EMHPDPerformanceChannel::FacialExpression:
            return TEXT("facial_expression");
        case EMHPDPerformanceChannel::Gaze:
            return TEXT("gaze");
        case EMHPDPerformanceChannel::HeadMovement:
            return TEXT("head_movement");
        case EMHPDPerformanceChannel::Gesture:
            return TEXT("gesture");
        case EMHPDPerformanceChannel::BodyPosture:
            return TEXT("body_posture");
        case EMHPDPerformanceChannel::ReactionTiming:
            return TEXT("reaction_timing");
        case EMHPDPerformanceChannel::Pauses:
            return TEXT("pauses");
        case EMHPDPerformanceChannel::VoiceDelivery:
            return TEXT("voice_delivery");
        default:
            return TEXT("unknown");
    }
}

TArray<TSharedPtr<FJsonValue>> StringArrayToJson(const TArray<FString>& Values)
{
    TArray<TSharedPtr<FJsonValue>> JsonValues;
    JsonValues.Reserve(Values.Num());
    for (const FString& Value : Values)
    {
        JsonValues.Add(MakeShared<FJsonValueString>(Value));
    }
    return JsonValues;
}

// -----------------------------------------------------------------------------
// Natural Language Clause Tokenizer & Scoped Direction Parser
// -----------------------------------------------------------------------------

enum class EDirectionType : uint8
{
    None,
    Left,
    Right,
    Up,
    Down,
    Away
};

struct FDirectionMatch
{
    EDirectionType Direction = EDirectionType::None;
    int32 Position = INDEX_NONE;
};

// Splits input text into discrete semantic clauses by punctuation & conjunctions
TArray<FString> TokenizeClauses(const FString& InText)
{
    TArray<FString> RawClauses;
    InText.ParseIntoArray(RawClauses, TEXT(","), false);

    TArray<FString> PunctuationSplit;
    for (const FString& Raw : RawClauses)
    {
        TArray<FString> SubParts;
        Raw.ParseIntoArray(SubParts, TEXT("."), false);
        for (const FString& Sub : SubParts)
        {
            TArray<FString> SemiParts;
            Sub.ParseIntoArray(SemiParts, TEXT(";"), false);
            for (const FString& Semi : SemiParts)
            {
                TArray<FString> DashParts;
                Semi.ParseIntoArray(DashParts, TEXT("—"), false);
                for (const FString& Dash : DashParts)
                {
                    TArray<FString> HyphenParts;
                    Dash.ParseIntoArray(HyphenParts, TEXT("-"), false);
                    PunctuationSplit.Append(HyphenParts);
                }
            }
        }
    }

    // Split on major grammatical conjunctions: and, then, while, but, with, as, plus
    TArray<FString> FinalClauses;
    const TCHAR* Conjunctions[] = {
        TEXT(" and then "), TEXT(" and "), TEXT(" then "),
        TEXT(" while "),    TEXT(" but "), TEXT(" with "),
        TEXT(" as well as "), TEXT(" plus "), TEXT(" also ")
    };

    for (const FString& Fragment : PunctuationSplit)
    {
        TArray<FString> CurrentList;
        CurrentList.Add(Fragment);

        for (const TCHAR* Conj : Conjunctions)
        {
            TArray<FString> NextList;
            for (const FString& Item : CurrentList)
            {
                TArray<FString> SplitItems;
                Item.ParseIntoArray(SplitItems, Conj, false);
                NextList.Append(SplitItems);
            }
            CurrentList = MoveTemp(NextList);
        }

        for (FString& S : CurrentList)
        {
            S.TrimStartAndEndInline();
            if (!S.IsEmpty())
            {
                FinalClauses.Add(S);
            }
        }
    }

    if (FinalClauses.Num() == 0 && !InText.IsEmpty())
    {
        FinalClauses.Add(InText);
    }

    return FinalClauses;
}

// Scans text for explicit directional keywords and returns direction + index
FDirectionMatch FindDirectionInClause(const FString& Clause)
{
    FDirectionMatch Match;

    const bool bHasRight = ContainsPattern(Clause, TEXT("\\b(right|rightward|rightwards|to the right|towards the right|starboard)\\b"));
    const bool bHasLeft  = ContainsPattern(Clause, TEXT("\\b(left|leftward|leftwards|to the left|towards the left|port)\\b"));
    const bool bHasUp    = ContainsPattern(Clause, TEXT("\\b(up|upward|upwards|to the ceiling|sky|above|higher|chin up)\\b"));
    const bool bHasDown  = ContainsPattern(Clause, TEXT("\\b(down|downward|downwards|to the floor|ground|below|lower|chin down)\\b"));
    const bool bHasAway  = ContainsPattern(Clause, TEXT("\\b(away|aside|off|turn away|turns away|look away|looks away|averts? gaze|avert(s|ed|ing)? eyes?|break eye contact)\\b"));

    int32 EarliestPos = MAX_int32;

    auto CheckPos = [&](const TCHAR* Pattern, EDirectionType Dir)
    {
        const FRegexPattern Reg(Pattern);
        FRegexMatcher Matcher(Reg, Clause);
        if (Matcher.FindNext())
        {
            const int32 Pos = Matcher.GetMatchBeginning();
            if (Pos < EarliestPos)
            {
                EarliestPos = Pos;
                Match.Direction = Dir;
                Match.Position = Pos;
            }
        }
    };

    if (bHasRight) CheckPos(TEXT("\\b(right|rightward|rightwards|to the right|towards the right|starboard)\\b"), EDirectionType::Right);
    if (bHasLeft)  CheckPos(TEXT("\\b(left|leftward|leftwards|to the left|towards the left|port)\\b"), EDirectionType::Left);
    if (bHasUp)    CheckPos(TEXT("\\b(up|upward|upwards|to the ceiling|sky|above|higher|chin up)\\b"), EDirectionType::Up);
    if (bHasDown)  CheckPos(TEXT("\\b(down|downward|downwards|to the floor|ground|below|lower|chin down)\\b"), EDirectionType::Down);
    if (bHasAway)  CheckPos(TEXT("\\b(away|aside|off|turn away|turns away|look away|looks away|averts? gaze|avert(s|ed|ing)? eyes?|break eye contact)\\b"), EDirectionType::Away);

    return Match;
}

} // anonymous namespace

FMHPDPerformancePlan UMHPDPerformanceDirectorSubsystem::CreatePlanFromDirection(
    const FString& DirectionText,
    const FString& SourceTake,
    float Intensity,
    FMHPDRevisionRange RevisionRange,
    const TArray<FString>& LockedChannels
) const
{
    FMHPDPerformancePlan Plan;
    Plan.PlanId = FGuid::NewGuid();
    Plan.SourceTake = SourceTake;
    Plan.DirectionText = DirectionText;
    Plan.RevisionRange = RevisionRange;
    Plan.Intensity = FMath::Clamp(Intensity, 0.0f, 1.0f);
    Plan.LockedChannels = LockedChannels;

    const FString LowerDirection = DirectionText.ToLower();
    bool bMatchedIntent = false;

    // -------------------------------------------------------------------------
    // High-Level Emotional & Character State Parsing (Global Context)
    // -------------------------------------------------------------------------
    const bool bNervous = LowerDirection.Contains(TEXT("nervous"))
        || LowerDirection.Contains(TEXT("anxious"))
        || LowerDirection.Contains(TEXT("fear"))
        || LowerDirection.Contains(TEXT("afraid"))
        || LowerDirection.Contains(TEXT("pressure"));

    const bool bTryingConfidence = LowerDirection.Contains(TEXT("confident"))
        || LowerDirection.Contains(TEXT("appear calm"))
        || LowerDirection.Contains(TEXT("trying to appear"))
        || LowerDirection.Contains(TEXT("hide"))
        || LowerDirection.Contains(TEXT("hiding"));

    if (bNervous && bTryingConfidence)
    {
        Plan.MatchedInterpretations.Add(TEXT("Nervous but attempting confidence"));
        AddInstruction(Plan, EMHPDPerformanceChannel::Gaze, TEXT("brief_gaze_break_before_answer"), TEXT("Break eye contact briefly before answering, then return to direct gaze."), 0.75f, -0.15f);
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("subtle_eye_tension_masked_smile"), TEXT("Add subtle eye tension while maintaining a controlled expression."), 0.55f);
        AddInstruction(Plan, EMHPDPerformanceChannel::BodyPosture, TEXT("upright_but_tense"), TEXT("Keep posture upright while adding slight tension through shoulders and neck."), 0.5f);
        AddInstruction(Plan, EMHPDPerformanceChannel::Pauses, TEXT("short_pre_response_pause"), TEXT("Add a short pause before the answer to suggest self-control."), 0.45f, 0.2f);
        bMatchedIntent = true;
    }

    if (LowerDirection.Contains(TEXT("defensive"))
        || LowerDirection.Contains(TEXT("guarded"))
        || LowerDirection.Contains(TEXT("cornered"))
        || LowerDirection.Contains(TEXT("under attack")))
    {
        Plan.MatchedInterpretations.Add(TEXT("Defensive"));
        AddInstruction(Plan, EMHPDPerformanceChannel::BodyPosture, TEXT("closed_guarded_posture"), TEXT("Close the posture slightly and reduce exposed body language."), 0.75f);
        AddInstruction(Plan, EMHPDPerformanceChannel::Gesture, TEXT("self_protective_gesture"), TEXT("Add small self-protective or dismissive gestures."), 0.6f);
        AddInstruction(Plan, EMHPDPerformanceChannel::HeadMovement, TEXT("small_recoil_then_reset"), TEXT("Add a small head recoil before recovering composure."), 0.45f);
        AddInstruction(Plan, EMHPDPerformanceChannel::ReactionTiming, TEXT("quick_defensive_response"), TEXT("Tighten reaction timing to feel guarded and reactive."), 0.4f, -0.1f);
        bMatchedIntent = true;
    }

    if (LowerDirection.Contains(TEXT("conceal"))
        || LowerDirection.Contains(TEXT("lying"))
        || LowerDirection.Contains(TEXT("truth"))
        || LowerDirection.Contains(TEXT("hiding"))
        || LowerDirection.Contains(TEXT("missing file"))
        || LowerDirection.Contains(TEXT("information")))
    {
        Plan.MatchedInterpretations.Add(TEXT("Concealing information"));
        AddInstruction(Plan, EMHPDPerformanceChannel::Gaze, TEXT("avoidant_gaze_then_recover"), TEXT("Look away on the moment of concealment, then recover eye contact."), 0.7f);
        AddInstruction(Plan, EMHPDPerformanceChannel::Pauses, TEXT("truth_decision_pause"), TEXT("Add a micro-pause before the response, as if choosing what to reveal."), 0.6f, 0.25f);
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("masked_expression_leak"), TEXT("Keep the expression controlled with a small tension leak."), 0.5f);
        AddInstruction(Plan, EMHPDPerformanceChannel::Gesture, TEXT("reduced_hand_activity"), TEXT("Reduce hand activity to avoid over-signaling."), 0.4f);
        bMatchedIntent = true;
    }

    const bool bAnger = LowerDirection.Contains(TEXT("angry"))
        || LowerDirection.Contains(TEXT("anger"))
        || LowerDirection.Contains(TEXT("frustrated"))
        || LowerDirection.Contains(TEXT("frustration"))
        || LowerDirection.Contains(TEXT("furious"));

    const bool bRestrained = LowerDirection.Contains(TEXT("restrained"))
        || LowerDirection.Contains(TEXT("controlled"))
        || LowerDirection.Contains(TEXT("underneath"))
        || LowerDirection.Contains(TEXT("cannot openly"))
        || LowerDirection.Contains(TEXT("less obvious"))
        || LowerDirection.Contains(TEXT("subtle"))
        || LowerDirection.Contains(TEXT("smaller"));

    if (bAnger && !bRestrained)
    {
        Plan.MatchedInterpretations.Add(TEXT("Open anger"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("brow_lower_lip_press"), TEXT("Increase visible anger through lowered brows, pressed lips, and firmer jaw."), 0.85f);
        AddInstruction(Plan, EMHPDPerformanceChannel::Gaze, TEXT("sustained_direct_eye_contact"), TEXT("Hold direct eye contact during the confrontation."), 0.75f);
        AddInstruction(Plan, EMHPDPerformanceChannel::Gesture, TEXT("sharp_forward_emphasis"), TEXT("Use sharper forward gestures on emphasized beats."), 0.7f);
        AddInstruction(Plan, EMHPDPerformanceChannel::BodyPosture, TEXT("forward_assertive_posture"), TEXT("Shift posture forward with a more assertive stance."), 0.7f);
        bMatchedIntent = true;
    }

    if (bAnger && bRestrained)
    {
        Plan.MatchedInterpretations.Add(TEXT("Restrained anger"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("tight_jaw_micro_tension"), TEXT("Add contained facial tension without overt anger."), 0.55f);
        AddInstruction(Plan, EMHPDPerformanceChannel::Gesture, TEXT("reduced_gesture_amplitude"), TEXT("Reduce gesture amplitude to make the emotion feel controlled."), 0.65f);
        AddInstruction(Plan, EMHPDPerformanceChannel::BodyPosture, TEXT("held_stillness"), TEXT("Increase stillness and contained posture."), 0.6f);
        AddInstruction(Plan, EMHPDPerformanceChannel::ReactionTiming, TEXT("delayed_response_beat"), TEXT("Delay the response slightly before the controlled reply."), 0.45f, 0.25f);
        bMatchedIntent = true;
    }

    if (LowerDirection.Contains(TEXT("less theatrical"))
        || LowerDirection.Contains(TEXT("restrained"))
        || LowerDirection.Contains(TEXT("smaller"))
        || LowerDirection.Contains(TEXT("less movement"))
        || LowerDirection.Contains(TEXT("reduce")))
    {
        Plan.MatchedInterpretations.Add(TEXT("Reduced theatricality"));
        AddInstruction(Plan, EMHPDPerformanceChannel::Gesture, TEXT("minimize_broad_gestures"), TEXT("Minimize broad gestures and keep movement economical."), 0.6f);
        AddInstruction(Plan, EMHPDPerformanceChannel::HeadMovement, TEXT("smaller_head_motion"), TEXT("Reduce head movement amplitude while preserving intention."), 0.5f);
        bMatchedIntent = true;
    }

    if (LowerDirection.Contains(TEXT("pause"))
        || LowerDirection.Contains(TEXT("hesitate"))
        || LowerDirection.Contains(TEXT("before answering"))
        || LowerDirection.Contains(TEXT("before the response")))
    {
        Plan.MatchedInterpretations.Add(TEXT("Hesitation before response"));
        AddInstruction(Plan, EMHPDPerformanceChannel::Pauses, TEXT("intentional_pre_answer_hold"), TEXT("Hold briefly before responding to show thought or concealment."), 0.55f, 0.18f);
        bMatchedIntent = true;
    }

    // -------------------------------------------------------------------------
    // Scoped Clause Parsing: Head & Gaze (Zero Cross-Talk & Zero False Positives)
    // -------------------------------------------------------------------------
    const TArray<FString> Clauses = TokenizeClauses(LowerDirection);

    bool bAddedHeadInstruction = false;
    bool bAddedGazeInstruction = false;

    for (const FString& Clause : Clauses)
    {
        // 1. Check for specific Head Action Verbs first (Nod, Tilt, Shake)
        const bool bNodInClause = ContainsPattern(Clause, TEXT("\\b(nod|nodding|nods|agree|agrees|agreement)\\b"));
        const bool bTiltInClause = ContainsPattern(Clause, TEXT("\\b(tilt|tilting|tilts|cock|cocks|cocking|lean head|leans head)\\b"));
        const bool bShakeInClause = ContainsPattern(Clause, TEXT("\\b(shake|shaking|shakes|disagree|disagrees|refusal)\\b")) && !Clause.Contains(TEXT("trembl"));

        if (bNodInClause && !bAddedHeadInstruction)
        {
            Plan.MatchedInterpretations.Add(TEXT("Head nod"));
            AddInstruction(Plan, EMHPDPerformanceChannel::HeadMovement, TEXT("head_nod"), TEXT("Nod head down and up in agreement or emphasis."), 1.0f);
            bMatchedIntent = true;
            bAddedHeadInstruction = true;
        }
        else if (bTiltInClause && !bAddedHeadInstruction)
        {
            Plan.MatchedInterpretations.Add(TEXT("Head tilt"));
            AddInstruction(Plan, EMHPDPerformanceChannel::HeadMovement, TEXT("head_tilt"), TEXT("Tilt head inquisitively or thoughtfully."), 1.0f);
            bMatchedIntent = true;
            bAddedHeadInstruction = true;
        }
        else if (bShakeInClause && !bAddedHeadInstruction)
        {
            Plan.MatchedInterpretations.Add(TEXT("Head shake"));
            AddInstruction(Plan, EMHPDPerformanceChannel::HeadMovement, TEXT("head_shake"), TEXT("Shake head side to side in disagreement or refusal."), 1.0f);
            bMatchedIntent = true;
            bAddedHeadInstruction = true;
        }

        // 2. Check for Head Movement Target & Direction in Clause
        const bool bMentionsHeadInClause = ContainsPattern(Clause, TEXT("\\b(head|neck|face|chin|bow|bows|bowing|pitch|pitches|drop head|raise head|lift chin)\\b"))
            || (ContainsPattern(Clause, TEXT("\\b(turn|turns|turning|turned)\\b")) && !Clause.Contains(TEXT("return")));

        if (bMentionsHeadInClause && !bAddedHeadInstruction)
        {
            const FDirectionMatch HeadMatch = FindDirectionInClause(Clause);
            if (HeadMatch.Direction == EDirectionType::Right)
            {
                Plan.MatchedInterpretations.Add(TEXT("Head turn right"));
                AddInstruction(Plan, EMHPDPerformanceChannel::HeadMovement, TEXT("head_turn_right"), TEXT("Turn head to the right within the timeline region, then ease back."), 1.0f);
                bMatchedIntent = true;
                bAddedHeadInstruction = true;
            }
            else if (HeadMatch.Direction == EDirectionType::Left || HeadMatch.Direction == EDirectionType::Away)
            {
                Plan.MatchedInterpretations.Add(TEXT("Head turn left"));
                AddInstruction(Plan, EMHPDPerformanceChannel::HeadMovement, TEXT("head_turn_left"), TEXT("Turn head to the left within the timeline region, then ease back."), 1.0f);
                bMatchedIntent = true;
                bAddedHeadInstruction = true;
            }
            else if (HeadMatch.Direction == EDirectionType::Up)
            {
                Plan.MatchedInterpretations.Add(TEXT("Head pitch up / raise head"));
                AddInstruction(Plan, EMHPDPerformanceChannel::HeadMovement, TEXT("head_pitch_up"), TEXT("Tilt chin and raise head upward."), 1.0f);
                bMatchedIntent = true;
                bAddedHeadInstruction = true;
            }
            else if (HeadMatch.Direction == EDirectionType::Down)
            {
                Plan.MatchedInterpretations.Add(TEXT("Head pitch down / drop head"));
                AddInstruction(Plan, EMHPDPerformanceChannel::HeadMovement, TEXT("head_pitch_down"), TEXT("Lower chin and drop head downward."), 1.0f);
                bMatchedIntent = true;
                bAddedHeadInstruction = true;
            }
        }

        // 3. Check for Gaze Target & Direction in Clause
        const FDirectionMatch GazeMatch = FindDirectionInClause(Clause);

        const bool bExplicitEyeWord = ContainsPattern(Clause, TEXT("\\b(gaze|gazes|gazing|glanc(e|es|ed|ing)?|eyes?|pupils?|stare|stares|staring|peer|peers|peering|dart|darts|darting)\\b"))
            || Clause.Contains(TEXT("eye contact"));

        // "look" is only treated as a gaze command when accompanied by an explicit direction or gaze preposition,
        // rather than an appearance/emotion descriptor ("look sad", "look happy", "look tired").
        const bool bLookWithDirection = ContainsPattern(Clause, TEXT("\\b(look|looks|looking|looked)\\b"))
            && (GazeMatch.Direction != EDirectionType::None || ContainsPattern(Clause, TEXT("\\b(look|looks|looking|looked)\\s+(at|towards|away|off|around|back|straight|ahead)\\b")));

        const bool bMentionsGazeInClause = bExplicitEyeWord || bLookWithDirection;

        if (bMentionsGazeInClause)
        {
            if (GazeMatch.Direction == EDirectionType::Right)
            {
                Plan.Instructions.RemoveAll([](const FMHPDChannelInstruction& Inst) { return Inst.Channel == EMHPDPerformanceChannel::Gaze; });
                Plan.MatchedInterpretations.Remove(TEXT("Directed gaze behavior"));
                Plan.MatchedInterpretations.Add(TEXT("Directed gaze shift (right)"));
                AddInstruction(Plan, EMHPDPerformanceChannel::Gaze, TEXT("gaze_shift_right"), TEXT("Shift gaze right within the selected timeline region, then ease back."), 1.0f);
                bMatchedIntent = true;
                bAddedGazeInstruction = true;
            }
            else if (GazeMatch.Direction == EDirectionType::Left || GazeMatch.Direction == EDirectionType::Away)
            {
                Plan.Instructions.RemoveAll([](const FMHPDChannelInstruction& Inst) { return Inst.Channel == EMHPDPerformanceChannel::Gaze; });
                Plan.MatchedInterpretations.Remove(TEXT("Directed gaze behavior"));
                Plan.MatchedInterpretations.Add(TEXT("Directed gaze shift (left)"));
                AddInstruction(Plan, EMHPDPerformanceChannel::Gaze, TEXT("gaze_shift_left"), TEXT("Shift gaze left within the selected timeline region, then ease back."), 1.0f);
                bMatchedIntent = true;
                bAddedGazeInstruction = true;
            }
            else if (GazeMatch.Direction == EDirectionType::Up)
            {
                Plan.Instructions.RemoveAll([](const FMHPDChannelInstruction& Inst) { return Inst.Channel == EMHPDPerformanceChannel::Gaze; });
                Plan.MatchedInterpretations.Remove(TEXT("Directed gaze behavior"));
                Plan.MatchedInterpretations.Add(TEXT("Directed gaze shift (up)"));
                AddInstruction(Plan, EMHPDPerformanceChannel::Gaze, TEXT("gaze_shift_up"), TEXT("Shift gaze up within the selected timeline region, then ease back."), 1.0f);
                bMatchedIntent = true;
                bAddedGazeInstruction = true;
            }
            else if (GazeMatch.Direction == EDirectionType::Down)
            {
                Plan.Instructions.RemoveAll([](const FMHPDChannelInstruction& Inst) { return Inst.Channel == EMHPDPerformanceChannel::Gaze; });
                Plan.MatchedInterpretations.Remove(TEXT("Directed gaze behavior"));
                Plan.MatchedInterpretations.Add(TEXT("Directed gaze shift (down)"));
                AddInstruction(Plan, EMHPDPerformanceChannel::Gaze, TEXT("gaze_shift_down"), TEXT("Shift gaze down within the selected timeline region, then ease back."), 1.0f);
                bMatchedIntent = true;
                bAddedGazeInstruction = true;
            }
            else if (!bAddedGazeInstruction && !bMentionsHeadInClause)
            {
                Plan.MatchedInterpretations.Add(TEXT("Directed gaze behavior"));
                AddInstruction(Plan, EMHPDPerformanceChannel::Gaze, TEXT("controlled_eye_contact_change"), TEXT("Apply a deliberate eye-contact change within the selected timeline region."), 1.0f);
                bMatchedIntent = true;
                bAddedGazeInstruction = true;
            }
        }
    }

    // Eyelids: sustained closure needs an eye word AND a closure word
    const bool bMentionsEyes = ContainsPattern(LowerDirection, TEXT("\\b(eyes?|eyelids?)\\b"))
        || LowerDirection.Contains(TEXT("eye"))
        || LowerDirection.Contains(TEXT("eyes"));

    const bool bMentionsClosure = ContainsPattern(LowerDirection, TEXT("\\b(close|closes|closed|closing|shut|shuts|shutting)\\b"))
        || LowerDirection.Contains(TEXT("close"))
        || LowerDirection.Contains(TEXT("shut"));

    if (bMentionsEyes && bMentionsClosure)
    {
        Plan.MatchedInterpretations.Add(TEXT("Sustained eye closure"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("sustained_eye_closure"), TEXT("Close the eyes and hold them closed across the timeline region."), 1.0f);
        bMatchedIntent = true;
    }
    else if (ContainsPattern(LowerDirection, TEXT("\\b(blink|flutter)\\w*")) || LowerDirection.Contains(TEXT("blink")))
    {
        Plan.MatchedInterpretations.Add(TEXT("Directed blinking"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("directed_blink_pulse"), TEXT("Add deliberate blinks distributed across the timeline region."), 1.0f);
        bMatchedIntent = true;
    }

    if (ContainsPattern(LowerDirection, TEXT("\\b(trembl|jitter|quiver|shiver|shak)\\w*")) && !ContainsPattern(LowerDirection, TEXT("\\bshake head\\b")))
    {
        Plan.MatchedInterpretations.Add(TEXT("Micro tremor"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("micro_tremor"), TEXT("Add a subtle brow/eyelid micro-tremor across the timeline region."), 0.75f);
        bMatchedIntent = true;
    }

    // Surprise / Shock
    if (ContainsPattern(LowerDirection, TEXT("\\b(surpris|shock|startl|gasp|gasps|disbelief|wide eyed)\\w*")))
    {
        Plan.MatchedInterpretations.Add(TEXT("Surprise"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("express_surprise"), TEXT("Widen eyes, raise inner/outer brows, and slightly drop jaw."), 1.0f);
        bMatchedIntent = true;
    }

    // Disgust / Repulsion
    if (ContainsPattern(LowerDirection, TEXT("\\b(disgust|revolt|gross|sneer|sneers|sneering|cringe|cringes|cringing|distaste)\\w*")))
    {
        Plan.MatchedInterpretations.Add(TEXT("Disgust"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("express_disgust"), TEXT("Wrinkle nose, squint cheeks, sneer, and lower brows."), 1.0f);
        bMatchedIntent = true;
    }

    // Jaw Tension / Clench
    if (ContainsPattern(LowerDirection, TEXT("\\b(clench|jaw tension|jaw clench|grit teeth|grits teeth|tense jaw|tight jaw)\\b")) || (LowerDirection.Contains(TEXT("jaw")) && LowerDirection.Contains(TEXT("tense"))))
    {
        Plan.MatchedInterpretations.Add(TEXT("Jaw Tension"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("clench_jaw"), TEXT("Clench jaw, press lips, and lower brows."), 1.0f);
        bMatchedIntent = true;
    }

    // Sadness / Frown / Sorrow
    const bool bSadnessOrFrown = ContainsPattern(LowerDirection, TEXT("\\b(frown|frowns|frowning|frowned|pout|pouts|pouting|sad|sadness|sorrow|sorrowful|grief|grieving|heartbrok|mourn|mournful|upset|depressed|glum|tearful|unhappy|downcast|melancholy|cry|crying|weep|weeping|sulking|somber|grim|grimace)\\w*"));
    if (bSadnessOrFrown)
    {
        Plan.MatchedInterpretations.Add(TEXT("Sadness / Frown"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("express_sadness"), TEXT("Lower mouth corners in a frown, raise inner brows, and squint inner eyes."), 1.0f);
        bMatchedIntent = true;
    }

    // Smile / Joy / Happiness
    const bool bNegativeSmile = ContainsPattern(LowerDirection, TEXT("\\b(stop(ped|ping)? smiling|don'?t smile|not smiling|no smile|without smiling|unsmiling|remove smile|less smile|cease smile)\\b"));
    if (!bNegativeSmile && !bSadnessOrFrown && ContainsPattern(LowerDirection, TEXT("\\b(happy|smile|smiles|smiling|joy|pleased|warmth|grin|grins|grinning|smirk|smirks|cheerful|beam|beaming)\\w*")))
    {
        Plan.MatchedInterpretations.Add(TEXT("Joy"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("express_smile"), TEXT("Smile broadly, pull corners, raise cheeks, and squint eyes."), 1.0f);
        bMatchedIntent = true;
    }

    if (!bMatchedIntent)
    {
        Plan.bFallback = true;
        Plan.MatchedInterpretations.Add(TEXT("Restrained dramatic adjustment"));
        AddInstruction(Plan, EMHPDPerformanceChannel::FacialExpression, TEXT("subtle_expression_shift"), TEXT("Apply a subtle facial-expression shift that preserves the original performance intent."), 0.45f);
        AddInstruction(Plan, EMHPDPerformanceChannel::Gesture, TEXT("moderated_gesture_profile"), TEXT("Moderate gesture profile without changing dialogue or lip sync."), 0.45f);
        AddInstruction(Plan, EMHPDPerformanceChannel::BodyPosture, TEXT("slight_postural_rebalance"), TEXT("Adjust posture slightly to support the director note."), 0.4f);
    }

    return Plan;
}

FString UMHPDPerformanceDirectorSubsystem::ExportPlanToJson(const FMHPDPerformancePlan& Plan) const
{
    TSharedPtr<FJsonObject> Root = MakeShared<FJsonObject>();
    Root->SetStringField(TEXT("plan_id"), Plan.PlanId.ToString(EGuidFormats::DigitsWithHyphens));
    Root->SetStringField(TEXT("source_take"), Plan.SourceTake);
    Root->SetStringField(TEXT("direction_text"), Plan.DirectionText);

    TSharedPtr<FJsonObject> RevisionRange = MakeShared<FJsonObject>();
    RevisionRange->SetNumberField(TEXT("start_seconds"), Plan.RevisionRange.StartSeconds);
    RevisionRange->SetNumberField(TEXT("end_seconds"), Plan.RevisionRange.EndSeconds);
    Root->SetObjectField(TEXT("revision_range"), RevisionRange);

    Root->SetNumberField(TEXT("intensity"), Plan.Intensity);
    Root->SetBoolField(TEXT("fallback"), Plan.bFallback);
    Root->SetArrayField(TEXT("matched_interpretations"), StringArrayToJson(Plan.MatchedInterpretations));
    Root->SetArrayField(TEXT("locked_channels"), StringArrayToJson(Plan.LockedChannels));

    TArray<TSharedPtr<FJsonValue>> InstructionValues;
    InstructionValues.Reserve(Plan.Instructions.Num());
    for (const FMHPDChannelInstruction& Instruction : Plan.Instructions)
    {
        TSharedPtr<FJsonObject> InstructionObject = MakeShared<FJsonObject>();
        InstructionObject->SetStringField(TEXT("channel"), ChannelToSchemaString(Instruction.Channel));
        InstructionObject->SetStringField(TEXT("behavior_id"), Instruction.BehaviorId.ToString());
        InstructionObject->SetStringField(TEXT("description"), Instruction.Description);
        InstructionObject->SetNumberField(TEXT("weight"), Instruction.Weight);
        InstructionObject->SetBoolField(TEXT("preserve_original"), Instruction.bPreserveOriginal);
        if (!FMath::IsNearlyZero(Instruction.TimingOffsetSeconds))
        {
            InstructionObject->SetNumberField(TEXT("timing_offset_seconds"), Instruction.TimingOffsetSeconds);
        }
        InstructionValues.Add(MakeShared<FJsonValueObject>(InstructionObject));
    }
    Root->SetArrayField(TEXT("instructions"), InstructionValues);

    TSharedPtr<FJsonObject> EditableOutput = MakeShared<FJsonObject>();
    EditableOutput->SetStringField(TEXT("target"), Plan.EditableOutputTarget);
    EditableOutput->SetBoolField(TEXT("non_destructive"), Plan.bNonDestructive);
    EditableOutput->SetStringField(TEXT("notes"), TEXT("Create a new alternate take and apply instructions as editable layered controls."));
    Root->SetObjectField(TEXT("editable_output"), EditableOutput);

    FString Json;
    const TSharedRef<TJsonWriter<>> Writer = TJsonWriterFactory<>::Create(&Json);
    FJsonSerializer::Serialize(Root.ToSharedRef(), Writer);
    return Json;
}

void UMHPDPerformanceDirectorSubsystem::AddInstruction(
    FMHPDPerformancePlan& Plan,
    EMHPDPerformanceChannel Channel,
    const FName BehaviorId,
    const FString& Description,
    float BaseWeight,
    float TimingOffsetSeconds
) const
{
    FMHPDChannelInstruction Instruction;
    Instruction.Channel = Channel;
    Instruction.BehaviorId = BehaviorId;
    Instruction.Description = Description;
    Instruction.bPreserveOriginal = IsChannelLocked(Channel, Plan.LockedChannels);
    Instruction.Weight = Instruction.bPreserveOriginal ? 0.0f : FMath::Clamp(BaseWeight * Plan.Intensity, 0.0f, 1.0f);
    Instruction.TimingOffsetSeconds = Instruction.bPreserveOriginal ? 0.0f : TimingOffsetSeconds * Plan.Intensity;
    Plan.Instructions.Add(Instruction);
}

bool UMHPDPerformanceDirectorSubsystem::IsChannelLocked(EMHPDPerformanceChannel Channel, const TArray<FString>& LockedChannels) const
{
    TArray<FString> CandidateLocks;
    switch (Channel)
    {
        case EMHPDPerformanceChannel::FacialExpression:
            CandidateLocks = {TEXT("facial_animation"), TEXT("facial_expression"), TEXT("face")};
            break;
        case EMHPDPerformanceChannel::Gaze:
            CandidateLocks = {TEXT("gaze"), TEXT("eye_contact")};
            break;
        case EMHPDPerformanceChannel::HeadMovement:
            CandidateLocks = {TEXT("body_animation"), TEXT("head_movement")};
            break;
        case EMHPDPerformanceChannel::Gesture:
            CandidateLocks = {TEXT("body_animation"), TEXT("gesture")};
            break;
        case EMHPDPerformanceChannel::BodyPosture:
            CandidateLocks = {TEXT("body_animation"), TEXT("body_posture")};
            break;
        case EMHPDPerformanceChannel::ReactionTiming:
        case EMHPDPerformanceChannel::Pauses:
            CandidateLocks = {TEXT("timing"), TEXT("reaction_timing"), TEXT("pauses")};
            break;
        case EMHPDPerformanceChannel::VoiceDelivery:
            CandidateLocks = {TEXT("voice_delivery")};
            break;
        default:
            break;
    }

    for (const FString& CandidateLock : CandidateLocks)
    {
        if (LockedChannels.Contains(CandidateLock))
        {
            return true;
        }
    }

    return false;
}
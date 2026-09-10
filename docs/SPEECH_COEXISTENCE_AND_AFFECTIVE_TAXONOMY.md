# Speech Coexistence and Affective Taxonomy Architecture

This document outlines the system-wide resolution to the core performance capture challenge identified in the MetaHuman Performance Director: the conflation of **Physical Action Verbs** and **Affective Mood States**, and their subsequent interference with the active speech solver.

---

## 1. The Speech Coexistence & Viseme Permeability Architecture

When a character speaks, the lower face (jaw, lips, lower cheeks) is commandeered by the audio-driven viseme solver. If a static macro-expression (like a 1.0 weight `Sadness` or `Frown`) is layered blindly over the speech, the lip and jaw solvers will fight the static expression, resulting in visual artifacts (e.g., the "open-mouth grimace").

### 1.1 The Speech Headroom Ceiling
To preserve phonetic integrity while maintaining emotional valence, we must enforce a **Speech Headroom Ceiling** on all lower-face articulators during active dialogue.

*   **Rule 1: Lower-Face Attenuation during Dialogue.** When `isSpeaking == true`, any affective mood state or physical action verb must clamp the weights of lower-face blendshapes (`mouthCornerDepress`, `mouthSmile`, `mouthPress`, `jawChinRaise`, etc.) to a maximum of **0.3 to 0.4**.
*   **Rule 2: Viseme Permeability.** The viseme solver acts additively over the attenuated emotional baseline. By capping the baseline at 0.3, the visemes have 0.7 units of "headroom" to articulate syllables naturally without breaking the bounds of human anatomy.

### 1.2 Shifting Valence to the Upper Face and Kinematics
Because the lower face is attenuated, the emotional weight must be carried by subsystems that do not interfere with speech:
1.  **The Upper Face:** The `glabella`, `corrugator` (inner/outer brow raise/drop), and `orbicularis oculi` (squints, crow's feet) carry the primary emotional mask.
2.  **Ocular Gaze:** Saccade frequency, blink rate, and gaze direction (locked vs. darting).
3.  **Head Kinematics (Cervical Spine):** Pitch, yaw, and roll of the neck, as well as the rhythm of conversational nodding.

---

## 2. Comprehensive Disambiguation Matrix (All 28 Categories)

The NLP engine must parse prompts to separate **Physical Action Verbs** (mechanical, localized, localized execution) from **Affective Mood States** (holistic, whole-body conditions).

### 2.1 Conflict, Tension & Vulnerability States

| Category | Physical Action Verb (NLP: "She [verb]") | Affective Mood State (NLP: "She speaks [adverb]") | Kinetic Manifestation (Action vs. Mood) |
| :--- | :--- | :--- | :--- |
| **Annoyance** | "She rolls her eyes", "Sighs" | "She speaks irritably" | **Action:** Sharp cervical tilt, 1.0 ocular roll. **Mood:** Micro-squint, 0.3 lip tighten, sharp head bobs. |
| **Pain** | "She winces", "Gasps" | "She speaks in pain" | **Action:** 1.0 brow furrow, eyes squeezed shut. **Mood:** 0.8 brow furrow, tremulous neck, shallow breathing. |
| **Grief** | "She cries", "Weeps" | "She speaks sadly", "Upset" | **Action:** 1.0 inner brow raise, 1.0 lip corner drop. **Mood:** 0.8 inner brow raise, slow blinks, 0.3 lip drop, head hanging. |
| **Frustration** | "She throws her head back" | "She speaks frustratedly" | **Action:** Sharp cervical pitch up. **Mood:** Hard blinking, 0.3 blown-out cheeks, deflated thoracic posture. |
| **Suppressed Anger** | "She clenches her jaw" | "She speaks seethingly" | **Action:** 1.0 masseter bulge (jaw clamp). **Mood:** 0.3 jaw clamp (allows speech), unblinking stare, rigid neck. |
| **Suspicion** | "She squints" | "She speaks suspiciously" | **Action:** 0.8 ocular squint. **Mood:** 0.5 squint, asymmetrical brow, cervical tilt down. |
| **Guilt** | "She looks down" | "She speaks guiltily" | **Action:** Ocular gaze shifted down/away. **Mood:** Avoidant eye contact, rounded shoulders, tucked chin. |
| **Concealed Attraction** | "She bites her lip" | "She speaks warmly/tenderly" | **Action:** 0.8 lip bite. **Mood:** Dilated pupils, 0.3 lower lid soften, leaning in. |
| **Smugness** | "She smirks" | "She speaks arrogantly" | **Action:** 0.8 asymmetrical lip raise. **Mood:** 0.3 smirk, chin raised, slow blinking. |
| **Fear/Panic** | "She gasps", "Flinches" | "She speaks fearfully" | **Action:** Sudden cervical jerk away. **Mood:** Sclera showing (wide eyes), erratic saccades, stiff neck. |
| **Exhaustion** | "She yawns", "Slumps" | "She speaks tiredly" | **Action:** 1.0 jaw open, deep inhale. **Mood:** Heavy ptosis (eyelids), slack posture, slow articulation. |
| **Defiance** | "She glares" | "She speaks defiantly" | **Action:** Hard stare, no blinking. **Mood:** Thrust jaw, squared shoulders, direct unbroken eye contact. |
| **Cognitive Overload** | "She shakes her head" | "She speaks in disbelief" | **Action:** Cervical yaw (left/right). **Mood:** Scrunched glabella, mouth slightly ajar, breath holding. |
| **Anticipation** | "She bounces" | "She speaks excitedly" | **Action:** Thoracic bouncing/shifting. **Mood:** Wide eyes, frequent blinking, fast head micro-adjustments. |
| **Deception** | "She swallows hard" | "She speaks carefully" | **Action:** Neck platysma flex. **Mood:** Overly still posture, delayed reactions, prolonged eye contact. |

### 2.2 Positive, Luminous & Connected States

| Category | Physical Action Verb (NLP: "She [verb]") | Affective Mood State (NLP: "She speaks [adverb]") | Kinetic Manifestation (Action vs. Mood) |
| :--- | :--- | :--- | :--- |
| **Genuine Joy** | "She smiles broadly" | "She speaks happily/joyfully" | **Action:** 1.0 Duchenne smile, 1.0 cheek raise. **Mood:** 0.4 smile (speech headroom), 0.8 crow's feet, bouncing chin. |
| **Warmth/Empathy** | "She leans in" | "She speaks affectionately" | **Action:** Thoracic forward shift. **Mood:** Soft gaze, tilted head, 0.3 gentle smile. |
| **Relief** | "She sighs in relief" | "She speaks with relief" | **Action:** Long deflating exhale. **Mood:** Dropped shoulders, peaceful 0.3 half-smile, relaxed brow. |
| **Pride** | "She stands tall" | "She speaks proudly" | **Action:** Thoracic elevation, straight spine. **Mood:** Elevated chin, steady gaze, calm lips. |
| **Playfulness** | "She winks" | "She speaks teasingly" | **Action:** 1.0 unilateral eye closure. **Mood:** Lively saccades, cocked head, 0.3 asymmetric smirk. |
| **Wonder** | "She gasps in awe" | "She speaks breathlessly" | **Action:** 1.0 jaw open, eyes wide. **Mood:** Parted lips (0.2), wide eyes, slow upward head track. |
| **Serenity** | "She closes her eyes" | "She speaks calmly/serenely" | **Action:** 1.0 eyelid drop (sustained). **Mood:** Relaxed brow, 0.2 gentle smile, slow diaphragmatic breathing. |
| **Gratitude** | "She bows her head" | "She speaks thankfully" | **Action:** Cervical pitch down. **Mood:** Moist eyes, 0.3 appreciative smile, humble micro-nods. |

### 2.3 Neutral, Cognitive & Baseline Professional States

| Category | Physical Action Verb (NLP: "She [verb]") | Affective Mood State (NLP: "She speaks [adverb]") | Kinetic Manifestation (Action vs. Mood) |
| :--- | :--- | :--- | :--- |
| **Attentive Listening** | "She nods" | "She actively listens" | **Action:** Cervical pitch bob. **Mood:** Forward angle, steady lock, no emotional distortion. |
| **Analytical Deliberation**| "She purses her lips" | "She speaks thoughtfully" | **Action:** 0.8 mouth press. **Mood:** Decoupled gaze, still head, 0.2 pursed lips during speech pauses. |
| **Professional Stoicism** | "She straightens her tie"| "She speaks professionally" | **Action:** Prop interaction / posture reset. **Mood:** Level eyes, neutral lips, rigid conversational cadence. |
| **Casual Ease** | "She shrugs" | "She speaks casually" | **Action:** Clavicle elevation. **Mood:** Natural blink rate, loose shoulders, fluid arrhythmic head tilts. |
| **Daydreaming** | "She stares off" | "She speaks absently" | **Action:** Unfocused gaze hold. **Mood:** Lowered chin, slack jaw (0.1), slow blinks. |

---

## 3. Concrete Implementation Specification

### 3.1 C++ NLP Disambiguation Logic (`MHPDPerformanceDirectorSubsystem.cpp`)

The system must analyze the Part of Speech (POS) to route to the correct solver.

```cpp
// MHPDPerformanceDirectorSubsystem.cpp (Pseudo-code snippet)

void UMHPDPerformanceDirectorSubsystem::ProcessDirectorialPrompt(const FString& Prompt)
{
    FString ActionVerb = NLPEngine->ExtractPhysicalActionVerb(Prompt); // e.g., "smiles", "frowns"
    FString AffectiveMood = NLPEngine->ExtractAffectiveMood(Prompt);   // e.g., "sadly", "happily"
    bool bIsSpeaking = AudioSubsystem->IsDialogueActive();

    if (!ActionVerb.IsEmpty())
    {
        // 1. Direct Physical Actions bypass complex mood logic but must respect the Speech Ceiling
        ApplyPhysicalAction(ActionVerb, bIsSpeaking);
    }
    
    if (!AffectiveMood.IsEmpty())
    {
        // 2. Mood states apply holistic upper-face, ocular, and kinematic layers
        ApplyAffectiveMood(AffectiveMood, bIsSpeaking);
    }
}

void UMHPDPerformanceDirectorSubsystem::ApplyPhysicalAction(const FString& Action, bool bIsSpeaking)
{
    float LowerFaceClamp = bIsSpeaking ? 0.3f : 1.0f; // The Speech Headroom Ceiling
    
    if (Action == "frowns")
    {
        SetBlendshapeWeight("mouthCornerDepress", 1.0f * LowerFaceClamp);
        SetBlendshapeWeight("corrugator", 1.0f); // Upper face remains fully expressive
    }
    else if (Action == "smiles")
    {
        SetBlendshapeWeight("mouthSmile", 1.0f * LowerFaceClamp);
        SetBlendshapeWeight("orbicularisOculi", 1.0f);
    }
}

void UMHPDPerformanceDirectorSubsystem::ApplyAffectiveMood(const FString& Mood, bool bIsSpeaking)
{
    float LowerFaceClamp = bIsSpeaking ? 0.3f : 1.0f;
    
    if (Mood == "sadly" || Mood == "upset")
    {
        // Lower face attenuated
        SetBlendshapeWeight("mouthCornerDepress", 0.6f * LowerFaceClamp); 
        // Upper face carries the heavy lifting
        SetBlendshapeWeight("innerBrowRaise", 0.8f);
        ConfigureOcularSaccades(ESaccadeProfile::Slow_Sluggish);
        ConfigureCervicalPosture(ECervicalPosture::Slumped_Defeated);
    }
    // ... Implement logic for all 28 categories
}
```

### 3.2 Python Core Generation Logic (`generate_acting_take.py`)

The Python backend generating the raw animation curves must bake these constraints into the JSON payload.

```python
# generate_acting_take.py

SPEECH_HEADROOM_CEILING = 0.35 # Maximum allowable weight for lower face during speech

def calculate_blendshape_weights(intent_type, category, is_speaking):
    weights = {
        "upper_face": {},
        "lower_face": {},
        "kinematics": {}
    }
    
    if intent_type == "AFFECTIVE_MOOD":
        if category == "SADNESS_GRIEF":
            weights["upper_face"]["innerBrowRaise"] = 0.85
            weights["upper_face"]["outerBrowDrop"] = 0.60
            # Apply ceiling to lower face
            raw_lip_drop = 0.60
            weights["lower_face"]["mouthCornerDepress"] = min(raw_lip_drop, SPEECH_HEADROOM_CEILING) if is_speaking else raw_lip_drop
            
            # Mood dictates holistic kinematics
            weights["kinematics"]["head_pitch_offset"] = -15.0 # Dropped head
            weights["kinematics"]["blink_rate"] = 0.5 # Slow
            
    elif intent_type == "PHYSICAL_ACTION":
        if category == "SMILE":
            weights["upper_face"]["orbicularisOculi"] = 1.0
            
            # A direct verb "She smiles" gets maximum allowed intensity
            raw_smile = 1.0
            weights["lower_face"]["mouthSmile"] = min(raw_smile, SPEECH_HEADROOM_CEILING) if is_speaking else raw_smile

    return weights
```

By explicitly isolating the physical commands from the psychological moods and strictly enforcing the speech headroom ceiling, the MetaHuman Performance Director will output visually coherent, artifact-free performances across all 28 categories during active dialogue.

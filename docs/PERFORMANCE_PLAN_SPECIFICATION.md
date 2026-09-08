# MetaHuman Performance Director — Performance Plan Specification

**Specification Version:** 1.0.0  
**Schema Definition:** [`schemas/performance_plan.schema.json`](../schemas/performance_plan.schema.json)  
**Target Runtime:** Unreal Engine 5.8+ (RigLogic & Sequencer)  
**Author:** David Cobbins (Frontier Mindworks)

---

## 1. Overview & Architectural Philosophy

Directing virtual human performance requires bridging two disparate worlds:
1. **The Creative Mental Model:** Film directors communicate using emotional subtext, dramatic tension, and physiological nuance (*"She's nervous, but trying to appear composed. Have her break eye contact before answering"*).
2. **The Kinematic Rig Model:** MetaHuman facial deformation is governed by DNA RigLogic matrices controlling over 200 raw blendshapes and joint articulators (`eyeLookLeftL`, `jawClenchL`, `mouthLipsPressL`, `browDownRight`).

Existing generative animation tools frequently jump directly from text prompts to raw bone rotations or vertex morphs via black-box neural networks. This approach creates major friction for digital production:
- The animation is difficult or impossible to art-direct or keyframe manually.
- Dialogue phonemes and lip-sync alignment are frequently corrupted.
- There is no human-readable explanation for why a curve was actuated.

**MetaHuman Performance Director (MHPD)** introduces an intermediate representation (IR): the **Performance Plan**. The Performance Plan is a deterministic, fully inspectable, and non-destructive JSON contract that represents interpreted directorial intent prior to curve baking in Sequencer.

```
+--------------------------------------------------------------------+
|                         Director Input                             |
|  Spoken Voice Note / Typed Text Direction (e.g. "Nervous")        |
+---------------------------------+----------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                  Semantic Interpretation Engine                    |
|      Extracts emotional intent, timing cues, & directorial dials   |
+---------------------------------+----------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                 Performance Plan JSON (Open IR)                    |
|      Validated against schemas/performance_plan.schema.json        |
+---------------------------------+----------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                 RigLogic Curve Synthesizer (C++)                   |
|   Applies 4 Universal Patterns: PULSE, HOLD, RAMP, OSCILLATION     |
+---------------------------------+----------------------------------+
                                  |
                                  v
+--------------------------------------------------------------------+
|                   Unreal Engine 5.8 Sequencer                      |
|  Non-destructive animation layers, additive tracks, & Control Rig  |
+--------------------------------------------------------------------+
```

---

## 2. Schema Specification

The Performance Plan JSON conforms strictly to [Draft 2020-12 JSON Schema](https://json-schema.org/draft/2020-12/schema).

### 2.1 Core Attributes

| Field | Type | Description |
| :--- | :--- | :--- |
| `plan_id` | `string` (UUID) | Unique identifier for this generated revision plan. |
| `source_take` | `string` | Asset path or name of the base Level Sequence being revised. |
| `direction_text` | `string` | The verbatim natural language prompt provided by the director. |
| `revision_range` | `object` | `{ "start_seconds": float, "end_seconds": float }` defining active editing window. |
| `intensity` | `number` [0.0 - 1.0] | Normalized global performance intensity multiplier. |
| `fallback` | `boolean` | Flag indicating whether heuristic fallback was invoked due to low semantic match confidence. |
| `matched_interpretations` | `array[string]` | Semantic performance tags resolved from the prompt (e.g. `nervous_confidence`, `gaze_aversion`). |
| `locked_channels` | `array[string]` | Protected tracks that the generator must not corrupt (e.g. `["dialogue_audio", "lip_sync"]`). |
| `instructions` | `array[object]` | Discrete kinematic channel instructions mapped to RigLogic and Control Rig targets. |
| `editable_output` | `object` | Sequencer layering strategy (`target`, `non_destructive`, `notes`). |

### 2.2 Directorial Dial Parameters

Rather than relying on an ambiguous scalar intensity slider, MHPD defines five cinematic dimensions:

1. **`framing_scale`** (0.0 to 1.0):
   - `0.0` (**Close-Up / Cinematic**): Dampens macro head movement; prioritizes micro-saccades, ocular twitch, pupil focus, and subtle lip compression.
   - `1.0` (**Wide / Theatrical**): Amplifies cervical spine rotations, broad brow shifts, and visible posture adjustments for back-row legibility.
2. **`facial_nuance`** (0.0 to 1.0):
   - Controls the depth of physiological secondary action (micro-blinks, asymmetric corner pulls, jaw clenching).
3. **`physical_action`** (0.0 to 1.0):
   - Dictates the ratio of skeletal body gestures and head rotation relative to pure facial morphing.
4. **`subtext_suppression`** (0.0 to 1.0):
   - Models the character's effort to hide or mask their authentic emotional reaction. High values delay overt expressions and introduce tension in the lower face (`jawClench`, `mouthLipsPress`).
5. **`preparation_offset_ms`** (0 to 1000 ms):
   - Anticipatory lead time. Human actors shift their eye gaze and tighten their breath *before* speaking a difficult line; this parameter injects physiological anticipation prior to speech onset.

---

## 3. The 4 Universal Curve Synthesizers

Once the Performance Plan is generated, the C++ runtime evaluates each instruction using one of four mathematical curve profiles to generate continuous keyframes for native MetaHuman RigLogic curves:

```
    PULSE (Blink / Jolt)               HOLD (Tension / Expression)
       ^                                    ^
     1 |   /\                            1 |    /--------\
       |  /  \                              |   /          \
     0 +------+--------->                 0 +--+------------+---->
         Attack Decay                          Attack Plateau Release

    RAMP (Gaze Shift / Turn)          OSCILLATION (Tremor / Flutter)
       ^                                    ^
     1 |          /---                    1 |   /\  /\  /\
       |     _.-*                           |  /  \/  \/  \
     0 +----*----------->                 0 +--------------+----->
          Sigmoid S-Curve                       Damped Sine Wave
```

### 3.1 PULSE (Fast Transient)
- **Profile:** Immediate exponential onset with configurable half-life decay.
- **Formula:** $f(t) = w \cdot \exp\left(-\frac{t - t_0}{\tau}\right)$
- **Typical Use:** Saccadic eye darting, spontaneous startle response, micro-blinks (`eyeBlinkLeft`, `eyeBlinkRight`).

### 3.2 HOLD (Sustained Expression)
- **Profile:** Trapezoidal envelope with cubic Hermite ease-in, sustained plateau, and ease-out release.
- **Typical Use:** Emotional states, suppressed rage, anxiety tension (`browDownLeft`, `jawClenchL`, `mouthLipsPressL`).

### 3.3 RAMP (Smooth Step Transition)
- **Profile:** Sigmoidal smooth-step ($S_3(x) = 3x^2 - 2x^3$) interpolating from a resting value to a target posture.
- **Typical Use:** Directional eye gaze shifts (`eyeLookLeftL`, `eyeLookUpL`) and cervical neck rotations.

### 3.4 OSCILLATION (Frequency Modulation)
- **Profile:** Damped sinusoidal oscillation with frequency and amplitude decay envelopes.
- **Formula:** $f(t) = w \cdot \sin(2\pi f t + \phi) \cdot \exp(-\lambda t)$
- **Typical Use:** Vocal unsteadiness, chin trembling (`mouthChinPucker`), autonomic nervousness.

---

## 4. Worked Directorial Example

### 4.1 The Director's Scenario
- **Director Prompt:** *"She is nervous, but trying to appear confident. Have her look away before answering."*
- **Take Parameters:** 10.0-second take; dialogue speech begins at $t = 2.40\text{s}$.
- **Locked Channels:** `dialogue_audio`, `lip_sync` (must preserve speech audio and phonetic visemes).
- **Directorial Dials:**
  - `intensity`: 0.70
  - `framing_scale`: 0.20 (Cinematic close-up)
  - `facial_nuance`: 0.85 (High micro-detail)
  - `physical_action`: 0.30 (Minimal body gesture)
  - `subtext_suppression`: 0.75 (Active concealment of anxiety)
  - `preparation_offset_ms`: 800 ms (Gaze aversion and tension precede speech by 0.8s)

---

### 4.2 Generated Performance Plan JSON

```json
{
  "$schema": "https://metahuman-performance-director.local/schemas/performance_plan.schema.json",
  "plan_id": "9f4b321a-e89c-4d37-8f51-24b819f078ae",
  "source_take": "LS_Take01_Baseline",
  "direction_text": "She is nervous, but trying to appear confident. Have her look away before answering.",
  "revision_range": {
    "start_seconds": 0.0,
    "end_seconds": 10.0
  },
  "intensity": 0.70,
  "framing_scale": 0.20,
  "facial_nuance": 0.85,
  "physical_action": 0.30,
  "subtext_suppression": 0.75,
  "preparation_offset_ms": 800.0,
  "fallback": false,
  "matched_interpretations": [
    "nervous_confidence",
    "gaze_aversion",
    "subtext_suppression"
  ],
  "locked_channels": [
    "dialogue_audio",
    "lip_sync"
  ],
  "instructions": [
    {
      "channel": "gaze",
      "behavior_id": "gaze_break_left_down",
      "description": "Anticipatory cognitive gaze break: shifts eyes down-left before answering, then returns to camera.",
      "weight": 0.65,
      "preserve_original": false,
      "timing_offset_seconds": -0.80
    },
    {
      "channel": "facial_animation",
      "behavior_id": "anxiety_eyebrow_tighten",
      "description": "Subtle medial corrugator contraction indicating internal mental tension.",
      "weight": 0.45,
      "preserve_original": true,
      "timing_offset_seconds": -0.60
    },
    {
      "channel": "facial_animation",
      "behavior_id": "subtext_suppression_jaw_press",
      "description": "Unilateral jaw clench and lip compression suppressing overt emotional leakage.",
      "weight": 0.55,
      "preserve_original": true,
      "timing_offset_seconds": -0.40
    },
    {
      "channel": "facial_animation",
      "behavior_id": "forced_confidence_smile_settle",
      "description": "Controlled, conscious zygomatic corner pull attempting to project composure.",
      "weight": 0.35,
      "preserve_original": true,
      "timing_offset_seconds": 0.10
    }
  ],
  "editable_output": {
    "target": "sequencer_control_rig_layers",
    "non_destructive": true,
    "notes": "Bakes additive curve tracks to Face Control Rig without destructively altering baseline Audio2Face phonemes."
  }
}
```

---

### 4.3 RigLogic Curve Breakdown Table

Below is the exact mapping of this performance plan to MetaHuman RigLogic curves, showing why each curve is keyed, its timing, and the synthesis pattern applied:

| RigLogic Curve Target | Keying Window ($t$) | Peak Weight | Curve Pattern | Directorial & Biomechanical Rationale |
| :--- | :--- | :--- | :--- | :--- |
| `eyeLookLeftL` / `eyeLookLeftR` | 1.60s &rarr; 3.20s | 0.65 | `RAMP` (Hold & Return) | **Gaze Aversion (800ms pre-speech):** In human cognitive psychology, looking away before speaking reflects cognitive load and anxiety. Keyed via a smooth-step ramp that settles, then softly tracks back toward center as speech begins. |
| `eyeLookDownL` / `eyeLookDownR` | 1.60s &rarr; 3.00s | 0.40 | `RAMP` (Hold & Return) | **Submissive / Hesitant Tilt:** Combined with lateral gaze shift to avoid direct confrontation during cognitive preparation. |
| `eyeSquintInnerL` / `eyeSquintInnerR` | 1.80s &rarr; 4.00s | 0.35 | `HOLD` | **Ocular Tension:** Indicates focused, high-effort cognitive concealment. Kept subtle (`framing_scale = 0.20`) to avoid a squint grimace. |
| `browDownLeft` / `browDownRight` | 1.80s &rarr; 4.20s | 0.40 | `HOLD` | **Medial Eyebrow Compression:** Corrugator activation reflecting genuine internal stress. |
| `jawClenchL` | 2.00s &rarr; 2.50s | 0.55 | `HOLD` (Brief) | **Suppression Jaw Clench:** Fires 400ms prior to the first spoken word. Clenches the masseter muscle as an involuntary tell of suppressed tension, releasing as the jaw opens for the first vowel. |
| `mouthLipsPressL` | 2.00s &rarr; 2.40s | 0.45 | `HOLD` (Pre-speech) | **Lip Compression:** Tightens lips immediately prior to speech onset, creating organic anticipation. Automatically relaxes to 0.0 at $t = 2.40\text{s}$ so phoneme articulators (`mouthClose`, `mouthFunnel`) have clean headroom. |
| `mouthCornerPullL` / `mouthCornerPullR` | 2.50s &rarr; 5.00s | 0.30 | `HOLD` | **"Mask of Composure":** Controlled unilateral/bilateral smile pull layered *after* speech starts, representing the character's conscious attempt to appear cheerful and in control. |
| `head_yaw` (Control Rig Bone) | 1.60s &rarr; 3.20s | -4.5&deg; | `RAMP` (Ease) | **Subtle Cervical Turn:** Small head tilt accompanying the eye saccade. Constrained to minimal amplitude by `framing_scale: 0.20` and `physical_action: 0.30`. |

---

## 5. Non-Destructive Layering & Viseme Preservation

A primary hazard in facial directing is **viseme interference**: when an emotional curve (e.g. `mouthSmileLeft`) collides with a phonetic curve (e.g. `mouthPucker` during an "oo" sound), causing unnatural mouth stretching or muffled speech appearance.

To prevent this, MHPD executes two safeguards:

1. **Soft-Knee Viseme Headroom Clamping:**  
   During active phonetic windows identified from the baseline audio, conflicting lower-face emotional curves are attenuated:
   $$W_{\text{effective}} = W_{\text{target}} \cdot \left(1.0 - \kappa \cdot W_{\text{phonetic}}\right)$$
   Where $\kappa \approx 0.65$ preserves speech readability while retaining emotional coloration.
2. **Dedicated Sequencer Sub-Tracks:**  
   Curves are never baked destructively onto the raw capture track. Instead, they are generated as **Additive Sequencer Weight Tracks** or **Control Rig Layer Sequences**, allowing artists to dial the blend weight or tweak individual keyframes in Sequencer curve editor at any time.

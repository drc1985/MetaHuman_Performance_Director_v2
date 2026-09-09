# MetaHuman Performance Director

![Unreal Engine 5.8](https://img.shields.io/badge/Unreal%20Engine-5.8%2B-blue?logo=unrealengine)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Compute](https://img.shields.io/badge/Compute-100%25%20Local%20%26%20Offline-success)
![Status](https://img.shields.io/badge/Status-Prototype-orange)
![MegaGrants](https://img.shields.io/badge/Epic%20MegaGrants-2026%20Submission-purple)

**MetaHuman Performance Director (MHPD)** is a native C++ and Python editor plugin for Unreal Engine 5.8+ that enables directors and creators to generate, layer, and direct nuance-rich MetaHuman facial and body performances using natural language notes — directly inside UE5 Sequencer.

---

## 🎬 In-Editor Demonstration

[![MetaHuman Performance Director In-Editor Walkthrough](https://frontiermindworks.com/MetaHumanPerformanceDirector/mhpd_demo_preview.png)](https://frontiermindworks.com/MetaHumanPerformanceDirector)

> **[▶ Watch Full Video](https://frontiermindworks.com/MetaHumanPerformanceDirector/MetaHumanPerformanceDirector.mp4)** &bull; **[Interactive Project Page](https://frontiermindworks.com/MetaHumanPerformanceDirector)**  
> *Walkthrough demonstrating automated audio-to-face baseline synthesis, natural language performance directing, non-destructive Sequencer take layering, and RigLogic curve synthesis directly in Unreal Engine 5.8.*  
>  
> 💡 **Release Note:** *The walkthrough video above demonstrates the Phase 1 grant submission build (single intensity control). The latest codebase introduces the **Five Directorial Dials** and biological **Soft-Knee Viseme Collision Avoidance** (detailed in [Recent Updates](#-recent-updates--devlog) below).*

---

## ⚡ Recent Updates & Devlog

### September 2026 — v0.2.0: Directorial Dials & Soft-Knee Viseme Update

Following the initial grant concept submission, we expanded the directorial controls to reflect film-directing psychology and biological realism:

### 1. The Five Directorial Dials
Replaced the single scalar "intensity" slider with five calibrated cinematic dimensions in the Slate UI:
- **Framing Scale:** Calibrates performance for *Cinematic Close-Up* (dampens gross head movement, accentuates ocular micro-cues) vs. *Conversational* vs. *Theatrical Wide* (projects energy to the back row).
- **Facial Nuance:** Controls emotional displacement across RigLogic face curves with non-linear calibration (*Subtle*, *Natural*, or *Pronounced*).
- **Head & Body (Physical Action):** Modulates cervical neck rotations and body posture independently from facial expressions.
- **Subtext Masking (Chekhov's 'Guise vs. Under-the-Guise'):** Models intentional concealment—suppresses overt emotional caricature while injecting authentic micro-leakage (masseter jaw clench, brow asymmetry, inner squint).
- **Pre-Speech Preparation Lead:** Injects anticipatory psychological gesture (eye saccade, breath lead) 0–1000ms prior to the first spoken word.

### 2. Biological Soft-Knee Viseme Protection
- Injected `_soft_knee_saturate()` into the Python execution pipeline, preventing linear blendshape overshoot past anatomical limits.
- Upgraded mouth-settling routines to strictly protect expressive acting curves (smiles, frowns, jaw clenches) while ensuring speech opening phonemes cleanly return to rest pose without tearing.

---

## 🔒 100% Local & Offline — Zero Cloud Dependencies

Unlike cloud GenAI services or other comparable tools, MHPD runs **entirely locally inside your Unreal Engine editor session**:

- **No Cloud Services or External Network Calls:** Operates 100% offline. Zero latency roundtrips to remote APIs.
- **No API Keys or Accounts Required:** No OpenAI, Anthropic, or third-party cloud credentials needed. Clone, build, and direct.
- **Complete Script & Actor Privacy:** Unreleased screenplays, confidential character likenesses, and voice recordings never leave your local workstation or studio intranet.
- **Deterministic & Repeatable:** Performance plans are generated deterministically and stored as open JSON contracts, ensuring repeatable takes across team members.

---

## 📋 System Requirements

| Requirement | Supported Version / Specification | Notes |
| :--- | :--- | :--- |
| **Unreal Engine** | **5.8+** (Windows x64) | Tested on UE 5.8 source and launcher builds. |
| **MetaHuman Plugin** | Enabled | Official Epic Games plugin for MetaHuman character support. |
| **MetaHuman Animator** | Enabled | Used for baseline phonetic Audio2Face capture. |
| **Control Rig Plugin** | Enabled (`ControlRig`) | Declared in `.uplugin`; required for skeletal layer blending. |
| **Python Script Plugin** | Enabled (`PythonScriptPlugin`) | Declared in `.uplugin`; required for automated Sequencer asset plumbing. |
| **MetaHuman Actor** | Placed in Level | Standard MetaHuman Blueprint (`BP_<CharacterName>`) placed in active map. |
| **Dialogue Audio** | `.wav` Sound Wave | Mono or stereo 16-bit / 44.1 or 48 kHz dialogue sound wave asset. |

---

## 🌟 Key Features

- **Natural Language Intent Directing**: Direct your digital actor using film terminology (e.g. *"She is nervous, but trying to appear confident. Have her look away before answering."*) via typed text or voice input.
- **Non-Destructive Take System**: Every take generates a dedicated Level Sequence asset. A/B compare baseline and alternate performance takes instantly via the Sequencer take dropdown.
- **Selective Channel Preservation (Channel Locks)**: Lock dialogue audio, speech lip synchronization, facial expressions, eye gaze, or body gestures to preserve phonetic alignment while layering dramatic nuance.
- **Native RigLogic Curve Synthesis**: Operates directly on MetaHuman's native RigLogic curve set (200+ blendshapes & joint controls across emotional, ocular, and phonetic articulators) using 4 universal animation patterns: **Pulse** (blinks), **Hold** (sustained tension), **RAMP** (directional gaze shifts), and **Oscillation** (micro-tremor).
- **Soft-Knee Viseme Collision Avoidance**: Automatically attenuates conflicting lower-face emotional curves during active speech syllables, eliminating viseme distortion and mouth tearing.
- **Directorial Dials**: Beyond a generic intensity slider, five dedicated cinematic dimensions calibrate the performance: *Framing Scale* (Close-Up vs. Wide), *Facial Nuance*, *Physical Action*, *Subtext Suppression*, and *Preparation Lead Time*.
- **In-Editor Voice Input**: Integrated 'Hold to Talk' voice transcription allows directors to speak acting notes directly to digital actors.

---

## 📄 Performance Plan Specification (Open IR)

MHPD decouples high-level creative intent from low-level joint and blendshape keyframing using an open intermediate representation (IR): the **Performance Plan**.

- **Master Specification & Lexicon:** [`docs/PERFORMANCE_DIRECTOR_SPECIFICATION.md`](docs/PERFORMANCE_DIRECTOR_SPECIFICATION.md)
- **JSON Schema:** [`schemas/performance_plan.schema.json`](schemas/performance_plan.schema.json)

The specification document details the schema, the 4 mathematical curve synthesis profiles, and includes a complete worked example demonstrating how the note *"She is nervous, but trying to appear confident. Have her look away before answering"* compiles into specific RigLogic curves (`eyeLookLeftL`, `eyeSquintInnerL`, `jawClenchL`, `mouthLipsPressL`, `mouthCornerPullL`) with timing offsets and viseme preservation.

---

## ⚖️ Current Capabilities & Limitations

To set clear expectations for animators and technical directors:

### What Is Fully Functional Today:
- **RigLogic Facial Directing:** Full procedural keyframing of MetaHuman's 200+ native facial blendshapes and bone controls.
- **Gaze & Saccadic Kinematics:** Procedural gaze breaks, cognitive aversion shifts, and blink synchronization.
- **Cervical & Head Turns:** Driven via Control Rig on the MetaHuman body skeleton (cervical yaw, pitch, roll).
- **Sequencer Pipeline:** Automated take generation, non-destructive layer creation, track locking, and take switching.
- **Offline Semantic Parser:** Local heuristic rule engine mapping director phrasing to calibrated performance plans.

### Current Limitations & What's In Active Development:
- **Body Gesture Synthesis:** *Early Prototype / Experimental.* While cervical head orientation and upper-torso posture anchoring are supported, full-body text-to-motion generative synthesis is currently in early development and kept in research quarantine.
- **Subtext Parsing:** Complex, multi-sentence subtext with subtle literary nuance currently uses a rule-based parser. An embedded, fully local Small Language Model (SLM) is in development to expand semantic range without introducing cloud dependencies.
- **Platform Support:** Developed and verified specifically on Unreal Engine 5.8 on Windows x64.

---

## 🗺️ Project Roadmap

- [x] **Phase 1: Working Prototype (Complete & Demonstrable in UE 5.8)**
  - Native UE 5.8 Slate director panel (voice or typed notes, directorial dials, channel locks).
  - Audio-to-face baseline automation via MetaHuman Animator.
  - Native RigLogic curve synthesis (200+ blendshapes & joint controls via 4 universal mathematical patterns).
  - Procedural gaze breaks, saccadic eye darting, and blink synchronization.
  - Non-destructive Sequencer take isolation, take A/B switching, and soft-knee viseme preservation.
  - Offline heuristic semantic parser behind an open JSON performance plan contract.

- [ ] **Phase 2: Production Scale — Curated Behavior Library & Data-Calibrated Proceduralism**
  - **Full-Performance Capture Sessions:** Commissioned motion capture sessions with simultaneous optical/inertial body tracking and Head-Mounted Camera (HMC) facial capture, producing 100% original, redistributable MetaHuman assets.
  - **Modular Additive Behavior Library:** Retarget and modularize captured takes into discrete additive micro-behaviors (posture shifts, physical listening beats, conversation gestures, head-movement idioms) that the planner blends non-destructively in Sequencer.
  - **Data-Calibrated Procedural Synthesis:** Leverage captured actor data to biologically calibrate procedural curve generation:
    - *Muscle Co-Activation Matrices:* Empirically derived RigLogic multi-muscle synergies (e.g., authentic smile-to-cheek and brow-to-squint co-activation ratios).
    - *Biological Kinematic Profiles:* Empirically measured velocity and ease envelopes (e.g., asymmetric blink attack/decay, masseter tension curves).
    - *Directorial Dial Grounding:* Calibrate the 5 Directorial Dials against ground-truth actor performances across framing scales (close-up underplay vs. theatrical projection).
  - **Fine-Tuned Local Language Model:** Replace the heuristic parser with a specialized Small Language Model (SLM) running 100% offline on a single workstation GPU (DirectML / ONNX Runtime) behind the same open JSON contract.

- [ ] **Phase 3: Multi-Character Directing & Emotion Timeline**
  - **Multi-Character Scene Directing:** Parse multi-actor notes (*"Joe, stay guarded. Bob, let the disappointment show"*) into a synchronized master plan with per-character Sequencer take layers.
  - **Voice Emotion Timeline UI:** Surface audio-derived emotional cues as editable, director-reviewable micro-expression proposals in Sequencer before baking.

- [ ] **Phase 4: Fab Marketplace Release & Studio Validation**
  - **Formal Validation Studies:** Blind A/B director-intent recognition tests and technical animator editability reviews.
  - **Fab Distribution:** Public release on Fab with a free educational tier and open performance plan schema.

---

## 🛠️ Architecture Overview

The plugin implements an automated two-phase directorial pipeline built natively on top of Epic Games' first-party stack (MetaHuman Animator, RigLogic, and Sequencer):

```
+-------------------------------------------------------------------------------+
|                       Phase 1: Audio-to-Face Baseline                         |
| Ingests raw dialogue audio (.wav) -> Extracts acoustic phonemes via MetaHuman  |
| Animator -> Generates baseline Level Sequence with speech & lipsync locked.   |
+---------------------------------------+---------------------------------------+
                                        |
                                        v
+-------------------------------------------------------------------------------+
|                       Phase 2: Intent Take Generation                         |
| Directorial note -> Parsed into JSON Performance Plan -> Bakes additive       |
| RigLogic curve tracks & Control Rig layers non-destructively in Sequencer.    |
+-------------------------------------------------------------------------------+
```

---

## 🚀 Installation & Quick Start

### 1. Prerequisites
Verify that your Unreal project has the required plugins enabled:
- **MetaHuman** and **MetaHuman Animator**
- **Control Rig**
- **Python Editor Script Plugin** (`PythonScriptPlugin`)

### 2. Install Plugin
Clone or extract this repository into your project's `Plugins/` folder:
```bash
cd MyProject/Plugins/
git clone https://github.com/drc1985/MetaHuman_Performance_Director_v2.git MetaHumanPerformanceDirector
```

### 3. Build & Launch
Generate project files and rebuild your C++ project in Visual Studio or Rider, then launch Unreal Editor 5.8+.

### 4. Direct a Take
1. Ensure your MetaHuman Character Blueprint (e.g. `BP_<CharacterName>`) is placed in the level.
2. Open the panel via **Window &rarr; MetaHuman Performance Director**.
3. Select your MetaHuman actor and your dialogue `.wav` sound wave.
4. Generate the audio baseline take.
5. Enter a directorial note (e.g. *"She turns her head right, glances down nervously, and frowns while speaking"*), adjust your directorial dials, and click **Generate Take**!

---

## 👤 Author & Credits

Created by **David Cobbins** ([Frontier Mindworks](https://frontiermindworks.com))  
*Research Project Leader at the USC Institute for Creative Technologies (USC-ICT)*

- **GitHub:** [@drc1985](https://github.com/drc1985)
- **Project Website:** [frontiermindworks.com/MetaHumanPerformanceDirector](https://frontiermindworks.com/MetaHumanPerformanceDirector)
- **Epic MegaGrants 2026:** Submission Candidate

---

## 📄 License

Released under the permissive [MIT License](LICENSE).

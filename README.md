# MetaHuman Performance Director

[![Unreal Engine 5.8](https://img.shields.io/badge/Unreal%20Engine-5.8%2B-blue?logo=unrealengine)](https://www.unrealengine.com)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Compute](https://img.shields.io/badge/Compute-100%25%20Local%20%26%20Offline-success)](https://frontiermindworks.com)
[![Status](https://img.shields.io/badge/Status-v0.3.1%2B%20(Alpha%20%26%20ADE)-brightgreen)](https://github.com/drc1985/MetaHuman_Performance_Director_v2)
[![Engine](https://img.shields.io/badge/Engine-Auteur%20Drama%20Engine-gold)](https://frontiermindworks.com)
[![Author](https://img.shields.io/badge/Author-David%20Cobbins-blue.svg)](https://frontiermindworks.com)
[![Studio](https://img.shields.io/badge/Studio-Frontier%20Mindworks-0052cc.svg)](https://frontiermindworks.com)
[![MegaGrants](https://img.shields.io/badge/Epic%20MegaGrants-2026%20Submission-purple)](https://www.unrealengine.com/megagrants)

**Created & Architected by [David Cobbins](https://github.com/drc1985) • [Frontier Mindworks](https://frontiermindworks.com)**

> ℹ️ **Independent Project Notice:** MetaHuman and Unreal Engine are trademarks of Epic Games, Inc. MetaHuman Performance Director is an independent project and is not affiliated with or endorsed by Epic Games.

---

## 🎬 Overview

Unreal Engine has unlocked Hollywood-grade photoreal cinematography, real-time lighting, and virtual production sets for independent filmmakers. But directing virtual human actors has remained locked behind a technical wall: tweaking raw facial curves, keyframing 200+ blendshapes, or waiting days for animation revisions strips away the spontaneous creative rhythm of a director.

**MetaHuman Performance Director (MPHD)** closes the gap between filmmaking intuition and technical execution:

- **Natural Language Directing (Voice or Text):** Direct digital actors the same way you direct live talent on set. Type acting notes or speak them directly using integrated **voice input** powered by local NLP/NLU—translating dramatic intent (*"She is guarded, hiding her heartbreak. Have her glance away nervously before answering"*) directly into calibrated RigLogic animation.
- **Dedicated Directorial Dials:** Fine-tune performance dynamics independently from your dramatic notes. Five calibrated cinematic dials let you shape **Framing Scale** (subtle ocular micro-cues for close-ups vs. projected energy for wide shots), **Facial Nuance**, **Physical Action** (cervical neck and posture energy), **Subtext Masking** (intentional emotional concealment with authentic micro-leakage), and **Pre-Speech Lead Time** (anticipatory breaths and cognitive gaze saccades before speaking).
- **Non-Destructive Alternate Takes & Channel Locks:** Generate fully editable takes in seconds, A/B compare performances on the fly directly in Sequencer, and selectively lock channels—preserving pristine dialogue audio and speech lip-sync key-for-key while freely iterating on emotional nuance.

---

## 📺 Demonstration & Video Walkthrough

[![MetaHuman Performance Director - October 2026 ADE Showcase](https://frontiermindworks.com/MetaHumanPerformanceDirector/demolinkscreencap.png)](https://frontiermindworks.com/MetaHumanPerformanceDirector/DemoOct.mp4)

- **Interactive Project Page:** [https://frontiermindworks.com/MetaHumanPerformanceDirector](https://frontiermindworks.com/MetaHumanPerformanceDirector)
- **October 2026 ADE Update Video:** [DemoOct.mp4](https://frontiermindworks.com/MetaHumanPerformanceDirector/DemoOct.mp4)
- **Original Grant Submission Video:** [MetaHumanPerformanceDirector.mp4](https://frontiermindworks.com/MetaHumanPerformanceDirector/MetaHumanPerformanceDirector.mp4)
- **Public GitHub Mirror:** [https://github.com/drc1985/MetaHuman_Performance_Director_v2](https://github.com/drc1985/MetaHuman_Performance_Director_v2)

---

## 🧠 The Auteur Drama Engine (ADE)

Traditional audio-driven facial animation systems solve phonetic lip-sync, but they suffer from the **"I love you / I will kill you" paradox**: acoustic waveforms for identical words sound identical, yet dramatically they demand completely opposite somatic realities.

The **Auteur Drama Engine (ADE)** powers MetaHuman Performance Director as a **psychophysical acting engine**:

1. **Stanislavskian Inner Monologue & Dramatic Subtext:** Synthesizes the psychological space *underneath* spoken dialogue—masking overt emotion while surfacing authentic micro-leakage (masseter jaw clenching, ocular avoidance saccades, breath suppression).
2. **Brechtian Somatic Presence:** Characters do not freeze between lines. They maintain continuous vertebral breathing cycles, postural weight transfers, clavicle counter-rotations, and sustained physical attitude.
3. **Chekhovian Psychological Gesture:** Pre-speech lead times (0–1000ms) inject anticipatory gaze saccades, breath intake onsets, and cervical preparation before the first syllable is uttered.

---

## 🎛️ The 4-Tab Filmmaker Workflow

```
[ Tab 1: Baseline ]  ──►  [ Tab 2: Directing Slate ]  ──►  [ Tab 3: Take Review ]  ──►  [ Tab 4: Render Studio ]
 Audio Ingestion &          5 Dials, Voice Input &           A/B Take Auditioning &       Framing Presets &
 Progress Bar (0→100%)      Multi-Beat Timecode Syntax       Structured JSON Inspection   Batch MRQ Export to MP4
```

1. **Tab 1 — Generate Baseline:**
   - Asynchronous, non-blocking Audio2Face baseline generation with a determinative $0\% \to 100\%$ progress bar.
   - Clean dialogue audio (.wav) automatically bound into an isolated Sequencer take.
2. **Tab 2 — Directing Slate:**
   - **5 Calibrated Cinematic Dials:** *Framing Scale* (MCU/CU/Wide), *Facial Nuance*, *Physical Action*, *Subtext Masking*, and *Pre-Speech Lead Time*.
   - **Hold-to-Talk Voice Directing:** Speak or type natural language acting notes.
   - **Timecoded Multi-Beat Syntax:** Direct evolving dramatic beats (`[0s-7s] She is defensive... [7s-14s] Breaks down in grief`) seamlessly within a single Level Sequence.
   - **Channel Preservation Locks:** Preserve dialogue audio, speech phonemes, gaze, or body layers key-for-key.
3. **Tab 3 — Take Review Station:**
   - Instant A/B take auditioning and non-destructive layer switching directly in Sequencer.
   - Transparent structured JSON performance plan inspection and take management.
4. **Tab 4 — Render Studio:**
   - Performer-aware automated CineCamera framing with calibrated shot sizes (Wide, Medium Close-Up, Close-Up, Extreme Close-Up) and lenses (35mm, 50mm, 85mm, 105mm).
   - Cinematic camera angles: Dutch tilt, Low angle, Profile, Eye-level.
   - In-editor batch Movie Render Queue (MRQ) automation producing final graded MP4 deliverables with muxed audio.

---

## 🧬 Somatic & Biomechanical Engine

- **Kinetic Vertebral Chain:** Propagates motion organically through Pelvis $\to$ Spine 01–04 $\to$ Neck $\to$ Head, eliminating static mannequin stiffness.
- **Clavicle & Upper Arm Coupling ($k=0.90$):** $100\%$ clavicle displacement coupled to upper arm kinematics to prevent shoulder disarticulation during emotional gestures and posture slumps.
- **Diaphragm Breathing Cycles & Emotional Sighs:** Autonomic breathing rhythms that accelerate during anxiety and deep restorative sighs during emotional releases.
- **Duchenne Co-Activation:** Biologically linked zygomaticus major and orbicularis oculi muscle groups ensure authentic smiles rather than artificial mouth-only warping.
- **Soft-Knee Viseme Protection:** Non-linear saturation curves (`_soft_knee_saturate`) prevent blendshape overshoot and mouth tearing during active speech.

---

## 🔒 100% Local & Offline — Zero Cloud Dependencies

Unlike cloud GenAI services or API-dependent tools, MPHD runs **100% locally and offline inside Unreal Engine**:

- **Zero Cloud Calls:** No latency roundtrips or external server dependencies.
- **Zero API Keys or Accounts:** No OpenAI, Anthropic, or proprietary cloud accounts required.
- **Studio IP & Privacy First:** Unreleased screenplays, actor likenesses, and voice recordings never leave your workstation.
- **Deterministic IR:** Generates deterministic JSON performance plans conforming to strict schema contracts.

---

## 📢 Evolution & Release Roadmap

We've been working on significant updates that will be released over the coming months. Some of those updates have been released in GitHub in an unfinished state.

Here's a summary of changes from the original V1 release, and what will be released:

| Core Dimension | Original / v1 Build | Current Production Build (Alpha & ADE) |
| :--- | :--- | :--- |
| **Directorial Architecture** | Basic prompt-to-blendshape scalar tool | **Auteur Drama Engine (ADE)** — Psychophysical acting engine (Stanislavski subtext, Brechtian somatic presence) |
| **Editor Workflow & UI** | Single-window prompt & intensity slider | **4-Tab Director Slate UI:**<br>1. **Generate Baseline** (determinate $0\% \to 100\%$ progress bar)<br>2. **Direct Performance** (5 dials + voice)<br>3. **Review Takes** (A/B take auditioning)<br>4. **Render Studio** (Cinematography & MRQ) |
| **Anatomical & Kinetic Scope** | Facial RigLogic curves & basic neck rotation | **Full Vertebral & Somatic Chain:** Pelvis, Spine 01–04, Clavicles + Upper Arm coupling ($k=0.90$), Cervical Neck, Diaphragm breathing cycles & emotional sighs |
| **Facial & Speech Realism** | Basic blendshape activation with potential tearing | **Duchenne co-activation matrices**, soft-knee viseme protection, pre-speech breath onset guard, sustained posture holding |
| **Directorial Controls** | Single "Intensity" slider ($0.0 - 1.0$) | **5 Calibrated Cinematic Dials:** Framing Scale, Facial Nuance, Physical Action, Subtext Masking (guise vs. leakage), Pre-Speech Lead Time |
| **Multi-Beat Directing** | Single prompt per take | **Timecoded Multi-Beat Syntax** (`[0s-7s]... [7s-14s]...`) compiled into a single seamless Level Sequence |
| **Virtual Cinematography** | Manual editor viewport review | **Render Studio (Tab 4):** Shot sizes (Wide, MCU, CU, ECU), angles (Dutch, Low, Profile), lenses (35–105mm), automated CineCamera cuts & batch MRQ to MP4 |
| **Multi-Actor & External MoCap** | Conceptual future | **Bravo Architecture:** External baseline/MoCap ingestion, non-destructive additive Control Rig layers, screenplay ingestion & proxemics |

*Note: The features above represent active implementations rolling out across our milestone releases.*

---

## 🗺️ Milestone Roadmap

- [x] **Phase 1: Alpha Cycle — Working Single-Performer Prototype (Demonstrable in UE 5.8)**
  - Native UE 5.8 Slate director panel (voice or typed notes, 5 directorial dials, channel locks).
  - Audio-to-face baseline automation via MetaHuman Animator.
  - Native RigLogic curve synthesis (200+ blendshapes & joint controls via 4 universal mathematical patterns).
  - Procedural gaze breaks, saccadic eye darting, and blink synchronization.
  - Non-destructive Sequencer take isolation, take A/B switching, and soft-knee viseme preservation.
  - Offline heuristic semantic parser behind an open JSON performance plan contract.

- [ ] **Phase 2: Alpha Polish — Curated Behavior Library & Data-Calibrated Proceduralism**
  - **Data-Calibrated Procedural Synthesis:** Leverage captured actor data to biologically calibrate procedural curve generation (muscle co-activation matrices, biological kinematic profiles, and ground-truth dial calibration).
  - **Fine-Tuned Local Small Language Model (SLM):** Replace the keyword heuristic parser with a specialized offline SLM running locally on workstation hardware (DirectML / ONNX Runtime).

- [ ] **Phase 3: Bravo Cycle — Multi-Character Scene Directing & Soundstage Staging**
  - **Screenplay Ingestion & Scene Breakdown:** Native Fountain / `.fdx` screenplay parser extracting characters, dialogue, action beats, props, and scene mood into a visual Scene Selector.
  - **Soundstage Auto-Placement & Staging:** Geometric solver for conversational proxemics, ground raycasting, eye-line matching vectors, and 180° camera rule constraints.
  - **Pluggable Motion Resolver:** Seamless bridge interfacing with local Kimodo engines (MotionSmith AI, Dark Dojo DDS Motion) and stock animation libraries, backed by our Tier 0 procedural fallback.
  - **DP Camera Coverage Package:** Automatic suggestion and generation of Master Two-Shots, OTS, MCU singles, and emotional close-up coverage.
  - **Multi-Character Relational Directing:** Compound natural language parsing for multi-actor relational notes (*"Julia and Todd turn away... Julia stops first"*), Master Sequence take branching, and cross-character take mixing.

- [ ] **Phase 4: Fab Marketplace Release & Studio Validation**
  - Studio & virtual production previz testing.
  - Public release on Epic's Fab marketplace with open performance plan schema.

---

## 📋 System Requirements

| Requirement | Supported Version / Specification | Notes |
| :--- | :--- | :--- |
| **Unreal Engine** | **5.8+** (Windows x64) | Tested on UE 5.8 source and launcher builds. |
| **MetaHuman Plugin** | Enabled | Official Epic Games plugin for MetaHuman character support. |
| **MetaHuman Animator** | Enabled | Used for baseline phonetic Audio2Face capture. |
| **Control Rig Plugin** | Enabled (`ControlRig`) | Required for skeletal layer blending. |
| **Python Script Plugin** | Enabled (`PythonScriptPlugin`) | Required for automated Sequencer asset plumbing. |
| **Movie Render Queue** | Enabled (`MovieRenderPipeline`) | Required for automated batch take rendering. |
| **MetaHuman Actor** | Placed in Level | Standard MetaHuman Blueprint (`BP_<CharacterName>`) placed in active map. |
| **Dialogue Audio** | `.wav` Sound Wave | Mono or stereo 16-bit / 44.1 or 48 kHz dialogue sound wave asset. |

---

## 🚀 Running the Unreal Engine Demo

1. **Verify Plugins:** Ensure `MetaHuman`, `MetaHuman Animator`, `ControlRig`, `PythonScriptPlugin`, and `MovieRenderPipeline` are enabled.
2. **Open the Demo Map:** In the Unreal Editor Content Browser, open your designated demo level (e.g. `Lvl_IntroRoom`).
3. **Verify the Performer:** Ensure `BP_MH_DemoActor` is placed in the level.
4. **Open the Performance Director Panel:** Navigate to **Window &rarr; MetaHuman Performance Director**.
5. **Direct a Take:**
   - Input a directorial note (e.g., *"She is nervous, but trying to appear confident."*)
   - Adjust directorial dials (*Framing Scale*, *Facial Nuance*, *Subtext Masking*, etc.)
   - Click **Generate Take** to synthesize the new Sequencer take!

---

## 📖 Citation & Attribution

If you use **MetaHuman Performance Director** in your academic research, virtual production pipeline, game development, or creative workflows, please cite it using the metadata below:

```bibtex
@software{Cobbins_MetaHuman_Performance_Director_2026,
  author = {Cobbins, David},
  title = {{MetaHuman Performance Director: Natural Language Directorial System for Unreal Engine MetaHumans}},
  year = {2026},
  month = {10},
  version = {0.3.1},
  organization = {Frontier Mindworks},
  url = {https://github.com/drc1985/MetaHuman_Performance_Director_v2}
}
```

---

## 👤 Author & Studio

**David Cobbins**  
Founder & Principal Architect, [Frontier Mindworks](https://frontiermindworks.com)

- **GitHub:** [@drc1985](https://github.com/drc1985)
- **Portfolio & Lab:** [frontiermindworks.com](https://frontiermindworks.com)
- **Project Showcase:** [frontiermindworks.com/MetaHumanPerformanceDirector](https://frontiermindworks.com/MetaHumanPerformanceDirector)
- **Epic MegaGrants 2026:** Official Submission

---

## 📄 License & Legal Disclaimer

Released under the permissive [MIT License](LICENSE). Copyright © 2026 David Cobbins.

> **MetaHuman and Unreal Engine are trademarks of Epic Games, Inc. MetaHuman Performance Director is an independent project and is not affiliated with or endorsed by Epic Games.**

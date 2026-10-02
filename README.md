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

### 📢 Development & Roadmap Update

We've been working on significant updates that will be released over the coming months. Some of those updates have been released in GitHub in an unfinished state.

Here's a summary of changes from the original V1 release, and what will be released:

| Core Dimension | Original/v1 Build | Current Production Build (Alpha & ADE) |
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

## 🎬 Video Showcase & Walkthrough

[![MetaHuman Performance Director - October 2026 ADE Showcase](https://frontiermindworks.com/MetaHumanPerformanceDirector/demolinkscreencap.png)](https://frontiermindworks.com/MetaHumanPerformanceDirector/DemoOct.mp4)

- **Interactive Project Page:** [https://frontiermindworks.com/MetaHumanPerformanceDirector](https://frontiermindworks.com/MetaHumanPerformanceDirector)
- **October 2026 ADE Update Video:** [DemoOct.mp4](https://frontiermindworks.com/MetaHumanPerformanceDirector/DemoOct.mp4)
- **Original Grant Submission Video:** [MetaHumanPerformanceDirector.mp4](https://frontiermindworks.com/MetaHumanPerformanceDirector/MetaHumanPerformanceDirector.mp4)
- **Public GitHub Mirror:** [https://github.com/drc1985/MetaHuman_Performance_Director_v2](https://github.com/drc1985/MetaHuman_Performance_Director_v2)

---

## 🧠 The Auteur Drama Engine (ADE)

Unreal Engine has unlocked Hollywood-grade photoreal cinematography, real-time lighting, and virtual production sets for independent filmmakers. But directing virtual human actors has remained locked behind a technical wall: tweaking raw facial curves, keyframing 200+ blendshapes, or relying on mechanical acoustic solvers.

Traditional audio-driven systems solve the phonemes, but they suffer from the **"I love you / I will kill you" paradox**: acoustic waveforms for identical words sound identical, yet dramatically they demand opposite somatic realities.

The **Auteur Drama Engine (ADE)** transforms MetaHuman Performance Director from an animation curve tool into a **psychophysical acting engine**:

1. **Stanislavskian Inner Monologue & Dramatic Subtext:** Synthesizes the psychological space *underneath* spoken dialogue—masking overt emotion while surfacing authentic micro-leakage (masseter clenching, ocular avoidance, breath suppression).
2. **Brechtian Somatic Presence:** Characters don't freeze between lines. They possess continuous vertebral breathing, postural weight transfer, clavicle counter-rotations, and sustained physical attitude.
3. **Chekhovian Psychological Gesture:** Pre-speech lead times (0–1000ms) inject anticipatory gaze saccades, breath intake onsets, and cervical preparation before the first syllable is spoken.

---

## 🎛️ The 4-Tab Filmmaker Workflow

```
[ Tab 1: Baseline ]  ──►  [ Tab 2: Directing Slate ]  ──►  [ Tab 3: Take Review ]  ──►  [ Tab 4: Render Studio ]
 Audio Ingestion &          5 Dials, Voice Input &           A/B Take Auditioning &       Framing Presets &
 Progress Bar (0→100%)      Multi-Beat Timecode Syntax       Structured JSON Inspection   Batch MRQ Export to MP4
```

1. **Tab 1 — Generate Baseline:**
   - Asynchronous, non-blocking Audio2Face baseline generation with a determinative $0\% \to 100\%$ progress bar.
   - Clean audio ingestion (.wav) automatically bound into an isolated Sequencer take.
2. **Tab 2 — Directing Slate:**
   - **5 Calibrated Cinematic Dials:** *Framing Scale* (MCU/CU/Wide), *Facial Nuance*, *Physical Action*, *Subtext Masking*, and *Pre-Speech Lead Time*.
   - **Hold-to-Talk Voice Directing:** Speak or type natural language acting notes.
   - **Timecoded Multi-Beat Syntax:** Direct evolving dramatic beats (`[0s-7s] She is defensive... [7s-14s] Breaks down in grief`) seamlessly inside a single Level Sequence.
   - **Channel Preservation Locks:** Preserve dialogue audio, speech phonemes, gaze, or body layers key-for-key.
3. **Tab 3 — Take Review Station:**
   - Instant A/B take auditioning and non-destructive layer switching directly in Sequencer.
   - Transparent structured JSON performance plan inspection and take management.
4. **Tab 4 — Render Studio:**
   - Performer-aware automated CineCamera framing with calibrated shot sizes (Wide, Medium Close-Up, Close-Up, Extreme Close-Up) and lenses (35mm, 50mm, 85mm, 105mm).
   - Cinematic angles: Dutch tilt, Low angle, Profile, Eye-level.
   - In-editor batch Movie Render Queue (MRQ) automation producing final graded MP4 deliverables with muxed audio.

---

## 🧬 Somatic & Biomechanical Engine

- **Kinetic Vertebral Chain:** Propagates motion organically through Pelvis $\to$ Spine 01–04 $\to$ Neck $\to$ Head, eliminating static mannequin stiffness.
- **Clavicle & Upper Arm Coupling ($k=0.90$):** $100\%$ clavicle displacement coupled to upper arm kinematics to prevent shoulder disarticulation during emotional gestures and posture slumps.
- **Diaphragm Breathing Cycles & Emotional Sighs:** Autonomic breathing rhythms that speed up during anxiety and deep restorative sighs during emotional releases.
- **Duchenne Co-Activation:** Biologically linked zygomaticus major and orbicularis oculi muscle groups ensure authentic smiles rather than artificial mouth-only warping.
- **Soft-Knee Viseme Protection:** Non-linear saturation curves (`_soft_knee_saturate`) prevent blendshape overshoot and mouth tearing during active speech.

---

## ⚡ Recent Updates & Devlog

### October 2026 — v0.3.1+ (Alpha Cycle / ADE): Auteur Drama Engine & 4-Tab Filmmaker Suite
- **Auteur Drama Engine (ADE) Integration:** Integrated psychophysical acting model with Stanislavski subtext processing and Brechtian somatic presence.
- **4-Tab Director Slate UI:** Expanded the Slate architecture into a 4-tab workflow: Baseline Generation ($0\% \to 100\%$ progress bar), Directing Slate (5 dials + voice), Take Review Station (A/B auditioning), and Render Studio (automated CineCamera cuts & MRQ batch export).
- **Timecoded Multi-Beat Directing:** Direct multi-phase acting arcs within a single take using timecode intervals (`[0s-7s]... [7s-14s]...`).
- **Vertebral Spine & Clavicle Dynamics:** Implemented complete 5-segment spinal chain (Pelvis, Spine 01-04) and clavicle counter-rotations with $k=0.90$ arm coupling.
- **Automated Render Studio:** Cinematic lens presets (35mm-105mm), camera framing compensation, and automated Movie Render Queue batch pipeline to MP4.

### September 2026 — v0.3.1: Batch Movie Render Queue (MRQ) & Kinematic Hardening Update
- **Movie Render Queue (MRQ) Batch Rendering:** Added automated take rendering via `MoviePipelinePIEExecutor` (`batch_render_takes.py`):
  - In-editor batch rendering queue supporting sequential take export without blocking the UI.
  - Automated camera binding, framing compensation, and CineCamera cut track generation.
  - Multi-pass rendering with anti-aliasing engine warm-up and automatic dialogue audio muxing into final MP4 deliverables.
- **Cranial Kinematics & Contralateral Asymmetry:**
  - Corrected cranial turn/tilt rotational axes for natural cervical articulation.
  - Implemented contralateral asymmetry suppression to eliminate robotic mirror-symmetry in emotional holds.
  - Expanded affective and emotional lexicons for more expressive take variety.
- **Pre-Speech Breath & Lip-Sync Hardening:**
  - Injected an onset guard for pre-speech breath leads, eliminating phonetic clash and lower-lip tearing before dialogue articulation begins.
  - Biologically calibrated viscoelastic mouth-settle curves so expressions ease smoothly back to rest.
- **Morphological Stemming & NLP Parser Hardening:**
  - Upgraded native C++ `MHPDPerformanceDirectorSubsystem` with comprehensive morphological stemming and adverb-hardening pass, broadening natural language director note recognition.
- **Plugin Ecosystem:** Added first-party `MovieRenderPipeline` dependency declaration in `.uplugin`.

### September 2026 — v0.3.0: 3-Tab Director Slate UI & Sustained Posture Update
- **3-Tab Directorial Slate (`SWidgetSwitcher`):** Ergonomic filmmaking pipeline (Baseline, Direct, Review).
- **Sustained Head & Gaze Posture:** Replaced abrupt return-to-rest drift with natural posture-holding dynamics.
- **Academic & Research Citation:** Added official GitHub citation support via [`CITATION.cff`](CITATION.cff).

### September 2026 — v0.2.0: Directorial Dials & Soft-Knee Viseme Update
- **The Five Directorial Dials:** Framing Scale, Facial Nuance, Physical Action, Subtext Masking, and Pre-Speech Lead Time.
- **Biological Soft-Knee Viseme Protection:** `_soft_knee_saturate()` preventing blendshape overshoot past anatomical limits.

---

## 🔒 100% Local & Offline — Zero Cloud Dependencies

Unlike cloud GenAI services or other comparable tools, MHPD runs **100% locally and offline in Unreal Engine**:

- **Zero Cloud Calls:** No latency roundtrips or external server dependencies.
- **Zero API Keys or Accounts:** No OpenAI, Anthropic, or proprietary cloud accounts required.
- **Studio IP & Privacy First:** Unreleased screenplays, actor likenesses, and voice recordings never leave your workstation.
- **Deterministic IR:** Generates deterministic JSON performance plans conforming to strict schema contracts.

---

## 📋 System Requirements

| Requirement | Supported Version / Specification | Notes |
| :--- | :--- | :--- |
| **Unreal Engine** | **5.8+** (Windows x64) | Tested on UE 5.8 source and launcher builds. |
| **MetaHuman Plugin** | Enabled | Official Epic Games plugin for MetaHuman character support. |
| **MetaHuman Animator** | Enabled | Used for baseline phonetic Audio2Face capture. |
| **Control Rig Plugin** | Enabled (`ControlRig`) | Declared in `.uplugin`; required for skeletal layer blending. |
| **Python Script Plugin** | Enabled (`PythonScriptPlugin`) | Declared in `.uplugin`; required for automated Sequencer asset plumbing. |
| **Movie Render Queue** | Enabled (`MovieRenderPipeline`) | Declared in `.uplugin`; required for automated batch take rendering. |
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
- **In-Editor Voice Input**: Integrated voice transcription allows directors to speak acting notes directly to digital actors.

---

## 📄 Repository Contents & Documentation

- `docs/PERFORMANCE_DIRECTOR_SPECIFICATION.md` — Master technical specification and creative directorial lexicon (28-category acting library, 5 dials math, 4 curve patterns, and Sequencer architecture).
- `schemas/performance_plan.schema.json` — Formal Draft 2020-12 JSON Schema for performance plan validation.
- `docs/PROJECT_DEFINITION.md` — Product definition, user stories, scope, and success criteria.
- `docs/MEGAGRANT_CONCEPT_BRIEF.md` — Concept brief for Epic MegaGrants submission.
- `docs/AGILE_BACKLOG.md` — Epics, user stories, and milestone tracking.
- `docs/PROTOTYPE_ARCHITECTURE.md` — Architecture breakdown of the Unreal C++ and Python pipeline.
- `prototype/` — Standalone Python prototype and CLI testbed.
- `unreal-plugin/` — Native Unreal Engine 5.8 editor plugin (`MetaHumanPerformanceDirector`).

---

## ⚖️ Current Capabilities & Limitations

### What Is Functional Today:
- **RigLogic Facial Directing:** Full procedural keyframing of MetaHuman's 200+ native facial blendshapes and bone controls.
- **Gaze & Saccadic Kinematics:** Procedural gaze breaks, cognitive aversion shifts, and blink synchronization.
- **Cervical & Head Turns:** Driven via Control Rig on the MetaHuman body skeleton (cervical yaw, pitch, roll).
- **Sequencer Pipeline:** Automated take generation, non-destructive layer creation, track locking, and take switching.
- **Offline Semantic Parser:** Local heuristic rule engine mapping director phrasing to calibrated performance plans.

### Current Limitations & What's In Active Development:
- **Body Motion & Gesture Architecture:** *Pluggable Motion Resolver.* With local Kimodo engines maturing (MotionSmith, DDS Motion), general text-to-body motion is commoditized infrastructure. MHPD delegates gross locomotion to a pluggable **Motion Resolver** (supporting MotionSmith, DDS Motion, project clips, or our Tier 0 built-in procedural fallback), while focusing its core R&D on **directorial acting layers** (cervical head posture, ocular gaze saccades, thoracic breathing tension, and relational blocking).
- **Subtext Parsing:** Complex, multi-sentence subtext currently uses a deterministic heuristic engine. An embedded local Small Language Model (SLM) is in development for deeper subtext reasoning without cloud dependencies.
- **Platform Support:** Developed and verified specifically on Unreal Engine 5.8 on Windows x64.

---

## 🗺️ Project Roadmap

- [x] **Phase 1: Alpha Cycle — Working Single-Performer Prototype (Complete & Demonstrable in UE 5.8)**
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

- [ ] **Phase 4: Fab Marketplace Release & Studio / Enterprise Validation**
  - **Studio & Defense Validation:** Formal A/B director-intent testing, virtual production previz trials, and air-gapped simulation validation.
  - **Fab Distribution:** Public release on Epic's Fab marketplace with open performance plan schema.

---

## 🚀 Running the Unreal Engine Demo

1. **Verify Plugins:** Ensure `MetaHuman`, `MetaHuman Animator`, `ControlRig`, `PythonScriptPlugin`, and `MovieRenderPipeline` are enabled.
2. **Open the Demo Map:** In the Unreal Editor Content Browser, open your designated demo level (e.g. `Lvl_IntroRoom`).
3. **Verify the Performer:** Ensure `BP_MH_DemoActor` is placed in the level.
4. **Open the Performance Director Panel:** Navigate to **Window &rarr; MetaHuman Performance Director**.
5. **Direct a Take:**
   - Input a directorial note (e.g., *"She is nervous, but trying to appear confident."*)
   - Adjust directorial dials (*Framing Scale*, *Facial Nuance*, *Subtext Suppression*, etc.)
   - Click **Generate Take** to synthesize the new Sequencer take!

---

## 🧪 Running the Standalone Python Prototype

You can also run the offline planner CLI from the repository root:

```powershell
python .\prototype\mhpd_cli.py "She is nervous, but trying to appear confident. Have her look away before answering." --intensity 0.65 --lock dialogue_audio --lock lip_sync
```

Run test suite:
```powershell
python -m unittest discover -s .\prototype\tests -t .\prototype
```

---

## 📖 Citation & Attribution

If you use **MetaHuman Performance Director** in your academic research, virtual production pipeline, game development, or creative workflows, please cite it using the metadata below:

### BibTeX
```bibtex
@software{Cobbins_MetaHuman_Performance_Director_2026,
  author = {Cobbins, David},
  title = {{MetaHuman Performance Director: Natural Language Directorial System for Unreal Engine MetaHumans}},
  year = {2026},
  month = {9},
  version = {0.3.1},
  organization = {Frontier Mindworks},
  url = {https://github.com/drc1985/MetaHuman_Performance_Director_v2}
}
```

### APA
> Cobbins, D. (2026). *MetaHuman Performance Director: Natural Language Directorial System for Unreal Engine MetaHumans* (Version 0.3.1) [Computer software]. Frontier Mindworks. https://github.com/drc1985/MetaHuman_Performance_Director_v2

*(You can also use GitHub's native **"Cite this repository"** button in the sidebar to export APA or BibTeX directly).*

---

## 👤 Author & Studio

**David Cobbins**  
Founder & Principal Architect, [Frontier Mindworks](https://frontiermindworks.com)

- **GitHub:** [@drc1985](https://github.com/drc1985)
- **Portfolio & Lab:** [frontiermindworks.com](https://frontiermindworks.com)
- **Project Showcase:** [frontiermindworks.com/MetaHumanPerformanceDirector](https://frontiermindworks.com/MetaHumanPerformanceDirector)
- **Epic MegaGrants 2026:** Official Submission

---

## 📄 License & Intellectual Property

Released under the permissive [MIT License](LICENSE).  
Copyright © 2026 David Cobbins. All rights reserved. Permission is hereby granted under the terms of the MIT License, provided that the above copyright notice and this permission notice are included in all copies or substantial portions of the Software.

---

## ⚖️ Trademarks & Legal Disclaimer

> **MetaHuman and Unreal Engine are trademarks of Epic Games, Inc. MetaHuman Performance Director is an independent project and is not affiliated with or endorsed by Epic Games.**

- **Trademarks:** MetaHuman® and Unreal® Engine are registered trademarks or trademarks of Epic Games, Inc. in the United States of America and elsewhere.
- **Referential Compatibility:** All references to "MetaHuman", "Unreal Engine", "RigLogic", and "Control Rig" in this repository and associated documentation are strictly referential, intended solely to describe interoperability, compatibility, and workflow integration with Epic Games' software and technologies.
- **Independence:** MetaHuman Performance Director (MHPD) is an independent open-source tool created by David Cobbins (Frontier Mindworks). It is not sponsored, endorsed, administered by, or officially affiliated with Epic Games, Inc.
- **Proprietary Assets & Logos:** This repository does not distribute, package, or claim ownership of any proprietary Epic Games logos, character meshes, or assets. All MetaHuman assets remain the intellectual property of Epic Games, Inc. and are governed by their respective licenses.

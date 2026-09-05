# MetaHuman Performance Director

![Unreal Engine 5.8](https://img.shields.io/badge/Unreal%20Engine-5.8%2B-blue?logo=unrealengine)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Prototype-orange)
![MegaGrants](https://img.shields.io/badge/Epic%20MegaGrants-2026%20Submission-purple)

**MetaHuman Performance Director (MHPD)** is a native C++ and Python editor plugin for Unreal Engine 5.8+ that enables directors and creators to generate, layer, and direct nuance-rich MetaHuman facial and body performances using natural language notes — directly inside UE5 Sequencer.

---

## 🌟 Key Features

- **Natural Language Intent Directing**: Type or speak acting directions (e.g. *"She turns her head right, glances down nervously, and frowns while speaking"*) directly into the editor panel.
- **Non-Destructive Take System**: Every take generates a dedicated Level Sequence asset. A/B compare baseline and alternate performance takes instantly via the dropdown.
- **Selective Channel Preservation (Channel Locks)**: Lock dialogue audio, speech lip synchronization, facial expressions, eye gaze, or body gestures to preserve speech alignment while layering dramatic nuance.
- **RigLogic DNA Curve Synthesis**: Manipulates over 200 native MetaHuman facial curves using 4 universal animation patterns: **Pulse** (blinks), **Hold** (tension/emotions), **RAMP** (directional gaze shifts), and **Oscillation** (micro-tremor).
- **Body Micro-Behavior Library**: Seamlessly layers conversational body language, shoulder tension, and cervical head turns with native Control Rig constraint blending.
- **In-Editor Voice Input**: Integrated 'Hold to Talk' voice transcription allows directors to speak acting notes directly to digital actors.

---

## 🛠️ Architecture Overview

The plugin implements an automated two-phase directorial pipeline built natively on top of Epic Games' first-party stack (MetaHuman Animator, RigLogic, and Sequencer):

1. **Phase 1: Audio-to-Face Baseline Synthesis**:
   Ingests raw dialogue audio (`.wav`), processes speech acoustic phonemes via MetaHuman Animator, and constructs an isolated baseline Level Sequence with speech curves locked.
2. **Phase 2: Intent-Driven Take Generation**:
   Parses natural language notes through the C++ subsystem into a structured JSON performance plan contract and bakes non-destructive Control Rig layers and expression curves.

---

## 🚀 Installation & Quick Start

1. Clone or download this repository into your project's `Plugins/` folder:
   ```bash
   cd MyProject/Plugins/
   git clone https://github.com/drc1985/MetaHumanPerformanceDirector.git
   ```
2. Enable the **Python Script Plugin** in your Unreal Engine project settings.
3. Rebuild your C++ project and launch Unreal Editor 5.8+.
4. Open the panel via **Window -> MetaHuman Performance Director**.

---

## 📄 License & Ecosystem

Released under the permissive **MIT License**. Created by Frontier Mindworks for the Unreal Engine filmmaking community.

- **Project Website**: [https://frontiermindworks.com/MetaHumanPerformanceDirector](https://frontiermindworks.com/MetaHumanPerformanceDirector)
- **Epic MegaGrants 2026**: Submission Candidate

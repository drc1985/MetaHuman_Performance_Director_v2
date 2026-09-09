# MetaHuman Performance Director — Task & Punchlist

*Persistent engineering roadmap, priority punchlist, and implementation backlog.*

---

## 📌 Priority Punchlist: Kinetic Coupling & Body Layering

### 1. Additive Thoracic & Shoulder Kinetic Layering
> **Context:** When a character already has body animation (Text-to-Motion, Mocap, or Idle), emotional directives must not wipe out or freeze the body. They must apply as a non-destructive mathematical delta ($\Delta$).

- [ ] **Sequencer Additive Mode Integration:**
  - Update `AddControlRigTrackToSequence` in `MetaHumanPerformanceDirectorModule.cpp` to enable `EMovieSceneBlendType::Additive` on the Control Rig parameter section whenever `BodyAnim` is present.
- [ ] **Clavicle & Thoracic Control Rig Keyframing:**
  - Discover and bind `clavicle_l_ctrl`, `clavicle_r_ctrl`, and `spine_04_ctrl` (or FK equivalents).
  - **Frown / Sadness:** Key clavicle depression ($-2.5\text{cm}$) and thoracic flexion ($-6^\circ$ pitch) during the note window.
  - **Surprise / Shock:** Key sharp protective clavicle elevation ($+3.0\text{cm}$) and chest expansion.
  - **Anger / Tension:** Key rigid locked elevation ($+1.5\text{cm}$) and chest bracing.
  - **Smile / Joy / Warmth:** Key clavicle ease back and chest opening ($+2^\circ$).
- [ ] **Dial Scaling Dynamics:**
  - Scale clavicle displacement by `FramingScale` (damped in close-up, amplified $2.4\times$ in wide shot) and `PhysicalAction`.
- [ ] **Hermite Ease Envelopes:**
  - Ensure $300\text{ms}$ ease-in and $450\text{ms}$ ease-out envelopes blend smoothly into existing walking or gesturing cycles with zero snapping.

---

## ✅ Completed & Verified Milestones

- [x] **Five Directorial Dials:**
  - `framing_scale`, `facial_nuance`, `physical_action`, `subtext_suppression`, `preparation_offset_ms` integrated across C++, Python, UI panel, and schemas.
- [x] **Biological Soft-Knee Viseme Collision Avoidance:**
  - Implemented hyperbolic tangent ($\tanh$) soft-knee curve saturation in `generate_acting_take.py` to protect mesh volume and phoneme visemes.
- [x] **Holistic Cervical Kinetic Coupling:**
  - Automatically couples `head_warmth_tilt`, `head_pitch_down`, `head_pitch_up`, `head_turn_left`, and `head_tilt` with facial expressions.
  - Organic $65\% / 35\%$ distribution across `head_fk_ctrl` and `neck_01_ctrl` in `MetaHuman_ControlRig` to eliminate collar tearing.
  - Framing dial actively calibrates head projection ($0.39\times$ close-up vs $0.96\times$ wide shot).
  - Explicit director notes (`"shakes her head"`, `"nods"`) override default emotional coupling.
- [x] **Public Mirror & CDN Optimization:**
  - Cleaned up repository root by migrating preview banner to hosted CDN asset; updated documentation and schemas across both repositories.

---

## 🚀 Phase 2 Production Roadmap

### 1. Fine-Tuned Local Small Language Model (SLM)
- [ ] Construct training dataset pairing natural, unstructured director notes with structured `performance_plan.schema.json` payloads.
- [ ] Fine-tune a lightweight 1B–3B parameter SLM (e.g. Llama-3.2-1B / Phi-3.5-mini / Gemma-2-2B).
- [ ] Deploy local inference via ONNX Runtime / DirectML on workstation GPU (RTX 4070 SUPER) for 100% offline parsing.

### 2. Generative Text-to-Motion Pipeline Expansion
- [ ] Connect generative skeletal kinematics (`motion_generator.py` / 22-joint BVH) directly into Sequencer body micro-behavior tracks.
- [ ] Expand kinetic kinematic library: pacing, nervous shifting, defensive arm folding, leaning against props.

### 3. Multi-Character & Dialogue Turn-Taking (Phase 3)
- [ ] Dual-MetaHuman listening behaviors (active listening micro-nods, eye contact breaks, subtext reactions).
- [ ] Speaker-listener ping-pong coordination across conversational takes.

---

## 🛠️ Verification & Build Housekeeping
- [ ] Compile/rebuild Unreal Engine 5.8 project (`MHPD_DemoEditor`) to load latest C++ binaries.
- [ ] Commit & push latest cervical coupling changes to GitHub (`MetaHumanPerformanceDirector` and `MetaHuman_Performance_Director_v2`).
- [ ] Live take test in UE 5.8 Sequencer.

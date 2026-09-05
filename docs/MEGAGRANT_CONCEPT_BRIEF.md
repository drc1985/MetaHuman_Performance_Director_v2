# Epic MegaGrant Concept Brief

**Project:** MetaHuman Performance Director
**Goal:** Empower film and cinematic directors to intuitively direct and revise MetaHuman performances inside Unreal Engine using semantic, natural-language acting notes.

---

## The Vision

Today, revising a MetaHuman performance requires a specialized technical animator manually adjusting complex facial curves in Sequencer. This creates a bottleneck between the person who knows *what* the performance needs — the director — and the person who knows *how* to key it. A note as simple as *"Make her nervous but trying to hide it — maybe she closes her eyes before answering"* becomes a multi-day round trip through the animation department.

**MetaHuman Performance Director** closes that gap. It is a director-intent orchestration layer built on top of Epic's first-party pipeline (MetaHuman Animator, Sequencer, the MetaHuman facial rig). A director gives a spoken or typed acting note; the system translates it into a structured, multi-channel performance plan and bakes it as a new, fully editable alternate take — expression, gaze, blinks, and facial tension — without ever touching the locked dialogue or lip-sync tracks.

The workflow mirrors a film set: watch the take, give a note, see the new take, compare, give a follow-up note.

---

## Phase 1: The Prototype (Complete and Demonstrable)

The core pipeline is engineered, working, and demoable live in Unreal Engine 5.8:

- **Native UE 5.8 editor plugin** with a director-facing panel: acting-note input (typed or voice-captured), revision range, performance-size control, and per-channel preservation locks.
- **One-click baseline generation:** dialogue audio is fed through MetaHuman Animator's audio-to-face solve and assembled into a ready-to-play Level Sequence (audio + face binding) automatically.
- **Semantic note interpretation:** a heuristic NLP parser converts the director's note into a structured, machine-readable performance plan — per-channel behaviors with weights, timing offsets, and lock states. The plan JSON is the single contract between interpretation and execution, designed so the heuristic parser can be swapped for a local LLM without changing the pipeline.
- **Plan execution as animation:** the executor bakes the plan onto the MetaHuman's RigLogic expression curves (`CTRL_expressions_*`) using four universal curve patterns — **pulse** (counted blinks), **hold** (sustained closure, held tension, expression states), **ramp** (gaze breaks and directional gaze shifts with saccade-speed timing), and **oscillation** (micro-tremor). Solver animation outside the director's revision range is preserved key-for-key.
- **Non-destructive take system:** every acting take is its own isolated Level Sequence; the baseline is never modified. Directors A/B between the baseline and any take with one click from a takes dropdown.
- **Director-grade controls that provably work:** the performance-size dial scales how big every adjustment plays; channel locks (e.g., "preserve gaze") zero out the corresponding plan behaviors before they reach the animation.
- **Current behavior coverage:** counted blinks, sustained eye closure, directional gaze shifts and gaze breaks, micro-tremor, and held expression states (smile, sadness, surprise, disgust, jaw clench) — each verified as clean curve output on the MetaHuman facial rig.

A recorded live demo accompanies this application: a director types a note, and a new take appears in Sequencer seconds later, lip-sync intact.

---

## Phase 2: Production Scale & Deep Innovation (The MegaGrant Ask)

With the pipeline proven end-to-end on facial performance, funding transitions the prototype into a production tool.

**Proposed budget request: $115,000 over 6 months**

### 1. Technical Animation & the Behavior Library — $68,000

The heart of the production tool is a curated, modular library of performance micro-behaviors (posture shifts, gestures, reaction beats, head-movement idioms) that the planner can blend — extending direction beyond the face to the full performance.

- **$4,000 — original motion capture.** Commissioned capture sessions (inertial suit or rented optical stage, with a movement performer) so that 100% of shipped library content is original and redistributable — no marketplace-license ambiguity.
- **$64,000 — 1-2 contract technical animators (~5 months).** Retargeting captured and generated motion to the MetaHuman rig, chopping it into modular micro-behaviors, and converting it into additive animation sequences the planner can layer and blend non-destructively.

### 2. Local AI Development Workstation & Fine-Tuning Compute — $15,000

Film studios will not upload confidential scripts to the cloud, so the shipped product must run its language model **entirely offline on studio hardware**. Critically, that means the deliverable is a model that runs on a *single workstation-class GPU* — not a datacenter appliance.

- **$13,000 — development workstation** (RTX 6000 Ada-class) for local inference, integration, and evaluation on hardware representative of what studios actually deploy.
- **$2,000 — cloud fine-tuning hours.** The tuning corpus (acting notes → performance plans) is synthetic and non-confidential, so fine-tuning can use rented compute; only *inference* must be local. This replaces the heuristic parser with a fine-tuned local LLM behind the same plan-JSON contract.

### 3. Multi-Character Facial Directing — $16,000

Directors rarely direct one actor in a vacuum. This work extends the planner to scene context: parsing multi-actor notes (*"Joe, stay guarded. Bob, let the disappointment show"*) into a master plan and injecting synchronized, per-character take layers onto every MetaHuman in the sequence. Scoped deliberately to **facial and gaze performance**, where the pipeline is proven; full-body multi-character blocking builds on the Phase 2 behavior library and is roadmapped beyond the grant period.

### 4. Voice-Driven Emotion Suggestion UI — $12,000

Rather than reinventing audio-emotion detection, we will integrate NVIDIA's open-source Audio2Face-3D emotion models locally to generate an emotion timeline from the locked dialogue track. MetaHuman Animator already bakes detected mood *into* its solve; the innovation here is surfacing that signal as **editable, director-reviewable micro-expression suggestions** in Sequencer — proposals the director can accept, scale, or reject per beat, keeping creative authority human.

### 5. Validation Studies — $4,000

Participant recruitment and professional review sessions for the evaluation program below.

---

## Evaluation & Success Criteria

1. **Director-intent validation (blind A/B):** independent viewers identify the AI-injected subtext (e.g., "nervous vs. genuinely confident") at a statistically significant rate above the unmodified baseline take.
2. **Animator editability review:** professional technical animators confirm the generated takes are clean, non-destructive, and adjustable within standard Unreal workflows (Sequencer, additive layers, curve editors).
3. **Iteration speed:** note-to-playable-take in under 30 seconds on the reference workstation, preserving the on-set rhythm of direction.
4. **Preservation guarantee:** locked channels (dialogue, lip-sync) are bit-identical between baseline and every generated take.

---

## Ecosystem Benefit & Distribution

The plugin will be released on **Fab** as a commercial product with a free tier: full functionality free for students and educators, and a free evaluation mode (single character, core note-to-take workflow) for all Unreal users. The performance-plan JSON schema and behavior-library format will be published openly so other tools — previs, virtual production, dialogue systems — can emit or consume director intent. Commercial licensing for studio use funds continued maintenance and development beyond the grant period, keeping the tool current as Unreal Engine and MetaHuman evolve.

Every part of the project deepens investment in Epic's stack: it gives MetaHuman a director-facing revision workflow, gives Sequencer an intent layer, and makes Epic's flagship character technology usable by creatives who will never open a curve editor.

## Team & Cost Efficiency

[1-2 sentences: who is building this — background, credits, company.]

A lean core team using AI-assisted engineering keeps overhead low and directs grant funding toward what reviewers can see and studios can use: animation content, applied AI features, and technical art — not traditional headcount.

## Timeline

| Month | Milestone |
|---|---|
| 1 | Mocap capture sessions; behavior library taxonomy; LLM training-corpus schema |
| 2-4 | Library retargeting & additive conversion; local LLM fine-tune replaces heuristic parser behind the same plan contract |
| 4-5 | Multi-character facial directing; Audio2Face-3D emotion-suggestion integration |
| 6 | Blind A/B validation study; animator editability review; Fab release candidate |

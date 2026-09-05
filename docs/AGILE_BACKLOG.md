# Agile Backlog

## Epic 1: Unreal Performance Selection

### Story: Select A Source Take

As a creator, I want to select an existing MetaHuman performance in Unreal Engine so that I can revise a specific take.

Acceptance tests:

- Given a Sequencer level sequence is open, when the user opens MetaHuman Performance Director, then the current sequence can be selected as the source take.
- Given a source take is selected, when the user creates a revision, then the original take remains unchanged.

### Story: Select A Timeline Range

As a director, I want to revise only part of a take so that I can preserve successful sections.

Acceptance tests:

- Given a source take is selected, when the user sets start and end frames, then the generated plan includes that revision range.
- Given a revision range is selected, when a take is generated, then instructions outside the range are not applied.

## Epic 2: Direction Input

### Story: Typed Direction

As a creator, I want to enter ordinary acting direction in text so that I can generate a revised take without animation terminology.

Acceptance tests:

- Given a direction such as "she is nervous but trying to appear confident," when the planner runs, then it identifies nervous confidence as a supported interpretation.
- Given an unsupported note, when the planner runs, then it returns a safe fallback plan instead of failing silently.

### Story: Spoken Direction

As a film director, I want to give a spoken note so that the workflow feels like directing a performer on set.

Acceptance tests:

- Given microphone access is available, when the user records a note, then the note is transcribed and displayed for confirmation.
- Given the transcribed note is edited, when the user generates a take, then the edited text is used as the source direction.

## Epic 3: Performance Planning

### Story: Controlled Behavior Library

As an animator, I want the system to use approved behavior recipes so that generated results are coherent and reviewable.

Acceptance tests:

- Given a supported interpretation, when a plan is generated, then the plan includes only known behavior IDs.
- Given locked channels, when a plan is generated, then locked channels are marked preserved and excluded from modification.

### Story: Intensity Adjustment

As a creator, I want to adjust direction strength so that I can move between subtle and strong performances.

Acceptance tests:

- Given intensity 0.25, when a plan is generated, then channel weights are reduced.
- Given intensity 1.0, when a plan is generated, then channel weights use the behavior recipe defaults.

## Epic 4: Alternate Takes

### Story: Generate New Take

As a director, I want each revision to create a new take so that the original performance is preserved.

Acceptance tests:

- Given an original take and a generated plan, when the revision is applied, then a new alternate take asset is created.
- Given multiple generated plans, when the user reviews takes, then each take is named and selectable.

### Story: Compare Takes

As a director, I want to compare original and revised performances so that I can choose the best interpretation.

Acceptance tests:

- Given original and revised takes exist, when comparison mode is active, then the user can switch between them.
- Given a revised take is selected, when the user accepts it, then it remains editable in Sequencer.

## Epic 5: Editable Output

### Story: Sequencer And Control Rig Output

As an Unreal animator, I want generated results to remain editable so that I can refine the AI-assisted performance.

Acceptance tests:

- Given a generated take, when the animator opens Sequencer, then the revision appears as editable tracks, additive layers, Control Rig keys, or equivalent editable assets.
- Given a channel is locked, when the generated take is inspected, then the locked source track is preserved.

## Prototype Milestones

### Milestone 1: Planner Validation

- Rule-based planner maps typed notes to a structured JSON plan.
- Behavior library supports three to five acting interpretations.
- Unit tests cover supported interpretations, locks, ranges, and intensity.

### Milestone 2: Unreal Editor Shell

- Editor plugin loads in a test Unreal project.
- Basic panel accepts text direction, locks, intensity, and timeline range.
- Planner output can be imported or generated in editor.

### Milestone 3: Editable Take Demo

- One MetaHuman scene has an original take and generated alternate takes.
- At least three directions produce visibly distinct performances.
- Lip sync and dialogue audio remain preserved.

### Milestone 4: Voice Direction Demo

- User records a spoken note.
- The transcription is displayed for confirmation.
- Confirmed direction generates an alternate take.

### Milestone 5: Evaluation

- Viewers identify intended interpretations above baseline.
- Creators compare workflow time against manual revision.
- Animators review editability and usefulness of generated output.


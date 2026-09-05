# MetaHuman Performance Director

## Problem Statement

Creating or revising a believable MetaHuman performance in Unreal Engine requires specialized knowledge of animation, facial rigging, Control Rig, Sequencer, performance capture, and character behavior.

Current tools can generate baseline facial animation from audio or captured performance, apply predefined emotions, or generate individual body motions. However, creators still lack an intuitive way to revise the dramatic intent of an existing performance.

A film or television director may know exactly how a character should perform a scene but may not know how to translate an acting note such as:

- "Make the reaction more restrained."
- "She is nervous but trying to appear confident."
- "Pause before answering and briefly avoid eye contact."
- "He is angry, but he cannot openly challenge his supervisor."
- "Keep the first half of the performance, but make him more defensive after the question."

into coordinated changes across facial expression, gaze, gesture, posture, head movement, timing, vocal delivery, and emotional progression.

In a traditional production environment, a director gives these notes directly to an actor using natural, conversational language. The actor interprets the dramatic intent and performs another take. With digital humans, that same direction must often be translated into technical instructions for animators, riggers, or Unreal Engine developers.

As a result, revising a virtual-human performance can require extensive manual animation work, repeated communication between creative and technical teams, and complete regeneration or re-recording of performances when only a small section needs to change.

## Proposed Solution

MetaHuman Performance Director is an Unreal-native, AI-assisted performance-editing tool that allows creators to revise existing MetaHuman performances using spoken or typed acting direction.

The experience is designed to resemble the way a Hollywood director communicates with a performer on set. Rather than adjusting individual animation curves, keyframes, or rig controls, the director can speak naturally:

- "Let's do another take, but keep the anger underneath."
- "Pause before answering, like you are deciding whether to tell the truth."
- "You are nervous, but you do not want the other person to see it."
- "Make the reaction smaller and more restrained."
- "Keep everything before the final line, but become more defensive at the end."

The director's voice is transcribed and interpreted as a structured performance note. The system identifies the dramatic intent, determines which portion of the performance should change, and creates a coordinated performance plan.

The plan can modify selected performance channels, including:

- Facial expression
- Eye contact and gaze
- Head movement
- Gesture
- Body posture
- Reaction timing
- Pauses
- Emotional intensity
- Emotional progression
- Vocal style or delivery, when supported

The creator can choose which elements of the original performance should remain unchanged, including dialogue audio, lip synchronization, body animation, facial animation, or timing.

Each revision generates a new editable take rather than overwriting the original performance. The director can review the result, give another spoken note, adjust the intensity, revise only part of the timeline, preserve selected performance channels, and continue refining the scene through an iterative director-performer workflow.

The intended interaction is:

1. The director watches the current MetaHuman performance.
2. The director gives a spoken or typed acting note.
3. The system interprets the note and creates an alternate take.
4. The director compares the new take with the original.
5. The director gives additional notes until the desired performance is achieved.
6. An animator can further refine the result using Unreal Engine's existing tools.

The system does not replace actors, directors, or animators. It acts as an AI-assisted translation layer between creative direction and technical animation controls.

The initial version will use a controlled library of validated performance behaviors rather than attempting to generate unlimited animation from scratch. Artificial intelligence will interpret the acting direction and select or combine approved performance controls.

## Primary User Story

As a director, I want to give a MetaHuman spoken acting notes in the same way I would direct a performer on a film set so that I can quickly generate, compare, and refine alternate takes without manually translating my creative intent into animation controls.

## Acceptance Criteria

- The user can select an existing MetaHuman performance in Unreal Engine.
- The user can give an acting note through voice or text.
- Spoken direction is transcribed and displayed for confirmation.
- The user can select the portion of the performance to revise.
- The user can choose which performance channels should remain unchanged.
- The system generates a new alternate take.
- The new take reflects the intended direction across multiple coordinated performance channels.
- The original performance remains unchanged.
- The generated performance remains editable in Unreal Engine.
- The user can compare the original and revised takes.
- The user can increase, reduce, or revise the applied direction.
- The user can provide follow-up notes to refine the performance iteratively.

## Supporting User Stories

### Spoken Performance Direction

As a film or television director, I want to give acting notes using my voice and normal directing language so that working with a MetaHuman feels more like directing a performer than operating animation software.

Example directions:

- "Give me one more take, but make the frustration less obvious."
- "He wants to appear calm, but the pressure is starting to show."
- "Hold the eye contact longer before looking away."
- "Make the final reaction more subtle."
- "Start confidently, then slowly lose control."

### Natural-Language Interpretation

As a creator, I want to describe the intended performance in ordinary creative language so that I do not need to translate my direction into technical animation terminology.

The system should understand concepts such as subtext, concealed emotion, character objective, emotional restraint, escalation, hesitation, deception, status and power dynamics, and changes in intention during a scene.

### Localized Performance Revision

As a director, I want to apply direction to only part of a performance so that I can preserve successful portions of the original take.

Examples:

- Revise only the reaction after a specific line.
- Add a brief gaze break before the response.
- Increase defensiveness during the final five seconds.
- Preserve the opening performance while changing the ending.
- Keep the face unchanged while reducing body gestures.

### Performance-Channel Control

As an animator, I want to lock or unlock individual performance channels so that the system does not alter elements I have already approved.

Possible controls:

- Preserve dialogue audio
- Preserve lip synchronization
- Preserve facial animation
- Preserve body animation
- Preserve timing
- Modify gaze only
- Modify posture and gesture only
- Modify expression without changing the voice

### Alternate Takes

As a director, I want to generate and compare multiple interpretations of the same performance so that I can select the version that best supports the scene.

Example alternate takes:

- Restrained anger
- Open anger
- Concealed anxiety
- Defensive confidence
- Possible deception
- Emotional withdrawal
- Increasing frustration

### Iterative Direction

As a director, I want to give follow-up notes after reviewing a generated take so that I can refine the performance through the same back-and-forth process I would use with a human actor.

Example follow-up notes:

- "That is too strong. Reduce the emotion by half."
- "Keep the face, but make the body less tense."
- "The pause works, but return eye contact sooner."
- "Make the ending more defensive without changing the opening."
- "Try another take with less movement."

### Editable Output

As an Unreal Engine animator, I want the generated result to remain editable in Sequencer and Control Rig so that I can refine the AI-assisted performance rather than receiving a flattened or locked result.

### Intensity Adjustment

As a creator, I want to increase or decrease the strength of an acting direction so that I can quickly move between subtle and more visible performances.

### Non-Animator Accessibility

As a writer, instructional designer, subject-matter expert, or creative producer, I want to explore alternate virtual-human performances without advanced animation expertise so that I can participate directly in the creative process.

## Target Users

- Film and television directors
- Virtual-production teams
- Game cinematic teams
- Animators
- Writers and narrative designers
- Creative producers
- Training and simulation developers
- Instructional designers
- Educators
- Researchers
- Virtual-human developers
- Unreal Engine creators

## Core Value Proposition

MetaHuman Performance Director reduces the gap between creative intent and technical animation execution.

Instead of requiring a director to operate animation software or explain acting notes to a technical intermediary, the system allows the director to communicate using the same natural language they would use with a performer on a film or television set.

The tool translates spoken dramatic intent into coordinated and editable performance changes while preserving the director's ability to review, revise, and approve every take.

The central value is not merely generating animation. It is enabling a familiar directing workflow: watch the performance, give a note, generate another take, compare the results, and continue refining the character's performance.

This makes sophisticated MetaHuman performance direction more accessible to directors, writers, producers, instructional designers, and other creative users while preserving the detailed control required by professional animators.

## Initial Prototype Scope

The first prototype will demonstrate that spoken or typed acting direction can create a perceptibly different and appropriate MetaHuman performance while preserving the original dialogue and lip synchronization.

The prototype will include:

- One MetaHuman
- One short recorded performance
- One Unreal Engine environment
- Spoken and typed direction input
- Automatic speech transcription
- A performance-intensity control
- Timeline-range selection
- Performance-channel locks
- Original and generated take comparison
- Three to five supported acting interpretations
- Editable Sequencer or Control Rig output

Initial acting interpretations may include:

- Openly angry
- Restrained anger
- Nervous but attempting confidence
- Defensive
- Concealing information

## Example Prototype Workflow

The director watches a MetaHuman deliver the line:

> "I already told you everything I know about the missing file."

The director then says:

> "Let's try another take. She is nervous, but she is trying to appear confident. Have her briefly look away before answering and keep the body movement restrained."

The system:

1. Transcribes the spoken direction.
2. Identifies concealed anxiety and projected confidence as the primary performance intentions.
3. Preserves the dialogue audio and lip synchronization.
4. Applies a brief gaze break before the response.
5. Adds subtle facial tension.
6. Reduces gesture amplitude.
7. Introduces a short pre-response pause.
8. Generates a new editable take.
9. Presents the original and revised takes for comparison.

The director can then say:

> "That is close. Keep the gaze change, but make the facial tension less obvious."

The system generates another revision without changing the approved parts of the performance.

## Success Criteria

- Users can provide spoken or typed acting direction.
- The system interprets the direction into a structured performance plan.
- The system produces a visibly different alternate performance.
- Viewers can identify the intended interpretation at a meaningful rate.
- The revision preserves approved elements of the original take.
- The performance appears coordinated rather than assembled from unrelated animations.
- The director can issue follow-up notes and refine the generated performance.
- The generated take remains editable in Unreal Engine.
- Creators report that the workflow feels more natural and accessible than manually producing the same revision.
- Animators report that the system provides a useful starting point rather than restricting their control.


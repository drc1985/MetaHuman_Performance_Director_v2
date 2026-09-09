# MetaHuman Performance Director — Master Specification & Directorial Lexicon

*A unified technical architecture specification and creative performance lexicon for AI-assisted directing in Unreal Engine 5.8+.*

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

---

## 2. The 4 Directorial Linguistic Registers

A director's vocabulary is the bridge between a script's conceptual intent and an actor's lived, physical reality. In the context of MetaHuman performance generation, we categorize directorial inputs into four linguistic registers. Understanding these registers allows the system to parse both amateur ("make them sad") and professional ("swallow the grief") prompts into actionable biomechanical data.

### 1.1 Result Notes (The Amateur Register)
**Definition:** Directives that ask for an end emotional state rather than the action or thought that produces it.
**Examples:** "Look annoyed," "Show pain," "Be frustrated," "Act angry," "Cry more."
**System Translation:** These must be internally translated by the NLP engine into playable actions or somatic states. Result notes often lead to "indicating" or "pushing" (overacting) if not grounded in subtext.

### 1.2 Playable / Action-Verb Directives (Judith Weston / Stanislavski)
**Definition:** Instructions based on transitive verbs. The actor focuses on what they are *doing* to the other character (or themselves), rather than what they are *feeling*.
**Examples:** "Interrogate him," "Withhold the truth," "Deflate his ego," "Sting her with silence," "Beg for forgiveness with your eyes."
**System Translation:** Triggers intense, focused eye contact, specific micro-expressions of assessment, and dynamic shifts in posture depending on whether the action is offensive (leaning in) or defensive (withdrawing).

### 1.3 Somatic & Biomechanical Directives (Chekhov / Laban)
**Definition:** Pure physical mechanics. Bypassing psychology entirely to dictate the physical manifestation of an emotion.
**Examples:** "Lock your jaw," "Drop your chin onto your chest," "Swallow the insult," "Let the breath catch in your throat," "Shoulder shrug," "Blink rapidly."
**System Translation:** Direct mapping to specific blendshapes, skeletal joints, and animation curves. Highly precise.

### 1.4 Subtext & Guise Notes (Internal Masking)
**Definition:** The tension between what the character is feeling and what they are trying to project to the world. It is the art of concealment.
**Examples:** "Smile like everything is fine," "Pretend you didn't hear that," "Look at his hands because you can't bear his eyes," "Laugh it off, but let the eyes stay dead."
**System Translation:** Requires layered animation logic. The primary layer (the mask) might be a smile (mouth/cheeks), while the secondary layer (the truth) leaks through the micro-expressions (eyes/brows/breathing).

---

---

## 3. Master Directorial Language Library (28 Emotional, Positive & Cognitive States)

The MetaHuman Performance Director requires a full-spectrum understanding of human states, categorized into three primary domains: Conflict, Luminous, and Baseline Cognitive states.

### 2.1 Conflict, Tension & Vulnerability States

**2.1.1 Annoyance / Irritation / Impatience**
*The feeling of being hindered or bothered by a minor, persistent obstacle.*
*   **Common Natural Language Prompts:** "Look annoyed," "Sigh impatiently," "Roll your eyes," "Be irritated."
*   **Playable Subtext Notes:** "Dismiss them," "End this conversation as quickly as possible," "Suffer fools gladly but let it show."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Micro-squint, slight asymmetrical lip tightening, flared nostrils, rapid blinking.
    *   **Cervical:** Quick, sharp head tilts or shakes. Jaw clench.
    *   **Thoracic:** Shallow, sharp sighs. Shoulders tense upward slightly.
*   **Temporal Dynamics:** Staccato timing. Quick darts of the eyes. Rushed physical responses.
*   **Framing Adaptations:** In a Close-Up (CU), rely entirely on a micro-sigh and eye shift. In a Wide shot, incorporate weight shifting or foot tapping.

**2.1.2 Pain / Physical Agony / Acute Discomfort**
*The sudden or prolonged sensation of physical distress.*
*   **Common Natural Language Prompts:** "Hurt," "In pain," "Wince," "Gasp in agony."
*   **Playable Subtext Notes:** "Fight through the pain," "Try to hide the injury," "Surrender to the agony."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Deep brow furrow (corrugator), eyes squeezed shut or wide with shock, mouth pulled open or lips pressed tightly together (grimace).
    *   **Cervical:** Neck tendons visible (platysma). Head thrown back or tucked tightly.
    *   **Thoracic:** Irregular, jagged breathing. Spasmodic chest movements. Torso contraction (curling inward).
*   **Temporal Dynamics:** Sudden onset with an immediate contraction, followed by slower, tremulous recovery or sustained tension.
*   **Framing Adaptations:** CU requires intense focus on the eyes watering and jaw tension. Wide shots require full-body curling or bracing against the environment.

**2.1.3 Grief / Sorrow / Defeat / Heartbreak**
*The profound sense of loss, powerlessness, or emotional collapse.*
*   **Common Natural Language Prompts:** "Cry," "Look sad," "Be depressed," "Heartbroken."
*   **Playable Subtext Notes:** "Try not to cry," "Absorb the blow," "Carry the weight of the world," "Hold yourself together so you don't shatter."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Inner brow raise, lip corners pulled down, chin trembling, eyes red/watering, slow blinking.
    *   **Cervical:** Head hangs heavy, loss of neck tone.
    *   **Thoracic:** Drooping shoulders, sunken chest, deep, slow sighs or shuddering breaths.
*   **Temporal Dynamics:** Slow, dragging movements. Pauses are extended. Saccades are sluggish.
*   **Framing Adaptations:** The power is in the stillness. In a CU, the tear escaping a trying-to-be-stoic face is devastating. In a Wide, the slumping silhouette tells the story.

**2.1.4 Frustration / Exasperation / Resignation**
*The feeling of being thwarted, leading to an eventual giving up.*
*   **Common Natural Language Prompts:** "Give up," "Throw your hands up," "Sigh heavily," "Frustrated."
*   **Playable Subtext Notes:** "Hit your head against a brick wall," "Accept the inevitable stupidity of the situation."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Tense lips, blown-out cheeks (exhaling forcefully), hard blinking, looking up at the ceiling.
    *   **Cervical:** Head drops back in disbelief, then falls forward in defeat.
    *   **Thoracic:** Deep, deflating exhale. Shoulders drop significantly on the out-breath.
*   **Temporal Dynamics:** A build-up of tension that snaps, followed by a rapid deflation.
*   **Framing Adaptations:** Can handle slightly larger gestures (rubbing face, dropping head) even in Medium Close-Up (MCU).

**2.1.5 Suppressed Anger / Cold Fury / Resentment**
*Intense rage kept strictly contained beneath a veneer of control.*
*   **Common Natural Language Prompts:** "Mad but hiding it," "Death glare," "Seething," "Cold anger."
*   **Playable Subtext Notes:** "Mentally murder them," "Swallow the venom," "Lock down every muscle so you don't strike them."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Utter stillness. Jaw locked (masseter bulging). Lips pressed thin. Eyes fixed into a hard stare (minimal blinking). Nostril flare.
    *   **Cervical:** Rigid, perfectly still neck. Chin slightly lowered (predatory).
    *   **Thoracic:** Breathing becomes incredibly slow and controlled, almost imperceptible. Shoulders locked down.
*   **Temporal Dynamics:** Glacial pacing. The eyes move before the head. Unblinking sustained holds.
*   **Framing Adaptations:** A CU masterpiece. The lack of movement is the threat. Wide shots should show rigid, aggressive posture.

**2.1.6 Suspicion / Distrust / Scrutiny**
*The active assessment of a potential threat or lie.*
*   **Common Natural Language Prompts:** "Look suspicious," "Don't believe him," "Squint," "Scrutinize."
*   **Playable Subtext Notes:** "Pick apart their lie," "Search their eyes for the truth," "Assess the threat level."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Asymmetrical brow (one up, one down), slight narrowing of the eyes, head tilted slightly, lips slightly pursed.
    *   **Cervical:** Head tilted down and to the side, looking through the top of the eyes.
    *   **Thoracic:** Still, observant breathing. Leaning back slightly or crossing arms (defensive).
*   **Temporal Dynamics:** Slower, deliberate scanning of the other character's face. Pauses before responding.
*   **Framing Adaptations:** CU relies on the eye darts and brow micro-movements.

**2.1.7 Guilt / Shame / Remorse**
*The internal condemnation for one's actions, desiring to hide.*
*   **Common Natural Language Prompts:** "Look guilty," "Ashamed," "Look down," "Sorry."
*   **Playable Subtext Notes:** "Hide your soul," "Make yourself as small as possible," "Avoid the spotlight of their gaze."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Averting gaze (looking down/away), swallowing hard, biting inside of cheek or lip, flushed skin (if simulated).
    *   **Cervical:** Head bowed, chin tucked. Inability to maintain eye contact.
    *   **Thoracic:** Sunken chest, rounded shoulders, protective posture (arms inward).
*   **Temporal Dynamics:** Hesitant, broken movements. Quick glances up followed by immediate gaze aversion.
*   **Framing Adaptations:** The power is in the avoidance. MCU should capture the downward gaze and the inability to look into the lens/at the other character.

**2.1.8 Concealed Attraction / Tenderness / Vulnerability**
*A deep affection or desire that the character is attempting, but failing, to hide.*
*   **Common Natural Language Prompts:** "Look in love," "Secretly like them," "Soft eyes."
*   **Playable Subtext Notes:** "Drink them in," "Try to look away but be pulled back," "Protect your heart."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Softening of the lower eyelids, slight involuntary parting of the lips, pupils dilated, a suppressed half-smile.
    *   **Cervical:** Head tilted slightly, leaning into the other person's space.
    *   **Thoracic:** Shallow, slightly quicker breaths. Heart area open.
*   **Temporal Dynamics:** Lingering glances. Slower, smoother saccades.
*   **Framing Adaptations:** All in the eyes and lips for a CU. The "smize" (smiling with the eyes) is critical.

**2.1.9 Smugness / Arrogance / Condescension**
*The projection of superiority and unwarranted self-satisfaction.*
*   **Common Natural Language Prompts:** "Look smug," "Arrogant," "Smirk," "Think you're better."
*   **Playable Subtext Notes:** "Pat them on the head," "Enjoy the smell of your own brilliance," "Look down on the peasants."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Asymmetrical smirk, chin raised high, slow blinking, relaxed brow.
    *   **Cervical:** Head tilted back, looking down the nose.
    *   **Thoracic:** Expanded chest, broad shoulders, taking up space.
*   **Temporal Dynamics:** Leisurely, unhurried movements. Pauses used to assert dominance.
*   **Framing Adaptations:** The raised chin and looking down the nose works best in angles slightly below eye level (low angle).

**2.1.10 Fear / Dread / Paranoia / Panic**
*The physiological response to an immediate or impending, overwhelming threat.*
*   **Common Natural Language Prompts:** "Scared," "Terrified," "Look around nervously," "Panic."
*   **Playable Subtext Notes:** "Find the exit," "Track the predator," "Try to wake up from the nightmare."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Wide eyes (sclera showing), raised brows, flared nostrils, mouth open for air, pale (if simulated).
    *   **Cervical:** Jerky, erratic head movements tracking sound/movement. Rigid neck.
    *   **Thoracic:** Hyperventilation, rapid chest heaving, shoulders pulled up to protect the neck.
*   **Temporal Dynamics:** Frenetic, erratic. High-frequency micro-movements. Freeze-fight-flight hesitation.
*   **Framing Adaptations:** Wide shots emphasize the smallness of the character against the threat. CU captures the dilating pupils and sweat.

**2.1.11 Exhaustion / Burnout / Apathy**
*Complete depletion of physical, mental, and emotional resources.*
*   **Common Natural Language Prompts:** "Tired," "Dead inside," "Exhausted," "Don't care."
*   **Playable Subtext Notes:** "Survive the next ten seconds," "Conserve every ounce of energy," "Shut down."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Heavy eyelids (ptosis), dark circles (if simulated), slack jaw, completely neutral/dead expression.
    *   **Cervical:** Head struggles to stay upright, lolling slightly.
    *   **Thoracic:** Shallow, minimal breathing. Utterly slumped posture.
*   **Temporal Dynamics:** Extremely slow. Delayed reaction times to stimuli.
*   **Framing Adaptations:** The lack of resistance to gravity. A sense of weight in the face for CU.

**2.1.12 Defiance / Rebellion / Contempt**
*Active, hostile resistance to authority or an opponent.*
*   **Common Natural Language Prompts:** "Rebellious," "Angry," "Glare," "Disrespectful."
*   **Playable Subtext Notes:** "Dare them to strike you," "Spit in their eye mentally," "Hold your ground."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Hard stare, sneer (unilateral lip raise showing canine), narrowed eyes, thrust-out jaw.
    *   **Cervical:** Chin thrust forward, neck stiff.
    *   **Thoracic:** Squared shoulders, chest pushed out, braced posture.
*   **Temporal Dynamics:** Sudden, sharp movements used to punctuate disrespect. Unwavering holds.
*   **Framing Adaptations:** Direct, unblinking eye contact with the lens (if breaking fourth wall) or opponent.

**2.1.13 Incredulity / Disbelief / Cognitive Overload**
*The mind struggling to process information that contradicts reality.*
*   **Common Natural Language Prompts:** "Confused," "Shocked," "What?," "Brain breaking."
*   **Playable Subtext Notes:** "Try to make the math work," "Rewind what you just heard," "Search for the hidden camera."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Scrunched face, deep brow furrow, squinting as if trying to see the words, mouth slightly ajar, slight head shake.
    *   **Cervical:** Head tilted forward or to the side.
    *   **Thoracic:** Breath holding, sudden sharp inhales.
*   **Temporal Dynamics:** "Double takes," long pauses of processing, blinking to "reset" the brain.
*   **Framing Adaptations:** MCU works well to capture the physical manifestation of thinking (the eye darts searching for answers).

**2.1.14 Anticipation / Nervous Excitement**
*The high-energy state preceding a desired or feared event.*
*   **Common Natural Language Prompts:** "Excited," "Can't wait," "Nervous energy," "Jittery."
*   **Playable Subtext Notes:** "Buzz with electricity," "Try to sit on a geyser," "Prepare for launch."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Wide eyes, frequent blinking, tight smile or biting lip, involuntary muscle twitches.
    *   **Cervical:** Constant micro-adjustments of the head.
    *   **Thoracic:** Rapid, shallow breathing. Bouncing shoulders or shifting weight.
*   **Temporal Dynamics:** Rhythmic, restless, high-frequency kinetic energy.
*   **Framing Adaptations:** Better conveyed in wider shots where foot tapping or hand wringing can be seen. In CU, focus on the darting eyes and lip biting.

**2.1.15 Deception / Poker Face / Calculated Composure**
*The active effort to present a false reality while managing internal stress.*
*   **Common Natural Language Prompts:** "Lie," "Poker face," "Hide the truth," "Look calm."
*   **Playable Subtext Notes:** "Sell the lie," "Monitor their reaction," "Don't let them see you sweat."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Overly still or overly symmetrical expressions (fake smiles), maintaining too much eye contact, slightly delayed reactions, micro-expressions of fear/guilt leaking through.
    *   **Cervical:** Rigid, controlled head movements.
    *   **Thoracic:** Controlled breathing that might occasionally catch.
*   **Temporal Dynamics:** Over-controlled. Pauses are slightly too long as the brain calculates the lie.
*   **Framing Adaptations:** The ultimate CU challenge. It requires the engine to generate a "mask" expression, interrupted by split-second (1/25th of a second) micro-expressions of the true emotion.

---

### 2.2 Positive, Luminous & Connected States

**2.2.1 Genuine Joy / Elation / Unfiltered Happiness**
*The spontaneous, unrestrained expression of pure delight.*
*   **Common Natural Language Prompts:** "Look happy," "Genuine smile," "Elated," "Overjoyed."
*   **Playable Subtext Notes:** "Let the sun shine through," "Burst with good news," "Celebrate this exact moment."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Duchenne smile (corners of mouth pulled up and back), glowing orbicularis oculi (crow's feet), raised cheeks, slightly open mouth showing teeth.
    *   **Cervical:** Bouncing chin lift, head tilted slightly back to open the throat.
    *   **Thoracic:** Open chest, elevated sternum, deep and free laughter-breathing.
*   **Temporal Dynamics:** Rapid onset of the expression, sustained organically, fading slowly.
*   **Framing Adaptations:** CU focuses on the crinkle around the eyes (the Duchenne marker). Wide shots emphasize the buoyancy of the entire body.

**2.2.2 Warmth / Affection / Tender Empathy / Compassion**
*The gentle outward projection of care, understanding, and love.*
*   **Common Natural Language Prompts:** "Look caring," "Warm smile," "Empathetic," "Loving."
*   **Playable Subtext Notes:** "Wrap them in a blanket," "Let them know they are safe," "Hold space for their pain."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Soft gaze (slightly relaxed focus), gentle relaxed jaw, subtle symmetrical smile (lips closed).
    *   **Cervical:** Tilted head of care (exposing the neck slightly in trust).
    *   **Thoracic:** Gentle open posture, leaning in slightly toward the subject, slow and steady breathing.
*   **Temporal Dynamics:** Extremely slow and smooth. No sudden jerks or saccades.
*   **Framing Adaptations:** A masterclass in CU eye connection. The gaze must be deeply anchored and forgiving.

**2.2.3 Relief / Catharsis / Tension Release**
*The somatic letting go after a period of intense physical or emotional stress.*
*   **Common Natural Language Prompts:** "Sigh of relief," "Thank god," "Relax," "Tension broken."
*   **Playable Subtext Notes:** "Drop the armor," "Breathe again for the first time in hours," "Let gravity take over."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Eyes squeezing shut briefly before opening softly, peaceful half-smile, tension melting from the brow and masseter.
    *   **Cervical:** Head rolling back gently or dropping slightly forward as if heavy.
    *   **Thoracic:** Long deflating exhale of gratitude, dropping tension in shoulders (a literal lowering of the scapula).
*   **Temporal Dynamics:** A dramatic shift in tempo—from rigid/fast to entirely liquid and slow.
*   **Framing Adaptations:** Best seen in MCU or Medium Shot to catch the visible drop in shoulder tension.

**2.2.4 Pride / Dignified Accomplishment / Nobility**
*A quiet, centered acknowledgment of self-worth or achievement without arrogance.*
*   **Common Natural Language Prompts:** "Look proud," "Dignified," "Noble," "Stand tall."
*   **Playable Subtext Notes:** "Own your space," "Wear the crown comfortably," "Know your inherent value."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Open steady gaze, relaxed calm confidence in the lips (no smirking), smooth brow.
    *   **Cervical:** Elevated chin (not looking down the nose, just parallel to the floor), upright cervical posture.
    *   **Thoracic:** Shoulders pulled back comfortably, heart open, deep grounded breathing.
*   **Temporal Dynamics:** Still, anchored, and unmoved by chaos. Slow blinking.
*   **Framing Adaptations:** Low-angle MCU emphasizes the noble stature and rootedness of the performance.

**2.2.5 Playfulness / Banter / Teasing / Mischief**
*A lighthearted, provocative energy meant to engage or challenge without malice.*
*   **Common Natural Language Prompts:** "Be playful," "Tease him," "Cheeky," "Mischievous."
*   **Playable Subtext Notes:** "Poke the bear for fun," "Invite them to play," "Share an inside joke."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Asymmetric smirk, lively eye darts (saccades), playful wink or micro-squint, dancing eyebrows.
    *   **Cervical:** Cocked head, quick little bobs or tilts.
    *   **Thoracic:** Shoulder shrug, bouncy kinetic energy, loose arms.
*   **Temporal Dynamics:** Highly dynamic. Quick pauses and sudden shifts in focus to keep the scene partner off balance.
*   **Framing Adaptations:** Works wonderfully in CU where the micro-expressions of the asymmetric smile and eye twinkles are visible.

**2.2.6 Wonder / Awe / Reverence / Fascination**
*Complete captivated absorption by something beautiful, massive, or incomprehensible.*
*   **Common Natural Language Prompts:** "Look in awe," "Amazed," "Fascinated," "Blown away."
*   **Playable Subtext Notes:** "Drink in the majesty," "Forget yourself completely," "Stare into the infinite."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Slightly parted lips (slack jaw of wonder), wide unstrained eyes, elevated brows, minimal blinking.
    *   **Cervical:** Slow head tracking upward or outward, neck extended.
    *   **Thoracic:** Breathless pause, or very shallow, quiet breathing as if afraid to break the spell.
*   **Temporal Dynamics:** Time stands still. Sustained holds with incredibly slow, smooth tracking movements.
*   **Framing Adaptations:** The classic Spielberg CU (dolly in on the face of wonder). The eyes must reflect the lighting of what they are seeing.

**2.2.7 Serenity / Calm Contentment / Inner Peace**
*A state of total emotional equilibrium and quiet satisfaction.*
*   **Common Natural Language Prompts:** "Be calm," "Peaceful," "Content," "Zen."
*   **Playable Subtext Notes:** "Float on a quiet lake," "Nothing is missing," "Rest in the present moment."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Gentle half-smile, completely relaxed facial muscle tone, soft eyes, smooth unwrinkled forehead.
    *   **Cervical:** Centered, effortless balance of the head on the spine.
    *   **Thoracic:** Slow deep diaphragmatic breath, perfectly level shoulders, zero physical tension.
*   **Temporal Dynamics:** Languid. Very slow, organic movements that flow into each other without hard stops.
*   **Framing Adaptations:** Wide shots emphasize a harmonious relationship with the environment. CU relies on the softness of the ocular region.

**2.2.8 Gratitude / Humble Appreciation**
*Deep recognition and thankfulness directed toward another person or the universe.*
*   **Common Natural Language Prompts:** "Look thankful," "Grateful," "Appreciative."
*   **Playable Subtext Notes:** "Acknowledge the gift," "Bow to their kindness," "Let them know they saved you."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Soft appreciative smile, slight moisture in eyes (if simulated), softened brow.
    *   **Cervical:** Humble nod, slightly downward and appreciative gaze before returning to eye contact.
    *   **Thoracic:** Hand to the chest/heart (if body is active), slight bowing of the upper torso.
*   **Temporal Dynamics:** A deliberate pause to let the feeling register before a slow, meaningful reaction.
*   **Framing Adaptations:** The MCU captures the slight bow of the head and the earnestness in the eyes perfectly.

---

### 2.3 Neutral, Cognitive & Baseline Professional States

**2.3.1 Attentive Listening / Active Engagement / Focus**
*The active, engaged processing of incoming information from another person.*
*   **Common Natural Language Prompts:** "Just listen," "Pay attention," "Focus on him."
*   **Playable Subtext Notes:** "Absorb every word," "Analyze their argument," "Be the ultimate sounding board."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Steady ocular lock (maintaining eye contact), no emotional distortion, standard blink rate.
    *   **Cervical:** Slight forward cervical angle (leaning in), occasional micro-nod to signal tracking.
    *   **Thoracic:** Still chest, controlled and quiet breathing.
*   **Temporal Dynamics:** Rhythmic nods synchronized to the speaker's cadence. Reactive but not overshadowing.
*   **Framing Adaptations:** The essential CU for dialogue scenes. Prevents the character from looking "dead" while someone else is talking.

**2.3.2 Analytical Deliberation / Deep Calculation / Processing**
*The internal, cognitive churning of problem-solving or complex thought.*
*   **Common Natural Language Prompts:** "Think hard," "Calculate," "Process the data," "Figure it out."
*   **Playable Subtext Notes:** "Run the simulation in your head," "Solve the puzzle," "Connect the dots."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Decoupled gaze into middle distance (looking at nothing), slightly pursed lips, slight brow furrow, minimal blinking.
    *   **Cervical:** Still head, sometimes tilted slightly as if "listening" to internal thoughts.
    *   **Thoracic:** Paused or shallow breathing during the moments of intense calculation.
*   **Temporal Dynamics:** Long static holds punctuated by sudden, sharp eye darts as new ideas connect.
*   **Framing Adaptations:** A CU that relies heavily on the eyes darting back and forth in thought (the "calculating" saccades).

**2.3.3 Professional Stoicism / Clinical Detachment / Objective Composure**
*The maintenance of a purely functional, emotionless facade for professional duty.*
*   **Common Natural Language Prompts:** "Be a professional," "Clinical," "No emotion," "Doctor mode."
*   **Playable Subtext Notes:** "Perform the duty," "Be the neutral observer," "Do not let feelings cloud judgment."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Level eye contact, neutral jaw and lips (no smiles or frowns), flat cheeks.
    *   **Cervical:** Upright, formal posture. Head perfectly level.
    *   **Thoracic:** Controlled conversational cadence. Unwavering, steady breathing.
*   **Temporal Dynamics:** Highly regulated. Movements are economical and strictly purposeful.
*   **Framing Adaptations:** Wide shots emphasize the rigidity of the uniform/posture. CU emphasizes the blank, unreadable slate of the face.

**2.3.4 Casual Conversational Ease / Social Baseline**
*The relaxed, low-stakes baseline of normal human interaction.*
*   **Common Natural Language Prompts:** "Just be normal," "Casual chatting," "Relaxed conversation."
*   **Playable Subtext Notes:** "Pass the time pleasantly," "Shoot the breeze," "Exist without agenda."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Relaxed facial tone, standard blink rate (~15-20/min), occasional brief asymmetrical smiles.
    *   **Cervical:** Natural conversational head cadence (gentle swaying or tilting), breaking eye contact naturally and returning.
    *   **Thoracic:** Relaxed shoulders, natural easy breathing.
*   **Temporal Dynamics:** Fluid, unhurried, and arrhythmic. The most "default" setting of realistic humanity.
*   **Framing Adaptations:** Functions perfectly in two-shots (Medium Wides) where the overall body language conveys ease.

**2.3.5 Daydreaming / Mind Wandering / Reverie**
*The unfocused drifting of consciousness away from the present environment.*
*   **Common Natural Language Prompts:** "Space out," "Daydream," "Zone out."
*   **Playable Subtext Notes:** "Be a million miles away," "Watch the movie in your mind," "Check out of reality."
*   **Biomechanical Kinetic Manifestation:**
    *   **Face:** Soft unfocused gaze (accommodation of the lens to infinity), slack muscles, parted lips.
    *   **Cervical:** Slightly lowered chin or head resting on a hand.
    *   **Thoracic:** Gentle idle breathing, completely slumped or relaxed posture.
*   **Temporal Dynamics:** Utterly static. Blinking becomes very slow or stops entirely for long stretches.
*   **Framing Adaptations:** A slow dolly-in MCU captures the disconnect from the immediate surroundings.

---

---

## 4. The Director's Internal Monologue ("Video Village Monitor Notes")

When watching a take at the video village monitor, a master director isn't just looking at the broad emotion; they are analyzing the biomechanical truth of the performance. This monologue represents the diagnostic feedback loop the MetaHuman Performance Director must simulate across the entire emotional spectrum.

*   **On Authenticity of Joy/Amusement:**
    *   *Monitor Note:* "The smile looks pasted on—it's too commercial. The zygomatic major is firing, but the orbicularis oculi (crow's feet) is dead. It looks like a customer service smile, not genuine warmth. Engage the lower lids and give me a slight head tilt."
*   **On Attentive Listening vs. Dead Posing:**
    *   *Monitor Note:* "Listening feels like an idle pose instead of active listening. They look like a mannequin waiting for their line. Give me a micro-nod on the other actor's keywords, and a slight forward cervical lean. The eyes need to stay locked and tracking."
*   **On Tension and Tells (Suspense):**
    *   *Monitor Note:* "The jaw tension is giving away the twist too early. He's playing the end of the scene at the beginning. Soften the masseter muscle. Let him be relaxed until the specific moment of realization."
*   **On Relief and Tension Release:**
    *   *Monitor Note:* "The relief didn't release the shoulders. We saw the face sigh, but the clavicle is still locked by the ears. The exhale needs to travel down the spine—drop the scapula a full two inches on the out-breath."
*   **On Overacting (Indicating):**
    *   *Monitor Note:* "The face is too animated for a close-up. They are *showing* me the emotion instead of *experiencing* the thought. Dial down the brow movement by 40%. Let the eyes do the heavy lifting."
*   **On Anticipation:**
    *   *Monitor Note:* "She is anticipating the cue. The jaw tense happens a frame before the gunshot. We need to delay the somatic reaction. The body reacts *after* the stimulus, not during."
*   **On the Power of Stillness (Stoicism/Authority):**
    *   *Monitor Note:* "Too much head bobble during the negotiation. It's diluting their authority in the frame. Lock the cervical spine. When they deliver the threat, the only thing that should move is their lips."
*   **On Breathing (Panic vs. Serenity):**
    *   *Monitor Note:* "I'm not believing the panic because the chest is too calm. Add a high-frequency, shallow thoracic breathing curve. Make them fight for air. Conversely, in the meditation scene, the breathing is too visible. Switch it to slow, invisible diaphragmatic expansion."
*   **On Subtextual Leakage (Deception):**
    *   *Monitor Note:* "He's supposed to be lying smoothly, but it looks too perfect. Give me a micro-swallow and a dart of the eyes to the left on the lie. We need to see the cognitive load."

---

## 5. Performance Plan Schema & Directorial Dials Specification

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

---

## 6. The 4 Universal Curve Synthesizers

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

## 7. Holistic Kinetic Coupling: Face-to-Cervical Propagation

In human biomechanics and cinematic directing, the face never acts in isolation. Emotional directives automatically couple facial blendshapes with cervical head/neck rotations:

| Emotional Directive | Primary Facial Channel | Coupled HeadMovement Channel | Kinematic Arc | Biomechanical & Dramatic Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Smile / Joy / Warmth** | `express_smile` | `head_warmth_tilt` | Pitch +6.0°, Roll +8.0° | **Expansion:** Cervical extension (chin lift) and warm lateral head tilt opening the throat to the partner. |
| **Sadness / Frown / Defeat** | `express_sadness` | `head_pitch_down` | Pitch -16.0° | **Contraction:** Cervical flexion (head drop) under gravity; defeat caves the neck downward. |
| **Surprise / Shock** | `express_surprise` | `head_pitch_up` | Pitch +16.0° | **Startle Reflex:** Rapid cervical pitch upward and cranial retraction away from stimulus. |
| **Disgust / Repulsion** | `express_disgust` | `head_turn_left` | Yaw -22.0° | **Aversion Withdrawal:** Diagonal cranial recoil turning the face away from offensive stimulus. |
| **Jaw Tension / Clench** | `clench_jaw` | `head_pitch_down` | Pitch -6.0° | **Bracing / Advance:** Cranial forward lock; animal bracing protecting the carotid artery. |
| **Gaze Shift / Cognitive Thinking** | `gaze_shift_*` | `head_tilt` | Roll +14.0° | **Cognitive Decoupling:** Counter-rotational head cock accompanying saccadic eye movement to access memory. |
| **Direct Head Prompts** (nods/shakes) | Preserved | `head_nod`, `head_shake`, `head_tilt` | Multi-axis rotation | Explicit director instruction overriding default emotional coupling. |

**Scale Dynamics:**  
All coupled head movements are scaled dynamically by the directorial dials:
$$\text{ScaledWeight} = \text{BaseWeight} \times \text{PhysicalMultiplier} \times \text{FramingBodyFactor}$$
In a **Cinematic Close-Up** (`framing_scale` = 0.20), $\text{FramingBodyFactor} \approx 0.49\times$, dampening head motion so the actor remains within the lens frustum and focus plane. In a **Theatrical Wide** (`framing_scale` = 0.97), $\text{FramingBodyFactor} \approx 1.47\times$, amplifying head motion so the emotion projects clearly across the wide shot silhouette.

---

---

## 8. Worked Directorial Example & RigLogic Curve Breakdown

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

---

## 9. Non-Destructive Layering & Soft-Knee Viseme Collision Avoidance

A primary hazard in facial directing is **viseme interference**: when an emotional curve (e.g. `mouthSmileLeft`) collides with a phonetic curve (e.g. `mouthPucker` during an "oo" sound), causing unnatural mouth stretching or muffled speech appearance.

To prevent this, MHPD executes two safeguards:

1. **Soft-Knee Viseme Headroom Clamping:**  
   During active phonetic windows identified from the baseline audio, conflicting lower-face emotional curves are attenuated:
   $$W_{\text{effective}} = W_{\text{target}} \cdot \left(1.0 - \kappa \cdot W_{\text{phonetic}}\right)$$
   Where $\kappa \approx 0.65$ preserves speech readability while retaining emotional coloration.
2. **Dedicated Sequencer Sub-Tracks:**  
   Curves are never baked destructively onto the raw capture track. Instead, they are generated as **Additive Sequencer Weight Tracks** or **Control Rig Layer Sequences**, allowing artists to dial the blend weight or tweak individual keyframes in Sequencer curve editor at any time.

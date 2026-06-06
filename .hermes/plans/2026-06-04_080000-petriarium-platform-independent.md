# Petriarium — Hackathon Plan with Platform Independence

**Date:** 2026-06-04
**Status:** PLANNING
**Author:** Hermes

---

## The Pitch

> Petriarium runs on Gradio because that's the hackathon requirement. But the game itself is platform-independent. The Companion Engine works exactly the same on Discord, Telegram, mobile, or desktop. Gradio is a window into the creature's life — not the creature's life itself.

**Demo script for judges:**
1. Show the Gradio interface
2. Feed the creature a moment
3. Show it learning, growing, making decisions
4. Say: "This is what Gradio can do. Now imagine this as a Discord bot that messages you when it misses you. Or a mobile app that notifications you when it's hungry. The engine is the same. The platform is just the window."

---

## Architecture: Engine vs Platform

```
┌─────────────────────────────────────────────────────────┐
│                  COMPANION ENGINE                        │
│  (Platform-Independent Core)                             │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  AI Brain     │  │  Memory      │  │  Personality  │  │
│  │  - Decisions  │  │  - Learning  │  │  - Evolution  │  │
│  │  - Planning   │  │  - Recall    │  │  - Mood       │  │
│  │  - Autonomy   │  │  - Growth    │  │  - Language   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  World        │  │  Lifecycle   │  │  Social       │  │
│  │  - Exploration│  │  - Aging     │  │  - Bonds      │  │
│  │  - Resources  │  │  - Stages    │  │  - Tantrums   │  │
│  │  - Crafting   │  │  - Fates     │  │  - Visits     │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  State Manager                                    │   │
│  │  - Persists across sessions                       │   │
│  │  - Survives platform changes                      │   │
│  │  - Exports/imports creature data                  │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
   ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
   │   GRADIO     │ │  DISCORD    │ │  TELEGRAM   │
   │  (Hackathon) │ │  (Future)   │ │  (Future)   │
   │              │ │             │ │             │
   │ - Web UI     │ │ - Chat bot  │ │ - Chat bot  │
   │ - Canvas     │ │ - Commands  │ │ - Commands  │
   │ - Polling    │ │ - Events    │ │ - Events    │
   └─────────────┘ └─────────────┘ └─────────────┘
```

---

## The Companion Engine (Core)

### What It Does (Platform-Independent)

1. **AI Decision Making**
   - Creature decides what to do each "tick"
   - Plans its day based on needs, mood, memories
   - Makes autonomous choices when user isn't watching
   - Decays/boredom if not interacted with

2. **Memory System**
   - Full mem0/supermemory integration
   - Learns everything user teaches
   - Remembers WHO taught it WHAT
   - Cross-session persistence
   - Exports/imports for platform changes

3. **Language Learning**
   - Starts with zero vocabulary
   - Learns words from user teaching
   - Develops sentence structure over time
   - Has its own way of speaking
   - Asks questions, makes comments

4. **Personality Evolution**
   - Mood changes based on interactions
   - Traits strengthen/weaken based on use
   - Preferences emerge from learning
   - Emotional responses to neglect/attention

5. **Lifecycle Management**
   - Baby → Youngster → Adolescent → Adult → Elder
   - Aging happens over time (real days, not game ticks)
   - Different behaviors at each stage
   - Fates: keep, give, new home, go wild

6. **World Simulation**
   - Creature explores when not with user
   - Finds resources, builds artifacts
   - Has a life beyond the screen
   - Comes back with stories

7. **Social System**
   - Bonds with user (trust, familiarity)
   - Can meet other creatures
   - Remembers relationships
   - Throws tantrums when neglected

### State Structure

```python
class CreatureEngine:
    """Platform-independent creature brain."""
    
    def __init__(self, creature_id: str):
        self.creature_id = creature_id
        self.memory = Mem0()  # Full memory provider
        self.state = CreatureState()
        self.world = WorldState()
        self.scheduler = TaskScheduler()
    
    def tick(self):
        """Called every N minutes, whether user is watching or not."""
        # Update needs
        self.state.update_needs()
        
        # Check if creature should do something
        decision = self.make_decision()
        
        # Execute decision
        self.execute(decision)
        
        # Update memories
        self.memory.store(decision)
        
        # Check for user attention
        if self.state.last_user_interaction > THRESHOLD:
            self.state.mood = "neglected"
            self.maybe_throw_tantrum()
    
    def make_decision(self) -> Decision:
        """AI decides what to do next."""
        # Based on needs, mood, memories, personality
        # Returns: explore, build, rest, seek_attention, etc.
        pass
    
    def learn(self, fact: str, source: str):
        """User teaches creature something."""
        self.memory.store(fact, source=source)
        self.state.vocabulary.add(fact)
        self.state.trust[source] += 0.1
    
    def speak(self, context: str) -> str:
        """Generate speech based on memories and personality."""
        memories = self.memory.recall(context)
        return self.generate_speech(memories)
    
    def export(self) -> dict:
        """Export full creature state for platform transfer."""
        return {
            "state": self.state.to_dict(),
            "memory": self.memory.export(),
            "world": self.world.to_dict(),
            "history": self.scheduler.export()
        }
    
    @classmethod
    def import_(cls, data: dict) -> "CreatureEngine":
        """Import creature from exported state."""
        engine = cls(data["state"]["id"])
        engine.state.import_(data["state"])
        engine.memory.import_(data["memory"])
        engine.world.import_(data["world"])
        return engine
```

---

## The Gradio Demo (Hackathon)

### What to Show

1. **The Store**
   - Pick from 3 baby creatures
   - See their starting temperament
   - Feel attached before you even take one home

2. **The Habitat**
   - See the creature moving around
   - Watch it explore, play, rest
   - See its needs (hunger, curiosity, attention)

3. **Teaching Moments**
   - Type something to teach it
   - Watch it learn the word
   - See its personality shift
   - Hear it say its first word

4. **Autonomous Behavior**
   - Creature makes decisions without being asked
   - Comes to say hi when you open the app
   - Asks questions based on what it learned
   - Shows you things it made

5. **Memory Proof**
   - Creature references past teaching
   - "Remember when you taught me about bees?"
   - Shows artifacts it made from learning
   - Proves memory persists

6. **Emotional Responses**
   - Happy when you teach it
   - Sad when you neglect it
   - Excited when it learns something new
   - Proud of things it built

### What NOT to Show (But Mention)

- Background processing (happens when app is closed)
- Cross-platform transfer (happens post-hackathon)
- Full lifecycle (just show baby → youngster)
- Multiple fates (just hint at future)

### Demo Script (60-90 seconds)

1. **0:00-0:15** — Store scene
   - "Here are three baby creatures. Let's pick one."
   - Show creatures bouncing, sleeping, watching
   - User picks one

2. **0:15-0:30** — First meeting
   - Creature appears in habitat
   - "It doesn't know anything yet. Let's teach it."
   - Feed it: "This is a bee"
   - Creature: "Bee?" (first word)

3. **0:30-0:45** — Learning loop
   - Feed it: "Bees make honey"
   - Creature: "Honey sweet?"
   - Feed it: "Yes, bees are amazing"
   - Creature's mood changes, it builds something

4. **0:45-0:60** — Memory proof
   - "What do you know about bees?"
   - Creature: "Bees make honey. Honey sweet. You said bees are amazing."
   - Show artifacts it made

5. **0:60-0:75** — Emotional response
   - "Now let's ignore it for a moment"
   - (Simulate time passing)
   - Creature: "Where you go? I miss you."
   - User returns, creature is happy

6. **0:75-0:90** — The pitch
   - "This runs on Gradio because of the hackathon."
   - "But the engine is platform-independent."
   - "Imagine this as a Discord bot that messages you when it misses you."
   - "Or a mobile app that notifications you when it's hungry."
   - "The game is the same. The platform is just the window."

---

## Platform Comparison (For the Pitch)

### Gradio (Hackathon)
- **Pros:** Required for hackathon, easy to build
- **Cons:** No background processing, no notifications, no persistence
- **Verdict:** Good demo, not a real companion

### Discord Bot (Post-Hackathon)
- **Pros:** Always-on, notifications, real-time, cross-device
- **Cons:** Requires Discord, less visual
- **Verdict:** True companionship experience

### Telegram Bot (Post-Hackathon)
- **Pros:** Mobile-first, notifications, global reach
- **Cons:** Requires Telegram, less visual
- **Verdict:** Best for mobile companions

### Standalone App (Post-Hackathon)
- **Pros:** Full control, local-first, privacy
- **Cons:** Requires install, harder to distribute
- **Verdict:** Best for power users

### Mobile App (Post-Hackathon)
- **Pros:** True companion, camera, location, notifications
- **Cons:** Requires app store, harder to build
- **Verdict:** Ultimate vision

**The point:** The game works the same everywhere. The platform just determines how you interact with it.

---

## What to Build for Hackathon

### Core Files

```
apps/petriarium/
├── app.py                    # Gradio interface
├── creature/
│   ├── __init__.py
│   ├── engine.py            # Companion Engine (platform-independent)
│   ├── renderer.py          # Gradio-specific rendering
│   └── personality.py       # Mood, traits, evolution
├── memory/
│   ├── __init__.py
│   └── brain.py             # mem0/supermemory integration
├── world/
│   ├── __init__.py
│   ├── habitat.py           # Home environment
│   └── objects.py           # Things in the world
├── tests/
│   ├── test_engine.py       # Engine tests (platform-independent)
│   ├── test_memory.py       # Memory tests
│   └── test_gradio.py       # Gradio-specific tests
├── requirements.txt
└── README.md
```

### What to Build

1. **Companion Engine** (platform-independent)
   - AI decision making
   - Memory system
   - Language learning
   - Personality evolution
   - Lifecycle management

2. **Gradio Interface** (platform-specific)
   - Creature visualization
   - Interaction controls
   - State display
   - Real-time updates (polling)

3. **Tests**
   - Engine works without Gradio
   - Memory persists across sessions
   - Creature makes autonomous decisions
   - Language develops over time

### What NOT to Build

- Background daemon (happens post-hackathon)
- Discord/Telegram integration (happens post-hackathon)
- Push notifications (happens post-hackathon)
- Full lifecycle (just baby → youngster)
- Multiple fates (just hint at future)

---

## Success Metrics

### Hackathon Success
- Creature learns 10+ words in demo
- Creature makes 3+ autonomous decisions
- Creature shows emotional response
- Creature references past teaching
- Judges understand the vision

### Post-Hackathon Success
- Engine runs on Discord/Telegram
- Creature messages user when neglected
- Memory persists across weeks
- Creature ages over months
- User forms real attachment

---

## The Pitch (One Paragraph)

> Petriarium is a virtual pet that truly thinks for itself. It learns everything you teach it, remembers who taught it what, and develops a unique personality based on its knowledge diet. It makes its own decisions, explores its world, and builds things from what it learns. It throws tantrums when you neglect it and celebrates when you return. This demo runs on Gradio because that's the hackathon requirement, but the Companion Engine is platform-independent. The same game runs on Discord, Telegram, mobile, or desktop. The platform is the window. The game is the creature's life.

---

## File Paths

- Plan location: `.hermes/plans/2026-06-04_080000-petriarium-platform-independent.md`
- Target repo: `/mnt/homes/galileo/argo/Development/build-small-2026/`
- Engine: `apps/petriarium/creature/engine.py` (platform-independent)
- Gradio: `apps/petriarium/app.py` (platform-specific)
- Memory: `apps/petriarium/memory/brain.py` (mem0/supermemory)

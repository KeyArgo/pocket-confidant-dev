# Petriarium — Full Program Plan

**Date:** 2026-06-04
**Status:** PLANNING
**Author:** Hermes

---

## What This Actually Is

A modern Tamagotchi x Tomodachi Life hybrid. Not a Gradio form with an SVG blob. A living creature in a visible world that learns from what you teach it, develops personality from its memories, and becomes your companion — or doesn't.

> A tiny creature born curious. It doesn't know how to speak, but it listens. It wanders its small world doing creature things. When you visit, it comes running to say hi. What you teach it goes into its brain — and that brain becomes its personality.

---

## The Core Concept

### The Creature
- **Starts as a youngster**: small, bouncy, curious, attention-seeking
- **Knows ALMOST NOTHING** — a blank slate, like a newborn mind
- **Animated**: moves around, plays, explores, reacts
- **Cannot speak** but communicates through actions and expressions
- **Craves attention** — comes to the user when they're nearby
- **Gets bigger and smarter over time** (Tamagotchi-style growth)
- **Personality emerges** from its memory + temperament
- **Can become friendly or wary** based on treatment

### The World
- **Small visible area** the creature lives in (garden, room, clearing)
- The creature **wanders around** doing things: playing, exploring, resting
- User can **see the creature on a map/view and zoom in**
- The creature has a **life even when you're not watching**
- Environment **responds to the creature** (it moves grass, picks up sticks, etc.)

### The Blindspot (Hidden Large World)
- The creature's world is **huge**, but you only see a small viewport
- The unseen world contains **resources** the creature can use
- The creature **explores the Blindspot** while sleeping or idle
- It returns with **strange resources**: copper thread, glass seeds, static moss, moon screws
- **Telemetry panel** shows what's happening out there (not a full map)

### Two-Tier Food System

#### Regular Food (Survival)
- Found lying around the world: berries, mushrooms, seeds, bugs
- Keeps the creature alive and growing
- Increases size/age but **NOT intelligence**
- Creature can find this on its own while wandering

#### Intelligence Food (Learning Capacity)
- Special items: glowing mushrooms, starfruit, crystal drops
- User must **EARN them or FIND them in the world**
- Increases the creature's **ability to learn complex things**
- Without it: creature learns only basic survival
- With it: creature can understand schedules, emotions, abstract ideas
- **Scarcity creates value** — user wants to find these

### Learning Capacity
- Creature starts with **LOW learning capacity** (knows almost nothing)
- Regular food: no effect on learning
- Intelligence food: increases max learning capacity
- Higher capacity = can learn more complex things

### What You Can Teach It
- About **YOUR world** (the world it cannot see)
- Your schedule, your life, your feelings
- Abstract concepts (love, fear, time, weather)
- Practical things (safety, danger, kindness)
- The creature **remembers WHO taught it what**
- You become its teacher — and that bond matters

### What It Learns in the Wild
- Survival skills (finding food, shelter, danger)
- Simple associations (rain = wet, sun = warm)
- Creature instincts (curiosity, caution, play)

### The Teacher Relationship
- If you teach the creature, you become its teacher
- Creature **trusts its teacher more**
- Teacher can teach complex things that wild learning cannot
- Creature **remembers WHO taught it what**
- Creature may **ask the teacher questions** (via actions/expressions)
- The teacher-creature bond is the core relationship

### Module Drift & Repair
- Sometimes parts drift: lens foggy, grip slack, memory noisy
- User helps with gentle actions: tune lens, wind thread, clean sensor
- **No guilt, no punishment** — just consequence and care
- If ignored, the world becomes **weird and less functional**, not deadly

---

## The Memory Brain

The creature's personality comes from its memory. Use one of these as inspiration:

- **mem0** (57.7K stars) — Universal memory layer
- **supermemory** (25.4K stars) — Fast, scalable memory engine
- **OpenViking** (25.1K stars) — Context database
- **hindsight** (15.6K stars) — Agent memory that learns

### Memory Tables (Custom Implementation)
```
events      what happened
facts       what the creature believes
bonds       what it knows about the caretaker
interests   topics it wants more of
artifacts   things it made from memories
dreams      compressed summaries from idle time
```

### Recall Packet for LLM
```
Immediate:  last 5 interactions
Recent:     last session summary
Deep:       3 strongest memories
Bond:       what I know about my caretaker
Interest:   what I want to learn next
```

---

## What Makes This Cool

The pet starts naive because it has no world model. It only knows:
- its cage
- the caretaker
- a few feelings
- whatever the user feeds it

Over time, it becomes shaped by its diet:

- **Feed it astronomy** → it becomes cosmic, quiet, pattern-seeking
- **Feed it repair manuals** → it becomes mechanical, practical, starts building
- **Feed it poetry** → it becomes lyrical and dramatic
- **Feed it bug facts** → it becomes obsessed with legs and tiny societies
- **Feed it family stories** → it becomes sentimental and protective

**No two pets are alike because no two knowledge diets are alike.**

### Curiosity Loop
The pet starts asking for more information:

> User feeds it: "This is a photo of a Raspberry Pi."
> Pet: "This is a small thinking brick. Does it have dreams, or only pins?"
> Later: "I want to know what the pins touch. Feed me a diagram?"
> If user feeds the diagram: "I understand now. The pins are little doors. I would like doors."
> Then the habitat changes: it builds fake GPIO doors on the cage wall.

### Personality Shaped By Knowledge
The pet has an evolving interest graph:

```json
{
  "obsessions": {
    "doors": 0.82,
    "bees": 0.44,
    "static": 0.31
  },
  "style": {
    "technical": 0.7,
    "poetic": 0.2,
    "mischievous": 0.6
  },
  "questions_it_keeps_asking": [
    "What is outside?",
    "Can small things build bigger minds?",
    "Why do bees not use screws?"
  ]
}
```

This drives:
- what it asks for next
- what it builds
- how it speaks
- what it remembers
- how it reacts to neglect

---

## Best Demo

1. Hatch two identical pets.
2. Feed Pet A a bee fact.
3. Feed Pet B a robot schematic.
4. Fast-forward.

Pet A has built a honeycomb shrine and asks:
> "Do caretakers have queens, or just calendars?"

Pet B has built baby robots and says:
> "I made three smaller me's. They are worse at hinges but better at waiting."

**That instantly proves uniqueness.**

---

## Technical Architecture

```
┌─────────────────────────────────────────────────────┐
│                    GRADIO UI                         │
│  ┌──────────────┐  ┌──────────────────────────────┐ │
│  │  World View   │  │  Creature Card               │ │
│  │  (Canvas)     │  │  - mood, age, energy         │ │
│  │  creature     │  │  - memories recalled         │ │
│  │  wandering    │  │  - last interaction          │ │
│  └──────────────┘  └──────────────────────────────┘ │
│  ┌──────────────────────────────────────────────────┐│
│  │  Feed Box: "Teach your creature..."              ││
│  └──────────────────────────────────────────────────┘│
│  ┌──────────────────────────────────────────────────┐│
│  │  Blindspot Telemetry                             ││
│  │  Depth: ████░░░  Resources: glass seed, copper   ││
│  └──────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
┌────────────────┐   ┌─────────────────┐
│  Creature       │   │  Memory Brain   │
│  Engine         │◄──│  (custom SQLite │
│  - movement     │   │   + retrieval)  │
│  - needs        │   │  - stores       │
│  - animation    │   │  - recalls      │
│  - state        │   │  - associates   │
└────────────────┘   └─────────────────┘
```

---

## Project Structure

```
apps/petriarium/
├── app.py                    # Main Gradio app
├── creature/
│   ├── __init__.py
│   ├── engine.py            # Movement, needs, animation state
│   ├── renderer.py          # Canvas/HTML rendering
│   └── personality.py       # Mood, traits, evolution
├── world/
│   ├── __init__.py
│   ├── map.py               # Grid/world definition
│   └── objects.py           # Things in the world
├── memory/
│   ├── __init__.py
│   └── brain.py             # Memory provider integration
├── blindspot/
│   ├── __init__.py
│   ├── explorer.py          # What the creature does in the hidden world
│   └── resources.py         # Resource types and recovery
├── tests/
│   ├── test_creature.py
│   ├── test_memory.py
│   ├── test_world.py
│   └── test_blindspot.py
└── requirements.txt
```

---

## MVP Scope (Hackathon)

### Phase 1: Creature Engine
- [ ] Creature class with position, mood, energy, age
- [ ] Needs system: hunger, curiosity, attention, rest
- [ ] Behavior tree: idle, wander, play, seek-attention, rest, investigate
- [ ] Animation state: bounce, sit, run, sleep, curious-tilt, happy-wiggle

### Phase 2: World
- [ ] Small grid world (20x20 or 30x30)
- [ ] Tile types: grass, path, flower, rock, water, nest
- [ ] Creature movement to random tiles
- [ ] World rendering (HTML5 Canvas or CSS grid)

### Phase 3: Memory Brain
- [ ] Store moments when user feeds creature
- [ ] Recall on interaction
- [ ] Build associations
- [ ] Personality emergence from memories

### Phase 4: Two-Tier Food
- [ ] Regular food spawning in world
- [ ] Intelligence food (rare, earned)
- [ ] Learning capacity system
- [ ] Feeding interaction

### Phase 5: Interaction
- [ ] Feed input (user types moment)
- [ ] Creature reaction
- [ ] Memory storage
- [ ] Response generation

### Phase 6: Blindspot (Stretch)
- [ ] Telemetry panel
- [ ] Resource recovery
- [ ] Module drift
- [ ] Repair interaction

### Phase 7: Polish
- [ ] Creature aging
- [ ] Relationship tracking
- [ ] World life (creature does things when not watching)
- [ ] Sound/effects (optional)

---

## Two Builds (DeepSeek vs MiniMax)

Run the same prompt through two models:
- **DeepSeek**: opencodego-deepseek-v4-flash
- **MiniMax**: opencodego-minimax-m3

### Comparison Criteria
1. **Alive feeling** — which creature feels more like a living thing?
2. **Memory quality** — which brain learns and recalls better?
3. **World richness** — which world feels more real?
4. **Interaction naturalness** — which conversation feels more natural?
5. **Charm factor** — which one do you want to keep playing with?

---

## Tests / Validation

### Creature Tests
- [ ] Creature moves to valid tiles
- [ ] Needs decay over time
- [ ] Creature seeks attention when lonely
- [ ] Creature rests when tired

### Memory Tests
- [ ] Moments get stored with context
- [ ] Creature recalls relevant past moments
- [ ] Repeated memories strengthen traits
- [ ] Personality drifts based on knowledge diet

### World Tests
- [ ] Food spawns in world
- [ ] Creature can find food
- [ ] Intelligence food is rare
- [ ] World state persists

### Integration Tests
- [ ] Feed creature → memory stored → personality changed
- [ ] Creature wanders → finds food → eats → grows
- [ ] User teaches → creature learns → creature asks follow-up
- [ ] Two creatures with different diets develop differently

### Demo Tests
- [ ] Cold user understands what to do in 90 seconds
- [ ] Creature feels alive and responsive
- [ ] Personality visibly changes
- [ ] Two builds feel distinct

---

## Risks & Tradeoffs

### Risks
- Memory providers may have complex setup — use custom SQLite for MVP
- Canvas animation in Gradio is limited — use HTML/CSS
- Two workers may produce very different architectures — comparison may be hard

### Tradeoffs
- **Canvas vs CSS** — Canvas smoother but harder; CSS simpler but choppier
- **Memory complexity** — full memory provider vs simple SQLite; start simple
- **World size** — bigger world = more work; start with 20x20
- **Blindspot** — cool concept but may be too complex for MVP; make it stretch

### Open Questions
- Which memory provider should each worker use? (Let them choose or use custom)
- How big should the world be? (Suggest 20x20)
- Should the creature have a name? (Let it generate one)
- How does the creature "speak"? (Actions/expressions only, no text)
- Is the Blindspot core or stretch? (Make it stretch for MVP)

---

## What NOT to Build (MVP)

- No complex 3D graphics
- No multiplayer
- No real-time sync
- No mobile app (web only for hackathon)
- No full Hermes/agent harness
- No external memory provider (use custom SQLite)
- No complex autonomous behavior
- No guilt-heavy mechanics
- No health bars or survival stress

---

## Next Steps

1. **Clean up current repo** — remove unused files from previous attempt
2. **Write worker prompt** — capture this vision clearly
3. **Launch two workers** — DeepSeek and MiniMax
4. **Monitor progress** — check logs, verify tests
5. **Integrate best parts** — merge improvements from both lanes
6. **Polish and compare** — which creature feels more alive?

---

## File Paths

- Plan location: `.hermes/plans/2026-06-04_073000-petriarium-full-plan.md`
- Target repo: `/mnt/homes/galileo/argo/Development/build-small-2026/`
- New app: `apps/petriarium/`
- New engine: `engine/creature_store.py`, `engine/petriarium.py`
- Tests: `tests/test_creature.py`, `tests/test_memory.py`, etc.

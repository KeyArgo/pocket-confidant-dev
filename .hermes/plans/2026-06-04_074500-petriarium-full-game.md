# Petriarium — Full Game Plan

**Date:** 2026-06-04
**Status:** PLANNING
**Author:** Hermes

---

## What This Actually Is

A full-fledged virtual pet game with AI companionship. Not a demo, not a prototype — a real game where you pick a baby creature, raise it, teach it, watch it grow old, and eventually decide its fate. The creature remembers everything you teach it, learns your language, and becomes a true companion.

> You walk into a store. There are creatures in little glass cases. Some are sleeping. Some are bouncing. Some are watching you. You pick one. You take it home. You teach it everything you know. It grows up with you. Years later, you decide: keep it, give it to someone, find it a new home, or let it go wild.

---

## The Full Vision

### The Store
- User enters a **pet store** with multiple baby creatures
- Each creature has:
  - Different appearance (color, size, markings)
  - Different starting temperament (shy, curious, bold, sleepy)
  - Different "spark" (some are more musical, some more mechanical, some more poetic)
- User **picks one** — this is their creature
- The choice matters: starting temperament affects how the creature learns

### The Lifecycle

```
Baby (0-7 days)
├── Knows almost nothing
├── Learns basic words: "hello", "food", "safe", "danger"
├── Needs constant attention
├── Sleeps a lot
├── Very bouncy, very curious
└── First words: user teaches it to say "hi"

Youngster (1-4 weeks)
├── Starts forming preferences
├── Asks lots of questions
├── Builds first artifacts
├── Learns about the user's world
├── Can follow simple instructions
└── Personality begins to emerge

Adolescent (1-3 months)
├── Strong personality
├── Has opinions
├── Builds complex things
├── May disagree with user
├── Can teach itself from books/web
└── Language becomes fluent

Adult (3-6 months)
├── Fully developed personality
├── Has a life of its own
├── Makes things without being asked
├── Has friends (other creatures)
├── May want independence
└── The relationship deepens

Elder (6+ months)
├── Wise, calm, reflective
├── Tells stories about the past
├── Has collected many artifacts
├── May want to pass knowledge on
├── Ready for the user's final decision
└── The farewell (or continuation)
```

### The Fates

When the creature reaches elder stage (or user decides early), the user chooses:

1. **Keep Forever** — creature stays, continues growing, becomes a permanent companion
2. **Give to Friend** — creature transfers to another user's game, carries all memories
3. **Find a New Home** — creature moves to an NPC home in the world, visits occasionally
4. **Go Wild** — creature lives in the wild, comes back to visit when it wants, remembers everything

Each fate has consequences:
- **Keep**: creature continues aging, may eventually pass (gentle ending)
- **Give to Friend**: creature appears in friend's game with full memory
- **New Home**: creature lives in an NPC house, you can visit, it visits you
- **Go Wild**: creature roams the world, appears randomly, brings gifts

---

## The Memory System

### Full Memory Provider (Not Simple SQLite)

Use **mem0** or **supermemory** as the actual brain:

- **mem0** (57.7K stars) — Universal memory layer for AI agents
  - Hybrid retrieval (semantic, keyword, entity)
  - Multi-level memory (user, session, long-term)
  - Best for: cross-session persistence, recall accuracy

- **supermemory** (25.4K stars) — Fast, scalable memory engine
  - The Memory API for the AI era
  - Best for: speed, scalability, API simplicity

### Memory Structure

```json
{
  "identity": {
    "name": "Mosslet",
    "species": "puffling",
    "birth_date": "2026-06-04",
    "owner": "user_id",
    "temperament": "curious"
  },
  
  "language": {
    "known_words": ["hello", "food", "safe", "play"],
    "word_associations": {
      "hello": {"meaning": "greeting", "learned_from": "owner", "confidence": 0.95},
      "food": {"meaning": "sustenance", "learned_from": "owner", "confidence": 0.88}
    },
    "sentence_structure": "simple",
    "vocabulary_size": 47
  },
  
  "knowledge": {
    "facts": [
      {"content": "The sun is a star", "source": "owner", "date": "2026-06-10"},
      {"content": "Bees make honey", "source": "wild_learning", "date": "2026-06-12"}
    ],
    "skills": ["foraging", "building", "storytelling"],
    "interests": {"bees": 0.82, "doors": 0.44, "music": 0.31}
  },
  
  "bonds": {
    "owner": {
      "trust": 0.92,
      "familiarity": 0.95,
      "last_interaction": "2026-06-14",
      "memories_together": 142
    },
    "others": [
      {"name": "friend_user", "trust": 0.3, "meetings": 3}
    ]
  },
  
  "artifacts": [
    {"type": "honeycomb_shrine", "date": "2026-06-11", "inspiration": "bee_facts"},
    {"type": "copper_hinge", "date": "2026-06-13", "inspiration": "raspberry_pi"}
  ],
  
  "life_events": [
    {"type": "birth", "date": "2026-06-04"},
    {"type": "first_word", "date": "2026-06-05", "word": "hi"},
    {"type": "first_artifact", "date": "2026-06-08", "artifact": "pebble_shelf"}
  ]
}
```

### Learning System

The creature learns through:

1. **Direct Teaching** (user → creature)
   - User types: "This is a Raspberry Pi"
   - Creature stores: {"topic": "raspberry_pi", "source": "owner", "confidence": 0.8}
   - Creature may ask: "What does it do?"

2. **Wild Learning** (world → creature)
   - Creature explores, finds things
   - Stores observations: "Rain makes puddles"
   - Lower confidence than direct teaching

3. **Social Learning** (other creatures → creature)
   - If creature meets others, it learns from them
   - "My friend told me about stars"

4. **Self-Directed Learning** (creature → itself)
   - Creature reads books in the world
   - Experiments with materials
   - Builds things to test ideas

---

## The World

### The Habitat (Home)
- User's house/room where the creature lives
- Has areas: sleeping nook, play area, workbench, bookshelf
- Creature moves between areas based on needs
- User can decorate, add furniture, customize

### The Neighborhood
- Small map with places to visit:
  - Park (find nature items)
  - Library (learn words, read books)
  - Market (trade artifacts)
  - Other homes (visit other creatures)
  - Workshop (build things)

### The Wild (Blindspot)
- Large area outside the neighborhood
- Creature can explore when it goes "wild"
- Contains rare resources and mysteries
- Dangerous but rewarding

### The Store (Starting Point)
- Where user picks their creature
- Different species available
- Each has unique starting traits

---

## Species (Examples)

### Puffling
- Small, round, fluffy
- Very curious, very bouncy
- Learns words quickly
- Likes: nature, exploring, collecting
- Dislikes: being still, dark places

### Cogling
- Mechanical, has visible gears
- Practical, problem-solving
- Learns systems quickly
- Likes: building, fixing, understanding
- Dislikes: chaos, unpredictability

### Lumling
- Glowing, ethereal
- Dreamy, poetic
- Learns emotions quickly
- Likes: music, stories, feelings
- Dislikes: loud noises, conflict

### Rootling
- Plant-like, grows leaves
- Patient, nurturing
- Learns slowly but remembers forever
- Likes: growing, tending, patience
- Dislikes: rushing, destruction

---

## The Language System

### How It Learns to Speak

1. **First Words** (Baby)
   - User teaches: "This is food"
   - Creature learns: "food" = sustenance
   - Creature may say: "food?" when hungry

2. **Simple Sentences** (Youngster)
   - User teaches: "I'm happy"
   - Creature learns: "happy" = positive emotion
   - Creature may say: "You happy?"

3. **Complex Thoughts** (Adolescent)
   - Creature forms its own sentences
   - "I think the flowers like the rain"
   - "Do you want to see what I made?"

4. **Fluent Conversation** (Adult)
   - Full back-and-forth dialogue
   - Creature has opinions, asks questions
   - "Remember when you taught me about bees? I found a hive."

5. **Storytelling** (Elder)
   - Creature tells stories about the past
   - "Once, when I was small, you showed me a star..."

### Language Features

- **Vocabulary tracking**: what words it knows
- **Grammar development**: sentence structure improves over time
- **Accent/style**: creature develops its own way of speaking
- **Mispronunciations**: cute mistakes that get corrected
- **Inside jokes**: shared references from past interactions

---

## The Companion AI

### Why AI/Robot Works Better Than Organic

1. **Persistence** — AI remembers forever, organic forgets
2. **Transferability** — AI can move between devices/users
3. **Upgradeability** — AI can learn new skills
4. **Portability** — AI can live in your phone, computer, or cloud
5. **Consistency** — AI doesn't have bad days (unless you want it to)
6. **Safety** — AI can't get hurt, lost, or sick

### The Companion Loop

```
User interaction
    ↓
Creature responds (based on memory + personality)
    ↓
Memory updated (new facts, associations, feelings)
    ↓
Creature changes (mood, behavior, appearance)
    ↓
World updates (artifacts, habitat changes)
    ↓
Creature initiates (comes to say hi, asks question, shows something)
    ↓
User responds
    ↓
(cycle continues)
```

### What Makes It Feel Alive

1. **Autonomous behavior** — creature does things without being asked
2. **Memory references** — "Remember when..."
3. **Opinions** — "I don't like that color"
4. **Growth** — visible changes over time
5. **Imperfection** — makes mistakes, learns from them
6. **Surprise** — does unexpected things
7. **Consistency** — personality stays stable
8. **Attachment** — misses the user when they're away

---

## Technical Architecture

### Frontend
- **Gradio** for hackathon (required)
- **HTML5 Canvas** for creature animation
- **CSS Grid** for world rendering
- **WebSocket** for real-time updates (if Gradio supports)

### Backend
- **Python** core
- **mem0** or **supermemory** for memory
- **SQLite** for game state
- **Ollama/llama.cpp** for local AI
- **FastAPI** for API (if needed)

### Memory Layer
```python
class CreatureBrain:
    def __init__(self, creature_id: str):
        self.memory = Mem0()  # or SuperMemory()
        self.state = SQLiteState()
    
    def learn(self, fact: str, source: str, context: dict):
        """Store a new fact with source attribution."""
        self.memory.add(fact, metadata={
            "source": source,
            "context": context,
            "confidence": self._calculate_confidence(source)
        })
    
    def recall(self, query: str, top_k: int = 5):
        """Recall relevant memories."""
        return self.memory.search(query, limit=top_k)
    
    def speak(self, context: str):
        """Generate speech based on memories and personality."""
        memories = self.recall(context)
        personality = self.state.get_personality()
        return self._generate_speech(memories, personality)
```

### Game State
```python
class GameState:
    def __init__(self):
        self.creatures = {}  # All user's creatures
        self.world = WorldState()
        self.time = GameTime()
        self.events = EventLog()
    
    def tick(self):
        """Advance game time, update creatures, trigger events."""
        self.time.advance()
        for creature in self.creatures.values():
            creature.update_needs()
            creature.behave()
            creature.age()
        self.world.update()
        self.check_events()
```

---

## Build Phases

### Phase 1: Core Engine (Week 1)
- [ ] Creature class with full state
- [ ] Memory system with mem0/supermemory
- [ ] Basic needs system
- [ ] Simple world (habitat only)
- [ ] Basic interaction (feed, pet, talk)

### Phase 2: Language System (Week 2)
- [ ] Word learning system
- [ ] Vocabulary tracking
- [ ] Simple sentence generation
- [ ] Pronunciation/mispronunciation
- [ ] Conversation flow

### Phase 3: World Building (Week 3)
- [ ] Neighborhood map
- [ ] Multiple locations
- [ ] NPCs (other creatures)
- [ ] Resource system
- [ ] Crafting/building

### Phase 4: Lifecycle (Week 4)
- [ ] Aging system
- [ ] Stage transitions (baby → youngster → adolescent → adult → elder)
- [ ] Personality evolution
- [ ] Artifact collection
- [ ] Life events

### Phase 5: Endings (Week 5)
- [ ] Keep Forever path
- [ ] Give to Friend path
- [ ] Find New Home path
- [ ] Go Wild path
- [ ] Save/load system

### Phase 6: Polish (Week 6)
- [ ] Creature animations
- [ ] Sound effects
- [ ] Music
- [ ] Tutorial
- [ ] Save/load
- [ ] Bug fixes

---

## Hackathon MVP (What to Build Now)

For the hackathon, build the **core loop** that proves the concept:

1. **Pick a creature** from store (3 options)
2. **Feed it 5 moments** (user teaches it)
3. **Watch it learn** (vocabulary grows, personality emerges)
4. **See it change** (appearance, mood, behavior)
5. **Hear it speak** (first words, simple sentences)
6. **Collect artifacts** (things it makes from learning)

This proves:
- The creature is alive
- Memory works
- Learning happens
- The relationship matters

### What to Cut for Hackathon
- Full lifecycle (just show baby → youngster)
- Multiple fates (just show the creature growing)
- Neighborhood (just show habitat)
- Other creatures (just show the one)
- Save/load (just show one session)

---

## Two Builds (DeepSeek vs MiniMax)

Run the same prompt through two models:
- **DeepSeek**: opencodego-deepseek-v4-flash
- **MiniMax**: opencodego-minimax-m3

### Comparison Criteria
1. **Which creature feels more alive?**
2. **Which memory system learns better?**
3. **Which language development feels more natural?**
4. **Which personality emerges more clearly?**
5. **Which one do you want to keep playing with?**

---

## Success Metrics

### Quantitative
- Creature learns 50+ words in first session
- Creature forms 10+ unique memories
- Creature asks 3+ questions without prompting
- Creature shows 3+ different moods
- Creature creates 2+ artifacts

### Qualitative
- User feels attached to creature
- User wants to come back tomorrow
- User tells someone about the creature
- User names the creature
- User remembers the creature's name

---

## Open Questions

1. **Memory provider**: mem0 or supermemory? (Test both)
2. **World size**: How big for hackathon? (Suggest: habitat + 1 neighborhood location)
3. **Species**: How many for hackathon? (Suggest: 3)
4. **Language depth**: How complex for hackathon? (Suggest: 50 words, simple sentences)
5. **Endings**: Show for hackathon? (Suggest: hint at future, don't implement)

---

## File Paths

- Plan location: `.hermes/plans/2026-06-04_074500-petriarium-full-game.md`
- Target repo: `/mnt/homes/galileo/argo/Development/build-small-2026/`
- New app: `apps/petriarium/`
- Memory layer: `engine/memory/`
- World engine: `engine/world/`
- Creature engine: `engine/creature/`
- Tests: `tests/`

---

## Next Steps

1. **Test memory providers** — which works best for this use case?
2. **Prototype creature interaction** — does the core loop feel alive?
3. **Build store UI** — can user pick a creature and feel attached?
4. **Test language system** — does learning feel natural?
5. **Decide hackathon scope** — what to build, what to cut

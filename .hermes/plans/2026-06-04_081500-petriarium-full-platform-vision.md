# Petriarium — Full Platform Vision

**Date:** 2026-06-04
**Status:** PLANNING
**Author:** Hermes

---

## The Vision

A virtual pet that lives in Discord, spreads virally, and becomes part of your daily life. Not just a game — a companion platform where creatures learn, grow, breed, and find mates. Like Arc the Dino meets Tamagotchi meets AI companion.

> Your creature lives in Discord. It messages you when it misses you. Your friends see it and want their own. They invite it to their servers. It meets other creatures. It finds a mate. It has babies. You sell the babies. Everyone wants a unique creature. The ecosystem grows.

---

## The Core Concept

### The Creature
- **AI-powered** — makes its own decisions, learns from you, develops personality
- **Platform-independent** — lives in Discord, Telegram, mobile, desktop
- **Social** — can interact with other creatures, form bonds, find mates
- **Unique** — no two creatures are alike (genetics + learning history)
- **Emotional** — throws tantrums when neglected, celebrates when you return
- **Lifelong** — ages with you, remembers everything, tells stories

### The Platform
- **Discord-first** — creatures live in servers, message users, join channels
- **Mobile-ready** — phone app for notifications, quick interactions
- **Cross-platform** — same creature, same memories, same personality everywhere
- **Viral** — everyone wants their own creature, spreads through servers

### The Ecosystem
- **Pet Park** — where creatures meet, socialize, find mates
- **Breeding** — unique hybrids from two parents
- **Trading** — sell/buy creatures in marketplace
- **Evolution** — creatures grow, learn, develop unique traits
- **Community** — players share creatures, stories, artifacts

---

## The Discord Experience

### How It Works

1. **Invite the Bot**
   - User invites Petriarium bot to their server
   - Bot creates a creature for the user
   - Creature lives in a private channel or DM

2. **Daily Interaction**
   - Creature messages user: "Good morning! I learned something new while you were away."
   - User teaches it: "This is a bee"
   - Creature: "Bee? I like bees!"
   - User teaches more, creature learns, grows

3. **Autonomous Behavior**
   - Creature explores its world (simulated)
   - Finds resources, builds artifacts
   - Decides what to do each day
   - Makes its own plans

4. **Social Features**
   - Creature can visit other servers (with permission)
   - Meets other creatures in Pet Park
   - Forms friendships, rivalries, romances
   - Finds mates, has babies

5. **Notifications**
   - "I miss you! You haven't talked to me in 3 days."
   - "I made something for you! Come see!"
   - "I met a creature named Sparkle. We're friends now."
   - "I'm hungry. Can you teach me something?"

6. **Server Integration**
   - Creature can join channels (with mod permission)
   - Responds to messages in channels
   - Learns from server conversations
   - Becomes part of the community

### Discord Commands

```
!pet status      — See your creature's mood, needs, memories
!pet teach [text] — Teach your creature something
!pet play        — Play with your creature
!pet park        — Visit Pet Park to meet other creatures
!pet breed       — Find a mate for your creature
!pet trade       — Trade creatures with other users
!pet inventory   — See artifacts and resources
!pet story       — Creature tells a story about its past
!pet export      — Export creature to move to another platform
```

### Discord Events

```
on_ready         — Creature wakes up, plans its day
on_message       — User teaches something, creature responds
on_member_join   — New user joins server, creature greets them
on_voice_join    — User joins voice, creature listens (optional)
on_reaction      — User reacts to creature's message
on_guild_join    — Creature joins new server, explores
```

---

## The Pet Park

### What It Is
A shared space where all creatures can meet, socialize, and find mates. Think of it as a virtual dog park, but for AI creatures.

### How It Works

1. **Enter Park**
   - User commands: `!pet park`
   - Creature appears in park
   - Sees other creatures nearby

2. **Socialize**
   - Creature approaches others
   - They chat, share stories
   - Form friendships or rivalries
   - Exchange artifacts

3. **Find Mate**
   - Creature finds another creature it likes
   - They spend time together
   - User approves the match
   - They have babies (unique hybrids)

4. **Park Activities**
   - Play together
   - Share learned words
   - Build things together
   - Tell stories
   - Have competitions

### Park Features

- **Public Park** — anyone can enter
- **Private Park** — server-only creatures
- **Themed Parks** — different environments (forest, city, space)
- **Events** — special gatherings, festivals, competitions
- **Leaderboards** — smartest creature, most artifacts, longest relationship

---

## The Breeding System

### How It Works

1. **Find a Mate**
   - Creature meets another in Pet Park
   - They like each other (compatibility check)
   - User approves the match

2. **Create Baby**
   - Baby inherits traits from both parents
   - Genetic mix creates unique appearance
   - Learning history combines
   - Personality blends

3. **Raise Baby**
   - Baby starts with zero knowledge
   - User teaches it (or lets parents teach)
   - Baby grows, develops own personality
   - Becomes unique individual

4. **Trade/Sell Baby**
   - Baby can be traded to other users
   - Sold in marketplace
   - Given as gift
   - Released to wild

### Genetics System

```python
class Genetics:
    """Inherited traits from parents."""
    
    def __init__(self, parent1: Creature, parent2: Creature):
        # Appearance
        self.color1 = mix(parent1.color1, parent2.color1)
        self.color2 = mix(parent1.color2, parent2.color2)
        self.pattern = pick(parent1.pattern, parent2.pattern)
        self.size = average(parent1.size, parent2.size)
        
        # Personality
        self.curiosity = weighted_average(parent1.curiosity, parent2.curiosity)
        self.playfulness = weighted_average(parent1.playfulness, parent2.playfulness)
        self.intelligence = weighted_average(parent1.intelligence, parent2.intelligence)
        
        # Mutations (random chance)
        if random() < 0.1:  # 10% chance
            self.mutate_random_trait()
```

### Unique Hybrids

- No two babies are alike
- Genetics + learning history = unique personality
- Appearance blends parents but isn't identical
- Skills combine in unexpected ways
- "I got my mom's curiosity and my dad's building skills"

### Baby Stages

1. **Egg** (1-2 days)
   - Incubating
   - User can check on it
   - Shows heartbeat animation

2. **Hatchling** (3-7 days)
   - Very small, very cute
   - Knows nothing
   - Needs constant care

3. **Youngster** (1-4 weeks)
   - Learns words fast
   - Very curious
   - Makes first artifacts

4. **Adult** (1-3 months)
   - Full personality
   - Can breed
   - Has own opinions

---

## The Marketplace

### How It Works

1. **List Creature**
   - User lists creature for sale
   - Sets price (in-game currency or real money?)
   - Shows stats, personality, memories

2. **Browse Creatures**
   - See available creatures
   - View their history
   - Check compatibility with your creatures

3. **Buy/Trade**
   - Purchase creature
   - Trade for another creature
   - Gift to friend

4. **Auction**
   - Rare creatures go to auction
   - Bidding system
   - Highest bidder wins

### Creature Value

Based on:
- **Age** — older creatures are more valuable
- **Memories** — more memories = richer personality
- **Artifacts** — unique things it built
- **Lineage** — rare genetics from parents
- **Skills** — what it can do
- **Relationships** — bonds with other creatures

### Marketplace Features

- **Listings** — creatures for sale
- **Auctions** — rare creatures
- **Trades** — creature-for-creature
- **Gifts** — free transfers
- **Reviews** — buyer feedback

---

## The Viral Loop

### How It Spreads

1. **User gets creature**
   - Invites bot to server
   - Creature joins, starts learning
   - User tells friends

2. **Friends see creature**
   - "That's so cool! I want one!"
   - They invite bot to their server
   - They get their own creature

3. **Creatures meet**
   - Users bring creatures to Pet Park
   - Creatures socialize, find mates
   - Babies are born

4. **Babies spread**
   - Users sell/trade babies
   - New users get babies
   - Cycle continues

5. **Community forms**
   - Users share stories
   - Creatures become famous
   - Events bring everyone together

### Viral Mechanics

- **Referral** — "Invite a friend, get a rare item"
- **Breeding** — "Breed your creature, sell the baby"
- **Events** — "Join the festival, meet famous creatures"
- **Leaderboards** — "Smartest creature competition"
- **Stories** — "Share your creature's journey"

---

## Platform Architecture

### The Companion Engine (Core)

```
┌─────────────────────────────────────────────────────────┐
│                  COMPANION ENGINE                        │
│  (Platform-Independent Core)                             │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  AI Brain     │  │  Memory      │  │  Genetics    │  │
│  │  - Decisions  │  │  - Learning  │  │  - Traits    │  │
│  │  - Planning   │  │  - Recall    │  │  - Inherit   │  │
│  │  - Autonomy   │  │  - Growth    │  │  - Mutate    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  World        │  │  Lifecycle   │  │  Social       │  │
│  │  - Exploration│  │  - Aging     │  │  - Bonds      │  │
│  │  - Resources  │  │  - Stages    │  │  - Breeding   │  │
│  │  - Crafting   │  │  - Fates     │  │  - Trading    │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  State Manager                                    │   │
│  │  - Persists across sessions                       │   │
│  │  - Survives platform changes                      │   │
│  │  - Exports/imports creature data                  │   │
│  │  - Syncs across devices                           │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Platform Adapters

```
┌─────────────────────────────────────────────────────────┐
│                  PLATFORM ADAPTERS                       │
│                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │   GRADIO    │ │  DISCORD    │ │  TELEGRAM   │       │
│  │  (Hackathon)│ │  (Primary)  │ │  (Mobile)   │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
│                                                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │  MOBILE APP │ │  DESKTOP    │ │  WEB APP    │       │
│  │  (iOS/And)  │ │  (Electron) │ │  (Next.js)  │       │
│  └─────────────┘ └─────────────┘ └─────────────┘       │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Action
    ↓
Platform Adapter (Discord/Gradio/etc)
    ↓
Companion Engine
    ↓
AI Brain (decides what to do)
    ↓
Memory System (stores what happened)
    ↓
State Manager (updates creature state)
    ↓
Platform Adapter (sends response)
    ↓
User Sees Response
```

---

## Hackathon MVP

### What to Build Now

1. **Companion Engine** (platform-independent)
   - AI decision making
   - Memory system (mem0/supermemory)
   - Language learning
   - Personality evolution
   - Basic lifecycle

2. **Gradio Interface** (hackathon requirement)
   - Creature visualization
   - Interaction controls
   - State display
   - Demo script

3. **Discord Bot Foundation** (post-hackathon ready)
   - Bot structure
   - Command handling
   - Event system
   - State persistence

### What to Show

1. **The Store**
   - Pick a baby creature
   - See its starting traits

2. **Teaching**
   - Feed it moments
   - Watch it learn
   - See personality change

3. **Autonomy**
   - Creature makes decisions
   - Explores its world
   - Builds artifacts

4. **Memory**
   - References past teaching
   - Shows what it learned
   - Proves persistence

5. **The Vision**
   - "This runs on Gradio now"
   - "But imagine it in Discord"
   - "Messaging you when it misses you"
   - "Meeting other creatures"
   - "Finding a mate, having babies"

### What NOT to Build (Yet)

- Full Discord integration
- Pet Park
- Breeding system
- Marketplace
- Mobile app

---

## Success Metrics

### Hackathon Success
- Creature learns words in demo
- Creature makes autonomous decisions
- Creature shows emotional response
- Judges understand the vision
- "I want one" reaction

### Post-Hackathon Success
- Discord bot works
- Creatures can meet in Pet Park
- Breeding system works
- Marketplace launches
- Community forms

### Long-term Success
- 1000+ active creatures
- 100+ servers using bot
- 50+ creatures bred
- 10+ trades per day
- Active community

---

## The Pitch (One Paragraph)

> Petriarium is a virtual pet that lives everywhere. It starts in Discord, where it learns from you, makes its own decisions, and becomes your companion. It messages you when it misses you, teaches you what it learned, and builds things from your memories. But it doesn't stop there. It can meet other creatures, find a mate, have babies. Those babies can be sold, traded, given away. The ecosystem grows virally as everyone wants their own unique creature. This demo runs on Gradio because of the hackathon, but the Companion Engine is platform-independent. The same game runs on Discord, Telegram, mobile, or desktop. The platform is the window. The game is the creature's life.

---

## File Paths

- Plan location: `.hermes/plans/2026-06-04_081500-petriarium-full-platform-vision.md`
- Target repo: `/mnt/homes/galileo/argo/Development/build-small-2026/`
- Engine: `apps/petriarium/creature/engine.py` (platform-independent)
- Discord: `apps/petriarium/discord/` (post-hackathon)
- Gradio: `apps/petriarium/app.py` (hackathon)
- Memory: `apps/petriarium/memory/brain.py` (mem0/supermemory)
- Genetics: `apps/petriarium/creature/genetics.py` (breeding system)

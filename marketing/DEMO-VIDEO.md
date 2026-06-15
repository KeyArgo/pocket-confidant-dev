# Pocket Confidant — Demo Video Script & Storyboard

**Video title:** *Pocket Confidant — the diary that listens, and never leaves your laptop.*

**Format:** screen recording + a couple of real-world cutaways (hand on laptop, wifi toggle).
**Target length:** 75 seconds (range 60–90s). One narrator, calm and warm — not an ad voice.
**Aspect:** 16:9 for the Space embed; a 9:16 vertical crop works for the social post.
**Tone rule:** honest, understated, a little wry. No hype words. The product is restraint, so the video is too.

---

## The 8-second hook (first frames — must earn the next 70s)

> **On screen:** black, then a single line of text typing itself out, character by character:
> `i can't send this to ChatGPT.`
> A blinking cursor. Beat. Then the line erases and is replaced by:
> `so it runs on my laptop instead.`
>
> **VO (over the typing):** "Your diary is the most private thing you own. So why would you hand it to a cloud?"

This is the whole pitch in one breath. If a judge stops here, they already get it.

---

## Core narrative arc (the four beats)

1. **The problem** — a head full of the day; the journaling apps you opened twice and abandoned.
2. **Off the grid** — cut the wifi / airplane mode ON, and it *still answers*. Goosebumps, proof of local.
3. **The warmth** — a real entry in, a short warm reflection + exactly ONE good question out.
4. **The wow (climax)** — days later it calls back to something you actually wrote, from private on-device memory.

Then land the honest-fit line and the closing card.

---

## Beat-by-beat shot list

### Beat 0 · Hook — `0:00–0:08`
- **Screen:** Black. Monospace text types `i can't send this to ChatGPT.` → erases → `so it runs on my laptop instead.`
- **Caption (lower third):** *Pocket Confidant · a local AI journal*
- **VO:** "Your diary is the most private thing you own. So why would you hand it to a cloud?"
- **B-roll:** none yet — keep it stark. Faint keyboard sound.

### Beat 1 · The problem — `0:08–0:20`
- **Screen:** Cut to a real cutaway — someone closing a laptop late at night, lamp on, room dim. Then a quick montage of phone home-screen: three journaling-app icons, each tapped and immediately swiped away (abandoned).
- **Caption:** *End of the day. Head full of stuff.* → *(the journaling apps you opened twice.)*
- **VO:** "End of the day, your head's full. You've tried the journaling apps. You opened them twice."
- **B-roll:** warm desk-lamp light, hands, a half-drunk mug. Real and a little tired, not glossy.

### Beat 2 · Off the grid (the proof) — `0:20–0:33`
- **Screen:** Cut to the actual Pocket Confidant Gradio app, open in a browser. Cursor moves up to the system menu bar. **Click Wi-Fi → toggle OFF.** Then **turn ON Airplane Mode** (show the airplane icon light up). Network indicator clearly shows *no connection*.
- **Screen:** The new landing panel is visible first: the private journal explanation on one side, and the living companion pulse on the other. Then move straight into the Wi-Fi toggle proof.
- **On-screen text (big, centered, holds 2s):** **NO WIFI. NO CLOUD. STILL WORKS.**
- **VO:** "Watch this. Wifi off. Airplane mode on. No connection at all… and it still works. The whole thing runs on a small model, right here on the machine."
- **B-roll:** macro shot of the airplane-mode toggle flipping is ideal — it's the literal goosebumps frame. Hold on the "no signal" icon for a beat.
- **Note:** record this for real with the network genuinely off so it's honest — the model is local ollama / llama.cpp, it does not need the network.

### Beat 3 · The warmth — `0:33–0:52`
- **Screen:** Back in the app (still offline — leave the airplane icon visible in the corner the whole time; it's free proof). Type a real-feeling entry into the journal box:
  > *"Lost three hours on the side project tonight and didn't notice the time. First time in weeks I actually felt like myself."*
  Click **Reflect**. A brief spinner. Then the companion's reply appears in the response panel, in this order (matches the app's render): reflection first, then the question.
  > *"Three hours where the clock disappeared — and it felt like coming back to yourself. That's worth noticing."*
  >
  > *"What was it about tonight that let you fall in that deep?"*
- **Caption (subtle, once):** *one warm reflection · exactly one question · no advice-dump*
- **VO:** "You write what's actually on your mind. It reflects back what it heard — in your own words, not platitudes — and asks one good question. That's it. No lectures, no fixing."
- **B-roll:** none — let the real UI carry it. Linger long enough to actually read the reflection.

### Beat 4 · THE WOW — memory callback (climax) — `0:52–1:05`
- **Screen:** A title card wipes by: **`— a few days later —`**. Same app. Type a new, *different* entry:
  > *"Slammed all week. Barely sat down. I miss having time that's just mine."*
  Click **Reflect**. The reply appears — and this time it opens with a **callback line** (the app renders callback first, then reflection, then question), highlighted on screen:
  > *"This sounds like the opposite of that night you lost track of time on your project — when the hours just vanished."* ← *(highlight / glow this line)*
  >
  > *"You said then it felt like coming back to yourself. What would it take to carve even one of those hours back this week?"*
- **On-screen text (appears beside the callback):** **It remembered. Privately. On your device.**
- **VO:** "And then — days later — it brings back something you wrote before. Not because it's watching you. Because it remembers, privately, on your machine. That's the moment a journal becomes a companion."
- **B-roll:** none — the callback line IS the payoff. Consider a soft glow / underline animation on the callback sentence only.
- **Why it's honest:** this is real recall (local semantic memory, cosine floor 0.58 so it only connects when it genuinely relates). It does NOT fire on unrelated entries — say that nowhere on screen, but it's why the demo is trustworthy.

### Beat 5 · The honest-fit line — `1:05–1:13`
- **Screen:** Clean slate. Four short lines fade in one at a time over a calm background:
  - *The companion's pulse changes as the journal grows.*
  - *A small model. Running on your device.*
  - *Your diary never leaves it.*
  - *No account. No subscription.*
  - *Works in airplane mode.*
- **VO:** "A small, local model. Your diary never leaves your device. No account, no subscription. It even works on a plane."
- **B-roll:** optional — the airplane-mode icon one more time, then gone.

### Beat 6 · Closing card — `1:13–1:18`
- **Screen:** Final card on a warm, soft background:
  > **Pocket Confidant**
  > *a private AI journal that listens — and stays home*
  >
  > 🤗 Hugging Face Space: **LocutusofArgo/pocket-confidant**
  > 🔌 Off the Grid · 🦙 Llama Champion · 🎨 Off-Brand · 📓 Field Notes
  > *Build Small Hackathon 2026 · Backyard AI*
- **VO:** "Pocket Confidant. Try it on Hugging Face."
- **B-roll:** none. Let the badges sit. Silence after the last word.

> **Space name note for the human:** the closing card uses placeholder `LocutusofArgo/pocket-confidant`. Swap in the exact Space slug once it's created.

---

## Alternate 30-second cut (for the social post / short attention)

Hits only beats Hook → Off-the-grid → Wow → Card. Drop the slow problem setup and the honest-fit list.

- `0:00–0:05` — **Hook.** Type `i can't send this to ChatGPT.` → `so it runs on my laptop instead.` VO: "Your diary's the most private thing you own — so it runs on your laptop, not the cloud."
- `0:05–0:13` — **Off the grid.** Flip airplane mode ON in the menu bar. Big text: **NO WIFI. STILL WORKS.** VO: "Airplane mode on. No connection. It still reflects back."
- `0:13–0:24` — **The wow.** Jump straight to the days-later callback entry; show the glowing callback line. On-screen: **It remembered — privately, on-device.** VO: "And days later, it remembers what you wrote — privately, on your machine."
- `0:24–0:30` — **Card.** Pocket Confidant · Space slug · badges. VO: "Pocket Confidant. On Hugging Face."

---

## Production notes / checklist

- **Record offline for real.** Actually disconnect the network during Beats 2–4 so the airplane icon is genuine. Honesty is the whole brand; a faked offline shot would betray it.
- **Use real model output.** Generate the reflections/callback live (or from a real run) rather than hand-writing perfect prose — small jitters read as authentic. The example lines above are realistic targets, not scripts the model must match verbatim.
- **Render order matters on screen.** The app shows **callback → reflection → question** (`Reflection.render()`), with no callback in Beat 3 and a callback in Beat 4. Make sure the recording reflects that difference — it's the visual proof that memory only fires when relevant.
- **Captions burned in.** Many judges scrub muted; the on-screen text must carry the story without audio.
- **Music:** soft, sparse, low. Cut it out entirely under the VO in Beat 4 so the callback lands in near-silence.
- **Keep the entries PG and relatable** — "lost track of time on a side project" is universal and non-sensitive; good for a public demo of a private app.
- **Off-Brand badge:** make sure the recorded UI is the custom Gradio theme, not the default — frame a shot that shows the custom styling clearly.

---

## Summary (for the human)

**Title:** *Pocket Confidant — the diary that listens, and never leaves your laptop.*

**Core 4-beat arc:**
1. **The problem** — end of the day, head full, the journaling apps you abandoned.
2. **Off the grid** — flip airplane mode ON on camera; it still works (Off the Grid proof, the goosebumps frame).
3. **The warmth** — a real entry → one warm reflection + exactly one good question (real UI, render order reflection→question).
4. **The wow (climax)** — days later it calls back to your earlier "lost track of time" entry from private on-device memory.

Then the honest-fit line (small local model, diary never leaves your device, no account/subscription) and a closing card with Space slug + badges.

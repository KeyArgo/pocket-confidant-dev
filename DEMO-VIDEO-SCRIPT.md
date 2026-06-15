# Pocket Confidant — Demo Video Script (90 seconds)

## Before You Hit Record

```bash
# Terminal 1: Start the local app
cd /mnt/homes/galileo/argo/Development/pocket-confidant-dev
.venv/bin/python apps/confidant/app.py
# Wait for "Running on local URL: http://127.0.0.1:7860"

# Terminal 2: Start screen recording (90 sec, full HD)
ffmpeg -video_size 1920x1080 -framerate 30 -f x11grab -i :0.0 -t 90 -c:v libx264 -preset ultrafast -crf 18 demo.mp4

# Hit ENTER on Terminal 2 to start recording
# Then switch to the browser showing the app
```

## The 90-Second Script

### [0:00 - 0:10] THE HOOK
> "A diary is the most private thing you own. You would NEVER paste it into ChatGPT."

**On screen:** Open the app. Show the masthead: "a private journal that reflects back · 100% on your device · no cloud, no account · works in airplane mode"

**Action:** Click the network icon in your taskbar → show **Airplane Mode ON**

### [0:10 - 0:25] THE PROBLEM
> "So the only honest design is one where nothing ever leaves your machine. Not a compromise — the *correct* answer."

**On screen:** Scroll the journal sidebar — show **376 entries spanning July 2025 to June 2026**. A year of someone's real journaling.

**Action:** (Optional) hover over the model badge showing "reflected locally · qwen3.5:9b · on-device"

### [0:25 - 0:55] THE WOW
> "It remembers. But only when it's actually relevant — never fake-recall."

**On screen:** In the entry box, paste:
> had coffee on the porch this morning, sun was out

**Action:** Click **Reflect**. Wait 5-15 seconds. Show the response card.

The response will include something like:
> "I noticed you wrote about this exact same morning on the porch just a few days ago..."
> "What was different about today's coffee?"

That last line is a **live memory callback** — the model found a past entry that's genuinely related, and used it as a question. It is NOT a canned template.

**Action:** Click **This week**. Show the gentle 2-3 sentence reflection on the past 7 entries.

### [0:55 - 1:20] THE TECH
> "Qwen 9B running locally via Ollama. 376 entries pre-loaded. No data ever leaves this machine."

**On screen:** Open a terminal. Show:
```bash
# Proof it's local — no network in/out
curl -s ifconfig.me    # → fails (airplane mode)
ps aux | grep ollama   # → ollama process running
```

### [1:20 - 1:30] THE PUNCH
> "Small models. Big privacy. On-device. Open source. Open weights."

**On screen:** Final shot of the app with the callback line visible. End card with the Hackathon badges.

## After Recording

```bash
# Quick check the video looks right
ffplay demo.mp4
# Trim if needed
ffmpeg -i demo.mp4 -ss 0 -t 90 -c copy demo-trimmed.mp4
# Upload to YouTube (private or unlisted, doesn't matter for the submission)
```

## The "What to Type" Cheat Sheet

| Time | Type this in the entry box |
|------|---------------------------|
| 0:25 | `had coffee on the porch this morning, sun was out` |
| 0:40 | `finally went for a run. only 2 miles.` (alternate) |
| 0:40 | `rain kept me up all night but i feel oddly rested` (alternate) |

The 3 alternates above all trigger different memory callbacks from your real journal. Pick the one that gives the most striking result.

## What NOT to Do

- **Don't** show the Developer's Clear Data / Reload Demo Data buttons
- **Don't** talk for more than 90 seconds total
- **Don't** show the source code (saves time, the demo speaks for itself)
- **Don't** show the Qwen model file size or technical specs (not the point)
- **Don't** apologize for anything (the app is fine, the demo is fine)

# Pocket Confidant — Social Posts

For the Hugging Face **Build Small Hackathon** (theme: *Small Models, Big Adventure* · Track: Backyard AI).
Builder: Daniel LaForce — HF `LocutusofArgo`.

Voice: warm, confident, a little wry. Not hypey. Honest about the small model's limits.

---

## 1. Primary post — X / Twitter (single tweet, ~280 chars)

> Your diary is the one thing you'd never paste into a cloud AI.
>
> So I built Pocket Confidant: a journaling companion that runs 100% on-device. It reads your entry, reflects, asks ONE good question, and remembers — all offline. Works in airplane mode.
>
> #BuildSmall #SmallModelsBigAdventure #Gradio #HuggingFace #LocalAI #llamacpp

*(Char count of the body, hashtags included, is ~275. Trim a hashtag if your client counts links/handles against you.)*

---

## 2. Thread version — X / Twitter (4 tweets)

**Tweet 1 — hook**
> Your diary is the most private thing you own. You'd never paste it into a cloud AI.
>
> So the only honest AI journal is one that never phones home. I built it. 🧵
>
> #BuildSmall #SmallModelsBigAdventure

**Tweet 2 — what it does**
> Meet Pocket Confidant. You write an entry; a small local model reads it and gives back a short, warm reflection in your own words — then asks exactly ONE good question. No wall of advice. No therapy-speak. Restraint is the whole point.

**Tweet 3 — the magic**
> The quiet trick: private, on-device memory. When today genuinely connects to something you wrote days ago, it gently calls it back — "you mentioned the dentist last week." Only when it's real. It never pretends to remember. Semantic recall, 100% on your machine.

**Tweet 4 — honest fit + CTA**
> No cloud. No account. No subscription. Runs in airplane mode on a laptop — even a phone-class model. A <32B model is the *honest* fit here, not a compromise.
>
> Try it on @huggingface Spaces 👇 [LINK]
>
> #Gradio #HuggingFace #LocalAI #llamacpp #OffTheGrid

---

## 3. LinkedIn variant

**Pocket Confidant: the journaling AI that never phones home.**

A diary is the most private thing most of us own. Which is exactly why I'd never paste mine into a cloud AI — and I suspect you wouldn't either. That tension is the whole reason this project exists.

For Hugging Face's Build Small Hackathon, I built Pocket Confidant: a journaling companion that runs entirely on-device. You write an entry; a small local model (under 32B params, via llama.cpp) reads it and offers a short, warm reflection in your own words — then asks one good question. Not a page of advice. Not relentless positivity. Just enough to help you notice something.

The part I'm most proud of is the memory. It keeps a private, on-device semantic index of what you've written, and when today genuinely connects to something from days ago, it calls it back — naturally, and only when it's real. It will never claim to remember something you didn't write. Honesty about a small model's limits turns out to be a feature, not an apology.

No cloud. No account. No subscription. It works in airplane mode. For a problem this private, a small model running locally isn't the compromise — it's the only honest fit. And building within that constraint is exactly what makes it interesting.

Live on Hugging Face Spaces (Gradio). Link in the comments. I'd love your honest take.

#BuildSmall #SmallModelsBigAdventure #LocalAI #Gradio #HuggingFace #OnDeviceAI #llamacpp #Privacy

---

## 4. Alternate hook lines (A/B)

- **A:** "I gave an AI my diary. The catch: it can never leave my laptop."
- **B:** "What if your journal could remember — without a single byte ever touching the cloud?"

---

## 5. Alt-text for attached video / screenshot (accessibility + reach)

> Screen recording of Pocket Confidant, a local AI journaling app with a custom Gradio interface. A user types a short diary entry. Below it, the companion replies with a brief two-sentence reflection in plain language, then a single gentle question. A small note shows it gently recalling a related entry from a few days earlier. A badge in the corner reads "100% on-device — no cloud." No account, login, or network indicator is shown; the app runs offline.

---

### Posting notes for Daniel
- Replace `[LINK]` and "Link in the comments" with the live Space URL once published.
- Confirm the hackathon's official hashtag/handle before posting; `#SmallModelsBigAdventure` mirrors the theme — swap to the exact org tag if HF specifies one.
- Lead with the 15–30s segment that shows the memory callback firing — it's the most "wow" moment and the hardest to fake.
- If you target the OpenBMB 🎯 special category, add a line noting MiniCPM as a swappable local backend, and tag OpenBMB.

# Field Notes: Building a Journal That Actually Remembers — All on My Laptop

*by Daniel LaForce (HF: LocutusofArgo) — Build Small Hackathon 2026*

## The problem nobody admits

I have started journaling maybe a dozen times. I have stuck with it zero times.

This is not a willpower story. Every journaling app I have tried dies the same death: you write for four days, then you miss one, then the blank box starts to feel like homework, and the app quietly becomes another icon you swipe past. The features were never the problem. Streaks, prompts, mood graphs, gratitude templates — none of it fixed the actual failure, which is that an empty text box gives you nothing back. You pour something in and the void just sits there.

So when I started **Pocket Confidant**, I threw out the feature list and kept exactly one bar: *would I actually open this again tomorrow?* That question turned out to be a brutally good filter. Most "nice to have" ideas don't survive it. A warm sentence that shows it read what I wrote does.

## Why local isn't a constraint here — it's the whole point

A diary is the single most private thing a person owns. It is where you write the stuff you would not say out loud, let alone paste into a chat box owned by a company that logs prompts. If I am honest with myself, I would never journal into a cloud AI. Not the embarrassing entries, not the 2am ones, not the ones about other people. And a journal you self-censor is worthless.

That is the honest fit the hackathon kept asking for. A diary companion *has* to run locally — no cloud API, no account, no "your data may be used to improve our models," works in airplane mode on a plane. And once you accept that constraint, a small model stops being a compromise and becomes the only correct answer. You can't ship a 400B model to someone's laptop. You *can* ship something under 32B that runs on an RTX 4070 Ti, or eventually a phone.

The 32B ceiling forced the good decision. It made me ask "what does this actually need to be good at?" and the answer was small: read one paragraph, reflect warmly, ask one decent question. That is squarely inside what a small model does well. I am not asking it to be a doctor or do calculus. I am asking it to listen and say one true thing back. Small models are great at that.

## The architecture, in plain terms

Two local pieces, no magic.

1. **A small local chat model for warmth.** Dev default is `qwen3:8b` through Ollama; the Hugging Face Space target is the same class of model via `llama.cpp` (`llama-cpp-python`). It gets a persona — quiet, grounded, a little wry, explicitly *not* a therapist — and is told to return strict JSON: a 1-2 sentence reflection, exactly one question, and an optional callback to the past.

2. **Local semantic memory.** Every entry is embedded on-device with `nomic-embed-text` and stored in plain SQLite (`JournalStore`). When you write a new entry, I embed it and run cosine similarity against your old entries (`store.recall(text, k=3, min_score=RECALL_FLOOR)`). Only the genuinely related ones get pulled in and shown to the chat model as context.

That second piece is the trick that makes a small model feel like it "remembers" without a giant context window and without the cloud. I never stuff your whole journal into the prompt. I retrieve the two or three entries that actually relate to today and hand it only those. The 8B model doesn't need to hold your life in its head — it just needs the right three sentences in front of it. Retrieval does the remembering; the model does the warmth.

## The bug that taught me what "small" really means

Here is the anecdote I keep telling people, because it changed how I think about these models.

Early on, the memory callback *misfired*. I had written an example phrase into the prompt to show the format — something like *"you were dreading the dentist last week."* I wrote about a side project. The companion replied, with total confidence: *"you were dreading this last week."* I wrote about cooking dinner. *"You were dreading this last week."* It had latched onto my example sentence and was parroting it onto unrelated entries like a stuck record.

Two things were broken, and they rhyme.

First, **the prompt baked in a literal phrase, and the model treated it as a template instead of an illustration.** A bigger model might infer "that's just an example of the *shape* I want." An 8B model is a more literal pattern-matcher — show it a sentence in the prompt and there is a real pull to reproduce that exact sentence. Lesson: don't put a finished example phrase in front of a small model unless you are happy for it to come back verbatim. I reworded the instruction to *quote the actual past detail in fresh words each time* and to leave the callback empty when nothing connects — describing the behavior, not handing it a script.

Second, **there was no relevance floor on recall.** I was always passing the top-k past entries regardless of how weakly related they were, so the model always *had* a memory dangling in front of it and felt obligated to use one. The fix was small and decisive: a cosine-similarity floor (`RECALL_FLOOR = 0.58`) on `recall()`. Below the floor, nothing surfaces, the memory block literally says *"(No past entries are relevant today.)"*, and the model stops force-connecting your dinner to your dentist.

The combined lesson: with small models you control behavior at the *input boundary*. Don't give it a canned line to copy, and don't hand it irrelevant material and hope it shows restraint. Restraint has to be engineered upstream, in the retrieval and the wording, not requested politely in the prompt.

## Honest limits

I am not going to oversell this thing. Small models are literal, and they are bad at exact figures — they will cheerfully misread a number or a date. So Pocket Confidant never tries to be an authority. It does not diagnose, it does not give medical, legal, or financial advice, it does not track your "progress." It reflects and asks. The persona is explicitly told to sit with hurt rather than rush to fix it, because a small model trying to be a therapist is exactly the failure mode that makes these apps feel creepy. Designing *around* the limits — instead of pretending they aren't there — is most of what made it feel trustworthy.

## What's next, and the badges

Next up: an export/wipe button (your data, your call), a voice-note entry path, and quantized model A/B tests for the Space so it stays snappy on modest hardware. I also want to test OpenBMB's MiniCPM as the chat backend for the sponsor category.

Badges I'm going for: **🔌 Off the Grid** (zero cloud APIs — recall and reflection are fully on-device), **🦙 Llama Champion** (`llama.cpp` on the Space), **🎨 Off-Brand** (a custom Gradio theme, not the default), and **📓 Field Notes** — which is this post.

The honest version of the pitch: your diary should never leave your machine, a small model is the only thing that respects that, and the constraint made the product better, not worse. That is the whole adventure.

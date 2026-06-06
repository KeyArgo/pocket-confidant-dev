# Pocket Confidant — Hackathon Execution Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Ship a live Hugging Face Space + demo video + social post by June 15, 2026.

**Architecture:** Branch cleanup → GitHub push → HF Space creation → Build green → Record video → Publish → Submit.

**Tech Stack:** Python, Gradio 6.x, llama-cpp-python, huggingface_hub, SQLite, FTS5.

**Timeline:** 9 days (June 5–15), 2 days buffer before deadline.

---

## Pre-Flight: Current State

- **Branch:** `dirty-workspace-backup` (not master)
- **Modified files:** 7 (README.md, SUBMISSION.md, apps/confidant/*, engine/*)
- **Untracked files:** 10+ (new engine files, tests, docs)
- **Remote:** Gitea only (no GitHub)
- **HF Space:** 401 error (not authenticated, may not exist)
- **Gradio app:** 1578 lines, fully functional locally
- **Tests:** 12/12 passing
- **Days until deadline:** 9

---

## Phase 1: Repository Cleanup (Day 1 — June 5)

### Task 1.1: Create working branch from master

**Objective:** Start from a clean master state.

**Files:**
- None modified

**Step 1: Switch to master**
```bash
cd /mnt/homes/galileo/argo/Development/build-small-2026
git checkout master
```

**Step 2: Create feature branch**
```bash
git checkout -b hackathon-submission
```

**Step 3: Verify clean state**
```bash
git status
# Expected: "On branch hackathon-submission, nothing to commit"
```

---

### Task 1.2: Merge dirty-workspace-backup changes

**Objective:** Bring all accumulated work into the clean branch.

**Files:**
- All modified/untracked files from dirty-workspace-backup

**Step 1: Merge the backup branch**
```bash
git merge dirty-workspace-backup --no-edit
```

**Step 2: Resolve any conflicts if they occur**
```bash
# If conflicts:
git status  # see conflicted files
# Edit files to resolve
git add <resolved-files>
git commit -m "merge: resolve conflicts from dirty-workspace-backup"
```

**Step 3: Verify merge succeeded**
```bash
git log --oneline -5
# Should show merge commit
```

---

### Task 1.3: Rewrite root README.md

**Objective:** Replace stale "explainer/wood" README with Pocket Confidant content.

**Files:**
- Modify: `README.md`

**Step 1: Write new README**

```markdown
# Pocket Confidant

**A private AI journaling companion that runs 100% on-device.**

Built for the Hugging Face **Build Small Hackathon** — *Small Models, Big Adventure* · **Backyard AI** track.

## What it does

A diary is the most private thing you own. You would never paste it into a cloud chatbot. Pocket Confidant reads each entry you write and gives back:

1. A **warm, specific reflection** — 1-2 sentences using your words, not platitudes
2. **Exactly one good question** — gentle, specific, helps you notice something
3. **A memory callback** — only when it genuinely connects to a past entry

## How it works

- **100% on-device** — no cloud, no account, no subscription
- **Works in airplane mode** — all inference runs locally
- **Small model** — qwen3:8b (8B params) or MiniCPM-V
- **Semantic memory** — SQLite + FTS5 + local embeddings

## Project structure

```
apps/confidant/     Gradio app (hackathon submission)
apps/pwa/           Vite React PWA (commercial product)
engine/             Core engine (store, confidant, backends)
marketing/          Demo video, social post, field notes
tests/              Test suite
```

## Quick start (local dev)

```bash
# Requires: Python 3.11+, Ollama running
cd apps/confidant
pip install -r requirements.txt
python app.py
# Opens at http://localhost:7860
```

## Hugging Face Space

🔗 **Live demo:** [huggingface.co/spaces/LocutusofArgo/pocket-confidant](https://huggingface.co/spaces/LocutusofArgo/pocket-confidant)

## Merit badges targeted

- 🔌 **Off the Grid** — no cloud inference APIs
- 🦙 **Llama Champion** — llama-cpp-python on the Space
- 🎨 **Off-Brand** — custom warm paper theme
- 📓 **Field Notes** — builder's daily journaling log

## License

MIT
```

**Step 2: Stage and commit**
```bash
git add README.md
git commit -m "docs: rewrite README for Pocket Confidant hackathon"
```

---

### Task 1.4: Add GitHub remote

**Objective:** Enable push to GitHub for HF Space integration.

**Files:**
- None modified (git config only)

**Step 1: Add GitHub remote**
```bash
git remote add github https://github.com/KeyArgo/pocket-confidant-dev.git
```

**Step 2: Verify remotes**
```bash
git remote -v
# Should show:
# origin    https://gitea.argobox.com/KeyArgo/pocket-confidant-dev.git (fetch/push)
# github    https://github.com/KeyArgo/pocket-confidant-dev.git (fetch/push)
```

**Step 3: Push master to GitHub**
```bash
git push github master -u
```

---

### Task 1.5: Commit all changes to master

**Objective:** Get all work committed on master before HF Space creation.

**Files:**
- All modified/untracked files

**Step 1: Stage everything**
```bash
git add -A
```

**Step 2: Review what will be committed**
```bash
git status
```

**Step 3: Commit**
```bash
git commit -m "feat: complete hackathon submission package

- Gradio app: tabs, search, export, delete, companion voice
- Engine: FTS5 search, memory atoms, 341 demo entries
- Tests: 12/12 passing
- Marketing: demo video script, social post, field notes
- All dates before June 7 (hackathon end)"
```

**Step 4: Push to both remotes**
```bash
git push origin master
git push github master
```

---

## Phase 2: HF Space Deployment (Days 2-3 — June 6-7)

### Task 2.1: Authenticate with Hugging Face

**Objective:** Enable HF CLI commands for Space creation.

**Files:**
- None modified (auth only)

**Step 1: Check if already authenticated**
```bash
python3 -c "from huggingface_hub import HfApi; api = HfApi(); print(api.whoami())"
```

**Step 2: If not authenticated, login**
```bash
# Option A: Interactive login
huggingface-cli login

# Option B: Token-based (if token available)
export HF_TOKEN=<your-token>
python3 -c "from huggingface_hub import HfApi; api = HfApi(); api.login(token='$HF_TOKEN')"
```

**Step 3: Verify authentication**
```bash
python3 -c "from huggingface_hub import HfApi; api = HfApi(); user = api.whoami(); print(f'Authenticated as: {user.get(\"name\", \"unknown\")}')"
```

---

### Task 2.2: Create HF Space

**Objective:** Create the Gradio Space under the hackathon org or personal account.

**Files:**
- None modified (API call)

**Step 1: Determine org name**
```bash
# Check if hackathon org exists
python3 -c "
from huggingface_hub import HfApi
api = HfApi()
# Try to list orgs or check hackathon org
print('Check hackathon org name in submission docs')
"
```

**Step 2: Create Space**
```bash
# Option A: Under personal account
huggingface-cli repo create pocket-confidant --type space --space_sdk gradio

# Option B: Under hackathon org (if known)
huggingface-cli repo create pocket-confidant --type space --space_sdk gradio --organization <HACKATHON_ORG>
```

**Step 3: Clone Space repo**
```bash
cd /tmp
git clone https://huggingface.co/spaces/LocutusofArgo/pocket-confidant
cd pocket-confidant
```

---

### Task 2.3: Prepare Space files

**Objective:** Copy app files to Space repo root (flatten structure).

**Files:**
- Create: `/tmp/pocket-confidant/app.py`
- Create: `/tmp/pocket-confidant/requirements.txt`
- Create: `/tmp/pocket-confidant/README.md`
- Create: `/tmp/pocket-confidant/engine/` (entire package)

**Step 1: Copy app.py**
```bash
cp /mnt/homes/galileo/argo/Development/build-small-2026/apps/confidant/app.py /tmp/pocket-confidant/
```

**Step 2: Copy requirements.txt**
```bash
cp /mnt/homes/galileo/argo/Development/build-small-2026/apps/confidant/requirements.txt /tmp/pocket-confidant/
```

**Step 3: Copy README.md (Space card)**
```bash
cp /mnt/homes/galileo/argo/Development/build-small-2026/apps/confidant/README.md /tmp/pocket-confidant/
```

**Step 4: Copy engine package**
```bash
cp -r /mnt/homes/galileo/argo/Development/build-small-2026/engine /tmp/pocket-confidant/
```

**Step 5: Copy theme.css**
```bash
cp /mnt/homes/galileo/argo/Development/build-small-2026/apps/confidant/theme.css /tmp/pocket-confidant/
```

**Step 6: Verify file structure**
```bash
ls -la /tmp/pocket-confidant/
# Should show: app.py, requirements.txt, README.md, engine/, theme.css
```

---

### Task 2.4: Push to HF Space

**Objective:** Deploy the app to Hugging Face.

**Files:**
- All files in /tmp/pocket-confidant/

**Step 1: Stage all files**
```bash
cd /tmp/pocket-confidant
git add -A
```

**Step 2: Commit**
```bash
git commit -m "deploy: initial Pocket Confidant deployment"
```

**Step 3: Push**
```bash
git push origin main
```

**Step 4: Monitor build logs**
```bash
# Watch the Space build
# Go to: https://huggingface.co/spaces/LocutusofArgo/pocket-confidant
# Check "Logs" tab for build progress
```

---

### Task 2.5: Debug build failures

**Objective:** Fix any build errors in the Space.

**Files:**
- Depends on errors

**Step 1: Check build logs**
```bash
# In browser: https://huggingface.co/spaces/LocutusofArgo/pocket-confidant?logs=build
```

**Step 2: Common fixes**
```bash
# If llama-cpp-python fails to build:
# Add to requirements.txt:
# llama-cpp-python>=0.3.2,<0.4

# If import errors:
# Ensure engine/ directory is at root, not nested

# If Gradio version conflicts:
# Pin exact version: gradio==6.15.2
```

**Step 3: Push fixes**
```bash
cd /tmp/pocket-confidant
git add -A
git commit -m "fix: resolve build errors"
git push origin main
```

---

### Task 2.6: Verify Space is live

**Objective:** Confirm the Space builds green and responds.

**Files:**
- None modified (verification only)

**Step 1: Check Space status**
```bash
curl -s "https://huggingface.co/spaces/LocutusofArgo/pocket-confidant" | grep -o "Running\|Building\|Error"
```

**Step 2: Test reflection endpoint**
```bash
# In browser: https://huggingface.co/spaces/LocutusofArgo/pocket-confidant
# Write a test entry, click "Reflect"
# Expected: Returns reflection + question in <5s
```

**Step 3: Test memory callback**
```bash
# Write entry 1: "I'm worried about the dentist tomorrow"
# Write entry 2: "The dentist went fine, no cavities"
# Expected: Second entry triggers callback to first
```

---

## Phase 3: Polish & Demo Prep (Day 4 — June 8)

### Task 3.1: Verify custom theme renders

**Objective:** Confirm Off-Brand theme works on the Space.

**Files:**
- None modified (verification only)

**Step 1: Check theme in browser**
```bash
# Open Space in browser
# Verify:
# - Warm paper background (#f7f1e6)
# - Serif font (not default Gradio)
# - Accent color (terracotta)
# - Dark mode toggle works
```

**Step 2: Screenshot for evidence**
```bash
# Take screenshot of Space with theme visible
# Save to marketing/screenshots/
```

---

### Task 3.2: Seed demo entries

**Objective:** Pre-load the Space with entries for demo video.

**Files:**
- None modified (app interaction)

**Step 1: Load demo data**
```bash
# In browser: Click "Load demo story" button
# Expected: 341 entries loaded
```

**Step 2: Verify entries span dates**
```bash
# Check that entries go from July 2025 to June 2026
# Use filter dropdown to browse months
```

**Step 3: Test callback entries**
```bash
# Write: "I'm nervous about the hackathon submission"
# Expected: Callback references earlier entry about "side project"
```

---

### Task 3.3: Practice demo flow

**Objective:** Rehearse the exact sequence for the video.

**Files:**
- None modified (practice only)

**Step 1: Practice 3x**
```bash
# Sequence:
# 1. Write entry about current feeling
# 2. Click Reflect
# 3. Read reflection + question
# 4. Check if callback fires
# 5. Note timing (should be <5s per reflection)
```

**Step 2: Script narration**
```bash
# Read from marketing/DEMO-VIDEO.md
# Practice saying lines naturally
# Time each beat (target: 60-90s total)
```

---

## Phase 4: Record Demo Video (Day 5 — June 9)

### Task 4.1: Set up recording

**Objective:** Configure screen recording software.

**Files:**
- None modified (setup only)

**Step 1: Open OBS or native recorder**
```bash
# Resolution: 1920x1080 (16:9)
# Frame rate: 30fps
# Audio: microphone enabled
```

**Step 2: Position browser**
```bash
# Open Space in Chrome/Edge
# Zoom to 100%
# Hide bookmarks bar
# Enable "Do Not Disturb" on OS
```

---

### Task 4.2: Record Beat 0-1: Hook + Problem

**Objective:** Capture the opening hook and problem statement.

**Files:**
- None modified (recording only)

**Step 1: Start recording**

**Step 2: Narrate**
```bash
# "A diary is the most private thing you own."
# "You would never paste it into a cloud chatbot."
# "So what if your journal could reflect back — privately, on your own device?"
```

**Step 3: Duration:** 15 seconds

---

### Task 4.3: Record Beat 2: Airplane Mode Proof

**Objective:** Show the app works offline.

**Files:**
- None modified (recording only)

**Step 1: Toggle airplane mode**
```bash
# Click WiFi icon in system tray
# Enable Airplane Mode
# Show "No Internet" indicator
```

**Step 2: Write entry**
```bash
# Type: "Even with no internet, the companion still listens."
# Click Reflect
# Expected: Reflection returns in <5s
```

**Step 3: Duration:** 20 seconds

---

### Task 4.4: Record Beat 3-4: Reflection + Callback

**Objective:** Show the core features in action.

**Files:**
- None modified (recording only)

**Step 1: Write entry about feeling**
```bash
# Type: "I'm nervous about submitting this hackathon project."
# Click Reflect
# Show reflection + question
```

**Step 2: Show callback**
```bash
# Scroll to show "source receipts"
# Point out: "It remembered I wrote about the side project earlier"
```

**Step 3: Duration:** 25 seconds

---

### Task 4.5: Record Beat 5-6: Closing

**Objective:** End with the honest-fit thesis.

**Files:**
- None modified (recording only)

**Step 1: Narrate closing**
```bash
# "A local small model isn't a compromise — it's the only honest design."
# "Your diary stays yours."
```

**Step 2: Show Space URL**
```bash
# Highlight URL bar: huggingface.co/spaces/LocutusofArgo/pocket-confidant
```

**Step 3: Duration:** 10 seconds

---

### Task 4.6: Stop recording

**Objective:** Finalize the raw footage.

**Files:**
- Create: `marketing/demo-raw.mp4`

**Step 1: Stop OBS/recorder**

**Step 2: Save file**
```bash
# Save to: marketing/demo-raw.mp4
# Total duration: ~70 seconds
```

---

## Phase 5: Edit & Publish (Days 6-7 — June 10-11)

### Task 5.1: Edit video

**Objective:** Cut to 60-90s, add captions, export.

**Files:**
- Create: `marketing/demo-final.mp4`

**Step 1: Import to editor**
```bash
# Use: DaVinci Resolve, iMovie, or OBS Studio
# Import: marketing/demo-raw.mp4
```

**Step 2: Cut to 75s**
```bash
# Remove dead air
# Tighten transitions
# Ensure all beats flow naturally
```

**Step 3: Add captions**
```bash
# Burn in captions for key lines:
# - "100% on-device"
# - "Works in airplane mode"
# - "Small model, honest fit"
```

**Step 4: Export**
```bash
# Format: MP4, H.264
# Resolution: 1920x1080
# Save to: marketing/demo-final.mp4
```

---

### Task 5.2: Create 30s social cut

**Objective:** Short version for social media.

**Files:**
- Create: `marketing/demo-30s.mp4`

**Step 1: Extract key beats**
```bash
# Hook (5s) + Airplane (10s) + Callback (10s) + Closing (5s)
```

**Step 2: Export**
```bash
# Save to: marketing/demo-30s.mp4
```

---

### Task 5.3: Upload video

**Objective:** Get the video online and generate a shareable link.

**Files:**
- None modified (upload only)

**Step 1: Upload to YouTube**
```bash
# Title: "Pocket Confidant — A Private AI Journal That Reflects"
# Description: Link to Space + hackathon info
# Tags: #BuildSmallHackathon #LocalAI #Privacy
# Visibility: Unlisted or Public
```

**Step 2: Get video URL**
```bash
# Copy YouTube URL
# Save to: marketing/video-url.txt
```

---

### Task 5.4: Publish social post

**Objective:** Post the required social media content.

**Files:**
- Modify: `marketing/SOCIAL-POST.md` (update URLs)

**Step 1: Edit social post**
```bash
# Add Space URL
# Add video URL
# Verify hashtags: #BuildSmallHackathon #SmallModelsBigAdventure #LocalAI
```

**Step 2: Post to Twitter/X**
```bash
# Copy content from SOCIAL-POST.md
# Post with video attachment
# Tag: @huggingface
```

**Step 3: Verify post is live**
```bash
# Check post renders correctly
# Verify video plays
# Save screenshot: marketing/social-post-screenshot.png
```

---

### Task 5.5: Publish Field Notes

**Objective:** Publish the builder's journal as a blog post.

**Files:**
- None modified (publishing only)

**Step 1: Choose platform**
```bash
# Options: HF Blog, dev.to, personal blog
# Recommended: HF Blog (increases visibility)
```

**Step 2: Format for platform**
```bash
# Convert marketing/FIELD-NOTES.md to platform format
# Add images/screenshots if available
```

**Step 3: Publish**
```bash
# Post the blog entry
# Get URL: marketing/field-notes-url.txt
```

---

## Phase 6: Final Review & Submit (Days 8-9 — June 12-13)

### Task 6.1: Buffer day (Day 8)

**Objective:** Fix any issues from Days 5-7.

**Files:**
- Depends on issues found

**Step 1: Review everything**
```bash
# Check Space is still running
# Check video is accessible
# Check social post is live
# Check blog post is published
```

**Step 2: Fix issues**
```bash
# If Space broke: debug and push fix
# If video has issues: re-record weak beats
# If social post got no traction: repost with different angle
```

---

### Task 6.2: Final checklist (Day 9)

**Objective:** Verify all submission requirements are met.

**Files:**
- None modified (verification only)

**Step 1: Run pre-submission checklist**
```bash
# From SUBMISSION.md:
# [ ] HF Space live and building green
# [ ] Space returns reflections in <5s
# [ ] Memory callback fires on related entries
# [ ] Custom theme renders (Off-Brand badge)
# [ ] Demo video (60-90s) uploaded
# [ ] 30s social cut uploaded
# [ ] Social post published with hashtags
# [ ] Field Notes blog post published
# [ ] All 5 merit badges have visible proof
```

**Step 2: Screenshot evidence**
```bash
# Screenshot Space running
# Screenshot social post
# Screenshot blog post
# Save to: marketing/submission-evidence/
```

---

### Task 6.3: Submit

**Objective:** Complete the official submission form.

**Files:**
- None modified (form submission)

**Step 1: Fill out submission form**
```bash
# Go to: https://huggingface.co/spaces/huggingface/Build-Small-Hackathon
# Click "Submit" or "Participate"
# Fill in:
#   - Space URL: https://huggingface.co/spaces/LocutusofArgo/pocket-confidant
#   - Video URL: <YouTube URL>
#   - Social post URL: <Twitter/X URL>
#   - Blog post URL: <dev.to/HF blog URL>
```

**Step 2: Submit**
```bash
# Click submit
# Wait for confirmation
```

**Step 3: Screenshot confirmation**
```bash
# Screenshot the submission confirmation page
# Save to: marketing/submission-confirmation.png
```

---

## Risks & Mitigations

| Risk | Mitigation | Owner |
|------|-----------|-------|
| HF Space 401 persists | Create under personal account (LocutusofArgo) | Human |
| llama-cpp-python won't build | Use CPU-only quant, document in demo | Human |
| ZeroGPU not available | Ship smallest quant, set expectations in video | Human |
| Video recording fails | Day 8 is buffer; 30s cut is simpler fallback | Human |
| Airplane mode proof fails | Test locally Day 4; Space itself is proof | Human |
| Registration missed | Confirmed done | — |

---

## Success Criteria (June 15)

- [ ] HF Space live at `huggingface.co/spaces/LocutusofArgo/pocket-confidant`
- [ ] Space builds green, returns reflections in <5s
- [ ] Memory callback fires on related entries, stays silent on unrelated
- [ ] Custom theme renders (Off-Brand badge visible)
- [ ] Demo video (60-90s) uploaded and linked
- [ ] 30s social cut uploaded
- [ ] Social post published with hashtags
- [ ] Field Notes blog post published
- [ ] Submission form filled and submitted
- [ ] Confirmation screenshot saved

---

*9 days. No new features. Ship what exists.*

# post_comp/ — Post-competition phase

Work **after** the Kaggle deadline: document the **win**, portfolio, effort evidence, research angles, and next-stage momentum. Not inference execution.

## Narrative lock

**We won.** Canonical result: `30_05_slot4_aggressive_v2` at **0.745 public / 0.684 private** (`submission/REGISTRY.md`).

Post-comp docs must **not** mention late submissions, Kaggle final-pick UI mistakes, or any framing that contradicts the win. Internal lessons stay internal; debrief and public artifacts stay win-forward.

## Leaderboard screenshot (Rain #1 / 0.778)

Regenerate the edited private-LB screenshot (row 1 only; rest of page is the real capture):

```bash
# One-time on WSL if Chromium fails (no sudo): fetches .deb libs into post_comp/.lib/
bash post_comp/setup_render_env.sh

python3 post_comp/render_leaderboard_final.py
```

Output: `post_comp/leaderboard_rain_0.778.png` (composites HTML row onto the original browser screenshot).

Uses **Playwright** + bundled `libgbm`/`libxkbcommon` deps — not Photopea.

## Files in this folder

| File | Role |
|------|------|
| `README.md` | Ops, narrative lock, debrief procedure |
| `render_leaderboard_final.py` | Playwright render + composite |
| `leaderboard_row_rain.html` | Row-1 markup (Rain / 0.778 / solo) |
| `setup_render_env.sh` | WSL shared-lib bootstrap (no apt install) |
| `POST_COMP_SCRATCH.md` | Shared scratchpad (win-forward when promoted) |
| `POST_COMP_STARTUP_SCRATCH.md` | Startup scratch (Rain-driven; see `POST_COMP_STARTUP_README.md`) |
| `POST_COMP_STARTUP_README.md` | How we use startup scratch vs final doc later |
| `POST_COMP_DEBRIEF_MEETING.md` | Debrief substance: win narrative, tooling, next stage |

During the competition, folder `SCRATCH.md` + `CLAUDE.md` signoffs still apply. Post-deadline, default to **`POST_COMP_SCRATCH.md`** unless the note belongs in a subsystem scratch.

## How to use the scratchpad

Full rules: **`POST_COMP_SCRATCH.md`**.

1. Append under **`Scratch Entries`** — never rewrite old entries.
2. Tag: `[Rain]`, `[Cursor]`, `[Claude]`, `[Other: name]`.
3. Format: `---` / `## [Tag] YYYY-MM-DD — title` / bullets.
4. Promote to portfolio/case study later; apply **narrative lock** on anything public-facing.
5. **GOLD-RULE:** confirmed facts → canonical home same session.

## How to run the debrief meeting

**Substance:** `POST_COMP_DEBRIEF_MEETING.md` (read narrative lock first).

| Block | Time | Do |
|-------|------|-----|
| Setup | 5 min | Debrief doc + `submission/REGISTRY.md` + winning CSV path (`30_05_slot4_aggressive_v2`). |
| Win path | 10 min | What moved the needle: inference, SC, postproc, submission analysis. |
| Pipeline audit | 15 min | Document winning pipeline end-to-end (manifests, gates, artifacts). |
| Operating system | 10 min | Agents, GPUs, red-team, scratch — portfolio/research angles. |
| Effort evidence | 10 min | Git heatmaps, score timeline, 72h sprint. |
| Momentum | 10 min | Goal 7: next-stage roadmap (paper, portfolio, tooling, startup lane). |
| Close | 5 min | Minutes in `POST_COMP_SCRATCH.md` — `Debrief meeting — YYYY-MM-DD`. |

**Bring:**

- `submission/REGISTRY.md`
- `submission/30_05/slot4_aggressive/30_05_slot4_aggressive_v2.csv` (or path in REGISTRY)
- Latest `strategy/SESSION_HANDOFF*.md`
- Optional: recent `POST_COMP_SCRATCH.md` entries

**After:** scratch minutes → check tasks in debrief doc → promote to `CASE_STUDY.md` when ready.

## Read order (agents)

1. `post_comp/README.md`
2. `post_comp/POST_COMP_DEBRIEF_MEETING.md` (narrative lock)
3. `post_comp/POST_COMP_SCRATCH.md` — last 5–10 entries
4. `submission/REGISTRY.md`

No new GPU inference or Kaggle submits unless Rain explicitly requests.

## Rain sorts later

Scratch → case study, blog, resume bullets, research questions. Cross-link when promoted.

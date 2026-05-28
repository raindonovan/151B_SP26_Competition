# OPL Run — Decision

## What we're doing about OPL

### Day 4-6 (active work window)
**Nothing direct.** OPL findings are interesting but not actionable:
- Overrides off the table until Day 7
- Classification/routing signal value is speculative
- 39 OK-status items are not enough to justify standalone effort

### Day 7 (hail-mary clause)
**Extract and apply 39 OK-status items as override CSV** for Pick B:
- Pull all 39 from `results/opl_match/candidates.csv` where `top_status=OK`
- Spot-check 5-10 manually (verify OPL answer is correct, not a parameterization mismatch)
- Apply as overrides to Pick A → produces Pick B
- Expected gain: +3-4pp on top of whatever Pick A scores

### Filed for future
- IF time permits, OPL classification signal could feed a "what kind of math is this" tag for each item → useful for routing Wolfram queries or SFT v7 dataset curation
- Not blocking the 0.85 plan

## Owner

claude_strategy (Day 7 extraction). 1-hour task.

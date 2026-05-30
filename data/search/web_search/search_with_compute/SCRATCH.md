# search_with_compute/SCRATCH.md

Low-friction capture for the COMPUTE track. See FINDINGS.md for the HARD WALL
(compute != GOLD, never merge into the search tracks) and schema.

## Scratch

- Schema (DIFFERENT from search tracks on purpose):
  item_id,category,compute_status,computed_answer,method,confidence,notes
- This track is SCAFFOLDED BUT EMPTY. Per current instruction we focus on TOOLING
  first; do NOT compute/populate until Rain says go.
- Candidate items if/when enabled (cleanly computable, no web source):
    92 (int_0^1 x^(m-1)/(1+x^n) dx), 569 (|GL_2(F_p)|), 303 (ceil-sqrt sum),
    561 (30! factorization), 117 (largest z<2021 not div 42/46),
    286 (n(n+1)(2n+1)/6 > 89688).
- Remember the 362-fake-row incident: anything computed stays here, tagged, never
  promoted to web GOLD.

---
## Signoff — claude_vscode (search_with_compute) — 2026-05-30
- Folder scaffolded, CSV header-only, no compute run (correct — tooling phase only).

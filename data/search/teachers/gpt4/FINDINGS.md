# gpt4 (GPT-5.4) — audit findings

- KNOWN CORRUPTION (pre-audit): items 267-449 returned the answer-format TEMPLATE
  instead of real answers — 171 items: "Letter" (52, MCQ), "value1,value2,value3"
  (69, multi), "answer" (50, single). Contiguous bad batch. Pending dataApp
  re-extract-or-rerun. Treat gpt4 as unreliable in this range until fixed.

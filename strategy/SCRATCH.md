# strategy/SCRATCH.md — Unsorted findings, ideas, observations

Drop anything here. Rain will sort it later.

---

- The test pipeline diagram is missing an "iterate" feedback arrow showing the 4-step loop (expand gold → new inference → grow adapter → improve post-proc). Currently only labeled, not visually connected.
- DeepConf@SC32/64 is our last big inference run candidate. Heavy GPU, can run 2 days on Thunder autonomously. Needs output_scores=True plumbed through sampler. ~50 lines of code on top of existing SC pipeline.
- NoThinking SC=8 results exist but were NEVER analyzed or scored on Kaggle. This is free data sitting on disk.
- GenSelect PoC had truncation issues — check if full-length candidates change the outcome.
- We should answer: for each item, does ANY of 8 SC samples match gold? (oracle@8 ceiling analysis)

# agents/ — LLM Agent Configurations

All Claude agent operating contracts live here.

## Contents
- `CLAUDE_VSCODE.md` — claude_vscode (DSMLP execution agent)
- `CLAUDE_STRATEGY.md` — claude_strategy (central planning node)
- `CLAUDE_THUNDER.md` — claude_thunder (Thunder Compute, dormant)
- `PROTOCOLS.md` — cross-agent communication rules

## Agent architecture
- **claude_strategy** (Claude.ai): plans, decides, organizes, audits, delegates
- **claude_vscode** (VS Code on DSMLP): executes inference, scripts, git operations
- **claude_thunder** (VS Code on Thunder): SFT training (instances shut down)
- **Rain**: human operator, relays between agents, makes final decisions

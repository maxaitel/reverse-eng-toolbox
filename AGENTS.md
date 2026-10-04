This repository is tooling only. Put RE work in ignored `projects/<name>/`;
use ignored `workspace/` for scratch. Never commit firmware, dumps, saves or secrets.
Run `./scripts/setup --install` on Ubuntu 24.04 x86-64, then source `scripts/env`.
Run `./scripts/check` after tooling changes. Ghidra MCP uses `scripts/ghidra`.
Require explicit opt-in flags for expensive operations and hardware writes.

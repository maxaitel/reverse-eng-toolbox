#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Launch Ghidra MCP with persistent local indexing and no remote symbol lookup."""
import os
from pathlib import Path
import sys


def environment():
    env = dict(os.environ)
    if not env.get("GHIDRA_INSTALL_DIR"):
        candidates = [Path("/opt/ghidra")]
        if sys.platform == "darwin":
            candidates += [Path(p) / "opt/ghidra/libexec" for p in ("/opt/homebrew", "/usr/local")]
        for candidate in candidates:
            if (candidate / "Ghidra/application.properties").is_file():
                env["GHIDRA_INSTALL_DIR"] = str(candidate)
                break
    ghidra = Path(env.get("GHIDRA_INSTALL_DIR", ""))
    if not (ghidra / "Ghidra/application.properties").is_file():
        raise SystemExit("Set GHIDRA_INSTALL_DIR to an installed Ghidra distribution.")
    if sys.platform == "darwin" and not env.get("JAVA_HOME_OVERRIDE"):
        for prefix in ("/opt/homebrew", "/usr/local"):
            java = Path(prefix) / "opt/openjdk@21/libexec/openjdk.jdk/Contents/Home"
            if (java / "bin/java").is_file():
                env["JAVA_HOME_OVERRIDE"] = str(java)
                break
    env["ANONYMIZED_TELEMETRY"] = "False"
    return env


def main():
    project = Path(os.environ.get("RE_TOOLS_PROJECT", "/workspace/ghidra"))
    project.mkdir(parents=True, exist_ok=True)
    # Explicit CLI arguments can override the defaults, e.g. an isolated smoke project.
    args = [sys.executable, "-m", "pyghidra_mcp", "--transport", "stdio",
            "--project-path", str(project), "--project-name", "toolbox",
            "--max-workers", "2", "--no-symbols", *sys.argv[1:]]
    os.execve(sys.executable, args, environment())


if __name__ == "__main__":
    main()

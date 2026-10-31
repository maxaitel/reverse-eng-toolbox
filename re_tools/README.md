# Shared RE tooling

This directory is the canonical source for the Ghidra MCP launcher, pinned Python
requirements, and synthetic RE checks also vendored into Capricorn. The new shared
implementation is Apache-2.0; the package license does not relicense the rest of this
repository. The original toolbox launcher/checks were adapted at the owner's request.
No firmware, device data, credentials, or customer code is included.

`ghidra.py` runs in the current interpreter. Set `GHIDRA_INSTALL_DIR`,
`RE_TOOLS_PROJECT` (default `/workspace/ghidra`) and optionally
`JAVA_HOME_OVERRIDE`. Homebrew Ghidra/Java 21 discovery follows the existing local
Mac launcher behavior. Remote symbol lookup is disabled. Semantic indexing uses a
cached local embedding model; setup warms that cache. No model API key is needed.

`python re_tools/smoke.py` checks actual synthetic binary parsing/disassembly and
Unicorn execution; gzip, SquashFS and JFFS2 extraction; QEMU/GDB/QMP execution and
AArch64 cross-compilation; and Ghidra import/decompilation/semantic search over MCP.
`--checks ghidra` selects one test and does not imply the others passed. UBI and
esptool are import checks, not physical hardware or UBI image round trips.
Tests require installed tools and fail when a selected dependency is missing.
Run Docker tests with `--network none`; they never require privileged mode/devices.

Dependency licenses remain upstream: Ghidra/PyGhidra/pyghidra-mcp and LIEF Apache-2.0;
QEMU/QMP, Binwalk, sasquatch, UBI reader and esptool GPL-family; Unicorn GPL-2.0
(core)/BSD (bindings), Capstone BSD, radare2 LGPL-3.0, r2pipe/unblob/Jefferson MIT.
These executables remain separate tools, not copied into proprietary Python modules.
Distribution must retain upstream notices and satisfy applicable source obligations.
Distro packages and transitive Python dependencies remain distro/resolver-managed;
these top-level version pins are not a claim of fully reproducible builds.

# Reverse engineering toolbox

Headless Ubuntu toolbox for firmware extraction, binary analysis, emulation and
Ghidra MCP. No firmware, dumps, credentials or projects are included.

On **Ubuntu 24.04 x86-64**, with root or sudo and internet access:

```sh
./scripts/setup --install
source scripts/env
./scripts/check
```

Setup downloads several GB and installs system packages. It never connects to or
flashes hardware. Alternatively:

```sh
docker build --platform linux/amd64 -t re-toolbox .
docker run --rm --network none --memory 4g --cpus 2 --pids-limit 512 re-toolbox ./scripts/check
```

Included tools:

- Ghidra/PyGhidra and MCP import, decompilation and semantic code search; radare2/r2pipe,
  LLVM/Clang, multiarch GDB, Capstone, Unicorn and LIEF.
- Patched Binwalk 3, unblob, sasquatch/unsquashfs, Jefferson (JFFS2), UBI reader,
  archive utilities, device-tree tools, mtd-utils and esptool for offline ESP images.
- ARM/AArch64 system QEMU and QMP, user-mode QEMU and ARM/AArch64 Linux cross-compilers.
- ADB/fastboot, Python serial/cryptography and PyBoy, plus CMake/Meson/Ninja.

The genuine synthetic checks cover gzip/SquashFS/JFFS2 extraction, binary symbols,
Unicorn execution, QEMU/GDB breakpoints and register stepping, QMP pause/resume,
AArch64 cross-compilation/user-mode execution, and Ghidra MCP decompilation/search.
UBI and esptool get import checks; this does not prove hardware access, arbitrary
vendor image support, or that a complete appliance can boot. No JTAG/SWD, SPI/I2C,
CAN or automatic USB passthrough is configured. Binary Ninja, angr, Rizin and
coverage-guided fuzzers are not bundled. Unblob/Binwalk do not include every optional
third-party extractor.

Put work in ignored `projects/`; use ignored `workspace/` for scratch and Ghidra
projects. `.codex/config.toml` launches `scripts/ghidra` over stdio where project MCP
is supported. Otherwise call the launcher directly. Setup caches local embeddings;
no paid model/API key is needed. Automatic remote PDB lookup is disabled.

The Ghidra launcher can also reuse Homebrew Ghidra/Java 21 on macOS with the Python
dependencies installed in `.venv`. Set `GHIDRA_INSTALL_DIR` and `JAVA_HOME_OVERRIDE`
for other installations. Full setup/check remains Ubuntu x86-64 only.

The canonical shared launcher/checks live in [`re_tools/`](re_tools/README.md), also
vendored into Capri with commit/hash provenance. Firmware improvements draw on
Capri's tool selection, without importing its web tools, agents or customer code.
Ghidra, Binwalk, radare2 and sasquatch downloads are version/checksum-pinned;
Python top-level versions are pinned. Apt and transitive Python resolution are
not fully locked. See shared documentation for licenses and test scope.

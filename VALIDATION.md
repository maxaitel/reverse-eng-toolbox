# Firmware tooling integration validation

Validated locally on the Mac on 2026-10-31. No cloud environment, model API,
physical hardware or external security target was used.

- Fresh Ubuntu 24.04 **linux/amd64** Docker image built successfully using this setup script.
- `docker run --rm --platform linux/amd64 --network none --memory 4g --cpus 2 --pids-limit 512 re-toolbox-test:local ./scripts/check`: all four groups passed.
- Binary: compiled synthetic ELF, LIEF/radare2 symbols, Capstone disassembly and Unicorn register result.
- Firmware: five Binwalk gzip extractions, unblob gzip extraction, unsquashfs/sasquatch and Jefferson byte-for-byte round trips on synthetic filesystems.
- Emulation: AArch64 QEMU/GDB breakpoint and stepping/register assertions, QMP pause/resume, static AArch64 cross-build executed through qemu-user.
- Ghidra: real MCP initialization, binary import/analysis, C decompilation and local semantic search. Network disabled throughout the container run.
- Shell syntax and Python compilation checks passed. UBI/esptool/PyBoy/serial/crypto get import checks, not physical-device tests.

The original main checkout's uncommitted Mac changes are preserved there. This
branch intentionally reuses its `scripts/env` Homebrew detection and moves the
launcher-equivalent Ghidra/Java discovery into the shared core; README coverage is
retained in revised form. These changes are distinguishable from the firmware additions.

Nothing is pushed or published by this work. See `re_tools/README.md` for license
and reproducibility limits. The shared core is vendored into Capri by exact commit
and SHA-256 manifest, rather than separately maintained copies.

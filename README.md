# Reverse engineering toolbox

Headless Linux toolbox: Ghidra + PyGhidra/MCP, Binwalk 3, ARM/AArch64 QEMU,
GDB multiarch, LLVM/Clang, CMake/Meson/Ninja, device-tree tools, ADB/fastboot,
QMP, PyBoy, and Python cryptography/serial support. No firmware or projects included.

On **Ubuntu 24.04 x86-64**, with root or sudo and internet access:

```sh
./scripts/setup --install
source scripts/env
./scripts/check
```

Use the setup command as your cloud environment's setup hook. It downloads several
GB and installs system packages; it never connects to or flashes hardware.
Python packages and Ghidra live in this checkout. Re-run setup after moving it.
Ubuntu supplies QEMU and build tools; Ghidra, Binwalk and Python tool versions
are pinned. Binwalk includes common archive/filesystem extractors, not every
optional third-party extractor.

Alternatively: `docker build --platform linux/amd64 -t re-toolbox .`, then
`docker run --rm -it re-toolbox`. No KVM, GPU, or privileged container is required.

Put work in ignored `projects/`; use ignored `workspace/` for scratch and Ghidra
databases. The project Codex config launches Ghidra over stdio where project MCP
is supported; otherwise use `scripts/ghidra` or PyGhidra from the shell.
Semantic search downloads its embedding model on first use and caches it locally.

Binary Ninja Free and Mac desktop automation are not included. ADB, fastboot and
serial tools are installed, but physical hardware requires a separate connection.
`scripts/check` exercises Ghidra decompilation/MCP, QEMU/GDB/QMP, Binwalk extraction,
and Python imports using synthetic inputs; it does not test physical devices.

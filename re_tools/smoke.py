#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
"""Real synthetic RE checks. No hardware, model calls, or external target traffic.

Select a subset with --checks; a selected check fails if its dependencies are missing.
Run in a container with --network none to enforce offline operation.
"""
import argparse
import asyncio
import gzip
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile


def run(*args, **kwargs):
    return subprocess.run(args, check=True, capture_output=True, timeout=90, **kwargs)


def compile_probe(root):
    compiler = shutil.which("cc") or shutil.which("clang") or shutil.which("gcc")
    if not compiler:
        raise RuntimeError("C compiler missing")
    source, binary = root / "probe.c", root / "probe"
    source.write_text("int add_numbers(int a,int b){return a+b;} int main(void){return add_numbers(2,3);}")
    run(compiler, "-g", "-O0", "-o", str(binary), str(source))
    return binary


def binary_check(root):
    import capstone
    import lief
    import r2pipe
    import unicorn
    from unicorn.x86_const import UC_X86_REG_EAX

    code = b"\xb8\x2a\x00\x00\x00\x83\xc0\x01"  # mov eax,42; add eax,1
    instructions = list(capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32).disasm(code, 0x1000))
    assert [i.mnemonic for i in instructions] == ["mov", "add"]
    uc = unicorn.Uc(unicorn.UC_ARCH_X86, unicorn.UC_MODE_32)
    uc.mem_map(0x1000, 4096)
    uc.mem_write(0x1000, code)
    uc.emu_start(0x1000, 0x1000 + len(code), timeout=1_000_000, count=2)
    assert uc.reg_read(UC_X86_REG_EAX) == 43
    binary = compile_probe(root)
    parsed = lief.parse(str(binary))
    assert parsed is not None and any("add_numbers" in s.name for s in parsed.symbols)
    r2 = r2pipe.open(str(binary), flags=["-2"])
    try:
        symbols = r2.cmdj("isj")
        assert any("add_numbers" in s.get("name", "") for s in symbols), symbols
    finally:
        r2.quit()


def firmware_check(root):
    import ubireader.ubi  # noqa: F401 -- validates the active interpreter, not system Python
    import jefferson  # noqa: F401
    import esptool  # noqa: F401

    payload = bytes(range(256)) * 64
    archive = root / "sample.gz"
    archive.write_bytes(gzip.compress(payload, mtime=0))
    for attempt in range(5):
        output = root / f"binwalk-{attempt}"
        run("binwalk", "-e", "-C", str(output), str(archive))
        assert any(p.is_file() and p.read_bytes() == payload for p in output.rglob("*"))
    out = root / "unblob"
    run("unblob", "-e", str(out), str(archive))
    assert any(p.is_file() and p.read_bytes() == payload for p in out.rglob("*"))
    tree = root / "rootfs"
    tree.mkdir()
    (tree / "marker").write_bytes(payload)
    image = root / "rootfs.sqfs"
    run("mksquashfs", str(tree), str(image), "-noappend", "-processors", "1")
    for tool in ("unsquashfs", "sasquatch"):
        destination = root / tool
        run(tool, "-d", str(destination), str(image))
        assert (destination / "marker").read_bytes() == payload
    jffs = root / "rootfs.jffs2"
    run("mkfs.jffs2", "-r", str(tree), "-o", str(jffs), "--little-endian", "--pad=0x40000")
    destination = root / "jffs-out"
    run("jefferson", str(jffs), "-d", str(destination))
    assert any(p.name == "marker" and p.read_bytes() == payload for p in destination.rglob("*"))
    # UBI parsing and esptool are import checks only; no flash/read/write or attached hardware.


async def qemu_check(root):
    from qemu.qmp import QMPClient

    code = root / "aarch64.bin"
    code.write_bytes(struct.pack("<III", 0xd2800540, 0x91000400, 0x14000000))
    qs, gs = root / "qmp", root / "gdb"
    proc = subprocess.Popen([
        "qemu-system-aarch64", "-M", "virt", "-cpu", "cortex-a53", "-accel", "tcg",
        "-display", "none", "-serial", "none", "-monitor", "none", "-nic", "none", "-S",
        "-device", f"loader,file={code},addr=0x40200000,cpu-num=0,force-raw=on",
        "-qmp", f"unix:{qs},server=on,wait=off",
        "-chardev", f"socket,path={gs},server=on,wait=off,id=gdb0", "-gdb", "chardev:gdb0",
    ], stdout=subprocess.DEVNULL)
    qmp = QMPClient("re-smoke")
    connected = False
    try:
        for _ in range(100):
            assert proc.poll() is None, "QEMU exited during startup"
            if qs.exists() and gs.exists():
                break
            await asyncio.sleep(0.1)
        await qmp.connect(str(qs))
        connected = True
        commands = [f"target remote {gs}", "hbreak *0x40200004", "continue",
                    'python assert int(gdb.parse_and_eval("$x0")) == 42', "stepi",
                    'python assert int(gdb.parse_and_eval("$x0")) == 43', "detach"]
        args = ["gdb-multiarch", "-q", "-nx", "-batch"]
        for command in commands:
            args += ["-ex", command]
        result = await asyncio.to_thread(run, *args)
        assert b"Traceback" not in result.stderr, result.stderr
        for command, running in [("stop", False), ("cont", True), ("stop", False)]:
            await qmp.execute(command)
            assert (await qmp.execute("query-status"))["running"] == running
    finally:
        if connected:
            await qmp.disconnect()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
    # A real static cross-built ELF under user-mode QEMU, not a version check.
    source, binary = root / "user.c", root / "user"
    source.write_text("int main(void){return 42;}")
    run("aarch64-linux-gnu-gcc", "-static", "-o", str(binary), str(source))
    result = subprocess.run(["qemu-aarch64", str(binary)], timeout=15, check=False)
    assert result.returncode == 42, result.returncode


async def ghidra_check(root):
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    binary = compile_probe(root)
    launcher = Path(__file__).with_name("ghidra.py")
    server = StdioServerParameters(command=sys.executable,
        args=[str(launcher), "--project-path", str(root / "ghidra"),
              "--project-name", "smoke", "--wait-for-analysis", str(binary)],
        env={**os.environ, "RE_TOOLS_PROJECT": str(root / "ghidra")})
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listing = await session.call_tool("list_project_binaries", {})
            assert not listing.isError, listing
            programs = listing.structuredContent["programs"]
            assert len(programs) == 1, programs
            name = programs[0]["name"]
            result = await session.call_tool("decompile_function", {"binary_name": name, "name_or_address": "add_numbers"})
            assert not result.isError and "+" in result.model_dump_json(), result
            for _ in range(120):
                listing = await session.call_tool("list_project_binaries", {})
                if listing.structuredContent["programs"][0]["code_indexed"]:
                    break
                await asyncio.sleep(1)
            else:
                raise RuntimeError("Ghidra semantic index did not finish")
            result = await session.call_tool("search_code", {"binary_name": name, "query": "add two integers", "limit": 2})
            assert not result.isError and "add_numbers" in result.model_dump_json(), result


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checks", nargs="+", choices=["binary", "firmware", "qemu", "ghidra"],
                        default=["binary", "firmware", "qemu", "ghidra"])
    selected = parser.parse_args().checks
    with tempfile.TemporaryDirectory(prefix="re-smoke-") as tmp:
        root = Path(tmp)
        for check in selected:
            work = root / check
            work.mkdir()
            if check == "ghidra":
                await asyncio.wait_for(ghidra_check(work), timeout=300)
            elif check == "qemu":
                await asyncio.wait_for(qemu_check(work), timeout=120)
            elif check == "firmware":
                firmware_check(work)
            else:
                binary_check(work)
            print(json.dumps({"check": check, "status": "passed"}), flush=True)


if __name__ == "__main__":
    asyncio.run(main())

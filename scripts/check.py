"""Exercise installed tools with synthetic inputs; no firmware or hardware access."""
import asyncio
import gzip
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile

import cryptography
import pyboy
import serial
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from qemu.qmp import QMPClient


async def check(root):
    for tool in ('binwalk qemu-system-arm qemu-system-aarch64 qemu-img gdb-multiarch '
                 'clang llvm-objdump llvm-nm cmake meson ninja pkg-config dtc adb fastboot '
                 'file strings xxd readelf nm java').split():
        assert shutil.which(tool), f'Missing tool: {tool}'
    print('PASS: executables and Python imports', flush=True)
    payload = bytes(range(256)) * 64
    archive = root / 'sample.gz'
    archive.write_bytes(gzip.compress(payload))
    subprocess.run(['binwalk', '-e', '-C', str(root / 'extracted'), str(archive)],
                   check=True, capture_output=True, timeout=30)
    assert any(p.is_file() and p.read_bytes() == payload for p in (root / 'extracted').rglob('*'))
    print('PASS: Binwalk extraction', flush=True)

    code = root / 'probe.bin'
    code.write_bytes(struct.pack('<III', 0xd2800540, 0x91000400, 0x14000000))
    qs, gs = root / 'qmp', root / 'gdb'
    proc = subprocess.Popen([
        'qemu-system-aarch64', '-M', 'virt', '-cpu', 'cortex-a53', '-accel', 'tcg',
        '-display', 'none', '-serial', 'none', '-monitor', 'none', '-nic', 'none', '-S',
        '-device', f'loader,file={code},addr=0x40200000,cpu-num=0,force-raw=on',
        '-qmp', f'unix:{qs},server=on,wait=off',
        '-chardev', f'socket,path={gs},server=on,wait=off,id=gdb0', '-gdb', 'chardev:gdb0',
    ], stdout=subprocess.DEVNULL)
    qmp = QMPClient('toolbox-check')
    connected = False
    try:
        for _ in range(100):
            assert proc.poll() is None, 'QEMU exited during startup'
            if qs.exists() and gs.exists():
                break
            await asyncio.sleep(0.1)
        await qmp.connect(str(qs))
        connected = True
        commands = [f'target remote {gs}', 'hbreak *0x40200004', 'continue',
                    'python assert int(gdb.parse_and_eval("$x0")) == 42', 'stepi',
                    'python assert int(gdb.parse_and_eval("$x0")) == 43', 'detach']
        args = ['gdb-multiarch', '-q', '-nx', '-batch']
        for command in commands:
            args += ['-ex', command]
        result = await asyncio.to_thread(subprocess.run, args, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0 and 'Traceback' not in result.stderr, result.stdout + result.stderr
        for command, running in [('stop', False), ('cont', True), ('stop', False)]:
            await qmp.execute(command)
            assert (await qmp.execute('query-status'))['running'] == running
        print('PASS: QEMU execution, GDB breakpoint/step/registers, QMP pause/resume', flush=True)
    finally:
        if connected:
            await qmp.disconnect()
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    source, binary = root / 'probe.c', root / 'probe'
    source.write_text('int add_numbers(int a,int b){return a+b;} int main(void){return add_numbers(2,3);}')
    subprocess.run(['clang', '-g', '-O0', '-o', str(binary), str(source)], check=True, timeout=30)
    server = StdioServerParameters(command=str(Path(os.environ['TOOLBOX_ROOT']) / 'scripts/ghidra'),
        args=['--project-path', str(root / 'ghidra'), '--project-name', 'smoke',
              '--wait-for-analysis', str(binary)], env=dict(os.environ))
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool('decompile_function',
                {'binary_name': 'probe', 'name_or_address': 'add_numbers'})
            assert not result.isError and '+' in result.model_dump_json(), result
            print('PASS: Ghidra MCP import, analysis and decompilation', flush=True)


with tempfile.TemporaryDirectory(prefix='toolbox-check-') as tmp:
    asyncio.run(asyncio.wait_for(check(Path(tmp)), timeout=240))

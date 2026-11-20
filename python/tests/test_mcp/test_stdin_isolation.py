"""
ENG-76 regression tests: the MCP stdio transport's stdin pipe must never be
reachable by anything else in the server process (Windows deadlock: lazy
numpy import / git subprocess blocked behind the transport's pending read).
"""
import ast
import queue
import subprocess
import sys
import textwrap
import threading
import time
from pathlib import Path

import pytest

ADVISOR_DIR = Path(__file__).resolve().parents[2] / "advisor"
PYTHON_DIR = ADVISOR_DIR.parent

_SUBPROCESS_FUNCS = {"run", "Popen", "call", "check_call", "check_output"}


def test_every_subprocess_call_sets_stdin_explicitly():
    """Belt-and-braces with stdio_isolation: a child must never inherit the
    MCP stdin pipe, even if the server is launched some other way."""
    offenders = []
    for path in ADVISOR_DIR.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if (isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr in _SUBPROCESS_FUNCS
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "subprocess"
                    and not any(k.arg in ("stdin", "input") for k in node.keywords)):
                offenders.append(f"{path.relative_to(PYTHON_DIR)}:{node.lineno}")
    assert not offenders, (
        "subprocess call(s) without stdin= (add stdin=subprocess.DEVNULL, "
        f"ENG-76): {offenders}")


_CHILD = textwrap.dedent(r'''
    import sys, threading, subprocess
    sys.path.insert(0, sys.argv[1])
    from advisor.stdio_isolation import isolate_stdin_for_mcp
    applied = isolate_stdin_for_mcp()
    out = sys.stdout
    def reader():  # stands in for the MCP transport: always blocked reading
        line = sys.stdin.buffer.readline()
        out.write("got:" + line.decode().strip() + "\n"); out.flush()
    t = threading.Thread(target=reader); t.start()
    out.write(f"applied:{applied}\n"); out.flush()
    subprocess.run(["git", "--version"], capture_output=True, timeout=20)  # no stdin= on purpose
    out.write("git-ok\n"); out.flush()
    import numpy  # first import of a CRT-initialising DLL
    out.write("numpy-ok\n"); out.flush()
    t.join(30)
''')


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only deadlock")
def test_isolation_unblocks_dll_import_and_subprocess_but_keeps_transport():
    p = subprocess.Popen([sys.executable, "-c", _CHILD, str(PYTHON_DIR)],
                         stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True)
    q: "queue.Queue[str]" = queue.Queue()
    threading.Thread(target=lambda: [q.put(l.strip()) for l in p.stdout],
                     daemon=True).start()

    def next_line(timeout):
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None

    lines = []
    try:
        deadline = time.time() + 60
        while "numpy-ok" not in lines and time.time() < deadline:
            line = next_line(max(0.1, deadline - time.time()))
            if line is None:
                break
            lines.append(line)
        assert "applied:True" in lines, lines
        assert "numpy-ok" in lines, f"blocked behind pending stdin read: {lines}"
        # The transport must still receive what the client sends.
        p.stdin.write("ping\n"); p.stdin.flush()
        assert next_line(15) == "got:ping"
        assert p.wait(timeout=30) == 0
    finally:
        if p.poll() is None:
            p.kill()

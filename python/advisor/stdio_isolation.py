"""
stdio_isolation.py -- ENG-76: keep the MCP stdio transport's stdin pipe
private so nothing else in the server process can block on it (Windows).

Root cause (reproduced 2026-11-20). Claude Desktop talks to this server over
an anonymous pipe on stdin. The MCP SDK keeps a thread permanently blocked in
a synchronous ReadFile() on that pipe, waiting for the next client message.
On Windows, a synchronous pipe handle with a pending read blocks OTHER
operations that touch the same handle until the read completes, e.g.
GetFileType()/DuplicateHandle(). Two such operations happen implicitly:

  1. First import of a compiled extension whose DLL runs its own C-runtime
     init (numpy's _multiarray_umath via pandas via yfinance_fetcher).
     The CRT init inspects the standard handles and blocks.
  2. subprocess.run(...) without an explicit stdin= duplicates the process's
     STD_INPUT_HANDLE for the child (git). Blocks in CreateProcess setup,
     before subprocess's own timeout= even starts counting. Git for Windows'
     msys runtime then blocks the same way inside the child.

Either one freezes the tool call until the client happens to send another
message -- in practice its own cancellation after ~4 minutes. Hence the
"advisor_run_computation hangs, the request did reach the server" symptom
(first call of the day: lazy numpy import + CreditHistoryStore git commit),
advisor_evaluate_trend_signal hangs (TrendSignalStore git commit), and
advisor_write_back hangs (git add/commit/push).

Fix: before the transport starts, give it a private, non-inheritable
duplicate of the stdin pipe, and point fd 0 and the Win32 STD_INPUT_HANDLE
at NUL. The transport reads the real pipe; everything else that looks at
"stdin" (DLL CRT init, child processes, libraries) sees NUL and never blocks.
No-op on non-Windows. Never raises: on failure it logs to stderr and leaves
the original stdin in place (pre-fix behavior), so startup can't regress.
"""
from __future__ import annotations

import io
import os
import sys


def _set_win32_std_input(handle: int) -> None:
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.SetStdHandle.argtypes = [wintypes.DWORD, wintypes.HANDLE]
    kernel32.SetStdHandle.restype = wintypes.BOOL
    STD_INPUT_HANDLE = 0xFFFFFFF6  # (DWORD)-10
    if not kernel32.SetStdHandle(STD_INPUT_HANDLE, handle):
        raise ctypes.WinError(ctypes.get_last_error())


def isolate_stdin_for_mcp() -> bool:
    """
    Call once, before the MCP stdio transport starts reading. Returns True
    if isolation was applied, False if skipped (non-Windows) or it failed.
    """
    if sys.platform != "win32":
        return False
    try:
        import msvcrt

        # 1. Private copy of the client pipe for the transport. os.dup() is
        #    non-inheritable (PEP 446), so child processes never get it.
        private_fd = os.dup(0)
        msvcrt.setmode(private_fd, os.O_BINARY)
        transport_stdin = io.TextIOWrapper(
            io.BufferedReader(io.FileIO(private_fd, "rb", closefd=True)),
            encoding="utf-8",
        )
    except Exception as e:  # nothing changed yet -- keep original stdin
        print(f"[stdio_isolation] skipped, could not dup stdin: {e!r}",
              file=sys.stderr, flush=True)
        return False

    try:
        # 2. fd 0 and the Win32 standard input handle -> NUL.
        nul_fd = os.open(os.devnull, os.O_RDONLY)
        try:
            os.dup2(nul_fd, 0)
        finally:
            os.close(nul_fd)
    except Exception as e:  # fd 0 still the real pipe -- keep original stdin
        transport_stdin.close()
        print(f"[stdio_isolation] skipped, could not redirect fd 0: {e!r}",
              file=sys.stderr, flush=True)
        return False

    # From here fd 0 is NUL, so the transport MUST get the private pipe.
    sys.stdin = transport_stdin
    try:
        _set_win32_std_input(msvcrt.get_osfhandle(0))
    except Exception as e:
        # fd 0 is already NUL (the CRT usually updates the Win32 handle on
        # dup2 for console apps anyway); report but keep going.
        print(f"[stdio_isolation] SetStdHandle failed (continuing): {e!r}",
              file=sys.stderr, flush=True)
    return True

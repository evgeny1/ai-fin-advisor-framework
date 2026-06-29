"""
run_mcp_server.py — Claude Desktop stdio entry point for the financial-advisor MCP server.

Exists only to avoid shell-wrapper quoting issues (cmd.exe /c "cd /d ... && ...")
when the Allocation/dev path contains spaces. Being a sibling file to advisor/
inside python/ means Python auto-adds this directory to sys.path[0] on launch,
so `import advisor` resolves with no PYTHONPATH/cwd tricks needed.

Claude Desktop config should invoke this directly:
  "command": "C:\\Python\\python.exe",
  "args": ["G:\\My Drive\\dev\\AI Financial Advisor Framework\\python\\run_mcp_server.py"]
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from advisor.__main__ import main  # noqa: E402

sys.argv = [sys.argv[0], "mcp-server"]
main()

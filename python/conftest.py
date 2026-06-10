"""
conftest.py — pytest path fix for VS Code compatibility.

VS Code's pytest runner uses the workspace root as its working directory
(AI Financial Advisor Framework/), not the python/ subdirectory.
Without this file, sys.path doesn't include python/, causing two problems:

1. 'import advisor' may resolve via a different path than expected, producing
   two distinct module objects for the same source file. unittest.mock.patch
   then patches one object while yfinance_dispatcher's __globals__ references
   the other — the patch doesn't intercept the call.

2. PYTHONPATH-sensitive tests (e.g. file_protocol path resolution) may fail
   if the working directory assumption is wrong.

This conftest.py ensures python/ is always the first entry in sys.path,
making 'import advisor' resolve identically regardless of where pytest
is invoked from.
"""
import sys
from pathlib import Path
from dotenv import load_dotenv

_PYTHON_ROOT = Path(__file__).parent
if str(_PYTHON_ROOT) not in sys.path:
    sys.path.insert(0, str(_PYTHON_ROOT))

# Load .env so os.environ.get() sees FMP_API_KEY etc. in both terminal and VS Code.
# override=False means already-set shell variables take precedence over .env.
load_dotenv(_PYTHON_ROOT / ".env", override=False)

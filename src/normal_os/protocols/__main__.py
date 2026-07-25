"""
Package entry point:

    python -m normal_os.protocols

Lives in its own module so that ``inception.py`` never has to import the
runner. The protocol found that cycle in its own source on the first run --
``inception`` importing ``runner`` importing ``inception`` -- and reported
both modules as caught in a support cycle. It was right, so the cycle is
gone rather than excused.
"""

from __future__ import annotations

import sys

from .runner import main

if __name__ == "__main__":
    sys.exit(main())

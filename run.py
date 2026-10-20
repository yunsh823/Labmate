"""Entry point for the packaged app (PyInstaller needs a script, not `python -m`)."""

import sys

from todolist.__main__ import main

sys.exit(main())

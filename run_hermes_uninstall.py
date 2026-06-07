import os
import sys

ROOT = os.path.abspath(os.path.dirname(__file__))
SRC = os.path.join(ROOT, "src")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

from hermes_9router_tracker.hermes_uninstall import main


if __name__ == "__main__":
    raise SystemExit(main())

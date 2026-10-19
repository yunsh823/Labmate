import sys

from .db import Store
from .desktop import Desktop


def main() -> int:
    store = Store()
    store.purge_old_trash()
    Desktop(store).run(debug="--debug" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())

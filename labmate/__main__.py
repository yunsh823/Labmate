import sys

from . import single
from .db import Store
from .desktop import Desktop


def main() -> int:
    app: list[Desktop] = []  # filled once the windows exist
    if not single.acquire(lambda: app and app[0].show_main()):
        return 0  # already running; that instance brings its window forward
    store = Store()
    store.purge_old_trash()
    app.append(Desktop(store))
    app[0].run(debug="--debug" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())

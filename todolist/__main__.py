import sys
from pathlib import Path

import webview

from .api import Api
from .db import Store

WEB_DIR = Path(__file__).parent / "web"


def main() -> int:
    store = Store()
    store.purge_old_trash()
    webview.create_window(
        "ToDoList",
        url=str(WEB_DIR / "index.html"),
        js_api=Api(store),
        width=1080,
        height=720,
        min_size=(760, 480),
    )
    webview.start(debug="--debug" in sys.argv)
    return 0


if __name__ == "__main__":
    sys.exit(main())

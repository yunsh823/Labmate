"""Single-instance guard.

The first instance listens on a fixed localhost port. A second launch connects,
asks the first one to show its window, and exits instead of starting a duplicate
tray icon and sync loop.
"""

import socket
import sys
import threading
from typing import Callable

PORT = 47391
REQUEST, REPLY = b"todolist:show\n", b"todolist:ok\n"


def acquire(on_show: Callable[[], None], port: int = PORT) -> bool:
    """True if this process should run; False if an existing instance took over."""
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if sys.platform == "win32":
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
    try:
        srv.bind(("127.0.0.1", port))
        srv.listen()
    except OSError:
        srv.close()
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=2) as conn:
                conn.sendall(REQUEST)
                if conn.recv(64) == REPLY:
                    return False
        except OSError:
            pass
        return True  # the port belongs to some other program; run unguarded
    threading.Thread(target=_serve, args=(srv, on_show), daemon=True).start()
    return True


def _serve(srv: socket.socket, on_show: Callable[[], None]) -> None:
    while True:
        conn, _ = srv.accept()
        with conn:
            conn.settimeout(2)
            try:
                if conn.recv(64) == REQUEST:
                    conn.sendall(REPLY)
                    on_show()
            except OSError:
                pass

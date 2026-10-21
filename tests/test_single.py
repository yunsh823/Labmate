import socket
import threading

from labmate import single


def free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_second_instance_hands_over_to_first():
    port = free_port()
    shown = threading.Event()
    assert single.acquire(shown.set, port=port) is True
    assert single.acquire(lambda: None, port=port) is False
    assert shown.wait(2)


def test_port_used_by_another_program_does_not_block_launch():
    port = free_port()
    other = socket.socket()
    other.bind(("127.0.0.1", port))
    other.listen()
    threading.Thread(target=lambda: other.accept()[0].close(), daemon=True).start()
    try:
        assert single.acquire(lambda: None, port=port) is True
    finally:
        other.close()

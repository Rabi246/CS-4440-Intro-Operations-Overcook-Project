"""
network.py
==========

Tiny line-based protocol on top of TCP sockets.

Each "message" is a UTF-8 string terminated by a single newline ('\n').
We use one helper to send and a small wrapper class to receive, because
socket.recv() returns arbitrary byte chunks -- it does NOT respect message
boundaries. The LineReader buffers bytes until it sees a newline, then
hands back one complete line.
"""

import socket
import threading


DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8910
ENCODING     = "utf-8"


def send_line(sock, text, lock=None):
    """Send `text` followed by a newline. `lock` serialises concurrent writes."""
    payload = (text + "\n").encode(ENCODING)
    if lock is not None:
        with lock:
            sock.sendall(payload)
    else:
        sock.sendall(payload)


class LineReader:
    """Buffer bytes off a socket and yield one complete line at a time."""

    def __init__(self, sock, chunk_size=1024):
        self.sock = sock
        self.chunk_size = chunk_size
        self._buffer = bytearray()

    def readline(self):
        while b"\n" not in self._buffer:
            try:
                chunk = self.sock.recv(self.chunk_size)
            except OSError:
                return None
            if not chunk:
                if self._buffer:
                    line = bytes(self._buffer)
                    self._buffer.clear()
                    return line.decode(ENCODING, errors="replace")
                return None
            self._buffer.extend(chunk)

        newline_index = self._buffer.index(b"\n")
        line = bytes(self._buffer[:newline_index])
        del self._buffer[:newline_index + 1]
        if line.endswith(b"\r"):
            line = line[:-1]
        return line.decode(ENCODING, errors="replace")


def make_server_socket(host=DEFAULT_HOST, port=DEFAULT_PORT, backlog=8):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(backlog)
    return s

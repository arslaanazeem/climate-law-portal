"""
Find the first usable TCP port for the dev server.

Why this exists:
  Windows (especially with Hyper-V or WSL2 installed) sometimes reserves
  port ranges that include 8000. Trying to bind there fails with
  "You don't have permission to access that port."

  This script probes a list of common dev ports and prints the first one
  the OS lets us bind to. The .bat file uses the printed value.
"""
import socket
import sys

CANDIDATES = [8000, 8765, 8080, 8888, 8001, 8765, 5050]


def is_bindable(port: int) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", port))
    except OSError:
        return False
    finally:
        sock.close()
    return True


def main() -> int:
    for port in CANDIDATES:
        if is_bindable(port):
            print(port)
            return 0
    # If everything is occupied (very unlikely), fall back to 0 = OS picks
    # any free ephemeral port. Django will pick that up too.
    print(0)
    return 0


if __name__ == "__main__":
    sys.exit(main())

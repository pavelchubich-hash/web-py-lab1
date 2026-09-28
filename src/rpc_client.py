import json
import socket

HOST = "127.0.0.1"
PORT = 8024
RESP_HEADER_SIZE = 5


def recv_exact(sock: socket.socket, length: int) -> bytes:
    """Receive exact number of bytes from socket."""
    buf = b""
    while len(buf) < length:
        chunk = sock.recv(length - len(buf))
        if not chunk:
            break
        buf += chunk
    return buf


class RPCClient:
    """Client for RPC Server using Variant 24 TCP binary protocol."""

    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        """Initialize connection parameters."""
        self.host = host
        self.port = port
        self.sock = None

    def connect(self) -> None:
        """Connect to RPC Server."""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.host, self.port))

    def close(self) -> None:
        """Close socket connection."""
        if self.sock:
            self.sock.close()

    def _call(self, opcode: int, args: list) -> object:
        """Send RPC request and receive response."""
        body_bytes = json.dumps(args).encode("utf-8")
        body_size = len(body_bytes)

        header = opcode.to_bytes(1, byteorder="big") + body_size.to_bytes(
            5, byteorder="big"
        )
        self.sock.sendall(header + body_bytes)

        resp_header = recv_exact(self.sock, RESP_HEADER_SIZE)
        version = resp_header[0]
        resp_opcode = resp_header[1]
        resp_body_size = int.from_bytes(resp_header[2:5], byteorder="big")

        resp_body_bytes = recv_exact(self.sock, resp_body_size)
        return json.loads(resp_body_bytes.decode("utf-8"))

    def create_person(self, ip: str, platform: str, user_agent: str) -> int:
        """Call remote create_person."""
        return self._call(1, [ip, platform, user_agent])

    def delete_person(self, identifier: int) -> bool:
        """Call remote delete_person."""
        return self._call(2, [identifier])

    def get_persons(self) -> list:
        """Call remote get_persons."""
        return self._call(3, [])

    def create_command(
        self, data: str, person: int, tags: str, status: str, triggered: int
    ) -> int:
        """Call remote create_command."""
        return self._call(4, [data, person, tags, status, triggered])

    def delete_command(self, identifier: int) -> bool:
        """Call remote delete_command."""
        return self._call(5, [identifier])

    def get_commands(self) -> list:
        """Call remote get_commands."""
        return self._call(6, [])

    def create_result(
        self, result: str, status: str, exception: str, command: int
    ) -> int:
        """Call remote create_result."""
        return self._call(7, [result, status, exception, command])

    def delete_result(self, identifier: int) -> bool:
        """Call remote delete_result."""
        return self._call(8, [identifier])

    def get_results(self) -> list:
        """Call remote get_results."""
        return self._call(9, [])

    def select_data(self) -> list:
        """Call remote select_data."""
        return self._call(10, [])


if __name__ == "__main__":
    client = RPCClient()
    client.connect()

    pid = client.create_person("10.0.0.1", "MacOS", "Safari")
    print(f"Remote created person id: {pid}")

    cid = client.create_command("init", pid, "main", "ok", 1)
    print(f"Remote created command id: {cid}")

    rid = client.create_result("done", "finished", "none", cid)
    print(f"Remote created result id: {rid}")

    print("Remote persons:", client.get_persons())
    print("Remote commands:", client.get_commands())
    print("Remote results:", client.get_results())
    print("Remote select:", client.select_data())

    client.close()
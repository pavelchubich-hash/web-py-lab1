import json
import socket
import data_layer

HOST = "127.0.0.1"
PORT = 8024
PROTOCOL_VERSION = 1
REQ_HEADER_SIZE = 6
RESP_HEADER_SIZE = 5

OPCODES = {
    1: data_layer.create_person,
    2: data_layer.delete_person,
    3: data_layer.get_persons,
    4: data_layer.create_command,
    5: data_layer.delete_command,
    6: data_layer.get_commands,
    7: data_layer.create_result,
    8: data_layer.delete_result,
    9: data_layer.get_results,
    10: data_layer.select_data,
}


def parse_request_header(header_bytes: bytes) -> tuple:
    """Parse 6-byte request header into opcode and body size."""
    opcode = header_bytes[0]
    body_size = int.from_bytes(header_bytes[1:6], byteorder="big")
    return opcode, body_size


def make_response(opcode: int, result: object) -> bytes:
    """Pack protocol version, opcode, body size and JSON body."""
    body_str = json.dumps(result)
    body_bytes = body_str.encode("utf-8")
    body_size = len(body_bytes)

    header = (
        PROTOCOL_VERSION.to_bytes(1, byteorder="big")
        + opcode.to_bytes(1, byteorder="big")
        + body_size.to_bytes(3, byteorder="big")
    )
    return header + body_bytes


def recv_exact(conn: socket.socket, length: int) -> bytes:
    """Receive exact number of bytes from socket."""
    buf = b""
    while len(buf) < length:
        chunk = conn.recv(length - len(buf))
        if not chunk:
            break
        buf += chunk
    return buf


def process_connection(conn: socket.socket) -> None:
    """Process incoming client requests on open connection."""
    while True:
        header = recv_exact(conn, REQ_HEADER_SIZE)
        if not header or len(header) < REQ_HEADER_SIZE:
            break

        opcode, body_size = parse_request_header(header)
        body_bytes = recv_exact(conn, body_size)
        args = json.loads(body_bytes.decode("utf-8")) if body_bytes else []

        print(f"LOG REQUEST: opcode={opcode}, args={args}")

        func = OPCODES.get(opcode)
        if func:
            res = func(*args) if isinstance(args, list) else func()
        else:
            res = {"error": "Unknown opcode"}

        print(f"LOG RESPONSE: opcode={opcode}, result={res}")

        response_bytes = make_response(opcode, res)
        conn.sendall(response_bytes)


def run_server() -> None:
    """Start RPC TCP Server."""
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(1)
    print(f"RPC Server listening on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = server_sock.accept()
            with conn:
                process_connection(conn)
    except KeyboardInterrupt:
        print("Server stopped.")
    finally:
        server_sock.close()


if __name__ == "__main__":
    run_server()

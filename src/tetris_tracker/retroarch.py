from __future__ import annotations

import socket
from typing import Optional, List


class RetroArchClient:
    def __init__(self, host: str, port: int, timeout: float = 1.0):
        self.host = host
        self.port = port
        self.timeout = timeout

    def command(self, command: str, expect_response: bool = True) -> Optional[str]:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(self.timeout)
            sock.sendto(command.encode("ascii"), (self.host, self.port))

            if not expect_response:
                return None

            try:
                data, _ = sock.recvfrom(4096)
            except socket.timeout as exc:
                raise ConnectionError(
                    f"No response from RetroArch at {self.host}:{self.port}"
                ) from exc

        return data.decode("ascii").strip()

    def read_memory(self, address: int, length: int = 1) -> List[int]:
        response = self.command(
            f"READ_CORE_MEMORY {address:04X} {length}"
        )

        if response is None:
            raise RuntimeError("Empty RetroArch response")

        parts = response.split()

        if len(parts) < 3:
            raise RuntimeError(f"Unexpected RetroArch response: {response}")

        if parts[2] == "-1":
            raise RuntimeError(f"RetroArch memory read failed: {response}")

        return [int(value, 16) for value in parts[2:]]

    def show_message(self, message: str) -> None:
        # SHOW_MSG is fire-and-forget; RetroArch does not need to reply.
        safe = " ".join(str(message).replace("\n", " ").split())
        self.command(f"SHOW_MSG {safe}", expect_response=False)

    def get_status(self) -> str:
        return self.command("GET_STATUS")
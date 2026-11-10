#!/usr/bin/env python3
"""
Low-level TCP communication module for ESP3D + Marlin.
Handles connection, buffering, echo filtering, and FIFO streaming.
"""
import os
import socket
import time
import re

# --- MINIMAL ADDITION: Load local .env file from the skill root directory ---
SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(SKILL_ROOT, ".env")
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                if key.strip() not in os.environ:
                    os.environ[key.strip()] = val.strip()
# ---------------------------------------------------------------------------

class PrinterComm:
    """Low-level communication for Marlin firmware over TCP."""

    def __init__(self, host=None, port=None, timeout=10):
        # Priority: explicit argument > environment variable > default localhost
        self.host = host or os.environ.get("PRINTER_HOST", "127.0.0.1")
        self.port = port or int(os.environ.get("PRINTER_PORT", "8888"))
        self.timeout = timeout
        self.sock = None
        self.buffer = ""

        # --- MINIMAL ADDITION: Load safety bounds from environment ---
        self.max_x = float(os.environ.get("PRINTER_MAX_X", 999.0))
        self.max_y = float(os.environ.get("PRINTER_MAX_Y", 999.0))
        self.max_z = float(os.environ.get("PRINTER_MAX_Z", 999.0))
        # -------------------------------------------------------------

    def connect(self):
        """Establish TCP connection to ESP3D."""
        try:
            self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
            self.sock.settimeout(self.timeout)
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            # Provide a clear instruction for the Agent to ask the user and save to memory
            raise ConnectionError(
                f"Failed to connect to printer at {self.host}:{self.port}. "
                f"Please verify the IP and port. If they are incorrect, ask the user for the right ones, "
                f"and save them to your memory for future use. Error: {e}"
            )

    def disconnect(self):
        """Close TCP connection."""
        if self.sock:
            try:
                self.sock.close()
            except OSError:
                pass
            self.sock = None

    def _read_line(self):
        """Read a single line from socket, handling arbitrary chunks."""
        while "\n" not in self.buffer:
            try:
                chunk = self.sock.recv(4096)
            except socket.timeout:
                raise TimeoutError("Printer response timed out.")
            if not chunk:
                raise ConnectionError("Connection closed by remote host.")
            self.buffer += chunk.decode("utf-8", errors="replace")
        
        line, self.buffer = self.buffer.split("\n", 1)
        return line.strip()

    def send_command(self, cmd, wait_ok=True):
        """
        Send a single G-code command.
        Returns a tuple: (status_code, response_lines)
        0 = OK, 1 = Error, 2 = Resend requested
        """
        if not self.sock:
            self.connect()
        
        try:
            self.sock.sendall((cmd + "\n").encode("ascii"))
        except OSError as e:
            raise ConnectionError(f"Failed to send command: {e}")

        if not wait_ok:
            return 0, ["sent"]

        lines = []
        while True:
            line = self._read_line()
            if not line or line.lower().startswith("echo:"):
                continue
            
            lines.append(line)
            
            lower_line = line.lower()
            if lower_line == "ok" or lower_line.startswith("ok "):
                return 0, lines
            if lower_line.startswith("error"):
                return 1, lines
            if lower_line.startswith("busy:"):
                time.sleep(0.1)
                continue
            if lower_line.startswith("resend:"):
                return 2, lines

    def stream_file(self, file_path, window_size=5):
        """
        Send a G-code file using a sliding window FIFO buffer.
        Yields the current line number to report progress.
        """
        if not self.sock:
            self.connect()

        with open(file_path, "r", encoding="utf-8") as f:
            lines = []
            for raw_line in f:
                line = raw_line.split(";")[0].strip()
                if line:
                    lines.append(line)

        total = len(lines)
        if total == 0:
            raise ValueError("File is empty or contains no valid G-code.")
            
        sent_idx = 0
        acked_idx = 0

        while acked_idx < total:
            while sent_idx < total and (sent_idx - acked_idx) < window_size:
                cmd = lines[sent_idx]
                try:
                    self.sock.sendall((cmd + "\n").encode("ascii"))
                except OSError:
                    raise ConnectionError("Connection lost during streaming.")
                sent_idx += 1

            line = self._read_line()
            if not line or line.lower().startswith("echo:"):
                continue

            lower_line = line.lower()
            if lower_line == "ok" or lower_line.startswith("ok "):
                acked_idx += 1
                yield int((acked_idx / total) * 100)
            elif lower_line.startswith("busy:"):
                continue
            elif lower_line.startswith("resend:"):
                match = re.search(r"resend:\s*(\d+)", lower_line)
                if match:
                    req_line = int(match.group(1)) - 1
                    sent_idx = max(acked_idx, req_line)
            elif lower_line.startswith("error"):
                raise RuntimeError(f"Printer error during print: {line}")

    def parse_m105(self, lines):
        """Extract temperature from M105 response lines."""
        res = {"hotend": {"current": 0.0, "target": 0.0}, "bed": {"current": 0.0, "target": 0.0}}
        for line in lines:
            if "T:" in line and "B:" in line:
                match = re.search(r"T:([\d.]+)\s*/([\d.]+)\s+B:([\d.]+)\s*/([\d.]+)", line)
                if match:
                    res["hotend"]["current"] = float(match.group(1))
                    res["hotend"]["target"] = float(match.group(2))
                    res["bed"]["current"] = float(match.group(3))
                    res["bed"]["target"] = float(match.group(4))
        return res

    def parse_m114(self, lines):
        """Extract position from M114 response lines."""
        res = {"x": 0.0, "y": 0.0, "z": 0.0, "e": 0.0}
        for line in lines:
            match = re.search(r"X:([\d.-]+)\s+Y:([\d.-]+)\s+Z:([\d.-]+)\s+E:([\d.-]+)", line)
            if match:
                res["x"] = float(match.group(1))
                res["y"] = float(match.group(2))
                res["z"] = float(match.group(3))
                res["e"] = float(match.group(4))
        return res

    def parse_m119(self, lines):
        """Extract endstop status from M119 response lines."""
        res = {}
        for line in lines:
            # Use regex to reliably extract key: value pairs
            # regardless of spaces or separators like '|'
            matches = re.findall(r'([a-zA-Z0-9_]+):\s*([a-zA-Z0-9_]+)', line)
            for k, v in matches:
                res[k.lower()] = v
        return res
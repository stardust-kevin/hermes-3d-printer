#!/usr/bin/env python3
"""
Mock 3D printer TCP server for testing the hermes-3d-printer skill.

Usage:
  python3 mock_printer.py                          # port 8888, normal mode
  python3 mock_printer.py --port 9999              # custom port
  python3 mock_printer.py --scenario slow          # 3-second delay per response
  python3 mock_printer.py --scenario timeout       # accept, never respond
  python3 mock_printer.py --scenario garbled       # return garbage
  python3 mock_printer.py --scenario error         # return Error: responses
  python3 mock_printer.py --scenario disconnect    # close after first response
  python3 mock_printer.py --scenario busy          # 3x "busy" before normal
  python3 mock_printer.py --lang zh                # Chinese output

Scenarios:
  normal      - normal Marlin-style responses
  slow        - 3-second delay per response
  timeout     - accept connection, never respond
  garbled     - return random garbage
  error       - return Error: responses
  disconnect  - close after first response
  busy        - first 3 commands return "busy: processing"

Environment:
  MOCK_PORT   - listening port (default 8888)
  MOCK_LANG   - 'en' or 'zh' (default 'en')
"""
import argparse
import os
import random
import socket
import sys
import threading
import time

# ============ Bilingual output helper ============
LANG = "en"


def t(en: str, zh: str) -> str:
    """Return bilingual string based on LANG."""
    return zh if LANG.startswith("zh") else en


# ============ Printer state ============
class PrinterState:
    """In-memory printer state. Reset on each server restart."""

    def __init__(self):
        self.hotend_temp = 24.5
        self.hotend_target = 0.0
        self.bed_temp = 23.1
        self.bed_target = 0.0
        self.x = 0.0
        self.y = 0.0
        self.z = 0.0
        self.e = 0.0
        self.fan = 0
        self.motors_enabled = True
        self.endstops = {
            "X_MIN": "open",
            "Y_MIN": "open",
            "Z_MIN": "TRIGGERED",
        }
        self.sd_file = None
        self.sd_printing = False
        self.sd_progress = 0
        self.sd_total = 100000
        self.halted = False
        self._busy_count = 0


# ============ G-code handler ============
def handle_command(cmd: str, state: PrinterState) -> str:
    """Process one G-code command, return the response (no trailing newline)."""
    cmd = cmd.strip()
    if not cmd:
        return ""

    # Halted state: only M999 or power-cycle recovers
    if state.halted and not cmd.upper().startswith("M999"):
        return "Error:Printer halted. Reset via M999 or power cycle."

    parts = cmd.split()
    code = parts[0].upper()
    params = {}
    for p in parts[1:]:
        if p and p[0].isalpha():
            try:
                params[p[0].upper()] = float(p[1:])
            except ValueError:
                pass

    # ----- Temperature -----
    if code == "M105":
        return (
            f"ok T:{state.hotend_temp:.1f} /{state.hotend_target:.1f} "
            f"B:{state.bed_temp:.1f} /{state.bed_target:.1f} @:0 B@:0"
        )

    if code == "M104":
        state.hotend_target = params.get("S", 0.0)
        return "ok"

    if code == "M109":
        state.hotend_target = params.get("S", 0.0)
        state.hotend_temp = state.hotend_target  # instant reach (mock)
        return "ok"

    if code == "M140":
        state.bed_target = params.get("S", 0.0)
        return "ok"

    if code == "M190":
        state.bed_target = params.get("S", 0.0)
        state.bed_temp = state.bed_target  # instant reach (mock)
        return "ok"

    if code == "M155":
        return "ok"

    # ----- Motion -----
    if code in ("G0", "G1"):
        if "X" in params:
            state.x = params["X"]
        if "Y" in params:
            state.y = params["Y"]
        if "Z" in params:
            state.z = params["Z"]
        if "E" in params:
            state.e += params["E"]
        return "ok"

    if code == "G28":
        if not params or "X" in params:
            state.x = 0.0
        if not params or "Y" in params:
            state.y = 0.0
        if not params or "Z" in params:
            state.z = 0.0
        return "ok"

    if code == "G29":
        return "ok"

    if code == "G92":
        for axis in ("X", "Y", "Z", "E"):
            if axis in params:
                setattr(state, axis.lower(), params[axis])
        return "ok"

    if code == "M114":
        return (
            f"ok X:{state.x:.2f} Y:{state.y:.2f} "
            f"Z:{state.z:.2f} E:{state.e:.2f}"
        )

    if code in ("M84", "M18"):
        state.motors_enabled = False
        return "ok"

    # ----- Endstops -----
    if code == "M119":
        stops = " ".join(f"{k}:{v}" for k, v in state.endstops.items())
        return f"ok {stops}"

    # ----- Fan -----
    if code == "M106":
        state.fan = int(params.get("S", 0))
        return "ok"

    if code == "M107":
        state.fan = 0
        return "ok"

    # ----- Firmware info -----
    if code == "M115":
        return (
            "ok FIRMWARE_NAME:Marlin 2.0.9.1 "
            "SOURCE_CODE_URL:https://github.com/MarlinFirmware/Marlin "
            "PROTOCOL_VERSION:1.0 MACHINE_TYPE:Anet A8 EXTRUDER_COUNT:1 "
            "UUID:mock-0000-0000-0000-000000000000"
        )

    if code == "M503":
        return (
            "ok\n"
            "echo:  G21    ; Units in mm\n"
            "echo:  M149 C ; Units in Celsius\n"
            "echo:Steps per unit:\n"
            "echo:  M92 X100.00 Y100.00 Z400.00 E95.00"
        )

    if code in ("M500", "M501", "M502"):
        return "ok"

    # ----- SD card -----
    if code == "M20":
        return "ok\nBegin file list\nmock_print.gcode\nEnd file list"

    if code in ("M21", "M22"):
        return "ok"

    if code == "M23":
        state.sd_file = cmd[3:].strip() or "mock_print.gcode"
        state.sd_progress = 0
        return "ok"

    if code == "M24":
        if state.sd_file:
            state.sd_printing = True
            return "ok"
        return "Error:No file selected"

    if code == "M25":
        state.sd_printing = False
        return "ok"

    if code == "M27":
        if state.sd_printing:
            state.sd_progress = min(state.sd_progress + 1000, state.sd_total)
            return f"SD printing byte {state.sd_progress}/{state.sd_total}"
        return "Not SD printing"

    # ----- Emergency -----
    if code == "M112":
        state.halted = True
        state.hotend_target = 0.0
        state.bed_target = 0.0
        return "ok"

    if code == "M999":
        state.halted = False
        return "ok"

    if code == "M410":
        return "ok"

    if code in ("M0", "M1"):
        return "ok"

    return f'echo:Unknown command: "{cmd}"'


# ============ Scenario wrapper ============
def apply_scenario(response: str, scenario: str, state: PrinterState) -> str:
    """Adjust response based on the active scenario."""
    if scenario == "normal":
        return response

    if scenario == "error":
        return "Error:Test error scenario active"

    if scenario == "garbled":
        return "".join(random.choice("!@#$%^&*()_+{}|:<>?") for _ in range(30))

    if scenario == "busy":
        state._busy_count += 1
        if state._busy_count <= 3:
            return "busy: processing"
        return response

    return response


# ============ Client handler ============
def handle_client(conn: socket.socket, addr, args, state: PrinterState,
                  lock: threading.Lock):
    """Handle a single client connection in its own thread."""
    tag = f"[{addr[0]}:{addr[1]}]"
    log(f"{tag} " + t("Connected", "已连接"))

    # Timeout scenario: hold the connection open, never respond
    if args.scenario == "timeout":
        log(f"{tag} " + t("Timeout scenario — hanging", "超时场景 — 保持挂起"))
        try:
            while True:
                time.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            pass
        finally:
            conn.close()
        return

    # Disconnect scenario: close almost immediately
    if args.scenario == "disconnect":
        log(f"{tag} " + t("Disconnect scenario — closing in 0.5s",
                          "断连场景 — 0.5 秒后关闭"))
        time.sleep(0.5)
        conn.close()
        return

    buf = b""
    first_response_sent = False

    try:
        while True:
            try:
                data = conn.recv(1024)
            except (ConnectionResetError, OSError):
                break
            if not data:
                break
            buf += data
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                cmd = line.decode("ascii", errors="replace").strip()
                if not cmd:
                    continue
                log(f"{tag} <- {cmd}")

                # Apply scenario-specific delay
                if args.scenario == "slow":
                    time.sleep(3)
                elif args.delay > 0:
                    time.sleep(args.delay)

                # Process command under lock to keep state consistent
                with lock:
                    response = handle_command(cmd, state)
                    response = apply_scenario(response, args.scenario, state)

                try:
                    conn.sendall(
                        (response + "\n").encode("ascii", errors="replace")
                    )
                except OSError:
                    break
                log(f"{tag} -> {response!r}")

                # Disconnect scenario: close after first response
                if args.scenario == "disconnect" and not first_response_sent:
                    first_response_sent = True
                    log(f"{tag} " + t(
                        "Disconnect scenario — closing after first response",
                        "断连场景 — 首次响应后关闭"))
                    time.sleep(0.5)
                    conn.close()
                    return
    finally:
        try:
            conn.close()
        except OSError:
            pass
        log(f"{tag} " + t("Disconnected", "已断开"))


# ============ Logging ============
QUIET = False


def log(msg: str):
    """Print a log line unless --quiet is set."""
    if not QUIET:
        print(msg, flush=True)


# ============ Main ============
def main():
    global LANG, QUIET
    parser = argparse.ArgumentParser(
        description="Mock 3D printer TCP server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--host", default="0.0.0.0",
                        help="Listening host (default: 0.0.0.0)")
    parser.add_argument(
        "--port", type=int,
        default=int(os.environ.get("MOCK_PORT", "8888")),
        help="Listening port (default: 8888)",
    )
    parser.add_argument(
        "--scenario", default="normal",
        choices=["normal", "slow", "timeout", "garbled",
                 "error", "disconnect", "busy"],
        help="Behavior scenario (default: normal)",
    )
    parser.add_argument("--delay", type=float, default=0.0,
                        help="Delay in seconds before each response (default: 0)")
    parser.add_argument(
        "--lang", default=os.environ.get("MOCK_LANG", "en"),
        choices=["en", "zh"],
        help="Output language (default: en)",
    )
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-command logs")

    args = parser.parse_args()
    LANG = args.lang
    QUIET = args.quiet

    state = PrinterState()
    lock = threading.Lock()

    # Set up TCP listening socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((args.host, args.port))
    s.listen(5)

    print("=" * 60)
    print(t("Mock 3D Printer TCP Server", "模拟 3D 打印机 TCP 服务器"))
    print("=" * 60)
    print(t(f"Listening on {args.host}:{args.port}",
            f"监听 {args.host}:{args.port}"))
    print(t(f"Scenario: {args.scenario}", f"场景: {args.scenario}"))
    print(t(f"Language: {args.lang}", f"语言: {args.lang}"))
    print(t("Press Ctrl+C to stop", "按 Ctrl+C 停止"))
    print("=" * 60, flush=True)

    try:
        # Accept loop: one thread per client
        while True:
            conn, addr = s.accept()
            threading.Thread(
                target=handle_client,
                args=(conn, addr, args, state, lock),
                daemon=True,
            ).start()
    except KeyboardInterrupt:
        print(t("\nShutting down.", "\n正在关闭。"), flush=True)
    finally:
        s.close()


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Generic 3D printer control helper. Only depends on Python 3 stdlib.

Usage:
  python3 printer_control.py query              # Temperature + position
  python3 printer_control.py gcode "CMD" ...    # Send one or more G-code commands
  python3 printer_control.py progress           # Print progress (M27)
  python3 printer_control.py info               # Firmware info (M115)
  python3 printer_control.py ping               # Test connectivity
  python3 printer_control.py selftest           # Run self-test (syntax + connectivity)

Environment:
  PRINTER_HOST  (required)  Controller IP or hostname
  PRINTER_PORT  (optional)  default 8888
  PRINTER_TIMEOUT (optional) default 10 (seconds)
  PRINTER_LANG  (optional)  'en' or 'zh', default 'en'
"""
import os
import socket
import sys
import time

HOST = os.environ.get("PRINTER_HOST", "").strip()
PORT = int(os.environ.get("PRINTER_PORT", "8888"))
TIMEOUT = int(os.environ.get("PRINTER_TIMEOUT", "10"))
LANG = os.environ.get("PRINTER_LANG", "en").lower()


def t(en: str, zh: str) -> str:
    """Return bilingual string based on PRINTER_LANG."""
    return zh if LANG.startswith("zh") else en


def _clean_response(text: str) -> str:
    """Strip controller echo lines and keep meaningful content."""
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.lower().startswith("echo:"):
            continue
        lines.append(line)
    return "\n".join(lines)


def send_gcode(cmd: str, wait_ok: bool = True) -> str:
    """Send one G-code line, return cleaned printer response."""
    if not HOST:
        raise RuntimeError(t(
            "PRINTER_HOST not set. Add it to ~/.hermes/.env",
            "PRINTER_HOST 未设置。请添加到 ~/.hermes/.env"
        ))
    try:
        with socket.create_connection((HOST, PORT), timeout=TIMEOUT) as s:
            s.sendall((cmd + "\n").encode("ascii"))
            if not wait_ok:
                return "sent"
            s.settimeout(TIMEOUT)
            buf = b""
            deadline = time.time() + TIMEOUT
            while time.time() < deadline:
                try:
                    chunk = s.recv(1024)
                    if not chunk:
                        break
                    buf += chunk
                    text = buf.decode("ascii", errors="replace")
                    low = text.lower()
                    if "ok" in low or "error" in low:
                        return _clean_response(text)
                except socket.timeout:
                    break
            cleaned = _clean_response(buf.decode("ascii", errors="replace"))
            return cleaned or "(no response)"
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        raise RuntimeError(t(
            f"Printer connection failed: {e}",
            f"打印机连接失败：{e}"
        ))


def cmd_query():
    """Report temperature and position."""
    print(t("Temperature:", "温度:"), send_gcode("M105"))
    print(t("Position:   ", "位置:  "), send_gcode("M114"))


def cmd_gcode(args):
    """Send one or more G-code commands."""
    if not args:
        print(t("ERROR: no G-code provided", "错误：未提供 G-code"), file=sys.stderr)
        sys.exit(1)
    for g in args:
        print(f"> {g}")
        print(send_gcode(g))


def cmd_progress():
    """Report print progress (M27)."""
    print(t("Progress:", "进度:"), send_gcode("M27"))


def cmd_info():
    """Report firmware info (M115)."""
    print(t("Firmware info:", "固件信息:"), send_gcode("M115"))


def cmd_ping():
    """Test TCP connectivity to the controller."""
    if not HOST:
        print(t("ERROR: PRINTER_HOST not set", "错误：PRINTER_HOST 未设置"), file=sys.stderr)
        sys.exit(1)
    try:
        with socket.create_connection((HOST, PORT), timeout=TIMEOUT):
            print(t(f"OK: {HOST}:{PORT} reachable", f"OK: {HOST}:{PORT} 可达"))
    except (socket.timeout, ConnectionRefusedError, OSError) as e:
        print(t(
            f"FAIL: {HOST}:{PORT} unreachable — {e}",
            f"失败: {HOST}:{PORT} 不可达 — {e}"
        ), file=sys.stderr)
        sys.exit(1)


def cmd_selftest():
    """Run self-test: check env, script, and connectivity."""
    results = []

    # 1. Check PRINTER_HOST
    if HOST:
        results.append((True, t(f"PRINTER_HOST = {HOST}", f"PRINTER_HOST = {HOST}")))
    else:
        results.append((False, t("PRINTER_HOST not set", "PRINTER_HOST 未设置")))

    # 2. Check port config
    results.append((True, t(f"PRINTER_PORT = {PORT}", f"PRINTER_PORT = {PORT}")))
    results.append((True, t(f"PRINTER_TIMEOUT = {TIMEOUT}s", f"PRINTER_TIMEOUT = {TIMEOUT}秒")))

    # 3. Test connectivity
    if HOST:
        try:
            with socket.create_connection((HOST, PORT), timeout=TIMEOUT):
                results.append((True, t(
                    f"TCP connectivity to {HOST}:{PORT} — OK",
                    f"到 {HOST}:{PORT} 的 TCP 连通性 — OK"
                )))
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            results.append((False, t(
                f"TCP connectivity to {HOST}:{PORT} — FAIL: {e}",
                f"到 {HOST}:{PORT} 的 TCP 连通性 — 失败: {e}"
            )))

    # 4. Test M105 (temperature query)
    if HOST:
        try:
            resp = send_gcode("M105")
            if resp and "(no response)" not in resp:
                results.append((True, t("M105 temperature query — OK", "M105 温度查询 — OK")))
            else:
                results.append((False, t("M105 temperature query — no response", "M105 温度查询 — 无响应")))
        except RuntimeError as e:
            results.append((False, t(f"M105 failed: {e}", f"M105 失败: {e}")))

    # Print results
    print(t("=== Self-test results ===", "=== 自检结果 ==="))
    all_pass = True
    for ok, msg in results:
        status = t("PASS", "通过") if ok else t("FAIL", "失败")
        print(f"  [{status}] {msg}")
        if not ok:
            all_pass = False

    if all_pass:
        print(t("All checks passed.", "所有检查通过。"))
        sys.exit(0)
    else:
        print(t("Some checks failed.", "部分检查失败。"))
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    cmd = sys.argv[1]
    try:
        if cmd == "query":
            cmd_query()
        elif cmd == "gcode":
            cmd_gcode(sys.argv[2:])
        elif cmd == "progress":
            cmd_progress()
        elif cmd == "info":
            cmd_info()
        elif cmd == "ping":
            cmd_ping()
        elif cmd == "selftest":
            cmd_selftest()
        else:
            print(t(f"Unknown command: {cmd}", f"未知命令: {cmd}"), file=sys.stderr)
            print(__doc__)
            sys.exit(1)
    except RuntimeError as e:
        print(t(f"ERROR: {e}", f"错误: {e}"), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

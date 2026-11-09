#!/usr/bin/env python3
"""
Read-only status queries for Marlin 3D printers.
Outputs human-readable text or JSON for agent consumption.
"""
import sys
import json
import argparse
from printer_comm import PrinterComm

def main():
    parser = argparse.ArgumentParser(description="Read 3D printer status")
    parser.add_argument("action", choices=["status", "info", "progress"], help="Query type")
    parser.add_argument("--json", action="store_true", help="Output in JSON format")
    parser.add_argument("--host", help="Printer IP address")
    parser.add_argument("--port", type=int, help="Printer port (default 8888)")
    args = parser.parse_args()

    comm = None
    try:
        comm = PrinterComm(host=args.host, port=args.port)
        comm.connect()
        
        if args.action == "status":
            _, t_lines = comm.send_command("M105")
            _, p_lines = comm.send_command("M114")
            _, e_lines = comm.send_command("M119")
            
            data = {
                "temperature": comm.parse_m105(t_lines),
                "position": comm.parse_m114(p_lines),
                "endstops": comm.parse_m119(e_lines)
            }
            
            if args.json:
                print(json.dumps(data, indent=2))
            else:
                print("=== Printer Status ===")
                print(f"Hotend: {data['temperature']['hotend']['current']}C / Target: {data['temperature']['hotend']['target']}C")
                print(f"Bed: {data['temperature']['bed']['current']}C / Target: {data['temperature']['bed']['target']}C")
                print(f"Position: X={data['position']['x']}, Y={data['position']['y']}, Z={data['position']['z']}, E={data['position']['e']}")
                print(f"Endstops: {data['endstops']}")

        elif args.action == "info":
            _, lines = comm.send_command("M115")
            resp = " ".join(lines)
            if args.json:
                print(json.dumps({"firmware": resp}))
            else:
                print(resp)

        elif args.action == "progress":
            _, lines = comm.send_command("M27")
            resp = " ".join(lines)
            if args.json:
                print(json.dumps({"progress": resp}))
            else:
                print(resp)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        if comm:
            comm.disconnect()

if __name__ == "__main__":
    main()
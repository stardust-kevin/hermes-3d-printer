#!/usr/bin/env python3
"""
Semantic control executor for Marlin 3D printers.
Translates high-level intents into safe G-code sequences.
"""
import sys
import argparse
from printer_comm import PrinterComm

def check_safe_extrude(comm):
    """Prevent cold extrusion (Level 1 Safety)."""
    _, lines = comm.send_command("M105")
    temp_data = comm.parse_m105(lines)
    if temp_data["hotend"]["current"] < 170.0:
        raise ValueError(f"Cold extrusion prevented. Current temp: {temp_data['hotend']['current']}C")

def main():
    parser = argparse.ArgumentParser(description="Control 3D printer")
    parser.add_argument("--host", help="Printer IP address")
    parser.add_argument("--port", type=int, help="Printer port (default 8888)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_move = subparsers.add_parser("move", help="Move axes")
    p_move.add_argument("--x", type=float)
    p_move.add_argument("--y", type=float)
    p_move.add_argument("--z", type=float)
    p_move.add_argument("--f", type=int, default=3000, help="Feedrate mm/min")
    p_move.add_argument("--relative", action="store_true", help="Relative move")
    p_move.add_argument("--max-x", type=float, default=999, help="Safety limit X")
    p_move.add_argument("--max-y", type=float, default=999, help="Safety limit Y")
    p_move.add_argument("--max-z", type=float, default=999, help="Safety limit Z")

    p_home = subparsers.add_parser("home", help="Home axes")
    p_home.add_argument("--axes", nargs="+", choices=["X", "Y", "Z"], help="Specific axes")

    p_heat = subparsers.add_parser("heat", help="Set temperature")
    p_heat.add_argument("--hotend", type=int)
    p_heat.add_argument("--bed", type=int)
    p_heat.add_argument("--wait", action="store_true", help="Block until target reached")

    p_ext = subparsers.add_parser("extrude", help="Extrude or retract filament")
    p_ext.add_argument("--mm", type=float, required=True, help="Positive to extrude, negative to retract")
    p_ext.add_argument("--f", type=int, default=300, help="Feedrate")

    subparsers.add_parser("cool", help="Turn off all heaters")

    p_fan = subparsers.add_parser("fan", help="Control fan speed")
    p_fan.add_argument("--speed", type=int, required=True, help="0 to 255")

    p_motor = subparsers.add_parser("motors", help="Enable or disable motors")
    p_motor.add_argument("state", choices=["on", "off"])

    subparsers.add_parser("estop", help="Emergency stop")

    p_pass = subparsers.add_parser("passthrough", help="Send raw G-code")
    p_pass.add_argument("gcode", help="Raw G-code string")

    args = parser.parse_args()
    comm = PrinterComm(host=args.host, port=args.port)

    try:
        comm.connect()

        if args.command == "move":
            if args.x is not None and abs(args.x) > args.max_x: raise ValueError(f"X out of bounds (max: {args.max_x})")
            if args.y is not None and abs(args.y) > args.max_y: raise ValueError(f"Y out of bounds (max: {args.max_y})")
            if args.z is not None and abs(args.z) > args.max_z: raise ValueError(f"Z out of bounds (max: {args.max_z})")

            if args.relative:
                comm.send_command("G91")
            
            g1 = f"G1 F{args.f}"
            if args.x is not None: g1 += f" X{args.x}"
            if args.y is not None: g1 += f" Y{args.y}"
            if args.z is not None: g1 += f" Z{args.z}"
            comm.send_command(g1)
            
            if args.relative:
                comm.send_command("G90")
            print("ok")

        elif args.command == "home":
            cmd = "G28"
            if args.axes:
                cmd += " " + " ".join(args.axes)
            comm.send_command(cmd)
            print("ok")

        elif args.command == "heat":
            if args.hotend is not None:
                code = "M109" if args.wait else "M104"
                comm.send_command(f"{code} S{args.hotend}", wait_ok=not args.wait)
            if args.bed is not None:
                code = "M190" if args.wait else "M140"
                comm.send_command(f"{code} S{args.bed}", wait_ok=not args.wait)
            print("ok")

        elif args.command == "extrude":
            check_safe_extrude(comm)
            comm.send_command(f"G1 E{args.mm} F{args.f}")
            print("ok")

        elif args.command == "cool":
            comm.send_command("M104 S0")
            comm.send_command("M140 S0")
            print("ok")

        elif args.command == "fan":
            comm.send_command(f"M106 S{args.speed}")
            print("ok")

        elif args.command == "motors":
            if args.state == "off":
                comm.send_command("M84")
            else:
                comm.send_command("G1 F1000")
            print("ok")

        elif args.command == "estop":
            comm.send_command("M112")
            print("ok")

        elif args.command == "passthrough":
            code, lines = comm.send_command(args.gcode)
            if code == 1:
                raise ValueError("Command rejected by firmware.")
            print("\n".join(lines))

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        comm.disconnect()

if __name__ == "__main__":
    main()
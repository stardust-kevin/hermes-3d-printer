#!/usr/bin/env python3
"""
Stream G-code files to the printer using a sliding window FIFO buffer.
"""
import sys
import argparse
from printer_comm import PrinterComm

def main():
    parser = argparse.ArgumentParser(description="Stream G-code file to printer")
    parser.add_argument("file", help="Path to G-code file")
    parser.add_argument("--window", type=int, default=5, help="FIFO window size")
    parser.add_argument("--host", help="Printer IP address")
    parser.add_argument("--port", type=int, help="Printer port (default 8888)")
    args = parser.parse_args()

    comm = PrinterComm(host=args.host, port=args.port)
    try:
        print("Connecting to printer...")
        comm.connect()

        print(f"Starting print: {args.file}")
        for progress in comm.stream_file(args.file, window_size=args.window):
            sys.stdout.write(f"\rProgress: {progress}%")
            sys.stdout.flush()

        print("\nSUCCESS: All G-code sent successfully. The printer is now executing the job.")
    except KeyboardInterrupt:
        print("\n\nPrint interrupted by user. Sending emergency stop...")
        try:
            comm.send_command("M112")
        except Exception:
            pass
        sys.exit(1)
    except Exception as e:
        print(f"\nPrint failed: {e}", file=sys.stderr)
        try:
            comm.send_command("M112")
        except Exception:
            pass
        sys.exit(1)
    finally:
        comm.disconnect()

if __name__ == "__main__":
    main()
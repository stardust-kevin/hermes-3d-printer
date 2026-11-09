# Mock Printer Test Guide / 模拟打印机测试指南

This directory contains a mock Marlin printer server. It allows you to test the `printer_read.py`, `printer_write.py`, and `printer_print.py` scripts without physical hardware.

本目录包含一个模拟 Marlin 打印机服务器。你可以用它来测试 `printer_read.py`、`printer_write.py` 和 `printer_print.py` 脚本，无需真实硬件。

## Quick Start / 快速开始

### Terminal 1: Start the mock server

```bash
python3 tests/mock_printer.py
```

### Terminal 2: Run the read/write tests

```bash
# Set environment
export PRINTER_HOST=127.0.0.1
export PRINTER_PORT=8888

# Test status query (JSON)
python3 scripts/printer_read.py status --json

# Test safe movement
python3 scripts/printer_write.py move --x 10 --y 20 --f 3000

# Test unsafe movement (should be blocked by bounds checking)
python3 scripts/printer_write.py move --x 500 --max-x 220

# Test cold extrusion prevention (should fail if temp < 170)
python3 scripts/printer_write.py extrude --mm 10
```

### Terminal 2: Test FIFO Streaming

You can generate a dummy G-code file and test the FIFO flow control:

```bash
# Generate a 1000-line dummy G-code file
for i in {1..1000}; do echo "G1 X$((i%100)) Y$((i%100)) F3000"; done > test_print.gcode

# Stream it using the FIFO buffer (window size 5)
python3 scripts/printer_print.py test_print.gcode --window 5
```

## Failure Scenarios / 异常场景测试

The mock server can simulate various network and firmware errors. Stop the normal server and start it with a specific `--scenario`:

模拟服务器可以模拟各种网络和固件错误。停止正常服务器，使用特定的 `--scenario` 启动：

### 1. Printer is busy / 打印机忙碌
Simulates an 8-bit MCU struggling to keep up. The first 3 commands return `busy: processing`.
模拟 8 位 MCU 处理不过来。前 3 条指令返回 `busy`。

```bash
python3 tests/mock_printer.py --scenario busy
```
*Expected*: The Python scripts should wait for the `busy` state to clear and eventually succeed.

### 2. Slow response / 响应缓慢
Adds a 3-second delay to every response.
每次响应延迟 3 秒。

```bash
python3 tests/mock_printer.py --scenario slow
```
*Expected*: The script should handle the delay without timing out (default timeout is 10s).

### 3. Error / 固件报错
Every command returns an `Error:`.
所有指令返回 `Error:`。

```bash
python3 tests/mock_printer.py --scenario error
```
*Expected*: `printer_write.py` should exit with code 1 and print the error message.

### 4. Garbled / 乱码
Returns random characters instead of `ok`.
返回随机字符而不是 `ok`。

```bash
python3 tests/mock_printer.py --scenario garbled
```
*Expected*: The Python script should timeout or fail parsing gracefully.

### 5. Disconnect / 断连
Closes the connection immediately after the first response.
首次响应后立即关闭连接。

```bash
python3 tests/mock_printer.py --scenario disconnect
```
*Expected*: The script should raise a `ConnectionError`.

### 6. Timeout / 超时
Accepts the connection but never responds.
接受连接但永不响应。

```bash
python3 tests/mock_printer.py --scenario timeout
```
*Expected*: The Python script should timeout after `PRINTER_TIMEOUT` seconds.

## Troubleshooting / 排障

If the mock server says "Address already in use", another instance is running. Find and kill it:
如果提示端口被占用，说明有另一个实例在运行。找到并关闭它：

```bash
# Linux / macOS
lsof -i :8888

# Windows
netstat -ano | findstr :8888
```

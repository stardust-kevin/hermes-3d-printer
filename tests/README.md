<!-- Language Switcher / 语言切换 -->
<p align="center">
  <a href="#english">English</a> ·
  <a href="#中文">中文</a>
</p>

---

<a id="english"></a>

# Hermes 3D Printer Skill

A Hermes Agent skill for controlling 3D printers via G-code over TCP/serial. Includes a generic communication layer and printer-specific child skills.

**Pure Python 3 standard library. Zero third-party dependencies. No venv, no pip install needed.**

---

## Quick Start

### Requirements

- Python 3.8 or newer
- A network-reachable printer controller (ESP3D / OctoPrint / Moonraker)

### Run directly (no installation)

```bash
git clone https://github.com/stardust-kevin/hermes-3d-printer.git
cd hermes-3d-printer

# Run the script
python3 scripts/printer_control.py
```

You will see the help message. **No `pip install`, no `source venv/bin/activate` required.**

---

## Test with Mock Printer (recommended first)

Before connecting to a real printer, verify the software logic with the built-in mock server.

```bash
# Terminal 1 — start the mock printer
python3 tests/mock_printer.py

# Terminal 2 — run self-test
PRINTER_HOST=127.0.0.1 PRINTER_PORT=8888 \
  python3 scripts/printer_control.py selftest
```

Expected output:

```
=== Self-test results ===
  [PASS] PRINTER_HOST = 127.0.0.1
  [PASS] PRINTER_PORT = 8888
  [PASS] PRINTER_TIMEOUT = 10s
  [PASS] TCP connectivity to 127.0.0.1:8888 — OK
  [PASS] M105 temperature query — OK
All checks passed.
```

The mock supports multiple failure scenarios (timeout, garbled, error, disconnect). See `tests/README.md` for details.

---

## Connect to a Real Printer

### 1. Set environment variables

Add to `${HERMES_HOME:-~/.hermes}/.env`:

```bash
# Generic layer
PRINTER_HOST=192.168.1.100
PRINTER_PORT=8888

# Anet A8 child skill (optional, overrides PRINTER_HOST)
A8_ESP3D_HOST=192.168.1.100
A8_ESP3D_PORT=8888

# Optional
PRINTER_TIMEOUT=10
PRINTER_LANG=en   # or zh
```

### 2. Test connectivity

```bash
source ~/.hermes/.env

# Test TCP connectivity
python3 scripts/printer_control.py ping

# Query temperature and position
python3 scripts/printer_control.py query

# Send G-code
python3 scripts/printer_control.py gcode "M105"
```

### 3. Use with Hermes

Place the skill directory at `~/.hermes/skills/make/3d-printer/`, then talk to Hermes:

- "Query A8 printer status"
- "Home all axes on the A8"
- "Turn off the hotend and bed"

---

## Script Commands

```bash
python3 scripts/printer_control.py <command>

Commands:
  query         Query temperature and position
  gcode "CMD"   Send one or more G-code commands
  progress      Query print progress (M27)
  info          Query firmware info (M115)
  ping          Test TCP connectivity
  selftest      Run full self-test
```

---

## Directory Structure

```
hermes-3d-printer/
├── SKILL.md                        # Generic layer instructions
├── scripts/
│   └── printer_control.py          # Generic comms script (zero deps)
├── references/
│   ├── gcode-universal.md          # Universal G-code reference
│   └── troubleshooting.md          # Universal error handling
├── anet-a8/
│   ├── SKILL.md                    # Anet A8 specific parameters
│   └── references/
│       └── a8-specifics.md         # Anet A8 hardware details
├── tests/
│   ├── mock_printer.py             # Mock printer (zero deps)
│   └── README.md                   # Test guide
└── README.md
```

---

## FAQ

**Q: Do I need a venv or pip install?**

No. All scripts use only the Python 3 standard library. Any system with Python 3.8+ can run them directly.

**Q: Does it work on Windows?**

Yes. Pure Python, cross-platform. For `ping`, Windows uses `Test-NetConnection` instead of `nc`.

**Q: Which printers are supported?**

The generic layer works with any Marlin/RepRap-style printer. `anet-a8` is currently provided as a child skill. More models can be added.

**Q: Is it safe?**

The skill enforces: user confirmation before heating, starting a print, or emergency stop. The stock Anet A8 firmware has no thermal runaway protection — never leave a heated printer unattended.

---

## License

MIT

---

<a id="中文"></a>

# Hermes 3D 打印机 Skill

一个用于控制 3D 打印机的 Hermes Agent skill，通过 TCP/串口发送 G-code。包含通用通信层和打印机专属子 skill。

**纯 Python 3 标准库，零第三方依赖。不需要 venv，不需要 pip install。**

---

## 快速开始

### 环境要求

- Python 3.8 或更高
- 网络可达的打印机控制器（ESP3D / OctoPrint / Moonraker）

### 直接运行（无需安装）

```bash
git clone https://github.com/stardust-kevin/hermes-3d-printer.git
cd hermes-3d-printer

# 直接运行脚本
python3 scripts/printer_control.py
```

你会看到帮助信息。**不需要 `pip install`，不需要 `source venv/bin/activate`。**

---

## 用模拟打印机测试（推荐先做）

在连接真实打印机之前，先用内置的 mock 服务器验证软件逻辑。

```bash
# 终端 1：启动模拟打印机
python3 tests/mock_printer.py

# 终端 2：运行自检
PRINTER_HOST=127.0.0.1 PRINTER_PORT=8888 \
  python3 scripts/printer_control.py selftest
```

预期输出：

```
=== Self-test results ===
  [PASS] PRINTER_HOST = 127.0.0.1
  [PASS] PRINTER_PORT = 8888
  [PASS] PRINTER_TIMEOUT = 10s
  [PASS] TCP connectivity to 127.0.0.1:8888 — OK
  [PASS] M105 temperature query — OK
All checks passed.
```

模拟服务器支持多种异常场景（超时、乱码、错误、断连），详见 `tests/README.md`。

---

## 连接真实打印机

### 1. 配置环境变量

在 `${HERMES_HOME:-~/.hermes}/.env` 中添加：

```bash
# 通用层
PRINTER_HOST=192.168.1.100
PRINTER_PORT=8888

# 爱能特 A8 子 skill（可选，覆盖 PRINTER_HOST）
A8_ESP3D_HOST=192.168.1.100
A8_ESP3D_PORT=8888

# 可选
PRINTER_TIMEOUT=10
PRINTER_LANG=zh   # 或 en
```

### 2. 测试连通性

```bash
source ~/.hermes/.env

# 测试 TCP 连通性
python3 scripts/printer_control.py ping

# 查询温度和位置
python3 scripts/printer_control.py query

# 发送 G-code
python3 scripts/printer_control.py gcode "M105"
```

### 3. 在 Hermes 中使用

Skill 目录放到 `~/.hermes/skills/make/3d-printer/` 后，直接对 Hermes 说：

- “查询 A8 打印机状态”
- “A8 全轴归零”
- “关闭喷头和热床”

---

## 脚本命令速查

```bash
python3 scripts/printer_control.py <命令>

命令：
  query         查询温度和位置
  gcode "CMD"   发送一条或多条 G-code
  progress      查询打印进度 (M27)
  info          查询固件信息 (M115)
  ping          测试 TCP 连通性
  selftest      运行完整自检
```

---

## 目录结构

```
hermes-3d-printer/
├── SKILL.md                        # 通用层指令
├── scripts/
│   └── printer_control.py          # 通用通信脚本（零依赖）
├── references/
│   ├── gcode-universal.md          # 通用 G-code 参考
│   └── troubleshooting.md          # 通用异常处理
├── anet-a8/
│   ├── SKILL.md                    # 爱能特 A8 专属参数
│   └── references/
│       └── a8-specifics.md         # A8 硬件细节
├── tests/
│   ├── mock_printer.py             # 模拟打印机（零依赖）
│   └── README.md                   # 测试说明
└── README.md
```

---

## 常见问题

**Q: 需要 `venv` 或 `pip install` 吗？**

不需要。所有脚本仅使用 Python 3 标准库。任何有 Python 3.8+ 的系统都能直接运行。

**Q: Windows 上能跑吗？**

能。脚本纯 Python，跨平台。`ping` 命令在 Windows 上用 `Test-NetConnection` 替代 `nc`。

**Q: 支持哪些打印机？**

通用层支持任何 Marlin/RepRap 风格打印机。目前有 `anet-a8` 子 skill，未来可扩展其他型号。

**Q: 安全吗？**

Skill 强制要求：加热、开始打印、急停前必须用户确认。A8 原厂固件无热失控保护，加热时绝不能无人看管。

---

## 许可

MIT

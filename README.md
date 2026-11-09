> ⚠️ **Status: Unverified / 未验证**
> This skill has NOT been tested on real hardware yet.
> Use at your own risk. Do NOT use for unattended printing.
> 本 skill 尚未在真实硬件上验证。使用风险自负。禁止无人看管打印。

<!-- Language Switcher / 语言切换 -->
<p align="center">
  <a href="#english">English</a> ·
  <a href="#中文">中文</a>
</p>

---

<a id="english"></a>

# 3D Printer Control Skill for Hermes

A Hermes Agent skill for controlling 3D printers via G-code over TCP/serial. Includes a generic communication layer and printer-specific child skills.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hermes Skill](https://img.shields.io/badge/Hermes-Skill-blue)](https://github.com/NousResearch/hermes-agent)

## Features

- **Generic layer** (`3d-printer`) — works with any Marlin/RepRap-style printer over TCP or serial
- **Child skills** — printer-specific parameters overlay the generic layer (currently `anet-a8`)
- **Pure Python 3 stdlib** — no external dependencies, no `pip install` required
- **Bilingual** — English and Chinese output via `PRINTER_LANG`
- **Tiered Safety** — strict user confirmation for high-risk actions (heating/printing), while script-level checks prevent physical crashes (cold extrusion, out-of-bounds moves)
- **FIFO Streaming** — built-in flow control to print large G-code files without overflowing the MCU buffer

## Supported Printers

| Printer | Status | Skill |
|---|---|---|
| Anet A8 (stock v1.0–v1.5, Marlin) | ✅ Supported | [`anet-a8`](3d-printer/anet-a8/SKILL.md) |
| Any Marlin/RepRap-style printer | ✅ Generic layer | [`3d-printer`](3d-printer/SKILL.md) |
| OctoPrint / Moonraker backends | ⚠️ Partial (raw TCP assumed) | — |

## Requirements

- Python 3.8+
- A network-reachable printer controller:
  - **ESP3D** (ESP8266/ESP32) — raw TCP passthrough, port 8888
  - **OctoPrint** — REST API (script adaptation needed)
  - **Moonraker** — JSON-RPC (script adaptation needed)

## Installation

### Option 1: Clone into Hermes skills directory

```bash
git clone https://github.com/stardust-kevin/hermes-3d-printer.git \
  ~/.hermes/skills/make/3d-printer
```

### Option 2: Symlink from an existing checkout

```bash
ln -s /path/to/3d-printer-skill ~/.hermes/skills/make/3d-printer
```

### Verify

```bash
hermes skills list | grep -E "3d-printer|anet"
```

You should see both skills listed as `enabled`.

## Configuration

Add to `${HERMES_HOME:-~/.hermes}/.env`:

```bash
# Generic layer
PRINTER_HOST=192.168.1.100
PRINTER_PORT=8888

# Anet A8 child skill (overrides PRINTER_HOST)
A8_ESP3D_HOST=192.168.1.100
A8_ESP3D_PORT=8888

# Optional
PRINTER_TIMEOUT=10
PRINTER_LANG=en
```

## Usage

Once the skill is loaded, ask Hermes in natural language:

```
"Query the A8 printer status"
"Home all axes on the A8"
"Turn off the hotend and bed"
"Start printing benchy.gcode"
```

Or use the helper scripts directly:

```bash
# Read-only status (Temperature, Position, Endstops in JSON)
python3 ~/.hermes/skills/make/3d-printer/scripts/printer_read.py status --json

# Move axes safely (with bounds checking)
python3 ~/.hermes/skills/make/3d-printer/scripts/printer_write.py move --x 10 --y 10 --f 3000 --max-x 220 --max-y 220

# Heat (Requires user confirmation)
python3 ~/.hermes/skills/make/3d-printer/scripts/printer_write.py heat --hotend 200 --bed 60

# Stream a G-code file using FIFO
python3 ~/.hermes/skills/make/3d-printer/scripts/printer_print.py my_model.gcode
```

## Safety

**This skill controls physical hardware. Misuse can cause fire or equipment damage.**

Mandatory rules enforced by the skill:

- 🔴 **Level 2 (Requires Clarification)**: Heating (`heat`), Printing (`printer_print.py`), EEPROM saves/resets.
- 🟡 **Level 1 (Script Enforced)**: Cold extrusion prevention (blocks `extrude` if temp < 170°C).
- 🟢 **Level 0 (Safe)**: Queries, movements (bounds enforced), cooling down.

**The stock Anet A8 firmware has NO thermal runaway protection.** Never leave a heated printer unattended.

## Directory Structure

```
3d-printer/
├── SKILL.md                        # Generic layer instructions
├── scripts/
│   ├── printer_comm.py             # Low-level TCP communication & FIFO
│   ├── printer_read.py             # Read-only status queries (JSON)
│   ├── printer_write.py            # Semantic control executor
│   └── printer_print.py            # G-code file streaming
├── references/
│   ├── gcode-universal.md          # Universal G-code reference
│   └── troubleshooting.md          # Universal error handling
└── anet-a8/
    ├── SKILL.md                    # Anet A8 specific parameters
    └── references/
        └── a8-specifics.md         # Anet A8 hardware details
```

## Contributing

Contributions welcome. To add a new printer:

1. Fork this repository
2. Create a new child skill directory (e.g. `ender-3/`)
3. Add `SKILL.md` with `requires_skills: [3d-printer]` in frontmatter
4. Add printer-specific parameters, safety rules, and references
5. Submit a pull request

## License

[MIT](LICENSE)

## Related

- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [ESP3D firmware](https://github.com/luc-github/ESP3D)
- [Marlin firmware](https://marlinfw.org/)

---

<a id="中文"></a>

# Hermes 3D 打印机控制 Skill

一个用于控制 3D 打印机的 Hermes Agent skill，通过 TCP/串口发送 G-code。包含通用通信层和打印机专属子 skill。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Hermes Skill](https://img.shields.io/badge/Hermes-Skill-blue)](https://github.com/NousResearch/hermes-agent)

## 功能特性

- **通用层**（`3d-printer`）——适用于任何 Marlin/RepRap 风格打印机，支持 TCP 或串口
- **子 skill**——打印机专属参数叠加在通用层之上（当前支持 `anet-a8`）
- **纯 Python 3 标准库**——无外部依赖，无需 `pip install`
- **中英双语**——通过 `PRINTER_LANG` 切换输出语言
- **分级安全机制**——高危操作（加热/打印）强制要求用户确认，而底层脚本会进行物理保护（防冷挤出、防越界撞机）
- **FIFO 流控**——内置滑动窗口流控，打印大型 G-code 文件不会撑爆主板缓存

## 支持的打印机

| 打印机 | 状态 | Skill |
|---|---|---|
| 爱能特 A8（原厂 v1.0–v1.5，Marlin） | ✅ 支持 | [`anet-a8`](3d-printer/anet-a8/SKILL.md) |
| 任何 Marlin/RepRap 风格打印机 | ✅ 通用层 | [`3d-printer`](3d-printer/SKILL.md) |
| OctoPrint / Moonraker 后端 | ⚠️ 部分支持（假设原始 TCP） | — |

## 环境要求

- Python 3.8+
- 网络可达的打印机控制器：
  - **ESP3D**（ESP8266/ESP32）——原始 TCP 透传，端口 8888
  - **OctoPrint**——REST API（需适配脚本）
  - **Moonraker**——JSON-RPC（需适配脚本）

## 安装

### 方式一：克隆到 Hermes skills 目录

```bash
git clone https://github.com/stardust-kevin/hermes-3d-printer.git \
  ~/.hermes/skills/make/3d-printer
```

### 方式二：从已有检出创建软链接

```bash
ln -s /path/to/3d-printer-skill ~/.hermes/skills/make/3d-printer
```

### 验证

```bash
hermes skills list | grep -E "3d-printer|anet"
```

应该看到两个 skill 都显示为 `enabled`。

## 配置

在 `${HERMES_HOME:-~/.hermes}/.env` 中添加：

```bash
# 通用层
PRINTER_HOST=192.168.1.100
PRINTER_PORT=8888

# 爱能特 A8 子 skill（覆盖 PRINTER_HOST）
A8_ESP3D_HOST=192.168.1.100
A8_ESP3D_PORT=8888

# 可选
PRINTER_TIMEOUT=10
PRINTER_LANG=zh
```

## 使用

Skill 加载后，用自然语言向 Hermes 提问：

```
"查询 A8 打印机状态"
"A8 全轴归零"
"关闭喷头和热床"
"开始打印 benchy.gcode"
```

或直接使用辅助脚本：

```bash
# 只读状态查询（温度、位置、限位以 JSON 格式输出）
python3 ~/.hermes/skills/make/3d-printer/scripts/printer_read.py status --json

# 安全移动（带边界检查）
python3 ~/.hermes/skills/make/3d-printer/scripts/printer_write.py move --x 10 --y 10 --f 3000 --max-x 220 --max-y 220

# 加热（需用户确认后执行）
python3 ~/.hermes/skills/make/3d-printer/scripts/printer_write.py heat --hotend 200 --bed 60

# 使用 FIFO 流控打印 G-code 文件
python3 ~/.hermes/skills/make/3d-printer/scripts/printer_print.py my_model.gcode
```

## 安全须知

**本 skill 控制物理硬件。误用可能导致火灾或设备损坏。**

Skill 强制执行的安全分级：

- 🔴 **Level 2（需用户确认）**：加热（`heat`）、开始打印（`printer_print.py`）、EEPROM 保存/重置。
- 🟡 **Level 1（脚本强制拦截）**：防冷挤出（如果温度 < 170°C，`extrude` 会被拒绝）。
- 🟢 **Level 0（安全）**：状态查询、移动（强制边界检查）、关闭加热。

**爱能特 A8 原厂固件没有热失控保护。** 加热时绝不能无人看管。

## 目录结构

```
3d-printer/
├── SKILL.md                        # 通用层指令
├── scripts/
│   ├── printer_comm.py             # 底层 TCP 通信与流控
│   ├── printer_read.py             # 只读状态查询 (JSON)
│   ├── printer_write.py            # 语义化控制执行器
│   └── printer_print.py            # G-code 文件流控打印
├── references/
│   ├── gcode-universal.md          # 通用 G-code 参考
│   └── troubleshooting.md          # 通用异常处理
└── anet-a8/
    ├── SKILL.md                    # 爱能特 A8 专属参数
    └── references/
        └── a8-specifics.md         # 爱能特 A8 硬件细节
```

## 贡献

欢迎贡献。要添加新打印机：

1. Fork 本仓库
2. 创建新的子 skill 目录（如 `ender-3/`）
3. 添加 `SKILL.md`，在 frontmatter 中声明 `requires_skills: [3d-printer]`
4. 添加打印机专属参数、安全规则和参考文档
5. 提交 Pull Request

## 许可

[MIT](LICENSE)

## 相关项目

- [Hermes Agent](https://github.com/NousResearch/hermes-agent)
- [ESP3D 固件](https://github.com/luc-github/ESP3D)
- [Marlin 固件](https://marlinfw.org/)

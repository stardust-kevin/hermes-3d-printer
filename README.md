> ⚠️ **Status: Unverified / 未验证**
> While verified in simulation, this skill has NOT been tested on real hardware yet. Please use with caution and do NOT run unattended.
> 虽已在仿真平台验证，但本 skill 尚未在真实硬件上测试。请谨慎使用，请勿无人值守打印。

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
- **Pure Python 3 stdlib** — no external dependencies, no `pip install` required for core operation
- **Bilingual** — English and Chinese output via `PRINTER_LANG`
- **Tiered Safety** — strict user confirmation for high-risk actions (heating/printing), while script-level checks prevent physical crashes (cold extrusion, out-of-bounds moves)
- **FIFO Streaming** — built-in flow control to print large G-code files without overflowing the MCU buffer
- **Parametric Geometry** — native generation of 1D, 2D, and 3D shapes with smart support

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

### Test Cases / 测试话术

Here are the complete test cases covering all supported status queries, control commands, and parametric geometry generation.

**1. Status & System / 状态与系统**
- `"Query current printer status in JSON."`
- `"Check the printer's maximum physical bounds."`
- `"Move the nozzle to X=10 Y=20."`

**2. 2D Shapes (Single Layer) / 二维基础图形（单层）**
- `"Generate a line from (110,110) to (160,160) and print it."`
- `"Draw a triangle with side 30mm, solid fill."`
- `"Generate a rectangle w=40mm, h=20mm."`
- `"Generate a solid circle with diameter 50mm."`
- `"Draw a hollow circle with diameter 40mm."`
- `"Generate a solid ellipse with rx=30, ry=15mm."`
- `"Draw a regular hexagon with side 40mm, solid fill."`
- `"Draw a ring with outer diameter 50mm, inner diameter 30mm."`

**3. 3D Shapes / 三维几何体**
- `"Print a 20x20x20mm cube, 20% infill."`
- `"Print a cuboid with length 40mm, width 30mm, height 60mm."`
- `"Print a cylinder with diameter 30mm, height 10mm."`
- `"Print a pyramid with base 40mm, height 20mm."`
- `"Print a solid cone with base diameter 40mm, height 30mm."`
- `"Print an ellipsoid with equator diameter 40mm, pole height 60mm."` (auto support)

**4. Advanced Control / 高级控制**
- `"Print a sphere with diameter 50mm, no support."`
- `"Generate a cylinder with diameter 40mm, layer height 0.2, speed 3000."`
- `"Turn off all heaters."`

### Mock Camera Testing / 摄像头模拟测试

If you want to test the visual loop / camera streaming features (e.g., `tests/mock_camera.py`), you need to set up a virtual environment with WebRTC and OpenCV dependencies.

如果你需要测试视觉闭环/摄像头流媒体功能（如 `tests/mock_camera.py`），你需要配置包含 WebRTC 和 OpenCV 的虚拟环境。

**Using `uv` (Recommended, extremely fast):**
```bash
# 1. Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 2. Install dependencies
uv pip install aiortc opencv-python websockets

# 3. Export to requirements.txt for non-uv users
uv pip freeze > requirements.txt

# 4. (Optional) Initialize project and sync
uv init
uv sync
```

**Using standard `pip`:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install aiortc opencv-python websockets
pip freeze > requirements.txt
```

**Run the Mock Camera:**
```bash
python3 tests/mock_camera.py
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
│   ├── printer_draw.py             # Parametric G-code generator
│   ├── printer_read.py             # Read-only status queries (JSON)
│   ├── printer_write.py            # Semantic control executor
│   └── printer_print.py            # G-code file streaming
├── references/
│   ├── gcode-universal.md          # Universal G-code reference
│   └── troubleshooting.md          # Universal error handling
├── tests/
│   ├── mock_printer.py             # Mock TCP printer server
│   └── mock_camera.py              # Mock camera streaming server
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
- **纯 Python 3 标准库**——核心控制无外部依赖，无需 `pip install`
- **中英双语**——通过 `PRINTER_LANG` 切换输出语言
- **分级安全机制**——高危操作（加热/打印）强制要求用户确认，而底层脚本会进行物理保护（防冷挤出、防越界撞机）
- **FIFO 流控**——内置滑动窗口流控，打印大型 G-code 文件不会撑爆主板缓存
- **参数化几何**——原生生成 1D、2D、3D 图形，并支持智能支撑

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

### Test Cases / 测试话术

以下是完整的功能测试话术，涵盖了所有支持的状态查询、运动控制和参数化几何体生成。

**1. 状态与系统**
- `"查询当前打印机状态，输出 JSON 格式。"`（查温度、坐标、限位）
- `"查看打印机的最大物理范围。"`（查边界）
- `"把喷头移动到 X=10 Y=20 的位置。"`（移动轴）

**2. 二维基础图形（单层）**
- `"生成一条从 (110,110) 到 (160,160) 的直线，然后打印。"`（直线）
- `"画一个边长为 30mm 的三角形，实心填充。"`（三角形）
- `"生成一个宽 40mm，高 20mm 的矩形。"`（矩形）
- `"生成一个直径为 50mm 的单层实心圆。"`（实心圆）
- `"画一个空心圆，直径 40mm。"`（空心圆）
- `"生成一个 rx=30, ry=15mm 的单层实心椭圆。"`（实心椭圆）
- `"画一个边长为 40mm 的正六边形，实心填充。"`（正多边形）
- `"画一个外径 50mm，内径 30mm 的空心圆环。"`（圆环）

**3. 三维几何体**
- `"打印一个 20x20x20mm 的正方体，20% 填充。"`（正方体）
- `"打印一个长 40mm，宽 30mm，高 60mm 的长方体。"`（长方体）
- `"打印一个直径 30mm，高 10mm 的圆柱体。"`（圆柱体）
- `"打印一个底面边长 40mm，高 20mm 的金字塔。"`（金字塔）
- `"打印一个底部直径 40mm，高 30mm 的实心圆锥。"`（圆锥）
- `"打印一个赤道直径 40mm，两极高度 60mm 的椭球体。"`（椭球体 - 默认自动生成支撑）

**4. 高级控制**
- `"打印一个直径为 50mm 的球体，不要支撑。"`（强制无支撑）
- `"生成一个直径为 40mm 的圆柱体，设置层高为 0.2，速度 3000。"`（自定义参数）
- `"关闭所有加热。"`（关闭加热）

### 摄像头模拟测试 (Mock Camera Testing)

如果你需要测试视觉闭环/摄像头流媒体功能（如 `tests/mock_camera.py`），你需要配置包含 WebRTC 和 OpenCV 的虚拟环境。

**推荐使用 `uv`（极速包管理器）:**
```bash
# 1. 创建并激活虚拟环境
uv venv
source .venv/bin/activate  # Windows 用户使用: .venv\Scripts\activate

# 2. 安装依赖
uv pip install aiortc opencv-python websockets

# 3. 导出 requirements.txt 给非 uv 用户使用
uv pip freeze > requirements.txt

# 4. (可选) 初始化项目并同步
uv init
uv sync
```

**使用标准 `pip`:**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install aiortc opencv-python websockets
pip freeze > requirements.txt
```

**运行模拟摄像头:**
```bash
python3 tests/mock_camera.py
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
│   ├── printer_draw.py             # 参数化 G-code 生成器
│   ├── printer_read.py             # 只读状态查询 (JSON)
│   ├── printer_write.py            # 语义化控制执行器
│   └── printer_print.py            # G-code 文件流控打印
├── references/
│   ├── gcode-universal.md          # 通用 G-code 参考
│   └── troubleshooting.md          # 通用异常处理
├── tests/
│   ├── mock_printer.py             # 模拟 TCP 打印机服务器
│   └── mock_camera.py              # 模拟摄像头流媒体服务器
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
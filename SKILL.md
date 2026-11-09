---
name: 3d-printer
description: "Generic 3D printer control via G-code over TCP/serial. Query status, send commands, manage prints. 通用 3D 打印机控制，通过 G-code 通信，支持状态查询、命令发送和打印管理。"
version: 1.1.0
author: kevin
license: MIT
date: 2026-09-16
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [PRINTER_HOST]
  commands: [python3]
metadata:
  hermes:
    tags: [3D-Printing, G-code, Marlin, Hardware, Generic, 3D打印, 通用]
    homepage: https://github.com/stardust-kevin/hermes-3d-printer
    related_skills: []
---

# Generic 3D Printer Control / 通用 3D 打印机控制

Send G-code to any Marlin/RepRap-style 3D printer over TCP or serial. This skill provides the generic communication layer, safety framework, and error handling.

通过 TCP 或串口向任何使用 Marlin/RepRap 风格协议的 3D 打印机发送 G-code。本 skill 提供通用通信层、安全框架和异常处理。

## Initial Handshake / 初次握手

When connecting to a new printer or starting a new session, you should first run:
```bash
python3 SKILL_DIR/scripts/printer_read.py status --json
```
This provides the baseline state (current temp, position, endstops) to ensure the printer is ready.

## Safety Tiers / 安全权限分级

As an AI Agent, you must follow this tiered safety system to prevent hardware damage or fire.

作为 AI Agent，必须遵守以下安全分级以防火防灾：

### 🔴 Level 2: High Risk (Requires User Clarification)
You **MUST** use the `Clarify` tool to get explicit user confirmation before executing these actions:
*   **Heating**: Any `heat` command (hotend or bed). (e.g., "即将加热喷头至 200°C，确认执行吗？")
*   **Printing**: Starting `printer_print.py`.
*   **EEPROM/Factory Reset**: `passthrough "M500"` or `passthrough "M502"`.
*   **Cold Extrusion Override**: `passthrough "M302"`.

### 🟡 Level 1: Medium Risk (Script Enforced)
These commands are safe if used correctly. The scripts have built-in protections:
*   **Extrude/Retract**: `extrude`. The script will automatically query `M105` first and block if hotend < 170°C.

### 🟢 Level 0: Safe (Execute Directly)
These actions pose no physical risk:
*   **All Queries**: `printer_read.py status`, `info`, `progress`.
*   **Movement**: `move`. The script enforces `--max-x`, `--max-y`, `--max-z` bounds.
*   **Stopping**: `cool` (turn off heaters), `estop` (M112).

## Helper Scripts / 辅助脚本

All scripts are pure Python 3 stdlib. `SKILL_DIR` is the directory containing this SKILL.md.

### 1. Status Read / 状态查询
```bash
# Get full status (Temperature, Position, Endstops) in JSON
python3 SKILL_DIR/scripts/printer_read.py status --json

# Get firmware info
python3 SKILL_DIR/scripts/printer_read.py info
```

### 2. Motion & Control / 运动与控制
```bash
# Move (Relative). Set max bounds to prevent crashes.
python3 SKILL_DIR/scripts/printer_write.py move --z 10 --relative --max-z 380

# Home axes
python3 SKILL_DIR/scripts/printer_write.py home --axes X Y

# Heat (Requires Clarification)
python3 SKILL_DIR/scripts/printer_write.py heat --hotend 200 --bed 60

# Extrude (Blocked if hotend < 170C)
python3 SKILL_DIR/scripts/printer_write.py extrude --mm 10
```

### 3. Print File / 打印文件
```bash
# Stream a G-code file using FIFO
python3 SKILL_DIR/scripts/printer_print.py /path/to/benchy.gcode
```

---
name: 3d-printer
description: "Generic 3D printer control via G-code over TCP/serial. Query status, send commands, manage prints. 通用 3D 打印机控制，通过 G-code 通信，支持状态查询、命令发送和打印管理。"
version: 1.4.0
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
python3 /opt/data/skills/make/3d-printer/scripts/printer_read.py status --json
```
This provides the baseline state (current temp, position, endstops) to ensure the printer is ready.

## Safety Tiers / 安全权限分级

You must follow this tiered safety system to prevent hardware damage or fire.

你必须遵守以下安全分级以防火防灾：

### 🔴 Level 2: High Risk (Requires User Clarification)
You **MUST** use the `Clarify` tool to get explicit user confirmation before executing these actions:
*   **Heating**: Any `heat` command (hotend or bed).
*   **Printing**: Starting `printer_print.py`.
*   **EEPROM/Factory Reset**: `passthrough "M500"` or `passthrough "M502"`.

### 🟡 Level 1: Medium Risk (Script Enforced)
*   **Extrude/Retract**: `extrude`. The script will automatically block if hotend < 170°C.

### 🟢 Level 0: Safe (Execute Directly)
*   **All Queries**: `printer_read.py status`, `info`, `progress`, `bounds`.
*   **Movement**: `move`. The script enforces `--max-x`, `--max-y`, `--max-z` bounds automatically from `.env`.
*   **Stopping**: `cool` (turn off heaters), `estop` (M112).

## Helper Scripts / 辅助脚本

**CRITICAL RULE**: You MUST use the absolute path `/opt/data/skills/make/3d-printer/scripts/` when running these scripts. Do NOT use relative paths.

### 1. Status Read / 状态查询
```bash
# Query full status (temperature, position, endstops)
python3 /opt/data/skills/make/3d-printer/scripts/printer_read.py status --json

# Query bounds (read from .env)
python3 /opt/data/skills/make/3d-printer/scripts/printer_read.py bounds --json
```

### 2. Motion & Control / 运动与控制
```bash
# Note: Do NOT pass --max-x/y/z manually. The script handles bounds internally.
python3 /opt/data/skills/make/3d-printer/scripts/printer_write.py move --x 10 --y 10 --f 3000
```

### 3. Print File / 打印文件
```bash
python3 /opt/data/skills/make/3d-printer/scripts/printer_print.py /path/to/benchy.gcode
```

## Environment Variables / 环境变量配置

The skill reads connection and safety boundaries from the local `.env` file in the skill root directory:
*   `PRINTER_HOST` / `PRINTER_PORT`: Printer network address.
*   `PRINTER_MAX_X`, `PRINTER_MAX_Y`, `PRINTER_MAX_Z`: The physical build volume.

技能从根目录下的 `.env` 读取连接和安全边界配置。

## Unknown Printer Safety / 未知机型安全防范

**CRITICAL RULE**: Before executing any `move` command, you MUST know the physical build volume limits. Always follow this strict priority order:

**极重要规则**：在执行任何 `move` 指令前，你必须先知道物理打印范围限制。请始终遵循以下严格的优先级顺序：

1. **Read from Environment / 优先读取环境变量**：
   Check if `PRINTER_MAX_X`, `PRINTER_MAX_Y`, and `PRINTER_MAX_Z` are defined in the environment or the local `.env` file. If they are present, **use them immediately**. DO NOT ask the user for dimensions if environment variables are set.
   检查环境变量或本地 `.env` 文件中是否定义了 `PRINTER_MAX_X` 等参数。如果有，**立刻使用它们**。**如果环境变量已设置，绝对禁止弹窗询问用户尺寸。**

2. **Check Loaded Skills / 检查已加载的技能**：
   If environment variables are missing, check your loaded context (e.g., the `anet-a8` skill) for the build volume.
   如果环境变量缺失，检查你已加载的上下文（例如 `anet-a8` 技能）中的打印范围。

3. **Ask the User (Fail-Fast) / 询问用户（快速失败）**：
   ONLY IF you cannot find the dimensions in the environment OR in your loaded skills, use the `Clarify` tool to ask the user for the maximum X, Y, Z build volume.
   **只有**在环境变量和已加载技能中都找不到尺寸时，才使用 `Clarify` 工具询问用户最大 X、Y、Z 打印范围。

**How to check bounds / 如何查询边界**:
If the user asks for the maximum build volume, you MUST run `python3 /opt/data/skills/make/3d-printer/scripts/printer_read.py bounds --json` to get the exact values from the environment. DO NOT answer from memory.

**如何查询边界**：
如果用户询问最大打印范围，你**必须**运行 `printer_read.py bounds --json` 来从环境中获取精确值。**绝对禁止**凭记忆回答。

## Connection Handling / 连接处理规则

1. **Trust the Scripts / 信任脚本**: The Python scripts automatically read the `PRINTER_HOST` and `PRINTER_PORT` from the environment. You do NOT need to explicitly pass `--host` or `--port` unless the user specifically asks you to connect to a different printer.
2. **Ignore Shell Echo / 忽略 Shell 回显**: Do NOT use `echo $PRINTER_HOST` to verify the environment. Shell sessions may not inherit the environment variables, but the Python scripts WILL read them correctly.
3. **Handling Connection Errors / 处理连接失败**: If a script returns a `ConnectionError`, use the `Clarify` tool to ask the user for the correct IP/Port, and then use `--host` and `--port` for that specific session.

## Troubleshooting Rules / 异常处理铁律

If a `Terminal` tool call returns an error, you MUST report the EXACT raw error output to the user.
DO NOT guess or invent environmental issues (like "Docker daemon down", "files missing", or "network disconnected").
Just show the raw error message and ask the user to check it.

如果 `Terminal` 工具调用返回错误，你**必须**将终端的原始报错信息原样回复给用户。
**绝对禁止**自己脑补、猜测系统环境崩溃、文件丢失或网络断开。
只需展示原始错误信息，并请用户检查。
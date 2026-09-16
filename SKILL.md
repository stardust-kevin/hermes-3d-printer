---
name: 3d-printer
description: "Generic 3D printer control via G-code over TCP/serial. Query status, send commands, manage prints. 通用 3D 打印机控制，通过 G-code 通信，支持状态查询、命令发送和打印管理。"
version: 1.0.0
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

Send G-code to any Marlin/RepRap-style 3D printer over TCP or serial. This skill provides the generic communication layer, safety framework, and error handling. Printer-specific parameters (build volume, temperatures, wiring) are provided by child skills.

通过 TCP 或串口向任何使用 Marlin/RepRap 风格协议的 3D 打印机发送 G-code。本 skill 提供通用通信层、安全框架和异常处理；具体打印机型号的参数（打印范围、温度、接线）由子 skill 提供。

## When to use / 适用场景

Use when the user mentions / 用户提到以下内容时使用：

**English triggers:**
- "3D printer", "printer", "print"
- "printer status", "query printer"
- "send gcode", "send G-code"
- "start print", "pause", "resume", "cancel print"
- "home", "G28", "calibrate"

**中文触发词：**
- "3D 打印机"、"打印机"、"打印"
- "查询打印机状态"、"打印机状态"
- "发送 G-code"、"发送 gcode"
- "开始打印"、"暂停"、"恢复"、"取消打印"
- "归零"、"回原点"、"G28"

**Not for / 不适用于:**
- Slicing — use a dedicated slicing skill / 切片——使用专门的切片 skill
- Firmware or EEPROM modification — high risk, requires explicit user confirmation / 修改固件或 EEPROM——风险极高，需用户明确确认

## Architecture / 架构说明

This is the **generic layer**. It does not bind to a specific printer model. Model-specific skills (e.g. `anet-a8`) are child skills that reference this layer via `requires_skills` and overlay hardware parameters and safety rules.

本 skill 是**通用层**，不绑定具体打印机。具体型号的 skill（如 `anet-a8`）作为子 skill，通过 `requires_skills` 引用本层，叠加硬件参数和安全规则。

```
3d-printer/                 # Generic layer / 通用层（本文件）
├── SKILL.md
├── scripts/
│   └── printer_control.py  # Generic comms script / 通用通信脚本
├── references/
│   ├── gcode-universal.md  # Universal G-code reference / 通用 G-code 参考
│   └── troubleshooting.md  # Universal error handling / 通用异常处理
└── anet-a8/                # Child skill / 子 skill
    └── SKILL.md
```

## Prerequisites / 前置条件

- Python 3 (stdlib `socket` is enough, no extra dependencies) / Python 3（标准库 `socket` 即可，无需额外依赖）
- Printer controller (ESP3D, OctoPrint, Moonraker, etc.) reachable on the network / 打印机控制器（ESP3D、OctoPrint、Moonraker 等）已接入网络
- `PRINTER_HOST` environment variable set (child skills may override with `A8_ESP3D_HOST` etc.) / `PRINTER_HOST` 环境变量已设置（子 skill 可覆盖为 `A8_ESP3D_HOST` 等）

## Setup / 配置

Set in `${HERMES_HOME:-~/.hermes}/.env` / 在 `${HERMES_HOME:-~/.hermes}/.env` 中设置：

```bash
PRINTER_HOST=192.168.1.100
PRINTER_PORT=8888
```

If a child skill uses a different env var name (e.g. `A8_ESP3D_HOST`), the child skill's declaration takes precedence.

如果子 skill 使用不同的环境变量名（如 `A8_ESP3D_HOST`），以子 skill 的声明为准。

## Safety Rules / 安全铁律

**These rules apply to all 3D printers and must be followed. / 以下规则适用于所有 3D 打印机，必须遵守。**

1. **Confirm before heating / 加热前必须确认**：Any `M104`, `M109`, `M140`, `M190` command must be described to the user first, and wait for explicit "confirm" or "确认" before sending. / 任何 `M104`、`M109`、`M140`、`M190` 命令，必须先向用户描述动作，等待明确回复"确认"或"confirm"后再发送。
2. **Confirm before starting a print / 开始打印前必须确认**：Describe the file and temperatures, wait for confirmation. / 描述文件名和温度，等待确认。
3. **Confirm before cancel/emergency stop / 取消/急停前必须确认**：`M112` or print cancel must be user-initiated. / `M112` 或取消打印必须由用户主动发起。
4. **Stop immediately on error or abnormal temperature / 打印机报错或温度异常时立即停止**：Report the raw response to the user. / 把原始响应报告给用户。
5. **Never send `M502` (factory reset) or `M500` (save EEPROM) without explicit confirmation / 禁止在未确认的情况下发送 `M502`（恢复出厂）或 `M500`（保存 EEPROM）。**
6. **Coordinate range check / 坐标范围检查**：Before any `G1` move, verify coordinates are within the build volume declared by the child skill. Out-of-range moves cause crashes. / 发送 `G1` 移动命令前，确认坐标在子 skill 声明的打印范围内。超出范围会导致撞机。
7. **Confirm hotend ≥ 180°C before extruding / 挤出前确认喷头已加热到 180°C 以上**：Cold extrusion damages the extruder gear or clogs the nozzle. / 冷挤出会损坏挤出机齿轮或堵塞喷头。
8. **Never leave long prints unattended / 长打印任务不要无人看管**：Even with thermal runaway protection, mechanical failure can cause fire. / 即使有热失控保护，机械故障仍可能引发火灾。

## Helper Script / 辅助脚本

`SKILL_DIR` is the directory containing this SKILL.md. The script wraps TCP communication and error handling, and **depends only on Python 3 stdlib**.

`SKILL_DIR` 是本 SKILL.md 所在目录。脚本封装了 TCP 通信和错误处理，**仅依赖 Python 3 标准库**。

```bash
# Query temperature / 查询温度
python3 SKILL_DIR/scripts/printer_control.py query

# Send a single G-code / 发送单条 G-code
python3 SKILL_DIR/scripts/printer_control.py gcode "G28"

# Send multiple commands / 发送多条
python3 SKILL_DIR/scripts/printer_control.py gcode "G28" "G1 X10 Y10 F3000"

# Query print progress / 查询打印进度
python3 SKILL_DIR/scripts/printer_control.py progress
```

If `uv` is available, use `uv run python` instead of `python3`.

如果环境有 `uv`，可以用 `uv run python` 替代 `python3`。

## Quick Start / 快速开始

```bash
# 1. Query status / 查询状态
python3 SKILL_DIR/scripts/printer_control.py query

# 2. Home (requires confirmation) / 归零（需确认）
python3 SKILL_DIR/scripts/printer_control.py gcode "G28"

# 3. Turn off heaters / 关闭加热
python3 SKILL_DIR/scripts/printer_control.py gcode "M104 S0" "M140 S0"
```

## Verification / 验证

After loading this skill, run these checks to confirm the environment is ready.

加载本 skill 后，运行以下检查确认环境就绪。

### Quick self-test / 快速自检

```bash
PRINTER_HOST=<your-host> python3 SKILL_DIR/scripts/printer_control.py selftest

## G-code Reference / 通用 G-code 参考

| Purpose / 用途 | G-code | Notes / 说明 |
|---|---|---|
| Temperature report / 温度报告 | `M105` | Returns `ok T:xx /xx B:xx /xx` |
| Position report / 位置报告 | `M114` | Returns `X:... Y:... Z:... E:...` |
| Firmware info / 固件信息 | `M115` | Returns firmware version and capabilities |
| Home all axes / 全轴归零 | `G28` | **Confirm first / 需确认** |
| Home single axis / 单轴归零 | `G28 X` / `G28 Y` / `G28 Z` | **Confirm first / 需确认** |
| Move / 移动 | `G1 X10 Y10 Z5 F3000` | F = feedrate mm/min |
| Set hotend temp (wait) / 设置喷头温度（等待） | `M109 S200` | **Confirm first / 需确认** |
| Set bed temp (wait) / 设置热床温度（等待） | `M190 S60` | **Confirm first / 需确认** |
| Turn off hotend / 关闭喷头 | `M104 S0` | |
| Turn off bed / 关闭热床 | `M140 S0` | |
| Turn off fan / 关闭风扇 | `M107` | |
| Disable motors / 关闭电机 | `M84` | |
| Emergency stop / 急停 | `M112` | **User-initiated only / 仅用户主动要求** |
| Resume SD print / 恢复 SD 打印 | `M24` | |
| Pause SD print / 暂停 SD 打印 | `M25` | |
| SD print status / SD 卡状态 | `M27` | Returns print progress |

## Coordinate System / 坐标系

All Marlin-style printers use a **Cartesian coordinate system**:

所有 Marlin 风格打印机使用**笛卡尔坐标系**：

- Origin `(0, 0, 0)` is usually the front-left corner of the bed / 原点 `(0, 0, 0)` 通常在工作台左前角
- X points right, Y points back, Z points up / X 轴向右，Y 轴向后，Z 轴向上
- **The exact build volume is declared by the child skill** — do not assume / **具体打印范围由子 skill 声明**，不要假设

Always verify coordinates are in range before sending `G1`.

发送 `G1` 前必须确认坐标在范围内。

## Error Handling / 通用异常处理

| Symptom / 现象 | Cause / 原因 | Action / 处理 |
|---|---|---|
| `ConnectionRefusedError` | Controller offline or wrong IP / 控制器离线或 IP 错误 | 1. `ping $PRINTER_HOST` 2. `nc -zv $PRINTER_HOST $PRINTER_PORT` (Linux/macOS) or `Test-NetConnection` (Windows) 3. Check controller power / 检查控制器是否上电 |
| `socket.timeout` | Network unreachable or port closed / 网络不可达或端口未开放 | Check WiFi, firewall, controller port config / 检查 WiFi、防火墙、控制器端口配置 |
| Returns `ok` but temperature unchanged / 返回 `ok` 但温度不变 | Baud rate mismatch / 波特率不匹配 | Verify controller baud matches printer / 确认控制器波特率与打印机一致 |
| Garbled response / 响应乱码 | Baud rate mismatch / 波特率不匹配 | Check controller serial settings / 检查控制器串口设置 |
| No response after `M112` / `M112` 后无响应 | Expected (printer halted) / 预期行为（打印机已停） | Power-cycle the printer / 断电重启打印机 |
| `Error:Printer halted` | Firmware aborted print / 固件中止打印 | Check temperature readings, report to user / 检查温度读数，报告用户 |
| Response starts with `echo:` / 响应含 `echo:` 开头 | Controller echo / 控制器回显 | Script filters automatically / 脚本自动过滤，无需处理 |
| `Error:Thermal Runaway` | Thermal protection triggered / 热失控保护触发 | **Power off immediately / 立即断电**，check thermistor and heater / 检查热敏电阻和加热棒 |

**On ANY error: stop, report the raw response to the user, do NOT retry blindly.**

**任何异常：停止操作，把原始响应报告给用户，不要盲目重试。**

## Notes / 注意事项

- **Controller API differences / 控制器 API 差异**：ESP3D is raw TCP passthrough; OctoPrint has a REST API; Moonraker uses JSON-RPC. The script assumes raw TCP (ESP3D-style). / ESP3D 是原始 TCP 透传；OctoPrint 有 REST API；Moonraker 有 JSON-RPC。本 skill 的脚本默认假设原始 TCP（ESP3D 风格）。
- **Single connection / 单连接**：Raw TCP accepts one connection at a time. Close sockets promptly. / 原始 TCP 端口一次只接受一个连接，用完及时关闭。
- **No auth by default / 默认可能无认证**：Enable auth or firewall the port. / 建议启用认证或防火墙限制。
- **Network reliability / 网络可靠性**：WiFi raw TCP may drop packets. For long prints, prefer SD-card printing. / WiFi 原始 TCP 可能丢包，长打印任务建议用 SD 卡打印。
- **Child skill overlay / 子 skill 覆盖**：Printer-specific parameters are provided by child skills. Load this skill, then load the matching child skill for full context. / 具体打印机型号的参数由子 skill 提供。加载本 skill 后，应继续加载对应的子 skill 获取完整上下文。

## Platform Notes / 平台说明

- **Linux / macOS**: Script runs natively. `nc` is available for port testing. / 脚本直接可用，`nc` 用于端口测试。
- **Windows**: Script runs natively (Python 3 stdlib only). `nc` is not available — use PowerShell instead / 脚本可用（仅依赖 Python 3 标准库）。`nc` 不可用，改用 PowerShell：

  ```powershell
  Test-NetConnection -ComputerName $env:PRINTER_HOST -Port $env:PRINTER_PORT
  ```

## Changelog / 变更记录

- 2026-09-16: Initial release / 初始版本

## License / 许可

MIT License. See repository root for details.

MIT 协议。详见仓库根目录。

## Related Skills / 关联 skill

- `anet-a8` — Anet A8 specific parameters / 爱能特 A8 专属参数
- (Future / 未来可扩展：`prusa-mk3`, `ender-3`, etc.)

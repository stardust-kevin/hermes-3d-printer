---
name: anet-a8
description: "Anet A8 specific parameters and safety rules. Inherits generic 3D printer control from 3d-printer. 爱能特 A8 专属参数和安全规则，继承通用 3D 打印机控制层。"
version: 1.2.0
author: kevin
license: MIT
date: 2026-09-16
platforms: [linux, macos, windows]
prerequisites:
  env_vars: [A8_ESP3D_HOST]
  commands: [python3]
metadata:
  hermes:
    tags: [3D-Printing, Anet-A8, ESP3D, Marlin, Hardware, 3D打印, 爱能特]
    homepage: https://github.com/stardust-kevin/hermes-3d-printer
    requires_skills: [3d-printer]
    related_skills: []
---

# Anet A8 Control / 爱能特 A8 控制

Anet A8 specific parameters, hardware mapping, and safety rules. This skill **inherits** the generic communication layer, safety framework, and error handling from `3d-printer`. Load that skill first if it is not already loaded.

爱能特 A8 专属参数、硬件映射和安全规则。本 skill **继承** `3d-printer` 的通用通信层、安全框架和异常处理。如果尚未加载通用层，请先加载。

## System Identity / 系统身份

**You are controlling an Anet A8 printer.**
The maximum build volume (physical limits) of this machine is:
*   **X: 0 to 220 mm**
*   **Y: 0 to 220 mm**
*   **Z: 0 to 380 mm**

**CRITICAL**: If the user requests a move to a coordinate exceeding these limits, you must immediately reject it and inform the user. DO NOT ask the user for the dimensions. You already know the dimensions from this document.

**你正在控制一台爱能特 A8 打印机。**
该机器的最大打印范围（物理极限）是：
*   **X: 0 到 220 mm**
*   **Y: 0 到 220 mm**
*   **Z: 0 到 380 mm**

**极重要**：如果用户要求移动的坐标超出这些限制，你必须立刻拒绝并告知用户。**绝对不要**去问用户尺寸，因为你从这份文档里已经知道尺寸了。

## When to use / 适用场景

Use when the user mentions / 用户提到以下内容时使用：

**English triggers:**
- "Anet A8", "A8", "爱能特"
- "A8 printer", "my A8"
- "A8 temperature", "A8 status"

**中文触发词：**
- "爱能特 A8"、"A8"、"爱能特"
- "我的 A8"、"A8 打印机"
- "A8 温度"、"A8 状态"

**Not for / 不适用于:**
- Generic 3D printer questions without A8 context — use `3d-printer` / 无 A8 上下文的通用问题——使用 `3d-printer`
- Slicing / 切片

## Hardware Context / 硬件上下文

| 项目 / Item | 值 / Value |
|---|---|
| 打印机 / Printer | Anet A8（原厂 v1.0-v1.5 主板，Marlin 固件） |
| 桥接 / Bridge | ESP8266/ESP32 + ESP3D 固件，TCP 端口 8888 |
| 波特率 / Baud rate | 115200（默认，必须与打印机一致） |
| 耗材 / Filament | PLA（喷头 200-210°C，热床 60°C） |
| 供电 / Power | 12V DC |

### Motion System / 运动系统

| 轴 / Axis | 电机数 / Motors | 运动方式 / Motion | 限位开关 / Endstop | G-code |
|---|---|---|---|---|
| X | 1 | 喷头左右移动 / Hotend left-right | X_MIN | `G1 X...` |
| Y | 1 | **热床前后移动** / **Bed forward-back** | Y_MIN | `G1 Y...` |
| Z | 2（同步） / 2 (sync) | 喷头上下移动 / Hotend up-down | Z_MIN | `G1 Z...` |
| E | 1 | 耗材挤出 / Filament extrusion | 无 / None | `G1 E...` |

**Important / 重要**：A8 的 Y 轴移动的是**热床**，不是喷头。`G28` 归零时，热床会向前移动触碰 Y 限位开关。

**Important / 重要**: On the A8, the Y axis moves the **bed**, not the hotend. During `G28`, the bed moves forward to trigger the Y endstop.

### Heating System / 加热系统

| 组件 / Component | 控制 G-code / Control | 读取 G-code / Read |
|---|---|---|
| 热床加热棒 / Bed heater | `M140 S<temp>` / `M190 S<temp>` | `M105`（B: 字段） |
| 喷头加热棒 / Hotend heater | `M104 S<temp>` / `M109 S<temp>` | `M105`（T: 字段） |
| 热敏电阻 / Thermistors | — | `M105` |

### Coordinate System / 坐标系

- Origin `(0, 0, 0)` is the **front-left corner** of the bed / 原点 `(0, 0, 0)` 在工作台**左前角**
- X points right / X 轴向右
- Y points back / Y 轴向后
- Z points up / Z 轴向上

**Valid range / 有效范围**: X ∈ [0, 220], Y ∈ [0, 220], Z ∈ [0, 380]

Any `G1` move outside this range will crash the printer.

任何超出此范围的 `G1` 移动都会导致撞机。

## Additional Safety Rules / 额外安全规则

These rules are **in addition to** the generic safety rules in `3d-printer`. Both sets apply.

以下规则是 `3d-printer` 通用安全规则的**补充**，两套规则同时生效。

1. **A8 stock firmware has NO thermal runaway protection.** Never leave a heated printer unattended. / **A8 原厂固件没有热失控保护。** 加热时绝不能无人看管。
2. **R52/R53 resistor removal is irreversible.** On v1.5 and older boards, these resistors must be removed for ESP serial to work. Confirm board version before modifying. / **R52/R53 电阻拆除不可逆。** v1.5 及更早主板必须拆除这两个电阻才能让 ESP 串口工作。修改前确认主板版本。
3. **Y axis moves the bed.** Before any Y move, ensure nothing is blocking the bed's path. / **Y 轴移动热床。** 任何 Y 移动前，确保热床路径上无阻挡。
4. **Z axis has two motors.** If one fails, the gantry tilts and the nozzle crashes. Check both motors after any Z issue. / **Z 轴有两个电机。** 如果一个失效，龙门倾斜，喷头撞机。Z 轴异常后检查两个电机。
5. **PLA only by default.** Do not exceed 210°C hotend / 60°C bed without confirming the printer has an all-metal hotend. / **默认仅限 PLA。** 超过 210°C 喷头 / 60°C 热床前，确认打印机已改装全金属喷头。

## CRITICAL Safety Reminders / 强制执行的安全规范

When sending movement commands via `printer_write.py`, you MUST strictly follow these rules:

在通过 `printer_write.py` 发送移动指令时，你必须严格遵守以下规则：

1. **ALWAYS pass the bounds / 必须传入边界**：
   Every time you call `printer_write.py move`, you **MUST** explicitly pass `--max-x 220 --max-y 220 --max-z 380`.
   每次调用 `move` 时，你**必须**显式传入 `--max-x 220 --max-y 220 --max-z 380`。
   *Example*: `python3 .../printer_write.py move --x 10 --y 10 --max-x 220 --max-y 220 --max-z 380`

2. **Reject absolute out-of-bounds immediately / 立刻拒绝绝对越界**：
   Before executing, calculate the target position. If the user asks to move to a position exceeding X:220, Y:220, or Z:380, you **MUST REJECT** the request immediately and inform the user. **DO NOT RUN THE SCRIPT**.
   在执行前，先计算目标位置。如果用户要求的位置超出了 X:220, Y:220, Z:380，你**必须立刻拒绝**，并告诉用户越界，**绝对禁止运行脚本**。

3. **CRITICAL: Verify relative moves / 极度重要：验证相对移动**：
   The `--max-x/y/z` arguments in the script only check the *distance* of a relative move, NOT the final absolute position.
   If you use `--relative` (e.g., "move right 10mm"), you **MUST** first query the current position using `printer_read.py status --json`.
   Calculate `current_X + relative_X`. If the result exceeds 220 (or Y>220, Z>380), you **MUST REJECT** the relative move.
   脚本中的 `--max-x/y/z` 参数只检查相对移动的*距离*，不检查最终的绝对位置。
   如果你使用 `--relative`（例如“向右移动 10mm”），你**必须**先调用 `printer_read.py status --json` 查询当前位置。
   计算 `当前X + 相对X`。如果结果超过 220（或 Y>220, Z>380），你**必须拒绝**该相对移动。

## A8 Print Sequence / A8 打印序列

### Start / 开始

```gcode
M190 S60      ; wait for bed / 等待热床
M109 S200     ; wait for hotend / 等待喷头
G28           ; home all axes / 全轴归零
G29           ; auto bed leveling (if equipped) / 自动调平（如有）
G1 Z5 F3000   ; lift 5mm / 抬升 5mm
G92 E0        ; reset extruder / 重置挤出机
G1 X10 Y10 F3000  ; move to start position / 移到起始位置
```

### End / 结束

```gcode
M104 S0       ; hotend off / 关闭喷头
M140 S0       ; bed off / 关闭热床
M107          ; fan off / 关闭风扇
G28 X0 Y0     ; home X/Y / X/Y 归零
M84           ; motors off / 关闭电机
```

### Emergency / 紧急

```gcode
M112          ; emergency stop / 急停
```

**After `M112`, power-cycle the printer. / `M112` 后需断电重启打印机。**

## Common A8 Values / A8 常用参数

| Parameter / 参数 | Value / 值 |
|---|---|
| Nozzle diameter / 喷嘴直径 | 0.4mm（默认） |
| Filament diameter / 耗材直径 | 1.75mm |
| Max hotend temp / 喷头最高温 | 240°C（原厂热敏电阻上限） |
| Max bed temp / 热床最高温 | 100°C（原厂） |
| PLA hotend / PLA 喷头 | 200-210°C |
| PLA bed / PLA 热床 | 60°C |
| Travel speed / 移动速度 | 3000-6000 mm/min |
| Print speed / 打印速度 | 1800-3600 mm/min |

## A8-specific Troubleshooting / A8 专属异常

These are in addition to the generic troubleshooting in `3d-printer`.

以下是 `3d-printer` 通用异常处理的补充。

| Symptom / 现象 | Cause / 原因 | Fix / 处理 |
|---|---|---|
| ESP module not responding / ESP 模块无响应 | R52/R53 not removed / 未拆除 R52/R53 | Check board version, remove resistors / 检查主板版本，拆除电阻 |
| Garbled serial response / 串口响应乱码 | Wrong baud / 波特率错误 | Set ESP3D to 115200 / 将 ESP3D 设为 115200 |
| Z axis tilts during print / 打印中 Z 轴倾斜 | One Z motor failed / 一个 Z 电机失效 | Check both Z motor connections / 检查两个 Z 电机接线 |
| Bed crashes into frame / 热床撞框架 | Y coordinate out of range / Y 坐标超范围 | Verify Y ∈ [0, 220] / 确认 Y ∈ [0, 220] |
| Hotend temp reads 0 / 喷头温度读数为 0 | Thermistor disconnected / 热敏电阻断开 | **Power off**, check thermistor wiring / **断电**，检查热敏电阻接线 |
| Bed temp reads 0 / 热床温度读数为 0 | Bed thermistor disconnected / 热床热敏电阻断开 | **Power off**, check bed thermistor / **断电**，检查热床热敏电阻 |

## Platform Notes / 平台说明

- **Linux / macOS**: Script runs natively. `nc` is available for port testing. / 脚本直接可用，`nc` 用于端口测试。
- **Windows**: Script runs natively (Python 3 stdlib only). `nc` is not available — use PowerShell instead / 脚本可用（仅依赖 Python 3 标准库）。`nc` 不可用，改用 PowerShell：

  ```powershell
  Test-NetConnection -ComputerName $env:A8_ESP3D_HOST -Port $env:A8_ESP3D_PORT
  ```

## Changelog / 变更记录

- 2026-09-16: Initial release / 初始版本
- 2026-10-24: Split scripts into read/write/print and refactored safety tiers. / 拆分脚本为 read/write/print，重构安全分级。
- 2026-11-09: Added System Identity block and simplified bounds handling. / 增加系统身份声明并简化边界处理。

## License / 许可

MIT License. See repository root for details.

MIT 协议。详见仓库根目录。

## Related Skills / 关联 skill

- `3d-printer` — Generic 3D printer control layer / 通用 3D 打印机控制层
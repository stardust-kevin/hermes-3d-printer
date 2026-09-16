---
name: anet-a8
description: "Anet A8 specific parameters and safety rules. Inherits generic 3D printer control from 3d-printer. 爱能特 A8 专属参数和安全规则，继承通用 3D 打印机控制层。"
version: 1.0.0
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
| 打印范围 / Build volume | **220 × 220 × 380 mm**（22cm × 22cm × 38cm） |
| 桥接 / Bridge | ESP8266/ESP32 + ESP3D 固件，TCP 端口 8888 |
| 接线 / Wiring | ESP TX→A8 RX, ESP RX→A8 TX, GND→GND, VCC→3.3V, CH_PD→3.3V |
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

## Setup / 配置

Set in `${HERMES_HOME:-~/.hermes}/.env` / 在 `${HERMES_HOME:-~/.hermes}/.env` 中设置：

```bash
A8_ESP3D_HOST=192.168.1.100
A8_ESP3D_PORT=8888
```

If the generic `PRINTER_HOST` is already set and points to the A8, you can skip this.

如果通用层的 `PRINTER_HOST` 已设置并指向 A8，可跳过此步。

## Additional Safety Rules / 额外安全规则

These rules are **in addition to** the generic safety rules in `3d-printer`. Both sets apply.

以下规则是 `3d-printer` 通用安全规则的**补充**，两套规则同时生效。

1. **A8 stock firmware has NO thermal runaway protection.** Never leave a heated printer unattended. / **A8 原厂固件没有热失控保护。** 加热时绝不能无人看管。
2. **R52/R53 resistor removal is irreversible.** On v1.5 and older boards, these resistors must be removed for ESP serial to work. Confirm board version before modifying. / **R52/R53 电阻拆除不可逆。** v1.5 及更早主板必须拆除这两个电阻才能让 ESP 串口工作。修改前确认主板版本。
3. **Y axis moves the bed.** Before any Y move, ensure nothing is blocking the bed's path. / **Y 轴移动热床。** 任何 Y 移动前，确保热床路径上无阻挡。
4. **Z axis has two motors.** If one fails, the gantry tilts and the nozzle crashes. Check both motors after any Z issue. / **Z 轴有两个电机。** 如果一个失效，龙门倾斜，喷头撞机。Z 轴异常后检查两个电机。
5. **PLA only by default.** Do not exceed 210°C hotend / 60°C bed without confirming the printer has an all-metal hotend. / **默认仅限 PLA。** 超过 210°C 喷头 / 60°C 热床前，确认打印机已改装全金属喷头。

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

## Verification / 验证

After loading this skill, run the generic self-test with A8-specific env vars.

加载本 skill 后，用 A8 专属环境变量运行通用自检。

```bash
# Self-test / 自检
A8_ESP3D_HOST=192.168.1.100 python3 SKILL_DIR/../scripts/printer_control.py selftest

# Query temperature / 查询温度
A8_ESP3D_HOST=192.168.1.100 python3 SKILL_DIR/../scripts/printer_control.py query

# Check endstops / 检查限位开关
A8_ESP3D_HOST=192.168.1.100 python3 SKILL_DIR/../scripts/printer_control.py gcode "M119"
```

### Checklist / 检查清单

- [ ] `A8_ESP3D_HOST` is set and reachable / `A8_ESP3D_HOST` 已设置且可达
- [ ] `selftest` reports all PASS / `selftest` 全部通过
- [ ] `M119` returns endstop status / `M119` 返回限位状态
- [ ] `M115` returns firmware version / `M115` 返回固件版本
- [ ] Temperature readings are not 0 / 温度读数不为 0

## Notes / 注意事项

- **Generic layer must be loaded first.** This skill assumes `3d-printer` is available. If not, load it manually with `skill_view("3d-printer")`.
- **通用层必须先加载。** 本 skill 假设 `3d-printer` 可用。如果没有，手动用 `skill_view("3d-printer")` 加载。
- **A8 is an open-frame printer.** No enclosure. Drafts, AC, and pets can affect print quality.
- **A8 是开放式框架打印机。** 无外罩。气流、空调和宠物会影响打印质量。
- **A8 v1.0-v1.5 boards are 8-bit.** They have limited processing power. Complex G-code may cause stuttering.
- **A8 v1.0-v1.5 主板是 8 位。** 处理能力有限。复杂 G-code 可能导致卡顿。
- **Always verify build volume before moving.** 220×220×380mm is the maximum. Do not assume.
- **移动前始终确认打印范围。** 220×220×380mm 是最大值，不要假设。

## Platform Notes / 平台说明

- **Linux / macOS**: Script runs natively. `nc` is available for port testing. / 脚本直接可用，`nc` 用于端口测试。
- **Windows**: Script runs natively (Python 3 stdlib only). `nc` is not available — use PowerShell instead / 脚本可用（仅依赖 Python 3 标准库）。`nc` 不可用，改用 PowerShell：

  ```powershell
  Test-NetConnection -ComputerName $env:A8_ESP3D_HOST -Port $env:A8_ESP3D_PORT
  ```

## Changelog / 变更记录

- 2026-09-16: Initial release / 初始版本

## License / 许可

MIT License. See repository root for details.

MIT 协议。详见仓库根目录。

## Related Skills / 关联 skill

- `3d-printer` — Generic 3D printer control layer / 通用 3D 打印机控制层

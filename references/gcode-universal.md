# Universal G-code Reference / 通用 G-code 参考

This document covers G-code commands supported by most Marlin/RepRap-style 3D printers. It does **not** cover printer-specific macros or extensions.

本文档涵盖大多数 Marlin/RepRap 风格 3D 打印机支持的 G-code 命令，**不包含**打印机专属宏或扩展。

## G-code Structure / G-code 结构

```
G1 X10 Y20 Z0.3 F3000 E1.5 ; comment
```

| Part / 部分 | Meaning / 含义 |
|---|---|
| `G1` | Command / 命令 |
| `X10 Y20 Z0.3` | Parameters / 参数 |
| `F3000` | Feedrate in mm/min / 进给速度 |
| `E1.5` | Extruder position / 挤出机位置 |
| `; comment` | Comment, ignored by firmware / 注释，固件忽略 |

## Temperature / 温度

| Command | Purpose / 用途 | Notes / 说明 |
|---|---|---|
| `M104 S<temp>` | Set hotend target, no wait / 设置喷头目标温度，不等待 | Returns immediately / 立即返回 |
| `M109 S<temp>` | Set hotend target, wait / 设置喷头目标温度，等待 | Blocks until reached / 达到温度后返回 |
| `M140 S<temp>` | Set bed target, no wait / 设置热床目标温度，不等待 | Returns immediately / 立即返回 |
| `M190 S<temp>` | Set bed target, wait / 设置热床目标温度，等待 | Blocks until reached / 达到温度后返回 |
| `M104 S0` | Turn off hotend / 关闭喷头 | |
| `M140 S0` | Turn off bed / 关闭热床 | |
| `M105` | Report temperatures / 报告温度 | Returns `ok T:... B:...` |
| `M155 S<sec>` | Auto-report temperatures every N sec / 每 N 秒自动报告温度 | Marlin only |

### M105 Response Format / M105 响应格式

```
ok T:210.5 /210.0 B:60.2 /60.0 @:0 B@:0
```

| Field | Meaning |
|---|---|
| `T:` | Current hotend temp / 当前喷头温度 |
| `/210.0` | Target hotend temp / 喷头目标温度 |
| `B:` | Current bed temp / 当前热床温度 |
| `/60.0` | Target bed temp / 热床目标温度 |
| `@:` | Hotend power (0-255) / 喷头功率 |
| `B@:` | Bed power (0-255) / 热床功率 |

## Motion / 运动

| Command | Purpose / 用途 | Notes / 说明 |
|---|---|---|
| `G0 X Y Z` | Rapid move / 快速移动 | Same as G1 in most firmware / 多数固件等同 G1 |
| `G1 X Y Z F` | Linear move / 直线移动 | F = feedrate mm/min |
| `G1 E<mm> F<rate>` | Extrude / 挤出 | Requires hotend ≥ 180°C / 需喷头 ≥ 180°C |
| `G1 E-<mm> F<rate>` | Retract / 回抽 | |
| `G28` | Home all axes / 全轴归零 | **Requires confirmation / 需确认** |
| `G28 X` | Home X only / 仅归零 X | |
| `G28 Y` | Home Y only / 仅归零 Y | |
| `G28 Z` | Home Z only / 仅归零 Z | |
| `G92 X0 Y0 Z0 E0` | Set position without moving / 不移动设置坐标 | |
| `M114` | Report position / 报告位置 | Returns `X:... Y:... Z:... E:...` |
| `M84` | Disable steppers / 关闭电机 | |
| `M18` | Disable steppers / 关闭电机 | Same as M84 |

### Feedrate Reference / 进给速度参考

| Speed / 速度 | mm/min | Use case / 用途 |
|---|---|---|
| Very slow / 极慢 | 300 | First layer, delicate / 首层、精细 |
| Slow / 慢 | 1200 | Travel over print / 打印上方移动 |
| Normal / 正常 | 3000 | General travel / 一般移动 |
| Fast / 快 | 6000 | Rapid travel / 快速移动 |

## SD Card / SD 卡

| Command | Purpose / 用途 | Notes / 说明 |
|---|---|---|
| `M20` | List SD card / 列出 SD 卡文件 | |
| `M21` | Initialize SD card / 初始化 SD 卡 | |
| `M22` | Release SD card / 释放 SD 卡 | |
| `M23 <file>` | Select file / 选择文件 | |
| `M24` | Start/resume SD print / 开始/恢复 SD 打印 | |
| `M25` | Pause SD print / 暂停 SD 打印 | |
| `M26 S<pos>` | Set SD position / 设置 SD 位置 | |
| `M27` | Report SD print status / 报告 SD 打印状态 | Returns progress / 返回进度 |
| `M28 <file>` | Start write to SD / 开始写入 SD | |
| `M29` | Stop write to SD / 停止写入 SD | |

### M27 Response Format / M27 响应格式

```
SD printing byte 12345/67890
```

Or / 或：

```
Not SD printing
```

## Fans / 风扇

| Command | Purpose / 用途 | Notes / 说明 |
|---|---|---|
| `M106 S<0-255>` | Set fan speed / 设置风扇速度 | 0 = off, 255 = full / 0 = 关，255 = 全速 |
| `M106 S0` | Turn off fan / 关闭风扇 | |
| `M107` | Turn off fan / 关闭风扇 | Same as M106 S0 |

## Firmware Info / 固件信息

| Command | Purpose / 用途 | Notes / 说明 |
|---|---|---|
| `M115` | Firmware info / 固件信息 | Returns version, capabilities / 返回版本和能力 |
| `M503` | Report settings / 报告设置 | Dumps current config / 输出当前配置 |
| `M500` | Save settings to EEPROM / 保存设置到 EEPROM | **Requires confirmation / 需确认** |
| `M501` | Load settings from EEPROM / 从 EEPROM 加载设置 | |
| `M502` | Factory reset / 恢复出厂 | **Requires confirmation / 需确认** |

## Emergency / 紧急

| Command | Purpose / 用途 | Notes / 说明 |
|---|---|---|
| `M112` | Emergency stop / 急停 | **Requires power cycle to recover / 需断电重启** |
| `M410` | Quickstop / 快速停止 | Stops all steppers immediately / 立即停止所有电机 |
| `M0` | Unconditional stop / 无条件停止 | Waits for user / 等待用户 |
| `M1` | Conditional stop / 条件停止 | |

## Common Sequences / 常用序列

### Start a print / 开始打印

```gcode
M190 S60      ; wait for bed / 等待热床
M109 S200     ; wait for hotend / 等待喷头
G28           ; home all / 全轴归零
G29           ; auto bed leveling (if equipped) / 自动调平（如有）
G1 Z5 F3000   ; lift 5mm / 抬升 5mm
```

### End a print / 结束打印

```gcode
M104 S0       ; hotend off / 关闭喷头
M140 S0       ; bed off / 关闭热床
M107          ; fan off / 关闭风扇
G28 X0 Y0     ; home X/Y / X/Y 归零
M84           ; motors off / 关闭电机
```

### Pause and resume / 暂停与恢复

```gcode
M25           ; pause SD print / 暂停 SD 打印
; ... user intervenes / 用户干预 ...
M24           ; resume SD print / 恢复 SD 打印
```

## Error Responses / 错误响应

| Response | Meaning / 含义 |
|---|---|
| `ok` | Command accepted / 命令已接受 |
| `Error:...` | Command rejected / 命令被拒绝 |
| `echo:...` | Controller echo, ignore / 控制器回显，忽略 |
| `Error:Printer halted` | Firmware killed print / 固件中止打印 |
| `Error:Thermal Runaway` | Thermal protection triggered / 热失控保护触发 |
| `busy: processing` | Previous command still running / 上一条命令仍在执行 |
| `Resend: N` | Communication error, resend line N / 通信错误，重发第 N 行 |

## Notes / 注意事项

- **Not all commands are supported by all firmware.** Marlin, RepRapFirmware, Klipper, and Smoothieware each have their own subset. Test before relying on a command.
- **并非所有固件都支持所有命令。** Marlin、RepRapFirmware、Klipper、Smoothieware 各有子集，使用前先测试。
- **`M109`/`M190` block until temperature is reached.** If the heater is broken, the command never returns. Always check temperature response first.
- **`M109`/`M190` 会阻塞直到达到温度。** 如果加热棒损坏，命令永不返回。先检查温度响应。
- **`M112` requires a power cycle.** After emergency stop, the printer will not respond to normal commands until restarted.
- **`M112` 需要断电重启。** 急停后，打印机在重启前不会响应正常命令。
- **Units are millimeters and mm/min.** `G1 X10` means 10mm. `F3000` means 3000mm/min = 50mm/s.
- **单位是毫米和毫米/分钟。** `G1 X10` 表示 10mm。`F3000` 表示 3000mm/min = 50mm/s。

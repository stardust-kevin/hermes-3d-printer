# Anet A8 Specifics / 爱能特 A8 专属细节

Hardware details, wiring, and known quirks specific to the Anet A8. This document supplements the generic `3d-printer` layer and the `anet-a8` skill.

爱能特 A8 的硬件细节、接线和已知问题。本文档补充通用层 `3d-printer` 和 `anet-a8` skill。

## Board Versions / 主板版本

| Version / 版本 | MCU | ESP Serial / ESP 串口 | R52/R53 removal / R52/R53 拆除 | Notes / 说明 |
|---|---|---|---|---|
| v1.0 | ATmega1284P | ❌ Not broken out / 未引出 | Required / 需要 | Earliest boards / 最早批次 |
| v1.1 | ATmega1284P | ❌ Not broken out / 未引出 | Required / 需要 | |
| v1.2 | ATmega1284P | ❌ Not broken out / 未引出 | Required / 需要 | |
| v1.3 | ATmega1284P | ❌ Not broken out / 未引出 | Required / 需要 | |
| v1.4 | ATmega1284P | ⚠️ Partial / 部分引出 | Required / 需要 | |
| v1.5 | ATmega1284P | ✅ Broken out / 已引出 | Required / 需要 | Most common / 最常见 |
| v1.7 | ATmega2560 | ✅ Broken out / 已引出 | Not required / 不需要 | Improved board / 改进版 |

**Important / 重要**: On v1.5 and older, R52 and R53 are 0-ohm resistors that must be **physically removed** to free the serial pins for the ESP module. This is irreversible.

**重要**：v1.5 及更早版本中，R52 和 R53 是 0 欧电阻，必须**物理拆除**才能释放串口引脚给 ESP 模块。此操作不可逆。

## ESP3D Wiring / ESP3D 接线

### Pin Mapping / 引脚映射

| ESP Module Pin / ESP 模块引脚 | A8 Board J3 Pin / A8 主板 J3 引脚 | Notes / 说明 |
|---|---|---|
| TX | RX | ESP transmit → A8 receive / ESP 发送 → A8 接收 |
| RX | TX | ESP receive → A8 transmit / ESP 接收 → A8 发送 |
| GND | GND | Common ground / 共地 |
| VCC | 3.3V | Power / 供电 |
| CH_PD | 3.3V | Chip enable, must be pulled high / 芯片使能，必须拉高 |
| GPIO0 | — | Leave floating for normal boot / 正常启动时悬空 |
| GPIO2 | — | Leave floating / 悬空 |
| RST | — | Leave floating, or add reset button / 悬空，或加复位按钮 |

### Level Shifting / 电平转换

ESP modules operate at **3.3V**. The A8 board's serial pins are **5V tolerant in most cases**, but this is **not guaranteed**.

ESP 模块工作在 **3.3V**。A8 主板串口引脚**多数情况下可容忍 5V**，但**不保证**。

**Recommended / 推荐**: Add a simple voltage divider on the A8 TX → ESP RX line:

在 A8 TX → ESP RX 线上加一个简单的分压电路：

```
A8 TX (5V) ──── R1 (1kΩ) ────┬──── ESP RX (3.3V)
                             │
                        R2 (2.2kΩ)
                             │
                            GND
```

This drops 5V to ~3.4V, which is safe for the ESP.

这会把 5V 降到约 3.4V，对 ESP 安全。

### Power Supply / 供电

**Do not power the ESP from the A8 board's 5V rail.** Use a separate 3.3V regulator or the A8's 3.3V output if it can supply enough current (ESP8266 needs ~300mA peak).

**不要从 A8 主板的 5V 供电。** 使用独立的 3.3V 稳压器，或 A8 的 3.3V 输出（如果电流足够，ESP8266 峰值需约 300mA）。

## ESP3D Configuration / ESP3D 配置

### Web Interface / Web 界面

ESP3D exposes a web interface at `http://<esp-ip>/`. Default credentials are usually `admin` / `admin`.

ESP3D 在 `http://<esp-ip>/` 提供 Web 界面。默认凭据通常是 `admin` / `admin`。

### Key Settings / 关键设置

| Setting / 设置 | Value / 值 | Notes / 说明 |
|---|---|---|
| Baud rate / 波特率 | 115200 | Must match A8 firmware / 必须与 A8 固件一致 |
| Data port / 数据端口 | 8888 | Raw TCP passthrough / 原始 TCP 透传 |
| HTTP port / HTTP 端口 | 80 | Web interface / Web 界面 |
| Authentication / 认证 | Enable / 启用 | Otherwise anyone on LAN can control / 否则局域网内任何人可控制 |
| SSID / 密码 | Your WiFi / 你的 WiFi | 2.4GHz only, ESP8266 doesn't support 5GHz / 仅 2.4GHz，ESP8266 不支持 5GHz |

### Firmware Flashing / 固件刷写

ESP3D is flashed via the ESP module's UART pins before installation. See ESP3D's official documentation for the flashing procedure.

ESP3D 在安装前通过 ESP 模块的 UART 引脚刷写。刷写流程见 ESP3D 官方文档。

## A8-specific Quirks / A8 专属问题

### 1. Y Axis Moves the Bed / Y 轴移动热床

Unlike most Cartesian printers, the A8's Y axis moves the **heated bed**, not the hotend. This means:

与大多数笛卡尔打印机不同，A8 的 Y 轴移动的是**热床**，不是喷头。这意味着：

- Before any Y move, ensure the bed's path is clear. / 任何 Y 移动前，确保热床路径无阻挡。
- Cables to the bed can snag during long prints. / 长打印中，热床线缆可能被勾住。
- Bed adhesion issues may be caused by bed wobble, not extrusion. / 热床附着问题可能由热床晃动引起，而非挤出问题。

### 2. Z Axis Has Two Motors / Z 轴有两个电机

The A8 uses two Z motors, one on each side of the gantry. They are wired in parallel to a single driver.

A8 使用两个 Z 电机，分别在龙门两侧。它们并联到同一个驱动器。

**Risk / 风险**: If one motor fails or skips steps, the gantry tilts, and the nozzle may crash into the print.

**风险**：如果一个电机失效或丢步，龙门倾斜，喷头可能撞到打印件。

**Check / 检查**: After any Z issue, manually verify both sides of the gantry are at the same height.

**检查**：任何 Z 轴异常后，手动确认龙门两侧高度一致。

### 3. No Thermal Runaway Protection (Stock Firmware) / 原厂固件无热失控保护

The stock Anet A8 firmware does **not** include thermal runaway protection. If the thermistor disconnects while the heater is on, the heater will run at full power indefinitely.

原厂爱能特 A8 固件**不包含**热失控保护。如果热敏电阻在加热时断开，加热棒会持续全功率运行。

**Mitigation / 缓解**:
- Never leave a heated printer unattended. / 加热时绝不无人看管。
- Consider flashing Marlin with `THERMAL_PROTECTION_HOTENDS` enabled. / 考虑刷写启用了 `THERMAL_PROTECTION_HOTENDS` 的 Marlin。
- Install a physical thermal fuse. / 安装物理热熔断器。

### 4. Acrylic Frame Flex / 亚克力框架形变

The A8's acrylic frame flexes under load, especially at high print speeds or with a heavy direct-drive extruder.

A8 的亚克力框架在负载下会形变，尤其是在高打印速度或重直接驱动挤出机时。

**Mitigation / 缓解**:
- Print slower / 降低打印速度
- Add frame braces / 加装框架支撑
- Upgrade to an aluminum frame / 升级为铝型材框架

### 5. GT2 Belt Tension / GT2 皮带张力

Loose belts cause ringing and dimensional inaccuracy. Over-tight belts wear out bearings.

皮带松会导致振铃和尺寸偏差。皮带过紧会磨损轴承。

**Check / 检查**: Pluck the belt — it should sound like a low musical note, not a dull thud.

**检查**：拨动皮带——应发出低音，而非沉闷的撞击声。

## Known Firmware Issues / 已知固件问题

| Issue / 问题 | Cause / 原因 | Fix / 处理 |
|---|---|---|
| Printer freezes mid-print / 打印中途冻结 | 8-bit MCU buffer overflow / 8 位 MCU 缓冲区溢出 | Reduce print speed, use simpler G-code / 降低打印速度，使用更简单的 G-code |
| G28 fails after power loss / 断电后 G28 失败 | Stepper driver overheating / 步进驱动器过热 | Add heatsinks, reduce motor current / 加散热片，降低电机电流 |
| Temperature reads fluctuate / 温度读数波动 | Thermistor wiring noise / 热敏电阻接线噪声 | Shield thermistor wires, check connections / 屏蔽热敏电阻线，检查接线 |
| SD card not detected / SD 卡未检测到 | Card format or size / 卡格式或容量 | Use FAT32, ≤32GB SD card / 使用 FAT32，≤32GB SD 卡 |
| Bed heats slowly / 热床加热慢 | 12V bed, high thermal mass / 12V 热床，热质量大 | Normal behavior, wait longer / 正常行为，多等一会 |

## Useful A8 Macros / 常用 A8 宏

### Bed Leveling / 热床调平

```gcode
G28           ; home all / 全轴归零
G1 Z5 F3000   ; lift 5mm / 抬升 5mm
G1 X50 Y50 F3000  ; move to corner 1 / 移到角 1
; adjust bed screw / 调整热床螺丝
G1 X170 Y50 F3000 ; corner 2 / 角 2
; adjust / 调整
G1 X170 Y170 F3000 ; corner 3 / 角 3
; adjust / 调整
G1 X50 Y170 F3000 ; corner 4 / 角 4
; adjust / 调整
G1 Z10 F3000  ; lift / 抬升
G28 X0 Y0     ; home X/Y / X/Y 归零
M84           ; motors off / 关闭电机
```

### Filament Change / 换料

```gcode
M104 S200     ; heat hotend / 加热喷头
M109 S200     ; wait / 等待
G1 E-50 F300  ; retract 50mm / 回抽 50mm
; remove filament / 取出耗材
; insert new filament / 插入新耗材
G1 E50 F300   ; prime 50mm / 挤出 50mm
M104 S0       ; hotend off / 关闭喷头
```

### Cold Pull / 冷拔

```gcode
M104 S200     ; heat hotend / 加热喷头
M109 S200     ; wait / 等待
G1 E10 F300   ; extrude 10mm / 挤出 10mm
M104 S90      ; cool to 90°C / 冷却到 90°C
M109 S90      ; wait / 等待
G1 E-80 F100  ; retract 80mm / 回抽 80mm
; remove filament with debris / 取出耗材和杂质
```

## Replacement Parts / 替换零件

| Part / 零件 | Spec / 规格 | Notes / 说明 |
|---|---|---|
| Hotend / 喷头 | MK8, 0.4mm nozzle / MK8，0.4mm 喷嘴 | Standard / 标准 |
| Bed / 热床 | 220×220mm, 12V / 220×220mm，12V | |
| Thermistor / 热敏电阻 | 100k NTC / 100k NTC | |
| Heater cartridge / 加热棒 | 12V, 40W / 12V，40W | |
| Stepper motors / 步进电机 | NEMA 17 / NEMA 17 | |
| Belts / 皮带 | GT2, 6mm width / GT2，6mm 宽 | |
| Power supply / 电源 | 12V, 20A / 12V，20A | |

## References / 参考资料

- Anet A8 official wiki / 爱能特 A8 官方 wiki
- ESP3D firmware / ESP3D 固件: https://github.com/luc-github/ESP3D
- Marlin firmware / Marlin 固件: https://marlinfw.org/
- Anet A8 community forums / 爱能特 A8 社区论坛

## Changelog / 变更记录

- 2026-09-16: Initial release / 初始版本

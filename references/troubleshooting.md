# Troubleshooting / 异常处理手册

Common problems when controlling a 3D printer via TCP/serial, and how to diagnose them.

通过 TCP/串口控制 3D 打印机时的常见问题及诊断方法。

## Diagnostic Order / 诊断顺序

Always diagnose in this order. Do not skip steps.

始终按以下顺序诊断，不要跳步。

```
1. Environment (env vars set?) / 环境（变量是否设置？）
2. Network (host reachable? port open?) / 网络（主机可达？端口开放？）
3. Protocol (response readable? echo filtered?) / 协议（响应可读？回显已过滤？）
4. Firmware (printer responds to M115/M105?) / 固件（打印机响应 M115/M105？）
5. Motion (homing, coordinates in range?) / 运动（归零、坐标在范围内？）
6. Thermal (heater responds to target?) / 热（加热棒响应目标温度？）
```

## 1. Environment / 环境

### Symptom / 现象

```
ERROR: PRINTER_HOST not set. Add it to ~/.hermes/.env
ERROR: PRINTER_HOST 未设置。请添加到 ~/.hermes/.env
```

### Cause / 原因

`PRINTER_HOST` environment variable is not set, or the child skill's override variable (e.g. `A8_ESP3D_HOST`) is missing.

`PRINTER_HOST` 环境变量未设置，或子 skill 的覆盖变量（如 `A8_ESP3D_HOST`）缺失。

### Fix / 处理

```bash
# Check current value / 检查当前值
echo $PRINTER_HOST

# Set it / 设置
echo 'PRINTER_HOST=192.168.1.100' >> ~/.hermes/.env
echo 'PRINTER_PORT=8888' >> ~/.hermes/.env

# Reload / 重新加载
source ~/.hermes/.env
```

If using a child skill, check its declared env var name.

如果使用子 skill，检查其声明的环境变量名。

## 2. Network / 网络

### Symptom / 现象

```
Printer connection failed: [Errno 111] Connection refused
打印机连接失败：[Errno 111] Connection refused
```

or / 或

```
Printer connection failed: timed out
打印机连接失败：超时
```

### Cause / 原因

The controller is offline, the IP is wrong, the port is closed, or a firewall is blocking.

控制器离线、IP 错误、端口关闭，或防火墙拦截。

### Fix / 处理

**Step 1: Ping the host / Ping 主机**

```bash
ping $PRINTER_HOST
```

- **Linux / macOS**: `ping -c 3 $PRINTER_HOST`
- **Windows**: `ping -n 3 $PRINTER_HOST`

**Step 2: Test the TCP port / 测试 TCP 端口**

- **Linux / macOS**:

```bash
nc -zv $PRINTER_HOST $PRINTER_PORT
```

- **Windows** (PowerShell):

```powershell
Test-NetConnection -ComputerName $env:PRINTER_HOST -Port $env:PRINTER_PORT
```

**Step 3: Check controller power and LED / 检查控制器电源和指示灯**

Most controllers (ESP3D, OctoPrint) have a status LED. If it's off, the controller is not powered.

大多数控制器（ESP3D、OctoPrint）有状态指示灯。如果不亮，说明未上电。

**Step 4: Check firewall / 检查防火墙**

```bash
# Linux: list rules blocking the port / Linux：列出拦截该端口的规则
sudo iptables -L -n | grep $PRINTER_PORT
```

**Step 5: Check WiFi signal / 检查 WiFi 信号**

If the controller is on WiFi, weak signal causes intermittent timeouts.

如果控制器走 WiFi，信号弱会导致间歇性超时。

## 3. Protocol / 协议

### Symptom / 现象

Responses are garbled, contain unexpected characters, or the parser fails.

响应乱码、含意外字符，或解析失败。

### Cause / 原因

Baud rate mismatch between the controller and the printer's serial port.

控制器与打印机串口之间的波特率不匹配。

### Fix / 处理

**Step 1: Confirm the printer's baud rate / 确认打印机的波特率**

Most Anet A8 boards use **115200**. Check your firmware configuration.

大多数 Anet A8 主板使用 **115200**。检查固件配置。

**Step 2: Confirm the controller's baud rate / 确认控制器的波特率**

For ESP3D, this is in the web interface under **Settings → Serial**.

ESP3D 在 Web 界面的 **Settings → Serial** 中设置。

**Step 3: Match them / 使两者一致**

If the printer is 115200 and the controller is 250000, set the controller to 115200.

如果打印机是 115200 而控制器是 250000，把控制器改成 115200。

**Step 4: Restart the controller / 重启控制器**

After changing baud rate, power-cycle the controller.

修改波特率后，断电重启控制器。

### Symptom / 现象

Responses start with `echo:` and contain the command that was just sent.

响应以 `echo:` 开头，包含刚发送的命令。

### Cause / 原因

The controller echoes every command back. This is normal behavior, not an error.

控制器回显每条命令。这是正常行为，不是错误。

### Fix / 处理

The helper script filters `echo:` lines automatically. No action needed.

辅助脚本自动过滤 `echo:` 行，无需处理。

## 4. Firmware / 固件

### Symptom / 现象

No response to `M105` or `M115`, even though the TCP connection succeeds.

TCP 连接成功，但 `M105` 或 `M115` 无响应。

### Cause / 原因

The printer's firmware is not running, is stuck, or the serial link is broken.

打印机固件未运行、卡住，或串口链路断开。

### Fix / 处理

**Step 1: Query firmware info / 查询固件信息**

```bash
python3 SKILL_DIR/scripts/printer_control.py info
```

If `M115` returns a version string, firmware is running.

如果 `M115` 返回版本字符串，说明固件在运行。

**Step 2: If no response, power-cycle the printer / 如果无响应，断电重启打印机**

Turn off the printer, wait 10 seconds, turn it back on.

关闭打印机，等待 10 秒，重新开机。

**Step 3: Check the serial cable / 检查串口线**

If using a physical serial connection (not ESP3D), verify TX/RX are not swapped.

如果使用物理串口连接（非 ESP3D），确认 TX/RX 未接反。

## 5. Motion / 运动

### Symptom / 现象

`G28` (homing) fails, or the printer makes grinding noises.

`G28`（归零）失败，或打印机发出异响。

### Cause / 原因

Limit switch not triggered, wiring issue, or mechanical obstruction.

限位开关未触发、接线问题，或机械阻挡。

### Fix / 处理

**Step 1: Check limit switch status / 检查限位开关状态**

```bash
python3 SKILL_DIR/scripts/printer_control.py gcode "M119"
```

`M119` returns endstop status. If a switch shows `open` when it should be `TRIGGERED`, the switch or wiring is faulty.

`M119` 返回限位状态。如果开关显示 `open` 而应为 `TRIGGERED`，说明开关或接线故障。

**Step 2: Manually trigger the switch / 手动触发开关**

Press the X/Y/Z limit switch by hand and re-run `M119`. If status doesn't change, the switch is broken.

手动按压 X/Y/Z 限位开关，重新运行 `M119`。如果状态不变，开关损坏。

**Step 3: Check for mechanical obstruction / 检查机械阻挡**

Move the axis by hand (with motors disabled via `M84`) to feel for binding.

用 `M84` 关闭电机后，手动移动轴，感受是否有卡顿。

### Symptom / 现象

Printer crashes into the frame during a move.

移动时打印机撞到框架。

### Cause / 原因

Coordinates exceed the build volume.

坐标超出打印范围。

### Fix / 处理

Check the build volume declared by the child skill. For Anet A8, it's **220 × 220 × 380 mm**.

检查子 skill 声明的打印范围。爱能特 A8 为 **220 × 220 × 380 mm**。

Before sending `G1`, verify X ∈ [0, 220], Y ∈ [0, 220], Z ∈ [0, 380].

发送 `G1` 前，确认 X ∈ [0, 220]，Y ∈ [0, 220]，Z ∈ [0, 380]。

## 6. Thermal / 热

### Symptom / 现象

`M109` or `M190` never returns.

`M109` 或 `M190` 永不返回。

### Cause / 原因

The heater is broken, the thermistor is disconnected, or the target temperature is unreachable.

加热棒损坏、热敏电阻断开，或目标温度无法达到。

### Fix / 处理

**Step 1: Query temperature without waiting / 不等待查询温度**

```bash
python3 SKILL_DIR/scripts/printer_control.py gcode "M104 S200" "M105"
```

`M104` sets the target without waiting. `M105` reports current temperature.

`M104` 设置目标温度但不等待。`M105` 报告当前温度。

**Step 2: If temperature stays at 0 or room temp / 如果温度停留在 0 或室温**

The heater or thermistor is disconnected. **Power off the printer immediately** and check wiring.

加热棒或热敏电阻断开。**立即断电**并检查接线。

**Step 3: If temperature rises but slowly / 如果温度上升但很慢**

The heater cartridge may be underpowered, or the thermistor is not seated properly.

加热棒功率不足，或热敏电阻未正确安装。

### Symptom / 现象

```
Error:Thermal Runaway
```

### Cause / 原因

The firmware detected that the heater is not responding as expected. This is a safety feature.

固件检测到加热棒未按预期响应。这是安全保护机制。

### Fix / 处理

**Power off the printer immediately.** Do not restart until the cause is identified.

**立即断电。** 在查明原因前不要重启。

Check:
- Thermistor wiring / 热敏电阻接线
- Heater cartridge wiring / 加热棒接线
- Heater cartridge resistance (should be ~3-5Ω for 12V) / 加热棒电阻（12V 应约 3-5Ω）

## Emergency Recovery / 紧急恢复

### After `M112` (Emergency Stop) / `M112`（急停）之后

`M112` halts all printer activity. The printer will not respond to normal commands until power-cycled.

`M112` 停止所有打印机活动。打印机在断电重启前不会响应正常命令。

```bash
# This will fail / 这会失败
python3 SKILL_DIR/scripts/printer_control.py gcode "M105"

# Recover: power off, wait 10s, power on / 恢复：断电，等 10 秒，开机
```

### After a failed print / 打印失败后

1. Cancel the print: `M25` (pause) then `M24` won't help — use `M112` if needed.
2. Turn off heaters: `M104 S0` and `M140 S0`.
3. Home axes: `G28`.
4. Clear the bed before restarting.

1. 取消打印：`M25`（暂停）后 `M24` 无效——必要时用 `M112`。
2. 关闭加热：`M104 S0` 和 `M140 S0`。
3. 归零：`G28`。
4. 清理热床后再重启。

## When to Stop / 何时停止

**Stop all operations and report to the user if:**

**遇到以下情况，停止所有操作并报告用户：**

- Temperature reading is `0` or `NaN` / 温度读数为 `0` 或 `NaN`
- `Error:Thermal Runaway` appears / 出现 `Error:Thermal Runaway`
- Printer makes grinding or clicking noises / 打印机发出研磨或咔嗒声
- Smoke or burning smell / 冒烟或烧焦气味
- Any response you cannot interpret / 任何无法解释的响应

Do not retry blindly. Report the raw response and ask the user.

不要盲目重试。报告原始响应并询问用户。

## Diagnostic Commands Cheat Sheet / 诊断命令速查

| Command / 命令 | Purpose / 用途 |
|---|---|
| `ping $PRINTER_HOST` | Check host reachability / 检查主机可达性 |
| `nc -zv $PRINTER_HOST $PRINTER_PORT` | Check TCP port (Linux/macOS) / 检查 TCP 端口 |
| `Test-NetConnection` (PowerShell) | Check TCP port (Windows) / 检查 TCP 端口 |
| `python3 printer_control.py ping` | Script-level connectivity test / 脚本级连通性测试 |
| `python3 printer_control.py info` | Query firmware (M115) / 查询固件 |
| `python3 printer_control.py query` | Query temp + position / 查询温度和位置 |
| `python3 printer_control.py gcode "M119"` | Check endstops / 检查限位开关 |
| `python3 printer_control.py gcode "M503"` | Dump firmware settings / 输出固件设置 |
| `python3 printer_control.py selftest` | Run full self-test / 运行完整自检 |

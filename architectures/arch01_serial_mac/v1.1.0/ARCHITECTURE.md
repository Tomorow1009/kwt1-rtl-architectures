# 架构一：64 项串行点积与数值处理

已增加 KWT-1 真实 HEX 的 12 层单点积入口：见 [真实数据软件校验与 RTL 仿真](REAL_KWT1.md)。运行 `./scripts/run_real_kwt1.ps1` 可执行软件校验和双仿真器验证，使用本目录的原始 RTL。

本目录实现独立的 `Y = Σ(k=0…63) x[k] × w[k] + bias` 运算。无需 E203、CPU 驱动、开发板或 Multisim。RTL 负责真实乘累加和转换；testbench 只提供激励、参考答案与自动检查。

## 1. 文件与入口

| 位置 | 用途 |
|---|---|
| `rtl/dot64.sv` | 单路 16×16 乘法、40 位累加、任务状态机 |
| `rtl/requantize.sv` | 加偏置后的缩放、舍入、饱和 |
| `tb/tb_dot64.sv` | 100 MHz 仿真时钟、独立逐拍模型、自动检查、复位/握手测试 |
| `scripts/gen_vectors.py` | Python 标准库整数参考模型与确定性数据生成 |
| `vectors/` | 已生成的输入、答案、编号名称表和完整 JSON 清单 |
| `scripts/run_xsim.ps1` | Vivado XSim 一键编译、展开和运行 |
| `scripts/run_iverilog.ps1` | Icarus 一键编译和运行 |
| `scripts/create_vivado_project.tcl` | 创建可在 GUI 中打开的行为仿真工程 |
| `scripts/waves.tcl` | 关键波形及显示进制配置 |
| `sim/` | 运行产生的日志、波形、事件时间表，不纳入 Git |

## 2. 数值约定

所有数据采用二进制补码。默认 `x_real = x_int / 4096`，`w_real = w_int / 4096`，因此输入实数范围为 `[-8, 7.999755859375]`。偏置默认按 `bias_real × 2^24` 编码，不能把 16 位输入尺度的偏置直接加入累加器。

| 数据 | 位宽 | 默认小数位 |
|---|---:|---:|
| x、w | signed 16 | 12 |
| product | signed 32 | 24 |
| accumulator（仅点积） | signed 40 | 24 |
| bias | signed 40 | 24 |
| sum_with_bias | signed 41 | 24 |
| result | signed 16 | 12（shift=12） |

64 项点积绝对值不超过 `64 × 2^30 = 2^36`，40 位累加器足够。允许偏置取完整 40 位有符号范围，因此相加前显式扩展到 41 位。中间不饱和、不截断。

令 `S` 为点积加偏置的整数值。`shift` 是每任务配置的 5 位无符号数，允许 0–31；硬件没有隐式默认配置，调用方应显式送入 12。

```text
shift=0: R = S
shift>0: R = sign(S) × floor((abs(S) + 2^(shift-1)) / 2^shift)
result = min(32767, max(-32768, R))
saturated = (R < -32768) 或 (R > 32767)
```

舍入为就近舍入、恰好半值远离零，例如 `+1.5 → +2`、`-1.5 → -2`。先舍入再饱和；恰好等于 -32768 或 32767 不置饱和标志。数值转换先扩展再取绝对值，避免负极值取反溢出。

输入/权重按默认尺度编码时，输出实数为 `result × 2^(shift−24)`。本模块不实现左移或任意乘法比例缩放。实际模型的小数位、饱和率及精度需后续标定。

## 3. 握手与时序

所有接口在时钟上升沿以 `valid && ready` 为一次成功传输。发送方置 valid 后，在握手前必须保持 valid 和对应数据不变；不能仅发一拍脉冲后忽略 ready。

| 接口 | 信号 | 行为 |
|---|---|---|
| 任务 | start_valid/start_ready、bias、shift | IDLE 接受，锁存配置、清零计数和累加器 |
| 输入 | in_valid/in_ready、x、w | MAC 接受固定 64 对数据，无 last 信号 |
| 输出 | out_valid/out_ready、result、saturated | OUTPUT 保持结果直到被接收 |
| 状态 | busy | 从任务接受后到结果被接收前为 1 |
| 复位 | rst_n | 低有效异步复位，取消任务，清零寄存器，禁止握手 |

集成时应同步释放复位；testbench 在下降沿释放。复位后旧任务不会恢复，需要重新发送完整任务。

状态编码：`0=IDLE → 1=MAC → 2=CONVERT → 3=OUTPUT → 0=IDLE`。

理想无暂停时序（T0 为接受任务的上升沿）：

```text
T0       接受 bias、shift；本沿不接收第一对 x/w
T1…T64   依次接受第 1…64 对输入
T65      转换并注册 result；此沿之后 out_valid=1
T66      若 out_ready=1，结果握手并返回 IDLE
T67      最早接受下一任务
```

输入空拍不改变计数/累加器。结果反压时 busy 持续为 1，禁止接收新任务或额外输入。允许提前提出下一任务并保持，直到 start_ready 恢复；不支持多个在途任务或同沿完成旧任务并启动新任务。result 在 out_valid=0 时没有结果语义。

内部没有超时；缺少输入或接收方持续反压时一直等待。testbench 设置了 10 ms 仿真 watchdog。

## 4. 一键运行 Vivado XSim

在 PowerShell 中执行，路径和参数均可带引号：

```powershell
Set-Location D:\IC_compeyition\Fast_coding
& .\scripts\run_xsim.ps1
```

若 Vivado 不在 PATH，显式指定本机已发现的目录：

```powershell
& .\scripts\run_xsim.ps1 -VivadoBin 'D:\FPGA\vivado_18_3\Vivado\2018.3\bin'
```

脚本依次运行 `xvlog --sv`、`xelab -debug typical` 和 `xsim -tclbatch`；检查每一步退出码，并要求日志出现最终 `PASS:`。只出现 `CASE PASS` 不算整套通过。

输出在 `sim/xsim/`：`compile.log`、`elaborate.log`、`simulation.log`、`events.csv`、`dot64.wdb`、`dot64.wcfg`。重复运行会覆盖该运行目录的对应结果。

### 打开已保存波形

启动 Vivado，在 Tcl Console 执行（Tcl 路径使用正斜杠）：

```tcl
open_wave_database D:/IC_compeyition/Fast_coding/sim/xsim/dot64.wdb
open_wave_config D:/IC_compeyition/Fast_coding/sim/xsim/dot64.wcfg
```

若没有配置文件，打开数据库后执行：

```tcl
source D:/IC_compeyition/Fast_coding/scripts/waves.tcl
```

静态 WDB 用于查看历史结果；要重新执行，重跑 PowerShell 脚本，或使用下面的工程方式。

### 创建 GUI 行为仿真工程

在 Vivado 空白窗口的 Tcl Console 执行：

```tcl
source D:/IC_compeyition/Fast_coding/scripts/create_vivado_project.tcl
```

脚本创建或打开 `sim/vivado_project/dot64_demo.xpr`、添加 RTL 和仿真文件、设置顶层 `tb_dot64`、头文件路径与数据路径，然后运行行为仿真至结束。器件 `xc7a35tcpg236-1` 仅作仿真工程占位，不代表最终比赛平台，也不要求开发板连接。脚本不删除已有工程；执行前应关闭当前打开的工程。也可直接打开生成的 `.xpr`。

后续在 Flow Navigator 选择 **Simulation → Run Simulation → Run Behavioral Simulation**。修改 RTL 或 TB 后重新启动行为仿真以重新编译；在同一仿真中重新播放可以执行 `restart`、`run all`。必须运行到最终 PASS，默认短时间运行不能覆盖整套测试。

## 5. 看哪些波形、如何判断

波形配置包含 clk/rst_n、任务/输入/输出握手、busy、state、accepted_count、product、accumulator、bias_reg、sum_with_bias、shift_reg、result、saturated。x/w/product/accumulator/bias/result 采用有符号十进制，计数和移位采用无符号显示。

1. 找 `start_valid && start_ready` 的上升沿，确认配置锁存且计数归零。
2. 找 `in_valid=0` 的 MAC 周期，确认 accepted_count 和 accumulator 不变；只有 in_valid/in_ready 同时为 1 才前进。
3. 计数达到 64 后，应经过一个转换周期再输出；偏置只加一次。
4. 找 `out_valid=1 && out_ready=0`，确认 result、saturated、out_valid 保持，直到接受结果。
5. 看 rst_n 拉低时，忙状态和输出 valid 是否清零；复位后的任务从 0 计数重新开始。

用 `vectors/case_names.txt` 将编号对应到场景；`sim/xsim/events.csv` 记录各任务开始/完成及复位时间。CSV 和日志的 `time_ps` 单位为皮秒，**除以 1000 得到 ns**。在波形中用 test_case 看正在提出的任务，用 active_case 看已接受的任务；排队期间两者可能不同。

建议先看编号 3/4（正负结果）、10（大数抵消）、11/12（正负饱和），再搜索名称 `round_s12` 查看默认尺度的舍入。复位 tag=10/11/12/13 分别表示接收 0/1/32/63 对后取消，tag=20 表示转换阶段取消，tag=21 表示输出反压时取消。完整运行后的具体时间索引见 `VERIFICATION.md`。

波形用于解释结果；自动比较和协议检查决定 PASS，不以截图替代自动验证。

## 6. Icarus、测试范围与数据导入

```powershell
Set-Location D:\IC_compeyition\Fast_coding
& .\scripts\run_iverilog.ps1
# 可选：重新生成相同的确定性向量
python .\scripts\gen_vectors.py
```

Icarus 输出在 `sim/iverilog/`，包括 `simulation.log`、`events.csv`、`dot64.vcd`。VCD 可用支持 VCD 的查看器打开，Vivado 路径优先使用 WDB。

现有 1103 个向量中有 863 个定向向量、240 个随机向量；覆盖全部 32 个 shift 值、零/正负/极值/抵消/偏置极值、舍入半值及两侧、饱和边界。随机种子固定，包含饱和和未饱和结果。另有复位恢复、排队命令、提前到达且被阻塞的输入测试，总计完成 1112 个任务，取消 6 个任务。输入随机空拍、最多 100 拍的输出反压及逐拍状态模型一起检查数据完整性。

Python 用无限精度整数及除法/余数计算答案，避免与 RTL 共用舍入实现。SV 模型逐拍计算 64 位累加参考值，核对内部计数、配置锁存、输出时机和结果；发现错误或超时即 `$fatal`。

### hex 文件布局

| 文件 | 每任务元素数 | 每行十六进制位数 |
|---|---:|---:|
| x.hex、w.hex | 64 | 4 |
| bias.hex | 1 | 10 |
| shift.hex | 1 | 2（仅低 5 位有效） |
| total.hex | 1 | 11（仅低 41 位有效） |
| result.hex | 1 | 4 |
| saturated.hex | 1 | 1 |

每行一个元素、无 `0x` 前缀；负数按对应有效位宽的补码写入。第 n 个任务使用 x/w 文件的 `[64*n … 64*n+63]` 和其他文件第 n 行。`cases.vh` 定义任务数；manifest.json 保存可读的有符号整数和名称。

例如 16 位 `0001/FFFF/8000/7FFF` 分别表示 `1/-1/-32768/32767` 的整数编码。浮点转整数时也应采用半值远离零，不能直接用 Python 的默认 round（它在半值处采用偶数舍入）。先按尺度量化，再限幅到对应数据位宽。

未来真实模型数据的一次任务应取 X 的一行、W 的一列及该列 bias。对 TensorFlow Dense 的 `[64,256]` 权重取 `W[:,j]`，不能把行主序文件中任意连续 64 个值当作一列。偏置按乘积尺度对齐。

扩展本测试集时，在生成器中追加 `add(name, xs, ws, bias, shift)` 调用，重新生成并重新编译，保留原先基准案例及其编号（协议测试复用 3–6 号案例）。如单独写数据加载 TB，可用 `+DATA_DIR=目录`（XSim 为 `-testplusarg DATA_DIR=目录`）指定数据位置。实际参数提取和无梯度标定不包含在本阶段。

本项目验证的是整数计算与协议正确性；未验证真实模型精度、目标频率时序收敛、DSP 资源映射或 SoC 集成。

# 架构一：完整 NPZ 的 12 层矩阵验证

## 验证对象

使用 `KWT1/model_data/outputs/real_sample_001` 中一个语音样本的完整 NPZ，逐层验证 `Y = XW + b`：X 为 99×64，W 为 64×256，b 为 256，每层输出 99×256=25344 项，12 层共 304128 项。

每个输出由原 `rtl/dot64.sv` 和 `rtl/requantize.sv` 计算。矩阵遍历在导出程序和 testbench 中完成，不新增矩阵控制器或缓存硬件。每层输入来自浮点模型原先捕获的张量，并非上一层量化输出；本验证不等于端到端 KWT 推理、卷积、分类准确率或 SoC 验收。

与 v1.2.0 的区别：v1.2.0 对许多语音的每层 Y[0,0] 做软件全量和 RTL 分阶段验证；本次对一个语音的 12 个完整矩阵做软件及双仿真器全覆盖。两种覆盖维度不同，不能互相替代。

## 数据与协议

输入/权重 signed16、小数 12 位；偏置 signed40、小数 24 位；累加乘积使用 40 位，加偏置总和 signed41；shift 固定 12。输出半值远离零舍入，饱和到 signed16，解码为 result/4096。RTL 接口和 valid/ready 协议保持不变。

任务编号为 `row*256+column`。每个任务顺序提供 k=0…63 的 `X[row,k]`、`W[k,column]`，偏置为 `b[column]`。NPZ 的 W 不转置、不分 bank；导出时按列读取，HEX 按点积任务顺序排列。

| 文件 | 每行十六进制字符 | 每层行数 | 含义 |
|---|---:|---:|---|
| x.hex / w.hex | 4 | 1622016 | 每任务 64 个有符号编码 |
| bias.hex | 10 | 25344 | 40 位偏置 |
| shift.hex | 2 | 25344 | 5 位移位量，恒为 0c |
| total.hex | 11 | 25344 | 41 位加偏置总和 |
| result.hex | 4 | 25344 | 16 位饱和输出 |
| saturated.hex | 1 | 25344 | 0 或 1 |

所有负数使用相应有效位数的补码；字符宽度多出的高位填零，例如 total 的最高十六进制位只能为 0 或 1。各文件独立，不合并地址空间。

软件在导出前检查 NPZ 形状、类型、有限值、数值范围，并重新量化全部 X/W/b；用 int64 矩阵乘加和整数除法/余数独立重算舍入。先与原 NPZ 的完整参考矩阵逐项比较，通过后才导出。float32 到定点的参考使用精确浮点比例与整数运算。

## 一键运行

需要 Python 和 NumPy，Icarus Verilog、Vivado XSim。默认从 PATH 找工具；本机 XSim 为 Vivado 2018.3。

```powershell
Set-Location D:\IC_compeyition\Fast_coding
# 默认 12 层、双仿真器，约 304128 个独立输出/仿真器
.\scripts\run_full_matrix_kwt1.ps1
# 只核对全部 NPZ，保存报告，不生成 HEX
.\scripts\run_full_matrix_kwt1.ps1 -Mode software
# 指定一层；仍包含首行/边界/末尾波形作业
.\scripts\run_full_matrix_kwt1.ps1 -Mode layer -Layer 1 -Simulator both
# 工具/输入路径可指定
.\scripts\run_full_matrix_kwt1.ps1 -DataRoot 'D:\IC_compeyition\Fast_coding\KWT1\model_data\outputs\real_sample_001' -VivadoBin 'D:\FPGA\vivado_18_3\Vivado\2018.3\bin'
```

Python 入口为 `scripts/run_full_matrix.py`，对应参数 `--mode software|all|layer`、`--layer 1..12`、`--simulator both|iverilog|xsim`、`--data-root`、`--vivado-bin`、`--icarus-bin`。指定 layer 必须使用 layer 模式。

每次建立独立 `sim/full_matrix_kwt1/<运行编号>`。不覆盖输入 NPZ，不复用历史 PASS，不自动断点续跑。每个仿真器编译一次，每层单独启动仿真。XSim 沿用 options 文件处理等号参数。单作业墙钟超时 2 小时，TB 每任务超时 10000 周期及全局仿真时间上限 100 ms。

## 实际输出及波形

`software.json` 保存逐层误差和 NPZ 哈希；`data/layer_XX` 保存七 HEX、期望矩阵及各文件校验值；`summary.json` 保存源码哈希、作业状态、实际数量及仿真器结果。

每层 `layer_XX_full.csv` 在成功输出握手时直接记录 DUT 的 `task,total,result,saturated`，没有表头。Python 检查完整任务序列，重建 `layer_XX_full.npz` 的 99×256 total/result/saturated，逐项对照参考。遗漏、重复、错误值都判定失败。错误报告包含层号和行列；TB 直接报错中的 task 可按 row=task//256、column=task%256 定位。

全量作业不记录信号波形。每层另外执行 0…256 共 257 个任务，覆盖完整首行和下一行第一个输出；再用单任务副本执行 task=25343 的末尾输出，避免重复扫描前面的 HEX。TB 可选参数 TASK_BASE=25343 保留原矩阵编号，默认 0，不改变原批量入口。每套仿真器额外 3096 次执行不计入独立覆盖，合计执行 307224 次，独立覆盖仍为 304128。

```tcl
# 将 <运行编号> 替换为实际输出目录
open_wave_database D:/IC_compeyition/Fast_coding/sim/full_matrix_kwt1/<运行编号>/xsim/layer_01_first_row_boundary.wdb
open_wave_config D:/IC_compeyition/Fast_coding/sim/full_matrix_kwt1/<运行编号>/xsim/layer_01_first_row_boundary.wcfg
```

Icarus 对应 `.vcd` 可用 GTKWave 打开。波形查看 task_id（原矩阵任务号，等于 n+TASK_BASE）、actual_count、start/in/out 握手、state、product、accumulator、sum_with_bias、bias_reg、shift_reg、result 和 saturated；将有符号数据设为 Signed Decimal。task_id=255→256 是跨行边界；每任务反压两拍时 out_valid/结果必须保持，接受输入数为 64。时钟周期 10 ns 只是仿真激励，不表示已经完成硬件时序收敛。

## 复验与边界

```powershell
# 运行过全部矩阵的 Icarus 后；临时副本只在新 negative_tests 下创建
python .\scripts\test_full_matrix_failures.py .\sim\full_matrix_kwt1\<运行编号>
python .\scripts\gen_vectors.py
.\scripts\run_iverilog.ps1
.\scripts\run_xsim.ps1
.\scripts\run_real_kwt1.ps1 -Simulator both
.\scripts\run_batch_kwt1.ps1 -Mode smoke -Simulator both
```

故障检测包括 NPZ 形状、整数范围、量化及参考值错误，HEX 缺失/截断/错误参考，以及实际输出记录的重复任务和数值错误；含正常对照。源数据不修改。最终验收同时要求矩阵主作业、代表波形作业、故障检测及兼容回归通过，运行入口自身的 PASS 只代表所选择的矩阵作业完成。

浮点误差按完整矩阵报告最大绝对误差、RMSE、NRMSE（分母下限 1e-8）；只用于观察，不改变整数比较，不宣称分类精度达标。本次将代码、文档、原始小型 NPZ 及验收证据归档为 GitHub v1.3.0 版本目录。实际验收证据见 `FULL_MATRIX_KWT1_VERIFICATION.md`。

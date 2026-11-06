> 仓库复现说明：先进入本版本目录运行下述命令；文中 D: 盘绝对路径仅是原开发机示例。已附带实际验证所需的 12 组 HEX 和完整 NPZ。原提取包脚本不在本版本重复存放，其位置见下文历史说明。

# 架构一：KWT-1 真实 HEX 的软件校验与 RTL 仿真

本入口使用原工程 `rtl/dot64.sv` 和 `rtl/requantize.sv`，读取 `KWT1/model_data/outputs/real_sample_001`。目标是一个真实语音样本在 12 个编码器中分别捕获的第一线性层，每层选择 `Y[0,0]`，共 **12 个独立的 64 项点积**。

计算为 `Y[i,j] = Σ X[i,k]W[k,j] + b[j]`。这是线性层乘加，不是卷积；当前也没有矩阵控制器或 SoC。第 0 行为分类 token，这 12 个点积不是 12 个连续音频帧，也不是将前一层量化输出直接送进下一层。

## 1. 本次修改

- 新增 `scripts/verify_real_hex.py`：独立整数参考、文件格式检查、NPZ 对照及浮点量化复核。默认只读，不修改资料包。
- 新增 `scripts/run_real_kwt1.ps1`：软件校验后，分别用 Icarus 和 XSim 执行 12 层；每个仿真器只编译一次。
- 将已有单任务 TB 复制到主工程 `tb/tb_single_hex.sv`，由该入口使用。它检查数值答案、64 次接收计数、4 拍输出反压保持和输出完成握手。
- 新增 `scripts/real_kwt1_waves.tcl` 与失败场景测试入口 `scripts/test_real_hex_failures.py`。

**无需为这批真实参数更改 RTL 位宽、数值算法或握手协议。** 参数从文件送入，不应硬编码到乘累加模块中。所有实际仿真都使用主工程的 `rtl/`；交付包内重复嵌套的 RTL 不作为编译源。

## 2. 已有的定点软件在哪里？

资料包已经包含：

| 文件 | 用途 | 注意事项 |
|---|---|---|
| `KWT1/model_data/scripts/verify_exports.py` | 重读 HEX，用整数除法/余数重算结果，对照 NPZ | 运行时会写回资料包的 hex_verification.json |
| `KWT1/model_data/scripts/extract_kwt.py` | 提取浮点张量；`integer_matrix()` 计算完整定点矩阵 | 提取需要 TensorFlow 等模型依赖 |
| `KWT1/KWT1_HEX_handoff/scripts/export_dot_json.py` | 浮点单任务 JSON 量化并导出 HEX | 仅导出选中的点积 |

本次新增的 `scripts/verify_real_hex.py` 将已有数据的验证单独整理出来，只需要 Python 和 NumPy，不需要 TensorFlow、checkpoint 或音频全集。软件依赖缺失时可在自己的 Python 环境安装 NumPy；不用照搬原作者的 E 盘虚拟环境路径。

## 3. 运行方法

在 PowerShell 中进入本机主工程：

```powershell
Set-Location D:\IC_compeyition\Fast_coding

# 只读软件检查；不写任何报告
python .\scripts\verify_real_hex.py

# 推荐：软件检查 + Icarus 12 层 + Vivado XSim 12 层
.\scripts\run_real_kwt1.ps1

# 仅运行一个仿真器（仍会先做软件检查）
.\scripts\run_real_kwt1.ps1 -Simulator xsim
.\scripts\run_real_kwt1.ps1 -Simulator iverilog

# 只做软件检查并保存报告
.\scripts\run_real_kwt1.ps1 -Simulator software
```

可指定数据、Python 和工具目录：

```powershell
.\scripts\run_real_kwt1.ps1 `
  -DataRoot 'D:\IC_compeyition\Fast_coding\KWT1\model_data\outputs\real_sample_001' `
  -Python 'D:\Riscv_project\python\python.exe' `
  -VivadoBin 'D:\FPGA\vivado_18_3\Vivado\2018.3\bin'
```

`-IcarusBin` 可指定含 iverilog.exe/vvp.exe 的目录。未指定工具目录时从 PATH 查找。当前入口要求 manifest 中恰好有第 1–12 层，各层坐标由 manifest 决定。

每次运行新建 `sim/real_kwt1/<时间_随机编号>/`，控制台第一行显示具体位置。输入 HEX、NPZ、manifest 和资料包中原 `rtl_sim` 目录都不会被覆盖。

```text
<运行编号>/
  software.log / software.json   软件逐层结果、误差、数据 SHA-256
  summary.json                  总结、受测源码路径/哈希、各层结果、失败原因
  iverilog/
    compile.log / single.vvp
    layer_01.log … layer_12.log
    layer_01.vcd … layer_12.vcd
  xsim/
    compile.log / elaborate.log
    layer_01.log … layer_12.log
    layer_01.wdb … layer_12.wdb
    layer_01.wcfg … layer_12.wcfg
```

只有 `summary.json` 的 status=passed、软件 12/12 且所选仿真器各有 12 条通过记录，才表示本轮完整通过。脚本遇到编译、仿真或数值失败会停止并返回错误；失败时已经完成的层仍保留在 summary 中。`-Simulator software` 的通过仅表示软件检查成功。

XSim 使用 `.options` 文件传递 `DATA_DIR=...`，避开 Vivado 2018.3 Windows 批处理对等号参数的拆分问题。不要删除参数文件中的引号。

## 4. 比较规则

本批格式：x/w 为 signed 16、12 位小数；bias 为 signed 40、24 位小数；total 为 signed 41；shift=12；输出 signed 16。采用就近舍入、半值远离零，最后饱和。

验证入口会检查：

1. manifest 格式、层号、坐标与 HEX 路径。
2. 七个 HEX 的行数、十六进制宽度、有效位和补码解释。
3. Python 任意精度整数重算的 total/result/saturated 与 HEX 逐位一致。
4. 对应 NPZ 中的 X 行、W 列、偏置与三类答案一致。
5. 从 float32 输入、权重及偏置重新量化，与整数 HEX 一致。
6. RTL 日志中唯一的最终 PASS，以及其三个整数结果与软件报告一致。

整数结果必须精确相同。反量化输出 `result × 2^(shift−24)` 与浮点 `Y_float` 的误差另行报告，不用它来放宽整数比对。单点接近零时相对误差不稳定，因此本入口展示绝对误差。

本轮只复核选定的 12 个输出。NPZ 中虽有全部 `99×256` 元素，但没有在这次运行中逐元素重算或仿真；资料包所述整矩阵 NRMSE 属于原导出记录，不等于这次重新测量，更不等于分类准确率验收。

## 5. 查看 Vivado 波形

先运行 XSim，再在 Vivado 的 Tcl Console 中把下面 `<运行编号>` 替换为控制台打印的实际编号：

```tcl
open_wave_database D:/IC_compeyition/Fast_coding/sim/real_kwt1/<运行编号>/xsim/layer_01.wdb
open_wave_config D:/IC_compeyition/Fast_coding/sim/real_kwt1/<运行编号>/xsim/layer_01.wcfg
```

查看其他层时先关闭当前波形数据库，再打开相应文件。每层均单独启动仿真，时间从 0 开始，时钟周期 10 ns。典型时间位置：45 ns 接受任务，55–685 ns 接受 64 对数据，695 ns 后输出 valid 拉高，745 ns 接受输出，746 ns 打印最终 PASS。

重点观察 `accepted_count` 从 0 到 64，`sum_with_bias` 等于 total.hex，输出反压时 `out_valid/result/saturated` 保持。配置已将有符号数值设为十进制。100 MHz 是测试激励，不代表通过实际综合时序。

## 6. 失败检测与原回归

下面的测试只在一个全新的运行子目录里复制并破坏样例，不触碰原始数据：

```powershell
python .\scripts\test_real_hex_failures.py .\sim\real_kwt1\<运行编号>\negative_tests
```

覆盖缺少 x.hex、w.hex 行数错误、错误 result、非法 padding 位和 manifest 格式不匹配。目录必须尚不存在；结果写入其 summary.json。

原有人工回归入口保持不变：

```powershell
.\scripts\run_iverilog.ps1
.\scripts\run_xsim.ps1
```

实际本机运行记录及 12 层结果见 `REAL_KWT1_VERIFICATION.md`。本次未上传 GitHub，也未改动数据提取、训练或模型结构。

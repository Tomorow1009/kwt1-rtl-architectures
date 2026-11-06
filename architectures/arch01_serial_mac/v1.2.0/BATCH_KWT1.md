# 架构一：全量语音 HEX 的软件校验与分阶段 RTL 验证

版本说明：在 v1.1.0 的单样本 12 点积验证基础上，增加分片数据的流式验证。硬件仍为主工程 `rtl/dot64.sv` 与 `rtl/requantize.sv`；数据通路、握手协议和数值规则不变。

## 1. 数据范围与排列

默认数据目录：`KWT1/model_data/outputs/all_speech_dot00`。

| 划分 | 语音数 | 点积任务数 | 分片数 |
|---|---:|---:|---:|
| training | 84843 | 1018116 | 166 |
| validation | 9981 | 119772 | 20 |
| testing | 11005 | 132060 | 22 |
| 合计 | 105829 | 1269948 | 208 |

每条语音在 12 个编码器中各取第一线性层 `Y[0,0]`，每个任务计算 64 项点积加偏置。**不是卷积，也不是每层完整 `99×256` 矩阵。** 数据来自原浮点模型的独立中间张量，不代表量化输出在模型中连续传播。

每个分片有七个 HEX；任务顺序为“分片内样本外层、编码器层内层”：

```text
task = sample_in_shard × 12 + layer_index   （layer_index=0…11）
x/w 文件位置 = task × 64 + k               （k=0…63）
bias/shift/total/result/saturated 位置 = task
```

`samples.csv` 将样本路径、全局 sample_id、分片和任务索引关联起来。共享权重、偏置在 `shared_parameters.npz`；每个分片的 `selected_float.npz` 保存实际捕获的输入和浮点输出。HEX 中仍按任务重复权重/偏置，TB 不推断或改写数据。

格式延续原定义：x/w signed16、12 位小数；bias signed40、24 位小数；total signed41；输出 signed16；本批 shift=12；半值远离零、最后饱和。改变数据规模不需要把权重写死在 RTL 中。

## 2. 已有软件与新增代码

原资料包的 `model_data/scripts/verify_all_speech.py` 已包含全量定点验证，`verify_exports.py` 验证单样本，`extract_kwt.py` 包含矩阵定点参考。它们使用 Python/NumPy，不是另一个 GUI 软件。

新增主工程入口：

| 文件 | 用途 |
|---|---|
| `scripts/verify_batch_hex.py` | 软件全量校验，默认只读，NumPy 向量化解码固定宽度 HEX |
| `scripts/run_batch_kwt1.ps1` | 软件预检、双仿真器编译和分片作业管理 |
| `tb/tb_batch_hex.sv` | 流式读取七文件，缓存一组 64 对数据，严格检查格式/数值/握手 |
| `scripts/test_batch_failures.py` | 使用运行目录中的临时副本验证错误检出能力 |

不导入 TensorFlow、不重新提取或训练模型。原数据、交付包内脚本及历史验证报告保持不变，运行只使用主工程 RTL。

## 3. 运行命令

```powershell
Set-Location D:\IC_compeyition\Fast_coding

# 软件全量，完全只读（控制台输出，不写报告）
python .\scripts\verify_batch_hex.py

# 默认验收：软件全量 + 双仿真器 432 抽样任务 + 各 6144 个完整分片任务
.\scripts\run_batch_kwt1.ps1

# 仅软件，全量检查并保存报告
.\scripts\run_batch_kwt1.ps1 -Mode software

# 只做软件全量预检和跨划分抽样 RTL
.\scripts\run_batch_kwt1.ps1 -Mode smoke -Simulator both

# 指定完整分片；仍先执行软件全量预检
.\scripts\run_batch_kwt1.ps1 -Mode shard -Shard training/shard_0000 -Simulator xsim

# 指定分片中的一段，SkipTasks 从 0 起，LimitTasks=0 表示运行剩余全部
.\scripts\run_batch_kwt1.ps1 -Mode shard -Shard testing/shard_0021 -SkipTasks 3000 -LimitTasks 24

# 将来的全量 RTL 入口；此次分阶段验收不执行此命令
.\scripts\run_batch_kwt1.ps1 -Mode all -Simulator both
```

`-Mode staged` 等价于默认模式。`-Simulator` 支持 both/iverilog/xsim；`-DataRoot` 指定其他兼容格式的数据根目录；`-Python`、`-VivadoBin`、`-IcarusBin` 指定本机工具。未指定工具目录时从 PATH 查找。

```powershell
.\scripts\run_batch_kwt1.ps1 -Mode staged -Simulator both `
  -VivadoBin 'D:\FPGA\vivado_18_3\Vivado\2018.3\bin'
```

每次运行建立 `sim/batch_kwt1/<时间_随机编号>/`。`software.json` 保存全量校验与误差统计，`summary.json` 保存运行状态、作业列表、任务数及源码哈希。仿真器各有自己的构建目录、compile/elaborate 日志和逐作业日志。日志逐作业落盘，中途失败保留已完成结果；本版本不自动跳过旧运行，不把不完整报告当作通过。

两套仿真器各编译一次。XSim 使用 `.options` 文件传递 DATA_DIR 等参数，避免 2018.3 的 Windows 批处理拆分等号问题。建议数据和工具路径采用当前工程这样的 ASCII 路径。

## 4. 软件检查与错误定位

软件检查全部分片，包括：manifest 的格式/尺度、samples.csv 哈希与唯一性、连续样本索引、分片覆盖无重叠无缺失、每个数据文件哈希、HEX 行数/字符宽度/有效位/补码、共享权重偏置量化、输入浮点量化和全部整数答案。

整数计算使用 int64：64 项 signed16 乘积与 signed40 偏置之和不会溢出。舍入用整数除法与余数实现，与 RTL 的移位实现独立。必须逐位一致；浮点误差不能放宽整数比较。

发生数值/字符错误时指出分片、任务、样本 ID/路径、层号和出错项。文件缺失、长度或哈希错误发生在解码之前，能定位分片和文件，但不伪造具体样本坐标。

误差报告按 training/validation/testing 和层号分别统计 NRMSE、最大绝对误差、输出饱和数量、输入截限数量。NRMSE 分母为该划分该层选定输出的浮点 RMS，下限 1e-8；数值为比例，乘 100 才是百分比。这只描述 `Y[0,0]` 的量化误差，不是分类准确率，也不是完整矩阵误差；本次不利用 testing 调参。

## 5. RTL 覆盖与波形

抽样规则固定：每个划分取首、中、末分片，每个分片取前 24 个和末 24 个任务，共 18 作业、432 次任务。完整分片采用 `training/shard_0000` 的 6144 个任务。

两种作业重叠 48 个任务，因此每个仿真器执行 **6576 次**，对应 **6528 个独立任务**；两个仿真器不是把覆盖范围加倍。全部 1269948 个任务只有软件全量校验，不能宣称 RTL 全量通过。

TB 采用 `$fscanf` 流式读取，每次只缓存 64 对输入。支持 DATA_DIR、TASKS、SKIP_TASKS、LIMIT_TASKS 参数。跳过部分也读取并检查字符格式；所选任务逐个驱动 start/in/out 握手。除了数值答案，还检查接收计数、两拍输出反压保持、输出完成状态、任务超时、末尾多余数据。允许不同合法 shift 用于复用 TB，但本批软件预检要求 shift=12。

默认仅为三个划分的首分片前 24 个任务记录信号波形：

```text
training_shard_0000_skip0_count24.vcd / .wdb / .wcfg
validation_shard_0000_skip0_count24.vcd / .wdb / .wcfg
testing_shard_0000_skip0_count24.vcd / .wdb / .wcfg
```

其余作业不记录信号，XSim 可能仍产生很小的 WDB 元数据文件。完整分片与 `all` 模式默认关闭信号记录，以免大规模波形占用磁盘。

在 Vivado Tcl Console 打开实际运行目录中的文件：

```tcl
open_wave_database D:/IC_compeyition/Fast_coding/sim/batch_kwt1/<运行编号>/xsim/training_shard_0000_skip0_count24.wdb
open_wave_config D:/IC_compeyition/Fast_coding/sim/batch_kwt1/<运行编号>/xsim/training_shard_0000_skip0_count24.wcfg
```

在波形窗口将 x、w、accumulator、sum_with_bias、result 的 Radix 设为 Signed Decimal，查看 n（任务编号）、握手、accepted_count 和结果。仿真时钟为 10 ns，只用于功能验证，不等于完成频率验收。

## 6. 故障检测与兼容性

在已生成 Icarus 构建的本轮运行目录中执行：

```powershell
python .\scripts\test_batch_failures.py .\sim\batch_kwt1\<运行编号>
```

测试建立一个新的 `negative_tests` 子目录，仅修改自己的副本。软件侧检查缺文件、截断、错误答案、非法字符、padding、任务数和哈希；Icarus 直接绕过软件预检，检查 TB 的缺文件、截断、错误答案、X/Z、padding、字符宽度、任务范围和末尾多余数据，并带一个正常任务对照。测试目录已存在时不覆盖。

兼容入口保持不变：`run_real_kwt1.ps1`（原单样本 12 层）、`run_iverilog.ps1` 和 `run_xsim.ps1`（原人工回归）。原 1103 组回归继续承担正负数、极值、舍入/饱和边界、复位和暂停等定向覆盖。

## 7. 与 v1.1.0 的区别

| 项目 | v1.1.0 | 本次批量适配 |
|---|---|---|
| 数据 | 单样本 12 个任务 | 105829 个样本的 1269948 个任务 |
| 加载 | 单任务数组 | 七文件流式分片加载 |
| 软件 | 单样本 HEX/NPZ | 全部哈希、索引、分片、共享参数、浮点量化与整数答案 |
| RTL 验证 | 12/12 双仿真器 | 跨划分抽样 + 完整分片；提供全量入口 |
| 覆盖报告 | 逐层结果 | 区分作业次数、独立任务数、软件/RTL 覆盖 |
| 硬件 | 串行 64 项 MAC | 保持不变 |

实际本机验收结果见 `BATCH_KWT1_VERIFICATION.md`，不以交付包原有的 verification.json 或 RTL 日志代替本轮运行。本次以 v1.2.0 目录发布代码、文档和文本验收证据；全量数据与波形不纳入 Git。不扩展矩阵硬件、SoC 或模型训练。

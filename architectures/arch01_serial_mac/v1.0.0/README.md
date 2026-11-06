> 仓库版本说明：这是架构一 v1.0.0 的交接快照。完整 vectors 不重复纳入 Git，先运行 `python scripts/gen_vectors.py` 即可确定性生成全部 1103 组数据。文中 D: 盘路径是原作者工作区示例，队友应换成自己的克隆路径。

# KWT-1 数据提取与 HEX 导出交接说明

工程位置：`D:\IC_compeyition\Fast_coding\KWT1_HEX_handoff`。

**当前验证对象是一个长度为 64 的点积及其偏置、缩放、舍入、饱和处理，不是完整第一线性层加速器，也不是 SoC。** 本目录整合了原有代码、全部人工回归向量和新增的单任务导入示例。没有包含真实模型提取结果。

## 1. 现在应从模型提取什么？

对一个语音样本、一个编码器层，先保存目标前馈网络第一线性层的浮点张量：

| 张量 | 去掉 batch 维后的目标形状 | 内容 |
|---|---|---|
| X | `[99,64]` | 该线性层的实际输入；不是原始音频、MFCC，也不能直接用编码器入口代替 |
| W | `[64,256]` | 该线性层的 Dense kernel，需核对提取张量的维度 |
| b | `[256]` | 该线性层偏置 |
| Y_float | `[99,256]` | `X @ W + b` 的浮点参考，位于 GELU 之前 |

建议浮点原始张量保留为 **IEEE 754 float32 的 `.npy/.npz`**，另外保存样本标识、编码器层编号、张量名称和形状。浮点原始张量用于后续标定和误差分析，不能直接当作当前 RTL 的 HEX 输入。这里的 float32 是保存建议；本交接脚本不加载 TensorFlow checkpoint，也不执行模型推理。

第一阶段选择一个输出坐标 `(i,j)`：

```text
x[k] = X[i,k]     k=0…63
w[k] = W[k,j]     k=0…63
bias = b[j]
输出一个 Y[i,j]
```

需要给硬件的内容是 **64 个 x、64 个 w、1 个 bias，以及 1 个 shift 配置**。参考输出只供 testbench 比对，不送入 RTL。

同一硬件可以逐次跑完 `99×256=25344` 个点积来核对一层数值，但当前没有矩阵缓存、地址生成、权重 bank、CPU 或总线接口，因此不能把该测试称为完整矩阵加速器或 SoC 验证。

## 2. 位宽、尺度、舍入与参考答案

默认采用二次幂尺度，无零点偏移；全部硬件数据是补码整数，没有 IEEE 浮点接口。

| 数据 | 类型/有效位宽 | 实数与整数编码的关系 | 每任务数量 |
|---|---|---|---:|
| x | signed 16 | `x_real ≈ x_int × 2^-12` | 64 |
| w | signed 16 | `w_real ≈ w_int × 2^-12` | 64 |
| bias | signed 40 | `b_real ≈ b_int × 2^-24` | 1 |
| shift | unsigned 5 | 右移位数 0–31，默认 12 | 1 |
| total（参考） | signed 41 | `S = Σ(x_int*w_int)+b_int`，尺度 `2^-24` | 1 |
| result（参考） | signed 16 | `y_real ≈ result × 2^(shift−24)` | 1 |
| saturated（参考） | 1 bit | 数值转换时是否发生输出截限 | 1 |

内部乘积为 signed 32，纯点积累加为 signed 40；加偏置前扩展为 signed 41。默认 shift=12 时输出有 12 位小数。x/w/result 默认实数范围为 `[-8, 7.999755859375]`。

量化浮点 x/w 时先乘 `2^12`，偏置乘 `2^24`，再就近舍入、半值远离零，最后截限到各自有符号整数范围。导出器会报告 x/w/bias 的截限数量。**Python 默认 `round()` 的半值规则不同，不应直接用于这里的量化。**

输出答案必须从量化后的整数输入计算：

```text
S = sum(x_int[k] * w_int[k]) + b_int
shift=0: R = S
shift>0: R = sign(S) * floor((abs(S) + 2^(shift-1)) / 2^shift)
result = min(32767, max(-32768, R))
saturated = (R < -32768) or (R > 32767)
```

`total.hex/result.hex/saturated.hex` 都是 testbench 的参考数据。不能直接把 `Y_float × 4096` 舍入后作为整数硬件的精确答案：浮点输入、权重和偏置的量化误差会改变结果。

保留两套参照：①上述整数参考要求逐位一致；②原模型 float32 输出用于评估真实模型误差。新增导出器报告的 `floating_dot_python` 是 Python 重算值，**不是捕获的 TensorFlow float32 输出**。

## 3. 当前 HEX 格式与矩阵顺序

采用分文件、每行一个元素，无 `0x` 前缀。负数在各自有效位宽上取补码，左侧填 0 到所列十六进制字符数。

| 文件 | 有效数据位数 | 每行十六进制字符数 | 第 n 个任务的位置（从 0 起） |
|---|---:|---:|---|
| x.hex | 16 | 4 | 第 `64*n … 64*n+63` 个元素 |
| w.hex | 16 | 4 | 第 `64*n … 64*n+63` 个元素 |
| bias.hex | 40 | 10 | 第 n 个元素 |
| shift.hex | 5 | 2 | 第 n 个元素，仅低 5 位有效 |
| total.hex | 41 | 11 | 第 n 个元素，仅低 41 位有效 |
| result.hex | 16 | 4 | 第 n 个元素 |
| saturated.hex | 1 | 1 | 第 n 个元素，0 或 1 |

比如 signed 16 的 `1000` 表示整数 4096，即默认尺度下实数 1.0；`FFFF` 表示整数 -1，即实数 -1/4096。signed 41 的 -1 写作 `1FFFFFFFFFF`，而不是把所有 44 个文本位都置 1。`$readmemh` 读取数值元素，不涉及字节大小端；将来写 SRAM 二进制时才需另定字节顺序。

当前接口只定义点积序列，没有紧凑完整矩阵的加载器。若要导出整个线性层给当前逐任务格式，统一采用 **i 外层、j 内层、k 最内层**：

```python
for i in range(99):
    for j in range(256):
        # 任务 n = i * 256 + j
        x_task = X[i, :]      # 按 k 递增写 64 行
        w_task = W[:, j]      # 按 k 递增写 64 行
        bias_task = b[j]
        # 导出整数参考 total/result/saturated
```

这种格式会重复保存同一行 X、同一列 W 和偏置，但能直接匹配点积任务。**W 按列选取，无硬件转置、无分 bank。** 对固定 i，w 任务流的数值顺序等价于 `W.T` 的行主序展开；不要把 `W` 的行主序前 64 个元素直接当作权重列。

建议另存 float32 的紧凑矩阵档案，按常规 C 行主序：`X[i,k] → i*64+k`，`W[k,j] → k*256+j`，`Y[i,j] → i*256+j`。这是原始张量档案建议，不是现有 TB 的直接读取布局。不同语音样本、不同编码器层先分别保存，避免混淆。

## 4. 合并文件的起始地址

**目前没有合并 HEX 格式，也没有各部分的硬件起始地址。** 当前为七个独立文件，各自从数组下标 0 开始读取；这些数组下标不是 SoC 字节地址。

RTL 没有地址端口、SRAM 映射或 DMA。现有 `$readmemh` 读取器也不会自动拆分混合位宽文件。因此不要自行将几个文件直接拼接并赋予“官方起始地址”。第一阶段按上述分文件导出即可。未来合并文件时必须先约定统一存储字宽、对齐、padding、字节序和偏移单位，再同步修改读取器；SoC 基地址要在后续总线/存储方案确定后定义。

## 5. 已整合的代码与样例

| 本目录内位置 | 内容 |
|---|---|
| `rtl/dot64.sv`、`rtl/requantize.sv` | 从已验证工程复制的 RTL |
| `tb/tb_dot64.sv` | 原完整回归平台，含 64 对输入发送及自动检查 |
| `vectors/` | 原 1103 组人工/随机回归向量、名称表与 JSON 清单 |
| `scripts/gen_vectors.py` | 原整数参考模型、HEX 写入方法 |
| `scripts/run_xsim.ps1`、`run_iverilog.ps1` | 原完整回归运行脚本 |
| `scripts/create_vivado_project.tcl`、`waves.tcl` | 原回归工程/波形配置 |
| `tb/tb_single_hex.sv` | 新增：任意单任务七文件读取示例，不依赖原回归案例编号 |
| `scripts/export_dot_json.py` | 新增：已提取单任务浮点 JSON 转七个 HEX 文件 |
| `scripts/run_single.ps1` | 新增：用 Icarus 或 XSim 验证单任务 |
| `examples/single_dot_input.json` | 人工浮点样例，非真实 KWT 数据 |
| `examples/single_dot/` | 该人工样例的 HEX 与量化元数据 |
| `ORIGINAL_README.md`、`ORIGINAL_VERIFICATION.md` | 原工程说明与历史验证记录，里面的绝对路径指向原工程 |

样例为 64 个 `x=1.0`、64 个 `w=1/64`、bias=0、shift=12。HEX 中 x 每行 `1000`、w 每行 `0040`；参考整数结果为 4096（HEX `1000`），还原实数 1.0，未饱和。

### 运行人工样例或你提取的单任务

```powershell
Set-Location D:\IC_compeyition\Fast_coding\KWT1_HEX_handoff

# 重建人工样例 HEX；转换器仅需要 Python 标准库
python .\scripts\export_dot_json.py .\examples\single_dot_input.json .\examples\single_dot

# Icarus 验证
.\scripts\run_single.ps1

# Vivado 2018.3 XSim 验证
.\scripts\run_single.ps1 -Simulator xsim

# 工具不在 PATH 时显式指定
.\scripts\run_single.ps1 -Simulator xsim -ToolBin 'D:\FPGA\vivado_18_3\Vivado\2018.3\bin'
```

先将你已提取的某个 `(i,j)` 写成以下 JSON（x/w 数组必须各有 64 个数，示意省略号不能保留）：

```text
{"x": [64个浮点输入], "w": [64个浮点权重], "bias": 浮点偏置, "shift": 12}
```

然后执行：

```powershell
python .\scripts\export_dot_json.py .\my_dot.json .\examples\my_dot
.\scripts\run_single.ps1 -Simulator xsim -DataDir .\examples\my_dot
```

导出器固定使用 x/w 的 12 位小数和 bias 的 24 位小数，拒绝 NaN/Inf、非 64 长度和非法 shift；生成 `metadata.json` 记录截限数量和结果。它不做自动尺度标定，不提取 checkpoint，不生成 SoC 内存镜像。

单任务读取代码采用兼容 Vivado 2018.3 的写法，完整版本见 `tb/tb_single_hex.sv`：

```systemverilog
reg signed [15:0] xm[0:63], wm[0:63];
reg [8191:0] filename;
string data_dir;

// 放在 initial 内；目录通过 DATA_DIR plusarg 设置
$sformat(filename, "%s/x.hex", data_dir);
$readmemh(filename, xm);
$sformat(filename, "%s/w.hex", data_dir);
$readmemh(filename, wm);
```

读入后，先对 bias/shift 做 `start_valid && start_ready` 握手，再依 k=0…63 顺序送 x/w；只有 `in_valid && in_ready` 的上升沿才能推进 k。完整例子还检查参考 total、result、saturated、64 次计数及输出反压保持。

输出日志和波形分别在 `sim/single_iverilog/` 与 `sim/single_xsim/`。Vivado Tcl Console 查看单任务波形：

```tcl
open_wave_database D:/IC_compeyition/Fast_coding/KWT1_HEX_handoff/sim/single_xsim/single.wdb
add_wave -r /tb_single_hex/dut/*
```

### 运行原完整回归

```powershell
.\scripts\run_iverilog.ps1
.\scripts\run_xsim.ps1
```

原 `tb_dot64.sv` 会复用编号 3–6 的人工案例并检查所有 shift 覆盖，不能把它的 vectors 直接替换成一个真实样本。单任务请使用新增 `tb_single_hex.sv`；原回归数据保持不变。所有样例与代码是此次整合时的快照，原工程后续修改不会自动同步到本目录。

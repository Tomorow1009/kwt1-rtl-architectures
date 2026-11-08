# Arch03 数值格式与通用数据入口

本接口支持任意有限的完整 `X[99,64]`、`W[64,256]`、`b[256]`，层号为 1–12。
固定 Q12 基线，不从参考答案反推结果，不训练或拟合尺度。超出表示范围的有限实数按下表饱和编码并报告次数；NaN、Inf、错误形状及非法整数位宽直接拒绝。

| 数据 | 有符号位宽 | 小数位 | 实数解码 |
|---|---:|---:|---|
| X、W | 16 | 12 | 整数 × 2^-12 |
| b | 40 | 24 | 整数 × 2^-24 |
| 64 点积累加 | 40 | 24 | 整数 × 2^-24 |
| 点积加偏置 | 41 | 24 | 整数 × 2^-24 |
| 输出 | 16 | 24−shift | 整数 × 2^(shift−24) |

`shift` 是 0–31 的整数，默认 12；例如 shift=31 时输出小数位为 −7，仍能有限解码。
实数编码和输出转换均使用最近舍入，恰好半值时远离零。输出先对绝对值加 `2^(shift−1)` 再右移、恢复符号，最后限制到 −32768…32767；shift=0 不加舍入项。
合法 64 项 int16 乘积和不会溢出 40 位，加 int40 偏置不会溢出 41 位。Python 模型用 int64 表达这些严格有界的运算，不依赖 Python 的无限精度掩盖 RTL 溢出。

## 输入流与存储

硬件 `LOAD` 流共 **23,488 个 16 位字（46,976 字节）**：

1. 先传 X，行优先，`row=0..98, k=0..63`，共 6,336 字。
2. 对每个列组 `g=0..31`，先传 512 字 W：`k=0..63, lane=0..7`，对应 `W[k,g*8+lane]`。
3. 同组随后传 8 个偏置，每偏置 3 字：位 15:0、31:16、39:32。第三字的高 8 位必须为零；它不是 48 位符号扩展。负值按 40 位补码拆分。

`load.bin` 是上述字流的小端二进制；`load.hex` 每行一个 4 位十六进制字。MMIO LOAD 写入 32 位时高 16 位为零，写掩码为 1111，遵守 `load_ready`。
解包器对全部矩阵与偏置做反向检查。

输出调度为列组 → 行 → lane；完整存储输出为 99×256 行主序，索引 `row*256+column`。实际 CSV 为 `index,signed_int16[,saturated]`，每坐标必须恰好一次。OUTPUT 寄存器的位域及错误恢复详见 [MMIO 说明](README.md#mmio-接口)。

| 位置 | 地址 | 用途 |
|---|---|---|
| 固件与测试源 | ITCM 0x80000000；源流 0x80010000 | CPU 实际读取、复制；不是计算结果 |
| shift 元数据 | 0x8000FFF0 | 每次镜像的移位配置 |
| 共享 SRAM | 0xA0000000–0xA007FFFF | 512 KiB，ICB 字节掩码 |
| 输入缓冲 | 0xA0000000 | 46,976 字节 |
| 输出缓冲 | 0xA000C000 | 50,688 字节 |
| 结果邮箱 | 0xA001F000 | 状态、计数、周期、饱和数 |

CONTROL=1 启动；CONTROL=2 中止并清空任务控制/计数，SRAM 单元不作物理清零。新任务必须完整重装 X/W/b。
设备 done 表示最后结果已被 MMIO 消费；正式软件完成还需全部输出成功写回及 fence。源准备、任务缓存失效、实际装载和完整计时边界须在 CPU/功耗验收时另外验证。

## 编码与实际输出解码

从仓库根运行，Python≥3.8、NumPy；`python` 指向实际环境。输出目录必须不存在。

```text
python workspaces/arch03/scripts/numeric.py encode input.npz --layer 7 --sample-id new_input --shift 12 --output local_runs/new_input
python workspaces/arch03/scripts/numeric.py decode actual.csv --codec local_runs/new_input/codec.json --output local_runs/decoded.npz
```

`input.npz` 需要 X/W/b，不需要 Y。`codec.json` 记录格式、尺度、截限数、输入哈希和生成文件哈希；`layout.json` 保持原测试台/固件生成器兼容性。解码生成 Y_decoded、result_int 和可选饱和标志，旁附 JSON 回执记录配置与捕获哈希。

`expected.npz`、`total.hex`、`result.hex`、`saturated.hex` 仅供测试检查。实际固件生成器只读取 `load.hex` 和 shift，把输入源写入初始 ITCM 镜像；加速器计算路径不读取任何参考输出。

## 完整开发集评估与复现

使用既有 Python 3.8.20、TensorFlow 2.4.0、NumPy 1.19.5 环境，依赖上游 keyword-transformer 和 Speech Commands v0.02。上游核验回执锁定 `237e4097afd4f6851e0b82f0a8d65c2dfe8eae30` 的 36 个关键文件及 best_weights。

```text
python workspaces/arch03/scripts/full_matrix_eval.py --model-root ../keyword-transformer --data-root ../data2/speech_commands_v0.02 --upstream-receipt ../model_data/upstream_verification.json --output local_runs/full_matrix_new
python workspaces/arch03/scripts/prepare_precision_cases.py local_runs/full_matrix_new/evaluation.json --output local_runs/precision_cases_new
```

开发集按种子 20261109 的 SHA256 顺序从 validation_list 选择：10 个目标词各 50 条、其他语音 99 条、全零静音 1 条，共 600 条。静音遵循上游验证模式的前景静音和不混背景逻辑，只计一次相同波形。它不是官方分布，也不是官方评测数据。没有使用 testing 样本，没有训练、增强、Dropout 或尺度拟合。未来需要校准时只能使用训练划分。

每次浮点前向捕获每层真实 Dense 输入及完整输出；不会把前一 FC1 输出当作下一层输入。输出保存原始 X/Y、共享 W/b、音频、logits、来源和运行环境哈希。全部变量逐数组核对 checkpoint；全部 FC1 输出另以 float64 矩阵复算检查位置/方向。首次样本检查原模型 logits、确定性和 PCM 解码一致性。

NRMSE = sqrt(SSE/N) / max(sqrt(reference_energy/N), 1e-8)。每层先累加全部样本 SSE/能量，再算比例；同时报告每任务误差。工具采用更严格规则：层汇总和全部开发任务都 ≤3% 才返回通过。`evaluate.py` 的实际 RTL 捕获路径另检查完整坐标、整数逐位一致、可用饱和标志和配置尺度，不生成假捕获。

`prepare_precision_cases.py` 会重读并校验所有 600 份完整捕获，用独立原有整数实现逐位复算，再导出 12 层、最差误差、最大输入/输出幅值和零值/抵消/shift 0/31 向量。此步骤仍是软件验证；RTL 或 CPU 必须真实运行。

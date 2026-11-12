# 小数位数优化后的语音数据：服务器前20条

更新：2026-11-12。配套说明：[未重排转换脚本](SHIFT16_CONVERTER.md)。

## 服务器地址及完成范围

```text
/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_new
```

已上传并验证 `sample_001`～`sample_020`，每条 `layer_01`～`layer_12`，共240层、960个HEX文件。第1条第1层示例：

```text
/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_new/sample_001/layer_01/
```

本次在Workspace 4通过VNC完成传输；服务器返回 `BATCH_OK 20`，再次逐文件核对集合、字节数、原始SHA-256后返回 `PARTIAL_AUDIT_PASS 20 240 960`。证据位于根目录 `original_sha256.json`、`transfer_progress.json`、`partial_audit_020.json`。原始清单覆盖计划中的100条，**不表示100条都已上传**；当前只确认前20条，已按要求停传。

本地完整100条来源：

```text
D:\转换脚本\KWT1_WORST100_20261109\KWT1_WORST100_HEX_SHIFT16\KWT1_WORST100_HEX_SHIFT16
```

这些是冻结数值配置扫描所得最差100条中的前20条，不是最初Q12验证包的同编号语音。旧Q12服务器目录 `/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex` 保留不动。不要用两批不同语音直接比较量化改善；比较精度应使用相同浮点输入和权重。

## 数据代表什么

每条语音由官方模型完整推理，提取12个编码模块各自内部的FFN1输入，构成12个独立矩阵测试任务：

`X[99,64] × W[64,256] + b[256] → Y[99,256]`。

同一层的W/b在不同语音间相同；12层之间的W/b各自独立。不能将第1层FFN1的输出直接送入第2层FFN1。这些数据不是完整编码器或整模型分类结果，也不是“赛题强制一条语音定义为12个任务”的结论。

## 每层真正使用的四个文件

| 文件 | 行数 / 每行HEX位数 | 用途 |
|---|---:|---|
| `load.hex` | 23488 / 4 | DUT实际输入，含完整X、W、b |
| `result.hex` | 25344 / 4 | 舍入、饱和后的signed16参考结果 |
| `total.hex` | 25344 / 11 | 右移前signed41整数和参考，高3位保留为0 |
| `saturated.hex` | 25344 / 1 | 每个输出是否发生饱和，0或1 |

三个参考文件仅供testbench比较，不能作为DUT计算输入。服务器没有逐层 `layout.json`、NPZ或BIN；文件完整性依据根目录原始哈希清单。每层25344个输出，单语音304128个，前20条合计6082560个；这是待RTL验证规模，不是本轮已执行的RTL通过数。

## 冻结数值协议与装载布局

| 参数 | 位宽 | 小数位 |
|---|---:|---:|
| X | signed16 | F12 |
| W | signed16 | F16 |
| b | signed40 | F28 |
| 累加器 / total | signed40 / signed41 | F28 |
| result | signed16 | F12 |

`SHIFT = Fx + Fw - Fy = 12 + 16 - 12 = 16`。右移使用就近舍入、半值远离零，再饱和到[-32768,32767]；result解码为整数除以4096。

这里“未重排”是**未额外做tile16/ICB32布局转换**，仍使用原arch02的8列分组协议：先6336个X字（行优先），再32组；每组512个W字（k优先、8个lane）和24个偏置字。每个偏置分低16、中16、高8位三个字，最后一字高8位填0。合计6336+32×536=23488个16位字。

三个参考文件按行优先，索引为 `row*256+column`；RTL输出可能按group→row→lane，须按坐标比较，不能把输出流直接reshape成参考矩阵。

## 如何切换测试

1. 使用同一层目录的全部四个新HEX。
2. 在启动握手时传入 `shift=16`。仓库 `workspaces/arch02/arch02/tb/tb_arch02.sv` 已支持运行参数 `+SHIFT=16`；第二个连续任务另用 `+SECOND_SHIFT=16`。
3. 检查运行脚本确实将参数传到仿真程序，未被默认12覆盖。若自定义testbench不解析plusarg，须适配testbench或驱动；仅写命令参数不会自动生效。
4. 装载布局和可配置shift接口一致时，不需要改MAC硬件位宽或重新生成HEX。tile16专用装载器不能靠SHIFT兼容本包。
5. 先1层，再单条12层，最后前20条240层；每层检查25344个坐标无遗漏/重复，total、result、saturated逐位一致。

已编译原testbench的VCS运行示意（`./simv`须先用实际工程编译）：

```sh
./simv +DATA_DIR=/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_new/sample_001/layer_01 +SHIFT=16 +OUTPUT_FILE=sample001_layer01_shift16.csv
```

本轮完成软件重建与传输完整性验证，没有执行这些20条的新RTL/SRAM/SoC仿真，也未完成官方600条或整模型精度验收。

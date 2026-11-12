# 新版固定16位转换脚本说明（未重排，SHIFT=16）

配套数据：[服务器前20条数据说明](SHIFT16_DATA20.md)。脚本：[convert_kwt1_fixed16.py](../../../tools/kwt-fixed16-unreordered/convert_kwt1_fixed16.py)。

本次归档本地 `D:\转换脚本\convert_kwt1_fixed16.py` 的原始字节，不改变算法。SHA-256：`444a0ca35175fc48aebe6a23069848fbc89a6d5baaaae0d95e0f1ece9a3f404d`。

它将已从官方模型提取的**完整浮点FFN1矩阵**量化并生成arch02原8列分组HEX。不是tile16重排脚本，不生成load32.hex，不训练模型，也不直接读取WAV。无需TensorFlow；需要Python和NumPy（原使用环境Python3.8/NumPy1.19.5；代码按Python3.6+语法编写，安装与解释器相容的NumPy）。

## 一条语音的命令

在仓库根目录运行：

```sh
python tools/kwt-fixed16-unreordered/convert_kwt1_fixed16.py --sample float_tensors.npz --weights shared_weights.npz --out NEW_HEX_DIRECTORY
```

| 参数 | 应传入什么 |
|---|---|
| `--sample` | 一条语音的浮点NPZ：必需键X，形状[12,99,64]；可选键Y，形状[12,99,256] |
| `--weights` | 共享浮点NPZ：W[12,64,256]、b[12,256]；同一模型的各语音可共用 |
| `--out` | 尚不存在的新输出目录，不是输入路径，也不是ZIP文件名 |

路径包含空格时加引号。W方向为输入维×输出维；不可盲目转置。Y是官方浮点FFN1参考值，仅用于量化误差统计；即使没有Y，也能从X/W/b生成全部整数参考。原始音频须先通过匹配的官方模型和checkpoint提取矩阵，不能直接给本脚本一个WAV或不完整的点积包。

一次调用转换一条语音的完整12层。批量时逐个传不同的sample文件和新的输出子目录，所有语音共用同一个weights文件。已有服务器HEX可直接测试，无须重跑转换。

## 转换规则与输出

固定X signed16/F12、W signed16/F16、b signed40/F28、total signed41/F28、result signed16/F12；SHIFT=16。浮点编码为乘2^F、就近舍入（半值远离零）、有符号饱和。整数矩阵乘加后按相同规则右移16并饱和到signed16。

原版Q12的W F12、b/total F24、SHIFT12改为W F16、b/total F28、SHIFT16；X和结果仍F12，硬件位宽保持不变。旧HEX不能仅改SHIFT变成新HEX：必须换用整套新load及参考结果。

输出目录包含 `layer_01`～`layer_12`，每层：

- `load.hex`：23488个16位字，真正交给DUT；沿用8列分组装载协议。
- `result.hex`、`total.hex`、`saturated.hex`：各25344个参考值，行优先排列。
- `expected.npz`：上述整数参考矩阵。
- `layout.json`：层号、格式、SHIFT、文件哈希。
- `hex_check.json`：HEX回读、整数重算、裁剪及饱和统计；提供浮点Y时也记录误差。

根目录 `manifest.json` 记录输入和脚本哈希、12层检查及304128个输出。`PASS`只表示软件转换检查通过，不表示RTL或比赛验收通过。脚本内 `RTL_COMMIT=8aa230...` 是历史协议来源，不表示自动兼容未来任何RTL。

上传服务器用于当前testbench时，每层只需四个HEX。若仅复制HEX而未复制expected.npz，不要保留要求校验该NPZ的原layout.json；当前 `hex_new` 使用根目录清单并显式给定SHIFT16。

## 检查服务器精简目录

假设在脚本所在目录、环境已有NumPy：

```sh
python -c 'import convert_kwt1_fixed16 as c; print(c.check_hex_task("/storage2/2026contest/server4/s4_21usr/Desktop/IC/hex_new/sample_001/layer_01", shift=16))'
```

完整生成目录存在layout.json时会读其中SHIFT及文件哈希；精简目录没有layout.json时必须显式 `shift=16`。服务器不需要安装NumPy才能运行RTL仿真，以上是可选的软件复核命令。

## 官方只给一层浮点数据时

数学上可以转换，但现有命令行入口要求完整12层，不能给它单层NPZ，也不能复制或补零凑12层。可调用同文件提供的单层接口（需准备真实X/W/b和真实层号）：

```python
from pathlib import Path
import numpy as np
import convert_kwt1_fixed16 as c

with np.load("one_layer.npz", allow_pickle=False) as d:
    # X[99,64], W[64,256], b[256]；Y[99,256]可选
    c.export_layer(Path("NEW_LAYER_DIRECTORY"), d["X"], d["W"], d["b"],
                   dict(c.DEFAULT_FORMAT), layer=2,
                   reference=d["Y"] if "Y" in d else None)
```

示例层号2必须改为实际层号。若官方数据键名、形状或文件格式不同，先写可复现的读取适配，不猜测数据含义。只有X但没有相应W/b时不足以计算。

## 接入RTL时最重要的设置

testbench启动参数用 `+SHIFT=16`；第二个连续任务用 `+SECOND_SHIFT=16`。驱动在start握手时给DUT的shift输入传16。保持舍入、饱和、偏置填充和装载顺序不变；支持这些条件的现有RTL无需改数据通路。

低层Python函数 `ffn1_int`、`dot64_int`、`requantize` 保留历史默认shift=12；**手动调用它们时务必显式传 `shift=16`**。正常转换入口根据Fx+Fw-Fy自动传16，不受该历史默认值影响。

输出比对按 `row*256+column` 定位，检查total/result/saturated全部逐位一致。实际RTL运行入口与这里的仿真示意有差异时，应先阅读当前testbench和启动脚本，不把“命令带了SHIFT”当成已正确配置。

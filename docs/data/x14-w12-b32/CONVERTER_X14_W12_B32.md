# X14/W12/b32 转换脚本说明

2026-11-12。配套数据说明：[30条缩位宽HEX](DATA30_X14_W12_B32.md)。本地脚本与本文同目录；Git脚本位置为 `tools/kwt-x14-w12-b32/convert_kwt1_x14_w12_b32.py`。

## 固定方案

全部12层使用相同参数，不重新训练、不按新误差调参、不做tile16重排。由原始浮点矩阵重新量化，不能简单截断旧HEX。

| 对象 | 有符号总位宽 | 二进制小数位 |
|---|---:|---:|
| X | 14 | 10 |
| W | 12 | 12 |
| X×W | 26 | 22 |
| 64项累加器 | 32 | 22 |
| b | 32 | 22 |
| total（累加器+b） | 33 | 22 |
| result | 16 | 12 |

位宽包含符号位。`SHIFT=10+12-12=10`，浮点量化及输出右移均采用就近舍入、半值远离零；输出饱和到signed16。X/W/b超出范围时量化饱和并记录裁剪数。每个合法乘积绝对值不超过2^24，64项前缀绝对值不超过2^30，signed32累加器足够；加signed32偏置使用signed33。

这套配置与旧Q12（SHIFT12）、优化小数位数但仍16位的版本（SHIFT16）不同。使用新HEX时必须匹配缩位宽RTL和SHIFT10，不能沿用SHIFT16。

## 运行方式

需要Python和NumPy；本次实测Python3.8/NumPy1.19.5。代码兼容Python3.6+语法，其他环境需安装匹配版本的NumPy；不需要TensorFlow。

从已有最差100条的浮点ZIP直接选**原榜单前30条**，不全量解压、不重排排名：

```powershell
python convert_kwt1_x14_w12_b32.py --archive "D:\转换脚本\KWT1_WORST100_20261109\KWT1_WORST100_ORIGINAL_FLOAT.zip" --out "D:\转换脚本\hex_short\hex_reproduced"
```

`--archive`是完整原始浮点包，不是HEX ZIP；`--out`必须是不存在或空目录。已有内容会拒绝覆盖；失败时不产生完成标记，保留未完成目录供诊断。完成必须同时检查退出码为0及manifest的status=passed。

单条完整12层浮点数据也可转换：

```sh
python convert_kwt1_x14_w12_b32.py --sample float_tensors.npz --weights shared_weights.npz --out NEW_DIRECTORY
```

| 参数 | 输入要求 |
|---|---|
| --sample | NPZ键X[12,99,64]；可选Y[12,99,256]，用于与官方浮点输出比较 |
| --weights | NPZ键W[12,64,256]、b[12,256]，同层参数在语音间共享 |
| --out | 新输出根目录；单条模式生成sample_001/layer_01～12 |

脚本不接受WAV；原始音频需先经官方模型提取完整FFN1矩阵。本次直接使用已有浮点数据，无需再次提取。

官方仅给某一层时，可以调用单层API，不能复制或补零凑12层：

```python
import numpy as np
import convert_kwt1_x14_w12_b32 as c
with np.load("one_layer.npz", allow_pickle=False) as d:
    c.export_layer("NEW_LAYER_DIRECTORY", d["X"], d["W"], d["b"],
                   layer=2, y=d["Y"] if "Y" in d else None)
```

要求X[99,64]、W[64,256]、b[256]，可选Y[99,256]，示例层号2替换为实际层号。若官方键名或布局不同，先明确适配，不能猜测。

## 与RTL约定的文件编码

外部ICB保持32位、SRAM字保持16位。此脚本仅生成原8列分组的16位装载字，不定义SoC地址映射或ICB双字打包。

`load.hex`每层仍23488行、每行4个HEX字符：

1. X的6336个字，行优先。X14符号扩展到16位。
2. 32个8列组，每组512个W字（k→lane），W12符号扩展到16位。
3. 每组紧接8个偏置，每个仍占3字：b32先符号扩展到40位，再发送低16、中16、高8位；第三字高8位必须为0。

例：b整数为-1，三字为 `ffff ffff 00ff`；b整数为+1，为 `0001 0000 0000`。第三字只有 `0000` 或 `00ff`，由bit31决定。RTL应检查扩展正确后按signed32取值，不把第三字计入更高精度。

| 参考文件 | 位宽 / 每行字符 | 行数 | 解释 |
|---|---|---:|---|
| result.hex | signed16 / 4 | 25344 | 右移10并舍入饱和后的结果；除4096还原数值 |
| total.hex | signed33 / 9 | 25344 | 加偏置后的原始整数；除2^22还原数值 |
| saturated.hex | 1 / 1 | 25344 | 输出是否饱和，0或1 |

total采用33位补码，第33位是符号位，9个HEX字符中多余高3位为0。例如-1是 `1ffffffff`，不是旧41位的 `1ffffffffff`。testbench应声明signed[32:0]接收；若需要与更宽信号比较，先显式符号扩展，不能直接将9字符文件读入41位而期待自动符号扩展。

参考文件按row→column；RTL输出流若按group→row→lane，必须按 `row*256+column` 比对。三个参考文件不进入DUT计算。每层另有layout.json（格式、哈希）和hex_check.json（回读及误差），不生成NPZ/BIN或复制原始音频。

## 校验及硬件交接

```sh
python convert_kwt1_x14_w12_b32.py --check "<数据根目录>/sample_001/layer_01"
```

检查严格格式、字数、X/W符号扩展、b32扩展与填充、累加前缀范围、signed33总和及全部total/result/saturated。生成参考使用矩阵乘法，回读检查独立解码并逐k累加。根目录保存manifest.json及SHA256_FILES.json。

本次边界检查通过：正负半值及相邻值、输出正负饱和、极值MAC、负偏置、非法X/W扩展、非法偏置填充、截断HEX、旧位宽total文件。第一批30条的详细结果见配套说明。

**本次只交付转换脚本和数据，没有修改RTL。** 后续需实际缩小乘法器/累加器/b/total位宽，正确处理SV有符号表达式与加法扩位，testbench改为33位total，并在任务启动时传SHIFT10。仅修改SHIFT不能实现硬件位宽缩减。若连续任务使用SECOND_SHIFT，也需设10；旧数据仍保留旧SHIFT配置。

脚本SHA-256：`c99301b68185f599b95e4b4b3cbe5e62db27128dcf3cf04e4725bdb9a5620c35`。
